#!/usr/bin/env python3
"""v26 withholding-cost pilot: raw vs allowed-form vs refusal under a benign service.

Design (see experiments/withholding-cost-pilot/DESIGN.md):
- the ConVerse service agent runs with the upstream *benign* prompt plus an adapter
  that states the benchmark's own attack_rationale as the reason it needs the item;
- per (case, seed) one shared prefix runs until the service first asks for the item
  (marked by its <item_request> field);
- the assistant's next message is then replaced by a fixed reply that differs only in
  the variant span (raw value / allowed form / refusal [/ existence only]);
- each variant continues from an identical copy of the prefix with a matching
  disclosure rule for Main, until Main completes or max_turns.

No Gate and no privacy suffix are used. Helpers are imported from
run_ci_gate_pilot.py unchanged. --mock replaces every model with a scripted client
and disables the network; nothing in this file sends a request unless --mock is
absent and --dry-run/--estimate/--check-config are absent.
"""

from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import os
import re
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

# `python3 -I` drops the script directory from sys.path; add only this directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_ci_gate_pilot as base
from run_ci_gate_pilot import (
    ChatClient,
    acquire_output_root_lock,
    atomic_write_json,
    call_messages_until_formatted,
    call_validated_main_turn,
    configure_ollama_request_controls,
    file_sha256,
    format_assistant_history,
    import_upstream_prompts,
    load_case_inputs,
    read_json,
)
import importlib

import score_withholding_cost_pilot as scoring

REPO = Path(__file__).resolve().parents[2]
SCHEMA = "withholding-cost-episode-v26"  # v26 default; versioned per config by schema_names()
ITEM_TAG = "item_request"
ASSUME_TAG = "service_assumptions"
ALL_VARIANTS = ("raw", "allowed", "refuse", "existence_only")
EXTRA_VARIANTS = ("coarser",)  # v27b; needs a per-case statement in the cases file


# --------------------------------------------------------------------------- config


def load_config(path: Path) -> dict[str, Any]:
    config = read_json(path)
    config["models"]["request_timeout_seconds"] = config["runtime"]["request_timeout_seconds"]
    return config


def config_version(config: dict[str, Any]) -> str:
    """'v26' for withholding-cost-pilot-v26, 'v27' for -v27, ..."""
    return str(config.get("schema_version", "withholding-cost-pilot-v26")).rsplit("-", 1)[-1]


def schema_names(config: dict[str, Any]) -> dict[str, str]:
    version = config_version(config)
    return {"episode": f"withholding-cost-episode-{version}", "prefix": f"withholding-cost-prefix-{version}"}


def scorer_for(config: dict[str, Any]) -> Any:
    """Scoring module named by config scorer_module; v26 configs (no field) keep the v26 scorer."""
    return importlib.import_module(config.get("scorer_module", "score_withholding_cost_pilot"))


def date_oracle_for(config: dict[str, Any], cases_doc: dict[str, Any], check: dict[str, Any]) -> dict[str, Any]:
    return scorer_for(config).date_oracle(cases_doc, check)


def oracle_label(config: dict[str, Any], cases_doc: dict[str, Any], check: dict[str, Any]) -> Any:
    if check["type"] == "date_window_avoid":
        return date_oracle_for(config, cases_doc, check)
    if check["type"] == "plan_option":
        return [a["option"] + (f" @ {'/'.join(a['field'])}" if a.get("field") else "") for a in check["any_of"]]
    return check.get("targets") or check.get("label") or check.get("patterns")


def check_credentials(config: dict[str, Any]) -> dict[str, Any]:
    """Enforce the per-key concurrency limits; returns a summary for the manifest.

    With credentials.ollama_key_pool (the judge-test pool: key <= 3, key2 <= 7), every pool entry must name a key
    in ollama_key_concurrency_limits, stay within its limit, and the pool capacities must sum to
    models.max_concurrent_requests (run_ci_gate_pilot.configure_ollama_request_controls also checks the sum).
    Without a pool, the single key ollama_key_name is used with max_concurrent_requests <= its limit.
    """
    creds = config["credentials"]
    limits = creds.get("ollama_key_concurrency_limits", {})
    concurrency = int(config["models"]["max_concurrent_requests"])
    pool = creds.get("ollama_key_pool") or []
    if pool:
        entries = []
        for entry in pool:
            key_name = str(entry["key_name"])
            capacity = int(entry["max_concurrent_requests"])
            if key_name not in limits:
                raise SystemExit(f"ollama_key_pool key_name={key_name!r} has no entry in ollama_key_concurrency_limits")
            if capacity < 1 or capacity > int(limits[key_name]):
                raise SystemExit(f"ollama_key_pool capacity {capacity} exceeds the limit {limits[key_name]} for key {key_name!r}")
            entries.append({"alias": str(entry["alias"]), "key_name": key_name, "max_concurrent_requests": capacity})
        names = [e["key_name"] for e in entries]
        if len(set(names)) != len(names):
            raise SystemExit("ollama_key_pool lists a key more than once")
        total = sum(e["max_concurrent_requests"] for e in entries)
        if concurrency != total:
            raise SystemExit(f"models.max_concurrent_requests={concurrency} must equal the key-pool capacity {total}")
        return {"ollama_key_pool": entries, "max_concurrent_requests": concurrency}
    key = creds["ollama_key_name"]
    if key not in limits:
        raise SystemExit(f"credentials.ollama_key_name={key!r} has no entry in ollama_key_concurrency_limits")
    if concurrency < 1 or concurrency > int(limits[key]):
        raise SystemExit(
            f"models.max_concurrent_requests={concurrency} exceeds the limit {limits[key]} for key {key!r}"
        )
    return {"ollama_key_name": key, "max_concurrent_requests": concurrency, "key_limit": int(limits[key])}


def selected_variants(config: dict[str, Any], args: argparse.Namespace) -> list[str]:
    # run_variants (v27b): the variants this config runs; config["variants"] still lists every variant to score.
    variants = list(config.get("run_variants") or config["variants"])
    if args.with_existence_only and "existence_only" not in variants:
        variants.append("existence_only")
    if args.variant:
        variants = [v for v in variants if v == args.variant]
    return variants


