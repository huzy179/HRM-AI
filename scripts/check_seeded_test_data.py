from __future__ import annotations

import argparse
import json

import requests


def main() -> None:
    parser = argparse.ArgumentParser(description="Check seeded fake HRM AI data through the API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin123")
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

    campaigns = session.get(f"{base_url}/campaigns", timeout=30)
    campaigns.raise_for_status()
    print("CAMPAIGNS")
    print(json.dumps(campaigns.json()[:10], indent=2, ensure_ascii=False))

    policy_docs = session.get(f"{base_url}/policy/documents", timeout=30)
    policy_docs.raise_for_status()
    print("POLICY_DOCS")
    print(json.dumps(policy_docs.json()[:10], indent=2, ensure_ascii=False))

    print("CANDIDATES_BY_CAMPAIGN")
    sample_profiles: list[tuple[int, int]] = []
    for campaign in campaigns.json()[:10]:
        if "Thang 07/2026" not in campaign["name"]:
            continue
        candidates = session.get(f"{base_url}/campaigns/{campaign['id']}/candidates", timeout=30)
        candidates.raise_for_status()
        print(campaign["id"], campaign["name"])
        candidate_rows = candidates.json()
        print(json.dumps(candidate_rows, indent=2, ensure_ascii=False))
        if candidate_rows:
            sample_profiles.append((campaign["id"], candidate_rows[-1]["id"]))

    print("SAMPLE_PROFILES")
    for campaign_id, candidate_id in sample_profiles:
        profile = session.get(f"{base_url}/campaigns/{campaign_id}/candidates/{candidate_id}/profile", timeout=30)
        print(campaign_id, candidate_id, profile.status_code)
        try:
            print(json.dumps(profile.json(), indent=2, ensure_ascii=False))
        except Exception:
            print(profile.text)

    chat = session.post(
        f"{base_url}/policy/chat",
        json={
            "query": "Nhân viên chính thức có bao nhiêu ngày phép năm và phụ cấp ăn trưa là bao nhiêu?",
            "k": 5,
        },
        timeout=120,
    )
    print("RAG_CHAT")
    print(chat.status_code)
    print(json.dumps(chat.json(), indent=2, ensure_ascii=False))
    chat.raise_for_status()


if __name__ == "__main__":
    main()
