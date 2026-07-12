from __future__ import annotations

import argparse
import json
from pathlib import Path

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

from backend.services.policy_rag import PolicyRAG


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def build_dataset(rows: list[dict], k: int) -> Dataset:
    rag = PolicyRAG()
    samples: list[dict] = []
    for row in rows:
        question = str(row["question"]).strip()
        answer = rag.answer(query=question, k=k)
        samples.append(
            {
                "question": question,
                "answer": answer.answer,
                "contexts": [c.snippet for c in answer.citations],
                "ground_truth": str(row.get("ground_truth") or ""),
            }
        )
    return Dataset.from_list(samples)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Policy RAG with Ragas.")
    parser.add_argument("--input", default="evals/policy_eval_questions.jsonl")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--output", default="evals/ragas_policy_results.json")
    args = parser.parse_args()

    rows = load_jsonl(Path(args.input))
    dataset = build_dataset(rows, k=args.k)
    result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ],
    )

    out = result.to_pandas().to_dict(orient="records")
    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