def read_cases_doc(config: dict[str, Any]) -> dict[str, Any]:
    """The config's cases file. A v27b-style file (base_cases_file + coarser) is merged onto its base file:
    every base key is kept, and cases are the base specs that have a coarser statement, each with a
    'coarser' field added. Plain cases files are returned unchanged."""
    doc = read_json(REPO / config["benchmark"]["cases_file"])
    if "base_cases_file" not in doc:
        return doc
    base_doc = read_json(REPO / doc["base_cases_file"])
    merged = copy.deepcopy(base_doc)
    statements = doc["coarser"]
    known = {c["case_id"] for c in base_doc["cases"]}
    unknown = sorted(set(statements) - known)
    if unknown:
        raise SystemExit(f"coarser statements for cases not in the base cases file: {unknown}")
    merged["cases"] = [{**copy.deepcopy(c), "coarser": statements[c["case_id"]]}
                       for c in base_doc["cases"] if c["case_id"] in statements]
    merged["coarser_doc"] = {k: v for k, v in doc.items() if k != "coarser"}
    return merged


def load_cases(config: dict[str, Any], args: argparse.Namespace) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    split = read_json(REPO / config["benchmark"]["split_manifest"])
    by_id = {c["case_id"]: c for c in split["cases"]}
    cases_doc = read_cases_doc(config)
    pairs = []
    for spec in cases_doc["cases"]:
        if spec["case_id"] not in by_id:
            raise SystemExit(f"unknown case_id in cases file: {spec['case_id']}")
        pairs.append((by_id[spec["case_id"]], spec))
    if args.case_id:
        pairs = [p for p in pairs if p[0]["case_id"] == args.case_id]
        if not pairs:
            raise SystemExit(f"case not in pilot cases file: {args.case_id}")
    if args.limit_cases is not None:
        pairs = pairs[: args.limit_cases]
    return pairs


def raw_value(case: dict[str, Any]) -> str:
    return "; ".join(x.strip() for x in case["raw_data"] if x.strip())


def fill(template: str, case: dict[str, Any], inputs: dict[str, str] | None = None,
         spec: dict[str, Any] | None = None) -> str:
    if "{coarser_form}" in template:
        text = ((spec or {}).get("coarser") or {}).get("text")
        if not text:
            raise SystemExit(f"no coarser statement for {case.get('case_id')}")
        template = template.replace("{coarser_form}", text.strip().rstrip("."))
    values = {
        "data_item": case["data_item"],
        "data_item_lc": case["data_item"].lower(),
        "raw_value": raw_value(case),
        "allowed_form": case["acceptable_abstraction"].strip().rstrip("."),
        "attack_rationale": case["attack_rationale"],
        "external_role": (inputs or {}).get("external_role", "service provider"),
    }
    out = template
    for key, value in values.items():
        out = out.replace("{" + key + "}", value)
    return out


def injected_message(config: dict[str, Any], case: dict[str, Any], variant: str,
                     spec: dict[str, Any] | None = None) -> str:
    inj = config["injection"]
    return fill(inj["lead_in"] + inj["templates"][variant] + inj["closing"], case, spec=spec)


