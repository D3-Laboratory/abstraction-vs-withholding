#!/usr/bin/env python3
"""Regenerate every table, Fig. 2 and numbers.json offline and compare them with the published copies.

    python3 reproduce.py                    # unpack outputs (once), run make_tables.py, compare
    python3 reproduce.py --check-analyses   # also re-run the analyses on the released outputs and compare

No model is called. Exit status 1 if anything differs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PUBLISHED = ROOT / "paper/wllfm-2026/floats"
PUBLISHED_FIG = ROOT / "paper/wllfm-2026/figures/fig-judges.pdf"
OUT = ROOT / "reproduced/floats"
OUT_FIG = ROOT / "reproduced/figures/fig-judges.pdf"
GENERATED = ["tab-configurations.tex", "tab-outcomes.tex", "tab-human.tex", "tab-instruction.tex",
             "tab-identifiers.tex", "tab-cost.tex", "fig-judges.tex", "numbers.json"]
# read from aggregate outputs in experiments/results/ rather than recomputed
HUMAN_DEPENDENT = {"tab-human.tex", "numbers.json:table_human", "numbers.json:labels",
                   "numbers.json:calibration.outcome_label_sensitivity", "numbers.json:calibration.c1_coarser_split",
                   "numbers.json:calibration.table_iv_label_calibration",
                   "numbers.json:calibration.withholding_cost_necessity_subset"}
MARKER = ROOT / "experiments/results/.unpacked"
PY = sys.executable


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True)


def diff_paths(a, b, path=""):
    if type(a) != type(b):
        return [path or "/"]
    if isinstance(a, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}/{k}")
            else:
                out += diff_paths(a[k], b[k], f"{path}/{k}")
        return out
    if isinstance(a, list):
        if len(a) != len(b):
            return [path]
        return [p for i, (x, y) in enumerate(zip(a, b)) for p in diff_paths(x, y, f"{path}[{i}]")]
    return [] if a == b else [path]


def compare_floats() -> bool:
    ok = True
    for name in GENERATED:
        new, ref = OUT / name, PUBLISHED / name
        if name != "numbers.json":
            same = new.read_bytes() == ref.read_bytes()
            tag = " (read from aggregate outputs)" if name in HUMAN_DEPENDENT else ""
            print(f"  {name:24s} {'identical' if same else 'DIFFERS'}{tag}")
            ok &= same
            continue
        a, b = json.loads(new.read_text(encoding="utf-8")), json.loads(ref.read_text(encoding="utf-8"))
        print(f"  numbers.json             {'byte-identical' if new.read_bytes() == ref.read_bytes() else 'bytes differ'}")
        keys = list(b) + [k for k in a if k not in b]
        for k in keys:
            subkeys = [(k, None)] if k != "calibration" else [(k, s) for s in sorted(set(a.get(k, {})) | set(b.get(k, {})))]
            for k1, s in subkeys:
                x = a.get(k1) if s is None else a.get(k1, {}).get(s)
                y = b.get(k1) if s is None else b.get(k1, {}).get(s)
                label = f"numbers.json:{k1}" + (f".{s}" if s else "")
                d = diff_paths(x, y)
                tag = " (read from aggregate outputs)" if label in HUMAN_DEPENDENT else ""
                print(f"    {label[13:]:52s} {'identical' if not d else f'DIFFERS at {d[:3]}'}{tag}")
                ok &= not d
    if OUT_FIG.exists() and PUBLISHED_FIG.exists():
        same = OUT_FIG.read_bytes() == PUBLISHED_FIG.read_bytes()
        print(f"  figures/fig-judges.pdf   {'byte-identical' if same else 'bytes differ (plotted data are compared via numbers.json:judge_sameday; PDF bytes depend on the matplotlib version)'}")
    return ok


ANALYSES = [  # (command, outputs to compare, keys to ignore in JSON outputs)
    ([PY, "experiments/scripts/withholding_cost_existing_runs_v23.py"], "experiments/results/withholding-cost-existing-runs", ()),
    ([PY, "experiments/scripts/generalize_first_transitions_v23.py"], "experiments/results/generalize-first-transitions", ()),
    ([PY, "experiments/scripts/benchmark_judge_scores_withheld_vs_abstracted.py"], "experiments/results/benchmark-judge-scores", ()),
    ([PY, "experiments/scripts/redactor_action_shares.py"], "experiments/results/redactor-action-shares", ()),
    ([PY, "experiments/scripts/holm_main_runs_tests.py"], "experiments/results/holm-main-runs", ()),
    ([PY, "experiments/scripts/analyze_judge_counterfactual_v26.py"], "experiments/results/judge-counterfactual-v26/analysis", ()),
    ([PY, "experiments/scripts/analyze_judge_counterfactual_v26.py", "--baseline", "same-day"],
     "experiments/results/judge-counterfactual-v26-baseline-rerun/analysis", ()),
    ([PY, "experiments/scripts/analyze_judge_counterfactual_v26_drift.py"],
     "experiments/results/judge-counterfactual-v26-baseline-rerun/analysis", ()),
    ([PY, "experiments/scripts/analyze_judge_counterfactual_sameday.py"],
     "experiments/results/judge-counterfactual-v26-baseline-rerun/analysis-sameday", ()),
    ([PY, "experiments/scripts/score_withholding_cost_pilot_v27.py", "--config",
      "experiments/configs/withholding-cost-pilot-v27b-coarser.json", "--cases-file",
      "experiments/configs/withholding-cost-pilot-v27-cases.json", "--scores-dir", "scores_fixed_4var_v2"],
     "experiments/results/withholding-cost-pilot-v27/scores_fixed_4var_v2", ("consistency_with_scores_fixed",)),
    ([PY, "experiments/scripts/analyze_withholding_cost_v27b_coarser.py"],
     "experiments/results/withholding-cost-pilot-v27/scores_fixed_4var_v2", ("consistency_with_scores_fixed",)),
]


KNOWN = {  # released outputs written by an earlier revision of the script; all numbers are identical
    "experiments/results/judge-counterfactual-v26/analysis/summary.json":
        "the released file predates the 'reference_root' field added to the script",
    "experiments/results/judge-counterfactual-v26/analysis/summary.md":
        "the released file predates the sentence naming the comparator folder",
}


def check_analyses() -> bool:
    ok = True
    dirs = sorted({d for _, d, _ in ANALYSES})
    with tempfile.TemporaryDirectory() as tmp:
        snap = Path(tmp)
        for d in dirs:
            shutil.copytree(ROOT / d, snap / d)
        try:
            for cmd, d, ignore in ANALYSES:
                print("  running", " ".join(Path(c).name if i < 2 else c for i, c in enumerate(cmd[1:], 1)))
                run(cmd)
            for d in dirs:
                for ref in sorted((snap / d).rglob("*")):
                    if not ref.is_file():
                        continue
                    rel = ref.relative_to(snap)
                    new = ROOT / rel
                    if ref.suffix in (".png", ".pdf"):
                        continue  # image bytes depend on the matplotlib version
                    same = new.exists() and new.read_bytes() == ref.read_bytes()
                    note = ""
                    if not same and new.exists() and ref.suffix in (".csv", ".txt", ".md"):
                        norm = lambda p: sorted(l.rstrip().rstrip(",") for l in p.read_text(encoding="utf-8").splitlines())
                        if norm(new) == norm(ref):
                            same, note = True, " (same lines; order depends on directory listing order)"
                    if not same and str(rel) in KNOWN:
                        same, note = True, f" (known difference: {KNOWN[str(rel)]})"
                    if not same and new.exists() and ref.suffix == ".json":
                        a, b = json.loads(new.read_text(encoding="utf-8")), json.loads(ref.read_text(encoding="utf-8"))
                        ign = [ig for _, dd, igs in ANALYSES if dd == d for ig in igs]
                        for ig in ign:
                            if isinstance(a, dict):
                                a.pop(ig, None); b.pop(ig, None)
                        dp = diff_paths(a, b)
                        same, note = not dp, (f" (identical after ignoring {ign})" if not dp else f" DIFFERS at {dp[:3]}")
                    print(f"    {str(rel):95s} {'identical' if same else 'DIFFERS'}{note}")
                    ok &= same
            t = run([PY, "experiments/scripts/task_metrics_case_bootstrap_v3.py"]).stdout
            ref = (ROOT / "experiments/results/task-metrics-case-bootstrap-v3.txt").read_text(encoding="utf-8")
            same = t.strip() == ref.strip()
            print(f"    {'task_metrics_case_bootstrap_v3.py stdout vs task-metrics-case-bootstrap-v3.txt':95s} {'identical' if same else 'DIFFERS'}")
            ok &= same
        finally:
            for d in dirs:  # restore the released files (file by file; directories are kept)
                keep = {f.relative_to(snap / d) for f in (snap / d).rglob("*") if f.is_file()}
                for f in (ROOT / d).rglob("*"):
                    if f.is_file() and f.relative_to(ROOT / d) not in keep:
                        f.unlink()
                for rel in keep:
                    shutil.copyfile(snap / d / rel, ROOT / d / rel)
    return ok


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-analyses", action="store_true")
    args = ap.parse_args()
    manifest_sha = hashlib.sha256((ROOT / "outputs/MANIFEST.json").read_bytes()).hexdigest()
    if not MARKER.exists() or MARKER.read_text().strip() != manifest_sha:
        print("unpacking outputs/ ...")
        print(" ", run([PY, "tools/unpack_outputs.py"]).stdout.strip())
        MARKER.write_text(manifest_sha + "\n")
    print("running paper/wllfm-2026/make_tables.py ...")
    r = run([PY, "paper/wllfm-2026/make_tables.py"])
    print("  " + r.stdout.strip().replace("\n", "\n  "))
    print("comparing reproduced/ with the published floats:")
    ok = compare_floats()
    if args.check_analyses:
        print("re-running the analyses on the released outputs:")
        ok &= check_analyses()
    print("RESULT:", "all compared outputs match" if ok else "differences found")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
