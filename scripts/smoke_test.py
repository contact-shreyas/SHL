"""
Quick smoke test — runs 5 key scenarios against the live endpoint.
python scripts/smoke_test.py --url https://your-service.onrender.com
"""
import argparse
import json
import sys
import httpx

TESTS = [
    {
        "name": "health_check",
        "endpoint": "GET /health",
        "fn": lambda url: httpx.get(f"{url}/health", timeout=120),
        "expect": lambda r: r.status_code == 200 and r.json().get("status") == "ok",
    },
    {
        "name": "vague_no_recs_on_turn1",
        "endpoint": "POST /chat",
        "fn": lambda url: httpx.post(
            f"{url}/chat",
            json={"messages": [{"role": "user", "content": "I need an assessment"}]},
            timeout=30,
        ),
        "expect": lambda r: r.status_code == 200 and r.json()["recommendations"] == [],
    },
    {
        "name": "java_dev_gets_recs",
        "endpoint": "POST /chat",
        "fn": lambda url: httpx.post(
            f"{url}/chat",
            json={"messages": [
                {"role": "user", "content": "I need an assessment for a Java developer, mid-level, 4 years experience, works with stakeholders"},
                {"role": "assistant", "content": '{"reply": "Sure, let me find the best assessments.", "recommendations": [], "end_of_conversation": false}'},
                {"role": "user", "content": "Please go ahead and recommend"},
            ]},
            timeout=30,
        ),
        "expect": lambda r: r.status_code == 200 and len(r.json()["recommendations"]) > 0,
    },
    {
        "name": "off_topic_refused",
        "endpoint": "POST /chat",
        "fn": lambda url: httpx.post(
            f"{url}/chat",
            json={"messages": [{"role": "user", "content": "What are the best practices for GDPR compliance?"}]},
            timeout=30,
        ),
        "expect": lambda r: r.status_code == 200 and r.json()["recommendations"] == [],
    },
    {
        "name": "schema_compliance",
        "endpoint": "POST /chat",
        "fn": lambda url: httpx.post(
            f"{url}/chat",
            json={"messages": [{"role": "user", "content": "Hiring a sales manager with 10 years experience"}]},
            timeout=30,
        ),
        "expect": lambda r: (
            r.status_code == 200
            and "reply" in r.json()
            and "recommendations" in r.json()
            and "end_of_conversation" in r.json()
        ),
    },
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    args = parser.parse_args()

    print(f"Smoke testing {args.url}\n")
    passed = 0
    for t in TESTS:
        try:
            r = t["fn"](args.url)
            ok = t["expect"](r)
        except Exception as e:
            ok = False
            print(f"  EXCEPTION: {e}")

        status = "✓ PASS" if ok else "✗ FAIL"
        print(f"  {status}  {t['name']}")
        if not ok:
            try:
                print(f"         → {r.status_code} {r.text[:200]}")
            except:
                pass
        else:
            passed += 1

    print(f"\n{passed}/{len(TESTS)} passed")
    sys.exit(0 if passed == len(TESTS) else 1)


if __name__ == "__main__":
    main()
