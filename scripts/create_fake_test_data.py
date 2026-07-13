from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "data" / "test_fixtures"
CAMPAIGN_DIR = FIXTURE_DIR / "campaigns"
POLICY_DIR = FIXTURE_DIR / "policy_docs"


CAMPAIGNS = [
    {
        "slug": "backend_python_fastapi",
        "name": "Backend Python FastAPI - Thang 07/2026",
        "settings": {
            "w_embed": 0.7,
            "required_skills": ["python", "fastapi", "postgresql", "docker", "redis", "pytest"],
            "min_years_override": 3.0,
        },
        "jd_file": "jd_backend_python_fastapi.pdf",
        "jd_title": "JD - Senior Python Backend Engineer",
        "jd": [
            "Vi tri: Senior Python Backend Engineer",
            "Dia diem: Ho Chi Minh City / Hybrid",
            "Kinh nghiem yeu cau: toi thieu 3 nam phat trien backend.",
            "Ky nang bat buoc: Python, FastAPI, PostgreSQL, Redis, Docker, pytest, REST API.",
            "Ky nang uu tien: Celery/RQ, observability, OpenTelemetry, Prometheus, CI/CD.",
            "Cong viec: thiet ke API, toi uu truy van SQL, xay dung job queue, viet test tu dong, van hanh service tren Docker.",
            "Tieu chi danh gia: ung vien can co kinh nghiem production backend, debugging, logging, security co ban va kha nang phoi hop voi frontend.",
        ],
        "cvs": [
            {
                "file": "cv_backend_top_match_linh_nguyen.pdf",
                "title": "CV - Linh Nguyen",
                "body": [
                    "Linh Nguyen - Senior Backend Engineer",
                    "Email: linh.nguyen.test@example.com | Phone: 0901000001",
                    "Kinh nghiem: 5 nam phat trien backend Python.",
                    "Ky nang: Python, FastAPI, PostgreSQL, Redis, Docker, pytest, REST API, RQ, Prometheus, OpenTelemetry.",
                    "Du an gan day: xay dung HR SaaS voi FastAPI, PostgreSQL, Redis queue, Docker Compose, CI/CD.",
                    "Thanh tich: giam 42% thoi gian API latency bang index SQL va caching Redis.",
                    "Hoc van: Dai hoc Bach Khoa, Khoa hoc may tinh.",
                ],
            },
            {
                "file": "cv_backend_mid_match_minh_tran.pdf",
                "title": "CV - Minh Tran",
                "body": [
                    "Minh Tran - Python Developer",
                    "Email: minh.tran.test@example.com | Phone: 0901000002",
                    "Kinh nghiem: 2 nam phat trien ung dung Python va Flask.",
                    "Ky nang: Python, Flask, MySQL, REST API, basic Docker, unit test.",
                    "Du an: dashboard noi bo, API tich hop CRM, script ETL hang ngay.",
                    "Chua co nhieu kinh nghiem FastAPI, Redis va PostgreSQL production.",
                    "Hoc van: Dai hoc Khoa hoc Tu nhien, Cong nghe thong tin.",
                ],
            },
            {
                "file": "cv_backend_low_match_hoa_pham.pdf",
                "title": "CV - Hoa Pham",
                "body": [
                    "Hoa Pham - Sales Executive",
                    "Email: hoa.pham.test@example.com | Phone: 0901000003",
                    "Kinh nghiem: 4 nam ban hang B2B, cham soc khach hang va quan ly pipeline.",
                    "Ky nang: CRM, negotiation, presentation, market research, account management.",
                    "Thanh tich: dat 120% target doanh so nam 2025.",
                    "Khong co kinh nghiem Python, FastAPI, PostgreSQL, Redis hoac Docker.",
                ],
            },
            {
                "file": "cv_backend_junior_anh_le.pdf",
                "title": "CV - Anh Le",
                "body": [
                    "Anh Le - Junior Backend Engineer",
                    "Email: anh.le.test@example.com | Phone: 0901000004",
                    "Kinh nghiem: 1 nam internship va 8 thang full-time.",
                    "Ky nang: Python, FastAPI co ban, SQLite, Docker co ban, Git, REST API.",
                    "Du an: API quan ly kho, authentication JWT, test mot so endpoint bang pytest.",
                    "Can huong dan them ve PostgreSQL tuning, Redis queue va monitoring.",
                ],
            },
            {
                "file": "cv_backend_scanned_like_poor_quality.pdf",
                "title": "CV - Scanned Like",
                "body": [
                    "SCAN COPY - Nguyen Van OCR",
                    "Email: ocr.backend.test@example.com",
                    "3 nam Python backend, FastAPI, Docker, PostgreSQL.",
                    "File nay co chu thua, khoang cach la va noi dung ngan de test quality/OCR fallback.",
                    "P y t h o n   F a s t A P I   D o c k e r   R e d i s",
                ],
            },
        ],
    },
    {
        "slug": "frontend_nextjs",
        "name": "Frontend Next.js - Thang 07/2026",
        "settings": {
            "w_embed": 0.65,
            "required_skills": ["typescript", "react", "next.js", "tailwind css", "api integration"],
            "min_years_override": 2.0,
        },
        "jd_file": "jd_frontend_nextjs.pdf",
        "jd_title": "JD - Frontend Engineer Next.js",
        "jd": [
            "Vi tri: Frontend Engineer Next.js",
            "Kinh nghiem yeu cau: toi thieu 2 nam lam viec voi React/Next.js.",
            "Ky nang bat buoc: TypeScript, React, Next.js, Tailwind CSS, API integration, responsive UI.",
            "Ky nang uu tien: accessibility, Playwright, component design, state management.",
            "Cong viec: xay dung man hinh CV screening, dashboard, form upload, xu ly loading/error states.",
        ],
        "cvs": [
            {
                "file": "cv_frontend_top_match_nam_do.pdf",
                "title": "CV - Nam Do",
                "body": [
                    "Nam Do - Frontend Engineer",
                    "Email: nam.do.test@example.com | Phone: 0902000001",
                    "Kinh nghiem: 4 nam React va 3 nam Next.js.",
                    "Ky nang: TypeScript, React, Next.js, Tailwind CSS, API integration, Playwright, accessibility.",
                    "Du an: admin portal, realtime dashboard, upload workflow, design system.",
                ],
            },
            {
                "file": "cv_frontend_mid_match_thao_vo.pdf",
                "title": "CV - Thao Vo",
                "body": [
                    "Thao Vo - Web Developer",
                    "Email: thao.vo.test@example.com | Phone: 0902000002",
                    "Kinh nghiem: 2 nam JavaScript, React, CSS.",
                    "Ky nang: React, JavaScript, CSS Modules, REST API. Moi hoc TypeScript va Next.js.",
                    "Du an: landing page, ecommerce UI, form validation.",
                ],
            },
            {
                "file": "cv_frontend_low_match_quan_bui.pdf",
                "title": "CV - Quan Bui",
                "body": [
                    "Quan Bui - Data Analyst",
                    "Email: quan.bui.test@example.com | Phone: 0902000003",
                    "Kinh nghiem: 3 nam SQL, Excel, Power BI, dashboard analytics.",
                    "Khong co kinh nghiem React, Next.js, TypeScript hoac Tailwind CSS.",
                ],
            },
        ],
    },
    {
        "slug": "data_ai_engineer",
        "name": "Data AI Engineer - Thang 07/2026",
        "settings": {
            "w_embed": 0.72,
            "required_skills": ["python", "sql", "pandas", "machine learning", "rag", "docker"],
            "min_years_override": 3.0,
        },
        "jd_file": "jd_data_ai_engineer.pdf",
        "jd_title": "JD - Data AI Engineer",
        "jd": [
            "Vi tri: Data AI Engineer",
            "Kinh nghiem yeu cau: toi thieu 3 nam lam viec voi data pipeline hoac AI application.",
            "Ky nang bat buoc: Python, SQL, pandas, machine learning, RAG, vector database, Docker.",
            "Ky nang uu tien: LangChain, Chroma, evaluation dataset, prompt engineering, monitoring model quality.",
            "Cong viec: xay dung pipeline ingest tai lieu, xu ly du lieu ung vien, viet feature extraction va danh gia ket qua AI.",
            "Ung vien can hieu cach do chat luong retrieval, xu ly du lieu thieu, logging, retry va batch jobs.",
        ],
        "cvs": [
            {
                "file": "cv_data_ai_top_match_khanh_mai.pdf",
                "title": "CV - Khanh Mai",
                "body": [
                    "Khanh Mai - Data AI Engineer",
                    "Email: khanh.mai.test@example.com | Phone: 0903000001",
                    "Kinh nghiem: 5 nam data engineering va 2 nam xay dung RAG application.",
                    "Ky nang: Python, SQL, pandas, scikit-learn, LangChain, Chroma, vector database, Docker, evaluation dataset.",
                    "Du an: policy chatbot noi bo, pipeline ingest PDF, benchmark retrieval, monitoring chat quality.",
                    "Thanh tich: tang recall retrieval tu 68% len 86% bang chunking va metadata filtering.",
                ],
            },
            {
                "file": "cv_data_ai_mid_match_tu_nguyen.pdf",
                "title": "CV - Tu Nguyen",
                "body": [
                    "Tu Nguyen - Data Engineer",
                    "Email: tu.nguyen.test@example.com | Phone: 0903000002",
                    "Kinh nghiem: 3 nam ETL, SQL va Python.",
                    "Ky nang: Python, SQL, pandas, Airflow, Docker, data warehouse.",
                    "Co tim hieu machine learning co ban nhung chua lam RAG hoac vector database production.",
                    "Du an: batch pipeline bao cao doanh thu va data quality checks.",
                ],
            },
            {
                "file": "cv_data_ai_low_match_lan_ho.pdf",
                "title": "CV - Lan Ho",
                "body": [
                    "Lan Ho - HR Generalist",
                    "Email: lan.ho.test@example.com | Phone: 0903000003",
                    "Kinh nghiem: 4 nam tuyen dung, onboarding, employee engagement.",
                    "Ky nang: HR policy, interview coordination, training, payroll support.",
                    "Khong co kinh nghiem Python, SQL, machine learning, RAG hoac Docker.",
                ],
            },
            {
                "file": "cv_data_ai_research_match_bao_tran.pdf",
                "title": "CV - Bao Tran",
                "body": [
                    "Bao Tran - Machine Learning Researcher",
                    "Email: bao.tran.test@example.com | Phone: 0903000004",
                    "Kinh nghiem: 3 nam machine learning, NLP, model evaluation.",
                    "Ky nang: Python, PyTorch, scikit-learn, pandas, experiment tracking.",
                    "Co kinh nghiem prototype RAG nhung it kinh nghiem Docker va SQL production.",
                    "Du an: semantic search cho tai lieu noi bo va classifier email ho tro khach hang.",
                ],
            },
        ],
    },
]


