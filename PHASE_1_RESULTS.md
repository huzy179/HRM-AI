# Phase 1 Results — CV Screening

**Date:** 2026-05-09  
**Environment:** Docker compose (ollama + app)

## Dataset

- #CV PDFs:
- #JD:
- Languages:
- Notes about scan PDFs / OCR:

## Parsing

- Parse OK rate:
- Needs OCR rate:
- Common errors:

## Ranking (Embeddings + Chroma)

- Chunk config: `CV_CHUNK_SIZE=`, `CV_CHUNK_OVERLAP=`
- Qualitative notes:
- Example good matches:
- Example bad matches:

## LLM Review (llama3)

- Review quality notes:
- Common hallucinations/limitations (if any):
- Prompt improvements needed:

## Performance

- Index time per CV (approx):
- Rank latency (approx):
- LLM review latency (approx):

## Backlog / Next steps

- [ ] Improve OCR (language pack, DPI tuning)
- [ ] Add explainability (top evidence snippets on ranking table)
- [ ] Add reranker / structured rubric scoring
- [ ] Phase 2: FastAPI API endpoints