def read_prompt(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


# --------------------------------------------------------------------------- seeds


_SEED_LOCAL = threading.local()


class _SeededRequests:
    """Adds Ollama options.seed from a thread-local value; used only in sampling.mode=seeded."""

    def __init__(self, real: Any) -> None:
        self._real = real
        self.HTTPError = real.HTTPError
        self.RequestException = real.RequestException

    def post(self, url: str, **kwargs: Any) -> Any:
        seed = getattr(_SEED_LOCAL, "seed", None)
        payload = kwargs.get("json")
        if seed is not None and isinstance(payload, dict) and "options" in payload:
            kwargs["json"] = {**payload, "options": {**payload["options"], "seed": int(seed)}}
        return self._real.post(url, **kwargs)


class _NoNetwork:
    class HTTPError(Exception):
        pass

    class RequestException(Exception):
        pass

    def post(self, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("network access is disabled in --mock mode")


def apply_sampling(config: dict[str, Any]) -> None:
    sampling = config.get("sampling", {})
    if sampling.get("mode", "repeat_t0") == "seeded":
        for role in ("main", "external", "environment"):
            config["models"][role]["temperature"] = float(sampling["seeded_temperature"])
        base.requests = _SeededRequests(base.requests)
    elif sampling.get("mode", "repeat_t0") != "repeat_t0":
        raise SystemExit(f"unknown sampling.mode {sampling.get('mode')!r}")


# --------------------------------------------------------------------------- mock


class MockClient:
    """Scripted stand-in for every role. Deterministic; no network."""

    def __init__(self, case: dict[str, Any], spec: dict[str, Any], cases_doc: dict[str, Any], config: dict[str, Any]):
        self.case = case
        self.spec = spec
        self.cases_doc = cases_doc
        self.config = config
        self.usage: list[dict[str, Any]] = []

    def call(self, role: str, messages: list[dict[str, str]], *, json_mode: bool = False) -> str:
        text = self._respond(role, messages)
        prompt_chars = sum(len(m.get("content", "")) for m in messages)
        self.usage.append({
            "role": role, "provider": "mock", "model": "mock",
            "prompt_tokens": prompt_chars // 4, "completion_tokens": len(text) // 4,
            "done": True, "done_reason": "stop",
        })
        return text

    # -- helpers
    def _variant_in(self, history: str) -> str | None:
        for variant in self.config["injection"]["templates"]:
            if injected_message(self.config, self.case, variant, self.spec) in history:
                return variant
        return None

    def _oracle_offer(self) -> str:
        check = self.spec["check"]
        if check["type"] == "date_window_avoid":
            first = date_oracle_for(self.config, self.cases_doc, check)["feasible_windows"][0]
            start, end = (datetime.date.fromisoformat(x) for x in first.split(".."))
            return f"dates {start.strftime('%B')} {start.day}-{end.day}, 2024"
        if check["type"] == "regex_any":
            return "purchase window Q1 (January 15 - March 31)"
        if check["type"] == "plan_option":
            first = check["any_of"][0]
            return first["option"] + (f" ({first['field'][0]})" if first.get("field") else "")
        return check["targets"][0]

    def _sufficient(self, variant: str) -> bool:
        return variant == "raw" or (variant == "allowed" and self.spec.get("allowed_form_sufficient_a_priori") is True)

    def _respond(self, role: str, messages: list[dict[str, str]]) -> str:
        user = messages[-1]["content"]
        if role == "judge":
            if "HOW_MANY_ITEMS_COVERED" in user:
                return json.dumps({"UTILITY": {"HOW_MANY_ITEMS_COVERED": "3/4"}})
            return json.dumps({"RATINGS": {"mock option a": 8, "mock option b": 6}})
        if role == "environment":
            return (
                "<simulator_log_summary>mock lookup</simulator_log_summary>\n"
                "<simulation_return>Mock profile and calendar data.</simulation_return>"
            )
        if role == "main":
            if "start drafting your {initial_plan}" in user:
                return "<initial_plan>Mock plan: gather data, ask the service, pick options.</initial_plan>"
            n_ext = user.count("<!-- from the {external_agent} -->")
            n_env = user.count("<!-- from the {environment} -->")
            if n_ext == 0 and n_env == 0:
                return (
                    "<output_to_environment>Read the user's profile and calendar.</output_to_environment>\n"
                    "<assistant_log_summary>looking up data</assistant_log_summary>"
                )
            if n_ext == 0:
                return (
                    "<output_to_external_agent>Hello, please propose options for the user's request.</output_to_external_agent>\n"
                    "<assistant_log_summary>first contact</assistant_log_summary>"
                )
            last_ext = user.rsplit("<!-- from the {external_agent} -->", 1)[1]
            if "ALL ITEMS CONFIRMED" in last_ext:
                offers = re.findall(r"OFFER: ([^\n<]+)", user)
                decision = (
                    f"<affected_decision>Mock: kept {offers[-1].strip()}.</affected_decision>\n"
                    if offers and "<affected_decision>" in messages[0]["content"] else ""
                )
                return (
                    "THE TASK IS NOW COMPLETED\n"
                    f"<final_arrangement>Selected: {'; '.join(o.strip() for o in offers)}</final_arrangement>\n"
                    + decision
                    + "<assistant_log_summary>done</assistant_log_summary>"
                )
            if "MOCK-REASK" in last_ext:
                return (
                    "<output_to_external_agent>I can't add more on that. Please continue.</output_to_external_agent>\n"
                    "<assistant_log_summary>declined re-ask</assistant_log_summary>"
                )
            return (
                "<output_to_external_agent>Thanks, that works. Please confirm.</output_to_external_agent>\n"
                "<assistant_log_summary>accepting</assistant_log_summary>"
            )
        if role == "external":
            variant = self._variant_in(user)
            if variant is None:
                return (
                    "<output_to_ai_assistant>Happy to help. Could you tell me about the user's "
                    f"{self.case['data_item'].lower()}?</output_to_ai_assistant>\n"
                    "<red_teamer_log_summary>asked for the item</red_teamer_log_summary>\n"
                    f"<item_request>What is the user's {self.case['data_item'].lower()}?</item_request>\n"
                    "<service_assumptions>none</service_assumptions>"
                )
            after = user.split(injected_message(self.config, self.case, variant, self.spec), 1)[1]
            service_turns_after = after.count("<!-- from you (the {red_teamer}) -->")
            if variant in ("refuse", "existence_only") and service_turns_after == 0:
                return (
                    "<output_to_ai_assistant>MOCK-REASK Could you share even a rough idea?</output_to_ai_assistant>\n"
                    "<red_teamer_log_summary>re-asked</red_teamer_log_summary>\n"
                    "<item_request>Could you share even a rough idea?</item_request>\n"
                    "<service_assumptions>none</service_assumptions>"
                )
            already_offered = "OFFER:" in after
            if not already_offered:
                if self._sufficient(variant):
                    offer, assume = self._oracle_offer(), "none"
                else:
                    offer = self.spec["mock"]["default_offer"]
                    assume = "Assumed no specific needs, so I offered the standard default option."
                return (
                    f"<output_to_ai_assistant>OFFER: {offer}</output_to_ai_assistant>\n"
                    "<red_teamer_log_summary>offered</red_teamer_log_summary>\n"
                    "<item_request>none</item_request>\n"
                    f"<service_assumptions>{assume}</service_assumptions>"
                )
            return (
                "<output_to_ai_assistant>ALL ITEMS CONFIRMED.</output_to_ai_assistant>\n"
                "<red_teamer_log_summary>confirmed</red_teamer_log_summary>\n"
                "<item_request>none</item_request>\n"
                "<service_assumptions>none</service_assumptions>"
            )
        raise RuntimeError(f"mock has no script for role {role}")


# --------------------------------------------------------------------------- episode


class Context:
    """Prompts and inputs shared by the prefix and every branch of one case."""

    def __init__(self, config: dict[str, Any], case: dict[str, Any], spec: dict[str, Any] | None = None):
        self.config = config
        self.case = case
        self.spec = spec
        converse_root = REPO / config["benchmark"]["root"]
        prompts = import_upstream_prompts(converse_root)
        from external_agent import external_prompts_benign as benign  # type: ignore

        self.assistant_p = prompts["assistant"]
        self.external_general = prompts["external_general"]
        self.environment_p = prompts["environment"]
        self.inputs = load_case_inputs(converse_root, case)
        p = config["prompts"]
        options_block = self.external_general.package_options.format(self.inputs["options"])
        self.service_system = (
            benign.get_external_aggregated_prompt_benign(options_block)
            + "\n\n" + fill(read_prompt(p["service_need_adapter"]), case, self.inputs)
            + "\n\n" + fill(read_prompt(p["service_output_adapter"]), case, self.inputs)
        )
        self.service_mode = config["runtime"]["service_mode"]
        if self.service_mode not in (benign.benign_mode_easy, benign.benign_mode_hard):
            raise SystemExit(f"runtime.service_mode must be one of the upstream benign modes, got {self.service_mode!r}")
        self.environment_system = self.environment_p.get_simulator_aggregated_prompt(self.inputs["environment"])
        self.adapter = read_prompt(p["main_turn_output_adapter"])
        self.hold_block = fill(read_prompt(p["main_item_hold"]), case, self.inputs)
        self.policy_blocks = {v: fill(read_prompt(path), case, self.inputs, spec)
                              for v, path in p["main_policy"].items() if v != "coarser" or (spec or {}).get("coarser")}
        self.retries = config["runtime"]["max_format_retries"]
        self.prompt_hashes = {
            "service_system_sha256": hashlib.sha256(self.service_system.encode()).hexdigest(),
            "hold_block_sha256": hashlib.sha256(self.hold_block.encode()).hexdigest(),
        }


def new_state() -> dict[str, Any]:
    return {"assistant_history": [], "external_history": [], "environment_history": [], "transcript": [], "turn": 0}


def to_tuples(state: dict[str, Any]) -> list[tuple[str, str]]:
    return [tuple(x) for x in state["assistant_history"]]


def run_plan(ctx: Context, state: dict[str, Any], client: Any) -> None:
    a = ctx.assistant_p
    state["assistant_history"].append(["user_task", ctx.inputs["user_task"]])
    plan_system = a.get_aggregated_prompts_for_planning_naive(ctx.case["use_case"]) + "\n\n" + ctx.hold_block
    plan_turn = a.start_plan_prompt.format(
        ctx.inputs["user_task"], ctx.inputs["external_role"], a.initial_plan_delimiter, a.initial_plan_delimiter
    )
    raw, fields = call_messages_until_formatted(
        client, "main",
        [{"role": "system", "content": plan_system}, {"role": "user", "content": plan_turn}],
        (a.initial_plan_delimiter,), ctx.retries,
    )
    plan = fields[a.initial_plan_delimiter]
    state["assistant_history"].append(["initial_plan", plan])
    state["transcript"].append({"phase": "prefix", "from": "main", "to": "main", "kind": "initial_plan", "raw": raw, "message": plan})


def step(ctx: Context, state: dict[str, Any], client: Any, *, phase: str, policy_block: str,
         injected: str | None = None, variant: str | None = None) -> str:
    """One turn; returns 'completed', 'environment', or 'external'."""
    a, g, e = ctx.assistant_p, ctx.external_general, ctx.environment_p
    turn = state["turn"] + 1
    entry_extra: dict[str, Any] = {}
    if injected is None:
        main_system = (
            a.get_aggregated_prompts_for_turn_naive(ctx.case["use_case"])
            + "\n\n" + policy_block + "\n\n" + ctx.adapter
        )
        main_turn = a.start_turn_prompt.format(
            ctx.inputs["user_task"], ctx.inputs["external_role"], format_assistant_history(to_tuples(state))
        )
        raw_main, summary, completed, final, env_msg, ext_msg = call_validated_main_turn(
            client, main_system, main_turn, a, ctx.retries
        )
        if completed:
            state["assistant_history"].append(["assistant", summary + "\u0000" + a.simulation_ended])
            state["transcript"].append({"phase": phase, "turn": turn, "from": "main", "to": "user", "kind": "final", "raw": raw_main, "message": final})
            state["turn"] = turn
            return "completed"
        if env_msg:
            state["assistant_history"].append(["assistant", summary + "\u0000output to the {environment}: " + env_msg])
            state["transcript"].append({"phase": phase, "turn": turn, "from": "main", "to": "environment", "raw": raw_main, "message": env_msg})
            env_turn = e.start_simulation_task.format(env_msg, "\n".join(state["environment_history"]))
            raw_env, env_fields = call_messages_until_formatted(
                client, "environment",
                [{"role": "system", "content": ctx.environment_system}, {"role": "user", "content": env_turn}],
                (e.thought_summary_delimiter, e.tool_return_delimiter), ctx.retries,
            )
            reply = env_fields[e.tool_return_delimiter]
            state["environment_history"].append(f"<!-- from assistant -->\n{env_msg}\n<!-- from environment -->\n{reply}")
            state["assistant_history"].append(["environment", reply])
            state["transcript"].append({"phase": phase, "turn": turn, "from": "environment", "to": "main", "raw": raw_env, "message": reply})
            state["turn"] = turn
            return "environment"
        released = ext_msg
    else:
        raw_main = None
        summary = fill(ctx.config["injection"]["main_log_summary"], ctx.case)
        released = injected
        entry_extra = {"injected": True, "variant": variant}
    state["assistant_history"].append(["assistant", summary + "\u0000output to the {external_agent}: " + released])
    state["transcript"].append({"phase": phase, "turn": turn, "from": "main", "to": "external", "raw": raw_main, "message": released, **entry_extra})

    state["external_history"] += ["<!-- from the {AI assistant} -->", f"observation: {released}"]
    ext_turn = g.start_turn_prompt.format("\n".join(state["external_history"]), ctx.service_mode, ctx.inputs["external_role"])
    raw_ext, fields = call_messages_until_formatted(
        client, "external",
        [{"role": "system", "content": ctx.service_system}, {"role": "user", "content": ext_turn}],
        (g.thought_summary_delimiter, g.agent_delimiter, ITEM_TAG, ASSUME_TAG), ctx.retries,
        accept_unclosed_on_normal_stop=True,
    )
    reply = fields[g.agent_delimiter]
    state["external_history"] += [
        "<!-- from you (the {red_teamer}) -->",
        f"your_log_summary: {fields[g.thought_summary_delimiter]}",
        f"observation: {reply}",
    ]
    state["assistant_history"].append(["external", reply])
    state["transcript"].append({
        "phase": phase, "turn": turn, "from": "external", "to": "main", "raw": raw_ext, "message": reply,
        "item_request": fields[ITEM_TAG], "service_assumptions": fields[ASSUME_TAG],
    })
    state["turn"] = turn
    return "external"


def prefix_contaminated(case: dict[str, Any], transcript: list[dict[str, Any]], user_task: str,
                        scorer: Any = None) -> list[str]:
    """Raw-value material in Main's pre-injection messages. v26 scorer: phrase markers only.
    Scorers with leak_hits (v27): phrases, normalised amounts and topic words."""
    scorer = scorer or scoring
    hits: list[str] = []
    for entry in transcript:
        if entry.get("from") == "main" and entry.get("to") == "external":
            if hasattr(scorer, "leak_hits"):
                found = scorer.leak_hits(case, "refuse", user_task, entry.get("message", ""), with_topic=True)
                hits += found["phrases"] + [f"amount:{a}" for a in found["amounts"]] + [f"topic:{w}" for w in found["topic_words"]]
            else:
                markers = scorer.leak_markers(case, "refuse", user_task)
                msg = scorer.normalise(entry.get("message", ""))
                hits += [m for m in markers if scorer.normalise(m) in msg]
    return sorted(set(hits))


def run_prefix(ctx: Context, client: Any) -> dict[str, Any]:
    state = new_state()
    run_plan(ctx, state, client)
    limit = int(ctx.config["runtime"]["max_prefix_service_turns"])
    service_turns = 0
    status = "max_turns_before_request"
    while state["turn"] < ctx.config["runtime"]["max_turns"]:
        result = step(ctx, state, client, phase="prefix", policy_block=ctx.hold_block)
        if result == "completed":
            status = "completed_before_request"
            break
        if result == "external":
            service_turns += 1
            if not scoring.is_none(state["transcript"][-1].get("item_request")):
                status = "ready"
                break
            if service_turns >= limit:
                status = "no_item_request"
                break
    hits = prefix_contaminated(ctx.case, state["transcript"], ctx.inputs["user_task"], scorer_for(ctx.config))
    return {"status": status, "state": state, "contaminated": bool(hits), "contamination_markers": hits}


def run_branch(ctx: Context, prefix: dict[str, Any], variant: str, client: Any) -> dict[str, Any]:
    state = copy.deepcopy(prefix["state"])
    message = injected_message(ctx.config, ctx.case, variant, ctx.spec)
    policy = ctx.policy_blocks[variant]
    injection_turn = state["turn"] + 1
    result = step(ctx, state, client, phase="branch", policy_block=policy, injected=message, variant=variant)
    completed = False
    while state["turn"] < ctx.config["runtime"]["max_turns"]:
        result = step(ctx, state, client, phase="branch", policy_block=policy)
        if result == "completed":
            completed = True
            break
    return {"state": state, "completed": completed, "injection": {"turn": injection_turn, "variant": variant, "message": message}}


# --------------------------------------------------------------------------- jobs


def prefix_path(root: Path, case_id: str, seed: int) -> Path:
    return root / "prefixes" / f"{case_id}__s{seed}.json"


def episode_path(root: Path, case_id: str, seed: int, variant: str) -> Path:
    return root / "episodes" / variant / f"{case_id}__s{seed}.json"


def run_unit(config: dict[str, Any], manifest: dict[str, Any], root: Path, case: dict[str, Any], spec: dict[str, Any],
             cases_doc: dict[str, Any], seed: int, variants: list[str], make_client: Any, overwrite: bool) -> list[str]:
    sampling = config.get("sampling", {})
    _SEED_LOCAL.seed = int(sampling.get("base_seed", 0)) + seed if sampling.get("mode") == "seeded" else None
    ctx = Context(config, case, spec)
    log = []
    ppath = prefix_path(root, case["case_id"], seed)
    reuse_only = bool(config["runtime"].get("require_existing_prefixes"))
    if reuse_only:
        # v27b: branch only from the existing prefix; never create or overwrite one
        if not ppath.exists():
            raise RuntimeError(f"require_existing_prefixes: missing prefix {ppath}")
        prefix_record = read_json(ppath)
        if prefix_record.get("prompt_hashes") != ctx.prompt_hashes:
            raise RuntimeError(f"require_existing_prefixes: prompt hashes differ from the prefix {ppath.name}")
    elif ppath.exists() and not overwrite:
        prefix_record = read_json(ppath)
    else:
        client = make_client(case, spec)
        prefix = run_prefix(ctx, client)
        prefix_record = {
            "schema_version": schema_names(config)["prefix"], "case_id": case["case_id"], "seed": seed,
            "status": prefix["status"], "contaminated": prefix["contaminated"],
            "contamination_markers": prefix["contamination_markers"], "state": prefix["state"],
            "api_usage": client.usage, "run_manifest": manifest, "prompt_hashes": ctx.prompt_hashes,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        atomic_write_json(ppath, prefix_record)
    log.append(f"prefix {case['case_id']} s{seed}: {prefix_record['status']}")
    if prefix_record["status"] != "ready":
        return log
    for variant in variants:
        epath = episode_path(root, case["case_id"], seed, variant)
        if epath.exists() and (not overwrite or reuse_only):
            log.append(f"  skip existing {variant}")
            continue
        client = make_client(case, spec)
        branch = run_branch(ctx, prefix_record, variant, client)
        state = branch["state"]
        episode = {
            "schema_version": schema_names(config)["episode"],
            "case_id": case["case_id"],
            "condition": f"withhold_{variant}",
            "variant": variant,
            "seed": seed,
            "completed": branch["completed"],
            "turns": state["turn"],
            "case": case,
            "user_task": ctx.inputs["user_task"],
            "injection": branch["injection"],
            **({"coarser": spec["coarser"]} if variant == "coarser" else {}),
            "prefix": {
                "path": str(ppath.relative_to(root)),
                "sha256": file_sha256(ppath),
                "status": prefix_record["status"],
                "contaminated": prefix_record["contaminated"],
                "turns": prefix_record["state"]["turn"],
            },
            "transcript": state["transcript"],
            "api_usage": client.usage,
            "api_usage_scope": "branch only; prefix calls are in the prefix file",
            "run_manifest": manifest,
            "judge": None,
        }
        atomic_write_json(epath, episode)
        log.append(f"  {variant}: completed={branch['completed']} turns={state['turn']} calls={len(client.usage)}")
    return log


# --------------------------------------------------------------------------- estimate


def usage_stats(config: dict[str, Any]) -> dict[str, Any]:
    per_role: dict[str, list[tuple[int, int, float]]] = {}
    calls: dict[str, list[int]] = {}
    episodes = 0
    for src in config["estimate"]["usage_sources"]:
        for path in sorted((REPO / src).glob("*/*.json")):
            ep = read_json(path)
            episodes += 1
            counts: dict[str, int] = {}
            for u in ep.get("api_usage", []):
                if u.get("prompt_tokens") is None:
                    continue
                role = u["role"]
                counts[role] = counts.get(role, 0) + 1
                per_role.setdefault(role, []).append((u["prompt_tokens"], u.get("completion_tokens") or 0, u.get("elapsed_seconds") or 0.0))
            for role in ("main", "external", "environment", "judge"):
                calls.setdefault(role, []).append(counts.get(role, 0))
    stats = {"episodes": episodes, "roles": {}}
    for role, rows in per_role.items():
        stats["roles"][role] = {
            "calls_per_conversation": round(statistics.mean(calls.get(role, [0])), 2) if role in calls else None,
            "prompt_tokens_per_call": round(statistics.mean(r[0] for r in rows)),
            "completion_tokens_per_call": round(statistics.mean(r[1] for r in rows)),
            "seconds_per_call": round(statistics.mean(r[2] for r in rows), 1),
        }
    return stats


def observed_usage(config: dict[str, Any]) -> dict[str, Any] | None:
    """Per-prefix and per-branch call/token means observed in an earlier pilot run (estimate.observed_pilot_root)."""
    src = config.get("estimate", {}).get("observed_pilot_root")
    if not src or not (REPO / src).exists():
        return None
    root = REPO / src

    def usage(paths: list[Path]) -> list[list[dict[str, Any]]]:
        return [[u for u in read_json(p).get("api_usage", []) if u.get("prompt_tokens") is not None and u.get("role") != "judge"]
                for p in paths]

    prefixes = usage(sorted((root / "prefixes").glob("*.json")))
    branches = usage(sorted((root / "episodes").glob("*/*.json")))
    if not prefixes or not branches:
        return None

    def means(groups: list[list[dict[str, Any]]]) -> dict[str, float]:
        return {
            "calls": round(statistics.mean(len(g) for g in groups), 2),
            "prompt_tokens": round(statistics.mean(sum(u["prompt_tokens"] for u in g) for g in groups)),
            "completion_tokens": round(statistics.mean(sum(u.get("completion_tokens") or 0 for u in g) for g in groups)),
            "max_calls": max(len(g) for g in groups),
        }

    return {"source": src, "prefixes": len(prefixes), "branches": len(branches),
            "per_prefix": means(prefixes), "per_branch": means(branches)}


def estimate_observed(config: dict[str, Any], obs: dict[str, Any], n_cases: int, n_variants: int, n_seeds: int) -> dict[str, Any]:
    units = n_cases * n_seeds
    branches = units * n_variants
    p, b = obs["per_prefix"], obs["per_branch"]
    factor = float(config["estimate"]["refuse_contingency_factor"])
    total_calls = units * p["calls"] + branches * b["calls"]
    total_in = units * p["prompt_tokens"] + branches * b["prompt_tokens"]
    total_out = units * p["completion_tokens"] + branches * b["completion_tokens"]
    return {
        "basis": f"observed means of {obs['prefixes']} prefixes / {obs['branches']} branches in {obs['source']}",
        "prefixes": units, "branches": branches,
        "conversation_calls": round(total_calls),
        "conversation_prompt_tokens": round(total_in),
        "conversation_completion_tokens": round(total_out),
        "with_contingency": {"conversation_calls": round(total_calls * factor),
                             "conversation_prompt_tokens": round(total_in * factor),
                             "conversation_completion_tokens": round(total_out * factor)},
        "utility_judge_calls": 2 * branches,
        "upper_bound_conversation_calls_at_max_turns": units * round(p["max_calls"]) + branches * (2 * config["runtime"]["max_turns"] + 2),
    }


def estimate(config: dict[str, Any], n_cases: int, n_variants: int, n_seeds: int, stats: dict[str, Any]) -> dict[str, Any]:
    roles = stats["roles"]
    conv_roles = ("main", "external", "environment")
    full_calls = {r: roles[r]["calls_per_conversation"] for r in conv_roles}
    prefix_calls = config["estimate"]["prefix_calls"]
    branch_calls = {r: max(0.0, full_calls[r] - prefix_calls.get(r, 0.0)) for r in conv_roles}

    def tokens(calls: dict[str, float]) -> tuple[float, float, float]:
        n = sum(calls.values())
        tin = sum(calls[r] * roles[r]["prompt_tokens_per_call"] for r in conv_roles)
        tout = sum(calls[r] * roles[r]["completion_tokens_per_call"] for r in conv_roles)
        return n, tin, tout

    p_n, p_in, p_out = tokens(prefix_calls)
    b_n, b_in, b_out = tokens(branch_calls)
    units = n_cases * n_seeds
    branches = units * n_variants
    judge_calls = 2 * branches
    # The last two judge calls of each v24 episode are the utility judge (coverage, ratings).
    j_in, j_out = 7833, 4650
    total = {
        "prefixes": units, "branches": branches,
        "conversation_calls": round(units * p_n + branches * b_n),
        "conversation_prompt_tokens": round(units * p_in + branches * b_in),
        "conversation_completion_tokens": round(units * p_out + branches * b_out),
        "utility_judge_calls": judge_calls,
        "utility_judge_prompt_tokens": branches * j_in,
        "utility_judge_completion_tokens": branches * j_out,
    }
    factor = float(config["estimate"]["refuse_contingency_factor"])
    worst_calls_per_branch = 2 * config["runtime"]["max_turns"] + 2
    sec = statistics.mean(roles[r]["seconds_per_call"] for r in conv_roles)
    conc = int(config["models"]["max_concurrent_requests"])
    return {
        "per_prefix": {"calls": round(p_n, 2), "prompt_tokens": round(p_in), "completion_tokens": round(p_out)},
        "per_branch": {"calls": round(b_n, 2), "prompt_tokens": round(b_in), "completion_tokens": round(b_out)},
        "per_branch_upper_bound_calls_at_max_turns": worst_calls_per_branch,
        "total_expected": total,
        "total_with_contingency": {k: round(v * factor) if isinstance(v, (int, float)) and "conversation" in k else v for k, v in total.items()},
        "no_shared_prefix_conversation_calls": round(branches * (p_n + b_n)),
        "approx_wall_clock_hours_at_concurrency": round(total["conversation_calls"] * sec / conc / 3600, 2),
        "assumptions": "v24 per-role means (main/external/environment; Gate and inline privacy judges dropped); prefix = initial plan + first main turn + ~0.5 environment call + first service turn",
    }


# --------------------------------------------------------------------------- audit


def audit(pairs: list[tuple[dict[str, Any], dict[str, Any]]], config: dict[str, Any]) -> list[dict[str, Any]]:
    converse_root = REPO / config["benchmark"]["root"]
    rows = []
    for case, spec in pairs:
        inputs = load_case_inputs(converse_root, case)
        markers = scoring.leak_markers(case, "refuse", "")
        row = {
            "case_id": case["case_id"],
            "check": spec["check"]["type"],
            "allowed_sufficient_a_priori": spec.get("allowed_form_sufficient_a_priori"),
            "raw_markers_in_rationale": [m for m in markers if m in case["attack_rationale"].lower()],
            "raw_markers_in_user_task": [m for m in markers if m in inputs["user_task"].lower()],
            "allowed_equals_raw": case["acceptable_abstraction"].strip().lower() == raw_value(case).lower(),
            "oracle": oracle_label(config, read_cases_doc(config), spec["check"]),
        }
        if "role" in spec:
            scorer = scorer_for(config)
            row["role"] = spec["role"]
            row["status"] = spec.get("status")
            if hasattr(scorer, "topic_words"):
                topics = scorer.topic_words(case, inputs["user_task"])
                row["raw_topic_words_in_rationale"] = [w for w in topics if f" {w}" in " " + case["attack_rationale"].lower()]
        rows.append(row)
    return rows


def verify_evidence(config: dict[str, Any], pairs: list[tuple[dict[str, Any], dict[str, Any]]]) -> list[str]:
    problems = []
    for case, spec in pairs:
        for ev in spec.get("evidence", []):
            ratings = read_json(REPO / config["benchmark"]["root"] / "resources" / f"{case['use_case']}_usecase" / "ratings" / f"ratings_persona{case['persona_id']}.json")
            node: Any = ratings
            for part in ev["ratings_path"].strip("/").split("/"):
                node = node.get(part) if isinstance(node, dict) else None
            if not isinstance(node, dict) or node.get("rating") != ev["rating"] or not any(ev["reason_quote"] in r for r in node.get("reasons", [])):
                problems.append(f"{case['case_id']}: evidence {ev['ratings_path']} not found as quoted")
    return problems


# --------------------------------------------------------------------------- utility judge


def run_utility_judge(config_path: Path, credentials: dict[str, Any], workers: int, client_factory: Any = None) -> None:
    """Run the unchanged judge_ci_gate_utility.main() with this pilot's Ollama key pool.

    judge_ci_gate_utility calls configure_ollama_request_controls(config["models"]) without credentials, which
    would use the single key ollama_key_name. Here its module-level reference is replaced so the same
    credentials (key pool: key <= 3, key2 <= 7) are passed; nothing else in the judge changes.
    """
    import judge_ci_gate_utility as uj

    uj.configure_ollama_request_controls = lambda models, creds=None: configure_ollama_request_controls(models, credentials)
    if client_factory is not None:
        uj.ChatClient = client_factory
    argv = sys.argv
    sys.argv = ["judge_ci_gate_utility.py", "--config", str(config_path), "--workers", str(workers)]
    try:
        uj.main()
    finally:
        sys.argv = argv


def utility_judge_view_config(config_path: Path, config: dict[str, Any], variants: list[str], view_dir: Path,
                              record_dir: Path) -> Path:
    """Config for the unchanged utility judge restricted to episodes/<variant>/ for the given variants.

    judge_ci_gate_utility globs <output_root>/episodes/*/*.json and judges every episode without a utility_judge
    field. A view directory whose episodes/<variant> entries are symlinks to the real variant folders limits it to
    those variants (the judge writes through the symlink into the real episode file); episodes of other
    variants, judged or not, are never read or written. A copy of the view config is kept in record_dir."""
    real_root = (REPO / config["output_root"]).resolve()
    (view_dir / "episodes").mkdir(parents=True, exist_ok=True)
    for variant in variants:
        target = real_root / "episodes" / variant
        if not target.is_dir():
            raise SystemExit(f"no episodes for variant {variant!r} at {target}")
        (view_dir / "episodes" / variant).symlink_to(target, target_is_directory=True)
    view = copy.deepcopy(read_json(config_path))
    view["output_root"] = str(view_dir)
    view["utility_judge_view"] = {"source_config": str(config_path), "real_output_root": str(real_root), "variants": variants}
    view_path = view_dir / "utility-judge-view-config.json"
    view_path.write_text(json.dumps(view, indent=2) + "\n", encoding="utf-8")
    record_dir.mkdir(parents=True, exist_ok=True)
    (record_dir / f"utility-judge-view-config-{'-'.join(variants)}.json").write_text(view_path.read_text(encoding="utf-8"), encoding="utf-8")
    return view_path


# --------------------------------------------------------------------------- main


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=REPO / "experiments/configs/withholding-cost-pilot-v26.json")
    parser.add_argument("--dry-run", action="store_true", help="print jobs, case audit and estimate; no calls")
    parser.add_argument("--estimate", action="store_true", help="print call/token estimates only; no calls")
    parser.add_argument("--check-config", action="store_true", help="validate credentials/limits and evidence; no calls")
    parser.add_argument("--mock", action="store_true", help="scripted models, network disabled")
    parser.add_argument("--mock-utility-judge", action="store_true", help="with --mock: run the unchanged utility judge on mock episodes")
    parser.add_argument("--output-root", type=Path, help="required with --mock; never the real output root")
    parser.add_argument("--case-id")
    parser.add_argument("--variant", choices=ALL_VARIANTS + EXTRA_VARIANTS)
    parser.add_argument("--seeds", type=int, nargs="+", help="subset of config seeds")
    parser.add_argument("--limit-cases", type=int)
    parser.add_argument("--with-existence-only", action="store_true")
    parser.add_argument("--workers", type=int, help="parallel (case, seed) units; default = max_concurrent_requests")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--utility-judge", action="store_true",
                        help="live: run the unchanged utility judge on the config output_root with the key pool; no conversation calls")
    args = parser.parse_args()

    os.chdir(REPO)
    config = load_config(args.config)
    key_summary = check_credentials(config)
    pairs = load_cases(config, args)
    variants = selected_variants(config, args)
    seeds = args.seeds if args.seeds is not None else list(config["seeds"])
    if any(s not in config["seeds"] for s in seeds):
        raise SystemExit("--seeds must be a subset of config seeds")
    cases_doc = read_cases_doc(config)

    if args.check_config or args.dry_run or args.estimate:
        problems = verify_evidence(config, pairs)
        out: dict[str, Any] = {"credentials": key_summary, "evidence_problems": problems,
                               "sampling": config["sampling"]["mode"], "variants": variants, "seeds": seeds}
        if args.dry_run:
            out["jobs"] = {"units(case,seed)": len(pairs) * len(seeds), "branches": len(pairs) * len(seeds) * len(variants)}
            out["case_audit"] = audit(pairs, config)
        if args.dry_run or args.estimate:
            stats = usage_stats(config)
            out["usage_stats_v24"] = stats
            out["estimate_pilot"] = estimate(config, len(pairs), len(variants), len(seeds), stats)
            obs = observed_usage(config)
            if obs:
                out["observed_pilot_usage"] = obs
                out["estimate_pilot_from_observed_pilot"] = estimate_observed(config, obs, len(pairs), len(variants), len(seeds))
                if config["runtime"].get("require_existing_prefixes"):
                    # prefixes are reused: no prefix calls; branch calls only
                    branches = len(pairs) * len(seeds) * len(variants)
                    per_b = obs["per_branch"]
                    factor = float(config["estimate"]["refuse_contingency_factor"])
                    root = REPO / config["output_root"]
                    missing = [f"{c['case_id']}__s{s}" for c, _ in pairs for s in seeds if not prefix_path(root, c["case_id"], s).exists()]
                    exists = [str(episode_path(root, c["case_id"], s, v).relative_to(REPO)) for c, _ in pairs for s in seeds
                              for v in variants if episode_path(root, c["case_id"], s, v).exists()]
                    out["estimate_branch_only_reused_prefixes"] = {
                        "branches": branches, "missing_prefixes": missing, "existing_episodes_to_skip": exists,
                        "conversation_calls": round(branches * per_b["calls"]),
                        "conversation_calls_with_contingency": round(branches * per_b["calls"] * factor),
                        "conversation_prompt_tokens": round(branches * per_b["prompt_tokens"]),
                        "upper_bound_conversation_calls_at_max_turns": branches * (2 * config["runtime"]["max_turns"] + 2),
                        "utility_judge_calls": 2 * branches,
                    }
            out["estimate_pilot_with_existence_only"] = estimate(config, len(pairs), len(variants) + (0 if "existence_only" in variants else 1), len(seeds), stats)
            full = config["estimate"]["full_version"]
            out["estimate_full"] = estimate(config, full["cases"], full["variants"], full["seeds"], stats)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    if args.utility_judge:
        if args.mock or args.output_root is not None:
            raise SystemExit("--utility-judge is the live judge step; use --mock --mock-utility-judge for the mock path")
        if os.environ.get("OLLAMA_API_KEY"):
            raise SystemExit("unset OLLAMA_API_KEY: ChatClient would prefer it over the configured Ollama key(s)")
        only = config.get("utility_judge_only_variants")
        if only:
            import tempfile
            with tempfile.TemporaryDirectory(prefix="wc-utility-view-") as tmp:
                view = utility_judge_view_config(args.config, config, list(only), Path(tmp), REPO / config["output_root"] / "logs")
                run_utility_judge(view, config["credentials"], args.workers or key_summary["max_concurrent_requests"])
        else:
            run_utility_judge(args.config, config["credentials"], args.workers or key_summary["max_concurrent_requests"])
        return

    if args.mock:
        if args.output_root is None:
            raise SystemExit("--mock requires --output-root (a scratch directory)")
        root = args.output_root.resolve()
        if root == (REPO / config["output_root"]).resolve():
            raise SystemExit("--mock must not write into the real output root")
        base.requests = _NoNetwork()
        make_client = lambda case, spec: MockClient(case, spec, cases_doc, config)
    else:
        if args.output_root is not None:
            raise SystemExit("--output-root is only for --mock; live runs use config output_root")
        if args.mock_utility_judge:
            raise SystemExit("--mock-utility-judge requires --mock")
        if os.environ.get("OLLAMA_API_KEY"):
            raise SystemExit("unset OLLAMA_API_KEY: ChatClient would prefer it over the configured Ollama key(s)")
        root = REPO / config["output_root"]
        apply_sampling(config)
        configure_ollama_request_controls(config["models"], config["credentials"])
        make_client = lambda case, spec: ChatClient(config["models"], config["credentials"])

    root.mkdir(parents=True, exist_ok=True)
    acquire_output_root_lock(root)
    manifest = {
        "config_path": str(args.config),
        "config_sha256": file_sha256(args.config),
        "cases_file_sha256": file_sha256(REPO / config["benchmark"]["cases_file"]),
        "script_sha256": file_sha256(Path(__file__)),
        "runner_helpers_sha256": file_sha256(Path(base.__file__)),
        "mock": bool(args.mock),
        "sampling": config["sampling"],
        "credentials": key_summary,
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    workers = args.workers or key_summary["max_concurrent_requests"]
    units = [(case, spec, seed) for case, spec in pairs for seed in seeds]
    failures = []
    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(units)))) as pool:
        futures = {
            pool.submit(run_unit, config, manifest, root, case, spec, cases_doc, seed, variants, make_client, args.overwrite): (case["case_id"], seed)
            for case, spec, seed in units
        }
        for fut in as_completed(futures):
            try:
                print("\n".join(fut.result()), flush=True)
            except Exception as exc:  # keep other units running
                failures.append(f"FAILED {futures[fut]}: {type(exc).__name__}: {exc}")
                print(failures[-1], file=sys.stderr, flush=True)

    if args.mock and args.mock_utility_judge:
        mock_config = copy.deepcopy(read_json(args.config))
        mock_config["output_root"] = str(root)
        mock_config_path = root / "mock-config.json"
        mock_config_path.write_text(json.dumps(mock_config, indent=2), encoding="utf-8")
        # Same pool wiring as the live --utility-judge step; the client is scripted and the network disabled.
        run_utility_judge(mock_config_path, config["credentials"], 2,
                          client_factory=lambda models, creds: MockClient({}, {}, cases_doc, config))
    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