POLICY_DOCS = [
    {
        "file": "policy_working_rules_2026.pdf",
        "title": "Quy che lam viec va ky luat lao dong 2026",
        "category": "working_rules",
        "visibility": "employee",
        "version": "2026.1",
        "status": "published",
        "body": [
            "Gio lam viec chinh thuc: 08:30 den 17:30 tu thu Hai den thu Sau.",
            "Nhan vien duoc phep check-in tre toi da 10 phut, khong qua 3 lan moi thang.",
            "Neu di muon qua 10 phut ma khong bao truoc, quan ly co the ghi nhan vi pham ky luat.",
            "Trang phuc: lich su tu thu Hai den thu Nam; thu Sau duoc mac tu do phu hop moi truong cong so.",
            "Lam viec tu xa can duoc truong nhom phe duyet truoc tren he thong HRM.",
        ],
    },
    {
        "file": "policy_benefits_leave_2026.pdf",
        "title": "Chinh sach phuc loi, nghi phep va bao hiem 2026",
        "category": "benefits",
        "visibility": "employee",
        "version": "2026.1",
        "status": "published",
        "body": [
            "Nhan vien chinh thuc co 12 ngay phep nam.",
            "Toi da 5 ngay phep chua su dung duoc chuyen sang nam tiep theo va phai dung truoc ngay 31/03.",
            "Phu cap an trua: 500.000 VND moi thang. Phu cap gui xe: 150.000 VND moi thang.",
            "Nghi om tu 2 ngay lien tiep can co giay xac nhan cua benh vien hoac chung tu bao hiem xa hoi.",
            "Bao hiem suc khoe bo sung ap dung cho nhan vien co tham nien tu 12 thang tro len.",
        ],
    },
    {
        "file": "policy_recruitment_review_2026.pdf",
        "title": "Quy trinh tuyen dung va danh gia ung vien 2026",
        "category": "recruitment",
        "visibility": "hr",
        "version": "2026.1",
        "status": "published",
        "body": [
            "Moi campaign tuyen dung can co JD ro rang va danh sach ky nang bat buoc.",
            "HR can upload CV ung vien vao dung campaign va chay screening truoc khi gui shortlist.",
            "Ung vien co diem tong tu 75 tro len duoc uu tien phong van vong ky thuat.",
            "Ket qua AI chi la goi y; quyet dinh cuoi cung thuoc ve hoi dong phong van.",
        ],
    },
    {
        "file": "policy_remote_work_2026.pdf",
        "title": "Chinh sach lam viec tu xa 2026",
        "category": "remote_work",
        "visibility": "employee",
        "version": "2026.1",
        "status": "published",
        "body": [
            "Nhan vien duoc lam viec tu xa toi da 2 ngay moi tuan neu cong viec phu hop.",
            "Lich remote can duoc dang ky truoc 17:00 ngay lam viec lien truoc.",
            "Trong ngay remote, nhan vien phai online tren Slack tu 09:00 den 17:00 va tham gia day du meeting.",
            "Du lieu cong ty khong duoc luu tren thiet bi ca nhan khong ma hoa.",
            "Quan ly co quyen yeu cau lam tai van phong khi du an can phoi hop truc tiep.",
        ],
    },
    {
        "file": "policy_expense_training_2026.pdf",
        "title": "Chinh sach cong tac phi va dao tao 2026",
        "category": "expense_training",
        "visibility": "employee",
        "version": "2026.1",
        "status": "published",
        "body": [
            "Cong tac phi noi dia can duoc phe duyet truoc chuyen di toi thieu 3 ngay lam viec.",
            "Hoa don hop le phai nop trong vong 7 ngay sau khi ket thuc cong tac.",
            "Ngan sach dao tao ca nhan la 6.000.000 VND moi nam cho nhan vien chinh thuc.",
            "Khoa hoc co chi phi tren 3.000.000 VND can co phe duyet cua truong bo phan va HR.",
            "Nhan vien can chia se tom tat kien thuc sau khoa hoc trong buoi team sharing.",
        ],
    },
]


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_text_stream(title: str, lines: list[str]) -> str:
    commands = ["BT", "/F1 18 Tf", "56 786 Td", f"({_pdf_escape(title)}) Tj"]
    current_size = 18
    for raw in lines:
        wrapped = textwrap.wrap(raw, width=88) or [""]
        for line in wrapped:
            if current_size != 11:
                commands.append("/F1 11 Tf")
                current_size = 11
            commands.append("0 -18 Td")
            commands.append(f"({_pdf_escape(line)}) Tj")
        commands.append("0 -6 Td")
    commands.append("ET")
    return "\n".join(commands)


