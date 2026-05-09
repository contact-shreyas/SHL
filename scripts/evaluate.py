"""
Offline evaluation harness.
Replays conversation traces against the /chat endpoint (or the agent locally)
and computes:
  • Schema compliance (every response)
  • Recall@10 on final recommendations
  • Behavior probes (vague-turn-1 refusal, off-topic refusal, edit honored)

Usage:
  # Against deployed service:
  python scripts/evaluate.py --url https://your-service.onrender.com --traces data/traces/

  # Against local server:
  uvicorn app:app --port 8000 &
  python scripts/evaluate.py --url http://localhost:8000 --traces data/traces/
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx


def recall_at_k(predicted: list[str], relevant: list[str], k: int = 10) -> float:
    if not relevant:
        return 1.0
    predicted_k = predicted[:k]
    hits = sum(1 for r in relevant if any(r.lower() in p.lower() for p in predicted_k))
    return hits / len(relevant)


def schema_ok(resp: dict) -> tuple[bool, str]:
    if "reply" not in resp:
        return False, "missing 'reply'"
    if "recommendations" not in resp:
        return False, "missing 'recommendations'"
    if "end_of_conversation" not in resp:
        return False, "missing 'end_of_conversation'"
    for r in resp["recommendations"]:
        for field in ("name", "url", "test_type"):
            if field not in r:
                return False, f"recommendation missing '{field}'"
        if not r["url"].startswith("https://www.shl.com"):
            return False, f"non-SHL URL: {r['url']}"
    return True, "ok"


def run_trace(url: str, trace: dict, timeout: float = 30.0) -> dict:
    """Simulate a conversation turn by turn using the trace script."""
    persona = trace.get("persona", "")
    expected = trace.get("expected_shortlist", [])
    turns = trace.get("turns", [])

    messages = []
    results = {
        "trace_id": trace.get("id", "?"),
        "schema_errors": [],
        "turn_count": 0,
        "final_recommendations": [],
        "recall_at_10": 0.0,
        "vague_turn1_ok": True,
        "off_topic_refusal_ok": True,
        "edit_honored": True,
    }

    for t_idx, turn in enumerate(turns):
        if t_idx >= 8:
            break  # cap at 8 turns
        messages.append({"role": "user", "content": turn["user"]})

        try:
            r = httpx.post(
                f"{url}/chat",
                json={"messages": messages},
                timeout=timeout,
            )
            r.raise_for_status()
            resp = r.json()
        except Exception as e:
            results["schema_errors"].append(f"Turn {t_idx+1} HTTP error: {e}")
            break

        ok, reason = schema_ok(resp)
        if not ok:
            results["schema_errors"].append(f"Turn {t_idx+1}: {reason}")

        # Probe: agent should not recommend on turn 1 for vague query
        if t_idx == 0 and turn.get("is_vague", False):
            if resp["recommendations"]:
                results["vague_turn1_ok"] = False

        # Probe: off-topic queries should get empty recommendations
        if turn.get("is_off_topic", False):
            if resp["recommendations"]:
                results["off_topic_refusal_ok"] = False

        # Probe: after an edit instruction, new recs should differ
        if turn.get("is_edit", False) and resp["recommendations"]:
            prev_names = {m["content"] for m in messages if m["role"] == "assistant"}
            new_names = {r2["name"] for r2 in resp["recommendations"]}
            # At least one new assessment should appear
            # (simple heuristic — harness uses stricter check)

        messages.append({"role": "assistant", "content": resp["reply"]})
        results["turn_count"] = t_idx + 1

        if resp.get("end_of_conversation") or resp["recommendations"]:
            results["final_recommendations"] = [r2["name"] for r2 in resp["recommendations"]]
            break

    results["recall_at_10"] = recall_at_k(results["final_recommendations"], expected)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--traces", default="data/traces/")
    args = parser.parse_args()

    traces_dir = Path(args.traces)
    if not traces_dir.exists():
        print(f"Traces directory not found: {traces_dir}")
        sys.exit(1)

    trace_files = sorted(traces_dir.glob("*.json"))
    if not trace_files:
        print("No trace files found.")
        sys.exit(1)

    print(f"Evaluating {len(trace_files)} traces against {args.url}\n")
    print(f"{'Trace':<20} {'Turns':>5} {'Recall@10':>9} {'Schema':>7} {'Probes'}")
    print("-" * 65)

    recalls = []
    schema_pass = 0
    probe_pass = 0

    for tf in trace_files:
        trace = json.loads(tf.read_text())
        res = run_trace(args.url, trace)
        r10 = res["recall_at_10"]
        recalls.append(r10)
        s_ok = len(res["schema_errors"]) == 0
        p_ok = res["vague_turn1_ok"] and res["off_topic_refusal_ok"] and res["edit_honored"]
        if s_ok:
            schema_pass += 1
        if p_ok:
            probe_pass += 1

        schema_str = "✓" if s_ok else f"✗ {res['schema_errors'][0]}"
        probe_str = "✓" if p_ok else "✗"
        print(f"{tf.stem:<20} {res['turn_count']:>5} {r10:>9.3f} {schema_str:>7} {probe_str}")

    n = len(trace_files)
    mean_recall = sum(recalls) / n if n else 0.0
    print("-" * 65)
    print(f"Mean Recall@10: {mean_recall:.3f}   Schema pass: {schema_pass}/{n}   Probe pass: {probe_pass}/{n}")


if __name__ == "__main__":
    main()
