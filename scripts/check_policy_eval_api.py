from __future__ import annotations

import argparse
import json
import time

import requests


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Policy Eval run and wait for the result.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--name", default="Smoke policy eval")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    session = requests.Session()
    created = session.post(f"{base_url}/policy/evals/runs", json={"name": args.name}, timeout=30)
    print("create", created.status_code, created.text)
    created.raise_for_status()
    run_id = created.json()["run_id"]

    detail = None
    for _ in range(90):
        response = session.get(f"{base_url}/policy/evals/runs/{run_id}", timeout=30)
        response.raise_for_status()
        detail = response.json()
        print(
            json.dumps(
                {
                    "status": detail["status"],
                    "score": detail["score"],
                    "passed": detail["passed_questions"],
                    "total": detail["total_questions"],
                    "error": detail["error"],
                },
                ensure_ascii=False,
            )
        )
        if detail["status"] in {"DONE", "ERROR"}:
            break
        time.sleep(2)

    print(json.dumps(detail, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