def write_pdf(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = _build_text_stream(title, lines).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    chunks = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(sum(len(chunk) for chunk in chunks))
        chunks.append(f"{index} 0 obj\n".encode("ascii"))
        chunks.append(obj)
        chunks.append(b"\nendobj\n")

    xref_offset = sum(len(chunk) for chunk in chunks)
    chunks.append(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    chunks.append(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        chunks.append(f"{offset:010d} 00000 n \n".encode("ascii"))
    chunks.append(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(b"".join(chunks))


def generate_files() -> dict:
    manifest: dict = {"campaigns": [], "policy_docs": []}

    for campaign in CAMPAIGNS:
        base = CAMPAIGN_DIR / campaign["slug"]
        jd_path = base / "jd" / campaign["jd_file"]
        write_pdf(jd_path, campaign["jd_title"], campaign["jd"])

        cv_paths = []
        for cv in campaign["cvs"]:
            cv_path = base / "cvs" / cv["file"]
            write_pdf(cv_path, cv["title"], cv["body"])
            cv_paths.append(str(cv_path.relative_to(ROOT)))

        manifest["campaigns"].append(
            {
                "name": campaign["name"],
                "slug": campaign["slug"],
                "jd": str(jd_path.relative_to(ROOT)),
                "cvs": cv_paths,
                "settings": campaign["settings"],
            }
        )

    for doc in POLICY_DOCS:
        path = POLICY_DIR / doc["file"]
        write_pdf(path, doc["title"], doc["body"])
        manifest["policy_docs"].append(
            {
                "file": str(path.relative_to(ROOT)),
                "category": doc["category"],
                "visibility": doc["visibility"],
                "version": doc["version"],
                "status": doc["status"],
            }
        )

    manifest_path = FIXTURE_DIR / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def upload_to_api(manifest: dict, base_url: str, username: str, password: str) -> None:
    import requests

    session = requests.Session()
    login = session.post(f"{base_url}/auth/login", json={"username": username, "password": password}, timeout=30)
    login.raise_for_status()
    token = login.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})

    for campaign in manifest["campaigns"]:
        created = session.post(f"{base_url}/campaigns", json={"name": campaign["name"]}, timeout=30)
        created.raise_for_status()
        campaign_id = created.json()["id"]
        print(f"created campaign {campaign_id}: {campaign['name']}")

        session.put(f"{base_url}/campaigns/{campaign_id}/settings", json=campaign["settings"], timeout=30).raise_for_status()

        with (ROOT / campaign["jd"]).open("rb") as fh:
            session.post(f"{base_url}/campaigns/{campaign_id}/jd", files={"file": (Path(campaign["jd"]).name, fh, "application/pdf")}, timeout=60).raise_for_status()

        files = []
        handles = []
        try:
            for cv in campaign["cvs"]:
                fh = (ROOT / cv).open("rb")
                handles.append(fh)
                files.append(("files", (Path(cv).name, fh, "application/pdf")))
            session.post(f"{base_url}/campaigns/{campaign_id}/cvs", files=files, timeout=120).raise_for_status()
        finally:
            for fh in handles:
                fh.close()

    policy_groups: dict[tuple[str, str, str, str], list[str]] = {}
    for doc in manifest["policy_docs"]:
        key = (doc["category"], doc["visibility"], doc["version"], doc["status"])
        policy_groups.setdefault(key, []).append(doc["file"])

    for (category, visibility, version, status), docs in policy_groups.items():
        files = []
        handles = []
        try:
            for item in docs:
                fh = (ROOT / item).open("rb")
                handles.append(fh)
                files.append(("files", (Path(item).name, fh, "application/pdf")))
            response = session.post(
                f"{base_url}/policy/ingest",
                data={"category": category, "visibility": visibility, "version": version, "status": status},
                files=files,
                timeout=120,
            )
            response.raise_for_status()
            print(f"uploaded {len(docs)} policy doc(s): {category}")
        finally:
            for fh in handles:
                fh.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create fake HRM AI PDFs and optional API seed data.")
    parser.add_argument("--upload", action="store_true", help="Upload generated files to a running API.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL.")
    parser.add_argument("--username", default="admin", help="API username.")
    parser.add_argument("--password", default="admin123", help="API password.")
    args = parser.parse_args()

    manifest = generate_files()
    print(f"generated fixtures in {FIXTURE_DIR.relative_to(ROOT)}")
    print(f"campaigns: {len(manifest['campaigns'])}")
    print(f"policy docs: {len(manifest['policy_docs'])}")

    if args.upload:
        upload_to_api(manifest, args.base_url.rstrip("/"), args.username, args.password)


if __name__ == "__main__":
    main()
