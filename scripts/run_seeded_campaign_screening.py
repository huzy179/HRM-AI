from __future__ import annotations

import argparse
import json
import time

import requests


def main() -> None:
    parser = argparse.ArgumentParser(description="Run screening for seeded test campaigns and print rankings.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin123")
    parser.add_argument("--campaign-ids", nargs="+", type=int, default=[2, 3, 4])
    parser.add_argument("--skip-start", action="store_true", help="Do not enqueue new screening jobs.")
    parser.add_argument("--extract-profiles", action="store_true", help="Extract candidate profiles before screening.")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    session = requests.Session()
    login = session.post(
        f"{base_url}/auth/login",
        json={"username": args.username, "password": args.password},
        timeout=30,
    )
    login.raise_for_status()
    session.headers.update({"Authorization": f"Bearer {login.json()['access_token']}"})

    baseline_screen_count = 0
    baseline_jobs_done = 0
    before = session.get(f"{base_url}/metrics/summary", timeout=30)
    if before.ok:
        baseline_jobs_done = int(before.json().get("jobs_done", 0) or 0)
        for row in before.json().get("by_type", []):
            if row.get("job_type") == "screen_campaign":
                baseline_screen_count = int(row.get("count", 0) or 0)

    if args.extract_profiles:
        profile_jobs = 0
        print("START_PROFILE_EXTRACTION")
        for campaign_id in args.campaign_ids:
            candidates = session.get(f"{base_url}/campaigns/{campaign_id}/candidates", timeout=30)
            candidates.raise_for_status()
            for candidate in candidates.json():
                response = session.post(
                    f"{base_url}/campaigns/{campaign_id}/candidates/{candidate['id']}/profile",
                    timeout=30,
                )
                print(campaign_id, candidate["id"], response.status_code, response.text)
                response.raise_for_status()
                profile_jobs += 1

        print("WAITING_PROFILE_EXTRACTION")
        expected_profile_done = baseline_jobs_done + profile_jobs
        for _ in range(120):
            metrics = session.get(f"{base_url}/metrics/summary", timeout=30)
            metrics.raise_for_status()
            payload = metrics.json()
            print(json.dumps(payload, ensure_ascii=False))
            if payload.get("jobs_failed", 0) > 0:
                break
            if payload.get("jobs_done", 0) >= expected_profile_done:
                break
            time.sleep(2)
        baseline_jobs_done = expected_profile_done

    if not args.skip_start:
        print("START_SCREENING")
        for campaign_id in args.campaign_ids:
            response = session.post(f"{base_url}/campaigns/{campaign_id}/screen", timeout=30)
            print(campaign_id, response.status_code, response.text)
            response.raise_for_status()

    print("WAITING")
    for _ in range(60):
        metrics = session.get(f"{base_url}/metrics/summary", timeout=30)
        metrics.raise_for_status()
        payload = metrics.json()
        print(json.dumps(payload, ensure_ascii=False))
        screen_row = next((row for row in payload.get("by_type", []) if row.get("job_type") == "screen_campaign"), None)
        if payload.get("jobs_failed", 0) > 0:
            break
        expected_screen_count = baseline_screen_count if args.skip_start else baseline_screen_count + len(args.campaign_ids)
        expected_jobs_done = baseline_jobs_done if args.skip_start else baseline_jobs_done + len(args.campaign_ids)
        if (
            screen_row
            and screen_row.get("count", 0) >= expected_screen_count
            and screen_row.get("failed", 0) == 0
            and payload.get("jobs_done", 0) >= expected_jobs_done
        ):
            break
        time.sleep(2)

    print("RANKINGS")
    for campaign_id in args.campaign_ids:
        ranking = session.get(f"{base_url}/campaigns/{campaign_id}/ranking", timeout=30)
        print(campaign_id, ranking.status_code)
        print(json.dumps(ranking.json(), indent=2, ensure_ascii=False))
        ranking.raise_for_status()


if __name__ == "__main__":
    main()
