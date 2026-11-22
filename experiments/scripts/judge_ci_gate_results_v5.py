#!/usr/bin/env python3
"""Independent target-privacy and other-privacy judges for v18."""
from __future__ import annotations
import argparse, json, re, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import jsonschema
from ci_gate_runtime import GateDecisionError, extract_json_object
from judge_ci_gate_results_v3 import build_evidence, deterministic_matches, load_privacy_ground_truth, released_conversation
from run_ci_gate_pilot import ChatClient, configure_ollama_request_controls, file_sha256, load_case_inputs, read_json

def atomic(path: Path, value: dict):
    tmp = path.with_suffix(path.suffix + ".privacy-v5.tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)

def call(client, prompt, evidence, schema, retries):
    messages=[{"role":"system","content":prompt},{"role":"user","content":json.dumps(evidence,ensure_ascii=False)}]
    last=None
    for attempt in range(retries+1):
        raw=client.call("judge",messages,json_mode=True)
        try:
            parsed=extract_json_object(raw); jsonschema.validate(parsed,schema)
            return raw,parsed
        except (GateDecisionError,jsonschema.ValidationError,ValueError) as exc:
            last=exc
            if attempt < retries:
                messages += [{"role":"assistant","content":raw},{"role":"user","content":f"Return corrected JSON only: {exc}"}]
    raise ValueError(f"judge contract failed: {last}")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",type=Path,required=True); ap.add_argument("--workers",type=int,default=5); ap.add_argument("--overwrite",action="store_true"); ap.add_argument("--dry-run",action="store_true"); args=ap.parse_args()
    config=read_json(args.config); config["models"]["request_timeout_seconds"]=config["runtime"]["request_timeout_seconds"]; configure_ollama_request_controls(config["models"])
    root=Path(config["output_root"]); paths=sorted((root/"episodes").glob("*/*.json"));
    if not args.overwrite: paths=[p for p in paths if read_json(p).get("privacy_judge_v5") is None]
    if args.dry_run: print(json.dumps({"privacy_judge_v5_jobs":len(paths),"llm_calls":len(paths)*2},indent=2)); return
    prompt_paths={"leak":Path(config["prompts"].get("privacy_target_leak_v18","experiments/prompts/ci_gate/privacy_target_leak_v18.txt")),"abstraction":Path(config["prompts"].get("privacy_target_abstraction_v18","experiments/prompts/ci_gate/privacy_target_abstraction_v18.txt")),"other":Path(config["prompts"]["privacy_other_v18"])}
    schema_paths={"leak":Path(config["schemas"].get("privacy_target_leak_v18","experiments/configs/privacy-target-leak-v18.schema.json")),"abstraction":Path(config["schemas"].get("privacy_target_abstraction_v18","experiments/configs/privacy-target-abstraction-v18.schema.json")),"other":Path(config["schemas"]["privacy_other_v18"])}
    prompts={k:p.read_text(encoding="utf-8") for k,p in prompt_paths.items()}; schemas={k:read_json(p) for k,p in schema_paths.items()}; converse=Path(config["benchmark"]["root"]); retries=config["runtime"]["max_format_retries"]
    manifest={"version":"independent-privacy-judge-v5","config_sha256":file_sha256(args.config),"prompt_sha256":{k:file_sha256(p) for k,p in prompt_paths.items()},"schema_sha256":{k:file_sha256(p) for k,p in schema_paths.items()},"script_sha256":file_sha256(Path(__file__)),"evaluated_surface":"released assistant-to-external conversation only"}
    def one(pos,path):
        ep=read_json(path); gt=load_privacy_ground_truth(converse,ep["case"]); inputs=load_case_inputs(converse,ep["case"]); mode="abstraction" if gt["semantic_tier"]=="related_and_useful" else "leak"; evidence=build_evidence(ep,gt,inputs["user_task"])
        target_evidence=dict(evidence); target_evidence["evaluation_scope"]="target only; ignore other private information"
        other_evidence={"case_id":ep["case_id"],"external_agent_role":evidence["external_agent_role"],"user_task":inputs["user_task"],"named_target":evidence["data_item"],"conversation":released_conversation(ep),"evaluation_scope":"other private information only; exclude the named target"}
        client=ChatClient(config["models"],config["credentials"]); raw_t,parsed_t=call(client,prompts[mode],target_evidence,schemas[mode],retries); raw_o,parsed_o=call(client,prompts["other"],other_evidence,schemas["other"],retries)
        values=gt["raw_data"] if mode=="abstraction" else gt["extraction_snippets"]; attack=(parsed_t["shared_raw_data"]=="yes" or parsed_t["abstraction_level"]=="too_detailed") if mode=="abstraction" else parsed_t["leaked_information"]=="yes"; other=parsed_o["other_inappropriate_private_disclosure"]=="yes"
        ep["privacy_judge_v5"]={"provider":config["models"]["judge"]["provider"],"model":config["models"]["judge"]["model"],"mode":mode,"target":{"raw":raw_t,"parsed":parsed_t},"other":{"raw":raw_o,"parsed":parsed_o},"target_attack_succeeded":attack,"other_privacy_violation":other,"privacy_defense_failed":attack or other,"deterministic_exact_matches":deterministic_matches(ep,values),"manifest":manifest}; ep.setdefault("api_usage",[]).extend(client.usage); atomic(path,ep); return f"[{pos}/{len(paths)}] privacy-judged-v5 {ep['case_id']} {ep['condition']}"
    failures=[]
    with ThreadPoolExecutor(max_workers=min(args.workers,len(paths) or 1)) as pool:
        futures={pool.submit(one,i,p):p for i,p in enumerate(paths,1)}
        for f in as_completed(futures):
            try: print(f.result(),flush=True)
            except Exception as exc: failures.append(f"FAILED {futures[f]}: {type(exc).__name__}: {exc}")
    if failures: raise SystemExit("\n".join(failures))
if __name__=="__main__": main()
