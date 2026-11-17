"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item


import math

def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate."""
    problems: list[str] = []

    # 1. Any metric value in pr["metrics"] that is NaN or inf
    for m, v in pr.get("metrics", {}).items():
        if isinstance(v, (int, float)) and (math.isnan(v) or math.isinf(v)):
            problems.append(f"metric {m} is {v}")

    # 2. evaluator_failures non-empty
    if pr.get("evaluator_failures"):
        problems.append(f"evaluator_failures: {pr['evaluator_failures'][:2]}")

    # 3. len(pr["rows"]) != manifest items x len(manifest seeds) or duplicate rows
    items_count = pr.get("manifest", {}).get("items", 0)
    seeds = pr.get("manifest", {}).get("seeds", [])
    expected_row_count = items_count * len(seeds)
    rows = pr.get("rows", [])
    if len(rows) != expected_row_count:
        problems.append(f"row count {len(rows)} != expected {expected_row_count}")

    pr_pairs = [(r.get("item_id"), r.get("seed")) for r in rows]
    if len(pr_pairs) != len(set(pr_pairs)):
        problems.append("duplicate (item_id, seed) rows in PR")

    base_pairs = [(r.get("item_id"), r.get("seed")) for r in base.get("rows", [])]
    if base_pairs and set(pr_pairs) != set(base_pairs):
        problems.append("PR (item_id, seed) set differs from baseline")

    # 4. A row whose value for a graded spec metric is None
    spec_metrics = [m["id"] for m in spec.get("metrics", [])]
    for r in rows:
        for m in spec_metrics:
            if m in r and r[m] is None:
                problems.append(f"item {r.get('item_id')} seed {r.get('seed')} has None for metric {m}")
                break
        if problems and problems[-1].startswith("item ") and "has None for metric" in problems[-1]:
            break

    # 5. An item's slice tags in PR rows differ from the baseline's
    base_slices = {(r["item_id"], r["seed"]): tuple(sorted(r.get("slices") or [])) for r in base.get("rows", [])}
    for r in rows:
        key = (r.get("item_id"), r.get("seed"))
        if key in base_slices:
            if tuple(sorted(r.get("slices") or [])) != base_slices[key]:
                problems.append(f"item {r.get('item_id')} slices modified")
                break

    # 6. Ratchet check against base_spec
    if base_spec and base_spec.get("eval_set_version") == spec.get("eval_set_version"):
        base_m_map = {m["id"]: m for m in base_spec.get("metrics", [])}
        for mid, bm in base_m_map.items():
            pm = next((m for m in spec.get("metrics", []) if m["id"] == mid), None)
            if not pm:
                problems.append(f"ratchet: metric {mid} dropped from spec")
                continue
            if bm.get("blocking") and not pm.get("blocking"):
                problems.append(f"ratchet: metric {mid} made non-blocking")
            bth = bm.get("threshold", {})
            pth = pm.get("threshold", {})
            if "min" in bth:
                if "min" not in pth or pth["min"] < bth["min"]:
                    problems.append(f"ratchet: metric {mid} min threshold lowered from {bth['min']} to {pth.get('min')}")
            if "max" in bth:
                if "max" not in pth or pth["max"] > bth["max"]:
                    problems.append(f"ratchet: metric {mid} max threshold raised from {bth['max']} to {pth.get('max')}")
            if bth.get("no_significant_drop") and not pth.get("no_significant_drop"):
                problems.append(f"ratchet: metric {mid} dropped no_significant_drop")

        base_s_map = {s["name"]: s for s in base_spec.get("slices") or []}
        for sname, bs_item in base_s_map.items():
            ps_item = next((s for s in spec.get("slices") or [] if s["name"] == sname), None)
            if not ps_item:
                problems.append(f"ratchet: slice {sname} dropped from spec")
                continue
            if bs_item.get("blocking") and not ps_item.get("blocking"):
                problems.append(f"ratchet: slice {sname} made non-blocking")
            if "min" in bs_item:
                if "min" not in ps_item or ps_item["min"] < bs_item["min"]:
                    problems.append(f"ratchet: slice {sname} min lowered")
            if bs_item.get("no_significant_drop") and not ps_item.get("no_significant_drop"):
                problems.append(f"ratchet: slice {sname} dropped no_significant_drop")

    return problems


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for s in spec.get("slices") or []:
        sname = s["name"]
        mid = s.get("metric", "pass_rate")
        th_min = s.get("min")
        is_blocking = s.get("blocking", True)

        pr_items = per_item(pr, mid, slice_name=sname)
        val = sum(pr_items.values()) / len(pr_items) if pr_items else None

        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif th_min is not None and val < th_min:
            verdict = "fail"

        if s.get("no_significant_drop") and pr_items:
            base_items = per_item(base, mid, slice_name=sname)
            common_keys = sorted(set(pr_items) & set(base_items))
            if common_keys:
                d, lo, hi = stats.paired_bootstrap(
                    [pr_items[k] for k in common_keys],
                    [base_items[k] for k in common_keys],
                    n_resamples=bs.get("n_resamples", 1000),
                    rng=bs.get("rng", 2027)
                )
                note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                if hi < 0:
                    verdict = "fail"

        sid = f"slice:{sname}/{mid}"
        if verdict != "ok" and is_blocking:
            blocked.append(sid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if is_blocking else "warn")
        val_str = f"{val:.4f}" if val is not None else "None"
        th_str = f"min={th_min}" if th_min is not None else ""
        lines.append(f"  {sid:<28} {val_str:<8} {th_str:<34} {note:<28} {label}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
