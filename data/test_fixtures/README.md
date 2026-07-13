# Fake test data for HRM AI

Thu muc nay chua bo du lieu gia lap de test CV Screening va Policy Chatbot.

## Noi dung

- `campaigns/backend_python_fastapi`
  - 1 JD PDF cho vi tri Senior Python Backend Engineer.
  - 5 CV PDF: top match, mid match, low match, junior, va poor-quality/scanned-like.
- `campaigns/frontend_nextjs`
  - 1 JD PDF cho vi tri Frontend Engineer Next.js.
  - 3 CV PDF: top match, mid match, low match.
- `campaigns/data_ai_engineer`
  - 1 JD PDF cho vi tri Data AI Engineer.
  - 4 CV PDF: top match, mid match, low match, research match.
- `policy_docs`
  - 5 PDF chinh sach noi bo: quy che lam viec, phuc loi/nghi phep, quy trinh tuyen dung, lam viec tu xa, cong tac phi/dao tao.
- `manifest.json`
  - Danh sach campaign, file JD/CV, policy docs va settings goi y.

## Tao lai file

```bash
python3 scripts/create_fake_test_data.py
```

## Upload vao API dang chay

Dam bao backend da chay, user test da co san, va dang dung tai khoan admin:

```bash
python3 scripts/create_fake_test_data.py --upload --base-url http://localhost:8000 --username admin --password admin123
```

Script se:

1. Tao campaign Backend Python FastAPI, Frontend Next.js va Data AI Engineer.
2. Upload JD va cac CV vao tung campaign.
3. Cap nhat campaign settings gom required skills va min years.
4. Upload policy docs vao Knowledge Base.

Sau khi upload, worker van can chay de parse, ingest va screening jobs.
