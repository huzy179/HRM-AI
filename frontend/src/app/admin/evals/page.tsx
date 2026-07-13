"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, CheckCircle2, FileText, Play, RefreshCw, XCircle } from "lucide-react";
import { api } from "@/lib/api";
import { PolicyEvalRun, PolicyEvalRunDetail } from "@/types";

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

const statusClass: Record<string, string> = {
  DONE: "text-emerald-300 bg-emerald-500/10 border-emerald-500/20",
  RUNNING: "text-cyan-300 bg-cyan-500/10 border-cyan-500/20",
  PENDING: "text-amber-300 bg-amber-500/10 border-amber-500/20",
  ERROR: "text-rose-300 bg-rose-500/10 border-rose-500/20",
};

export default function PolicyEvalsPage() {
  const [runs, setRuns] = useState<PolicyEvalRun[]>([]);
  const [selected, setSelected] = useState<PolicyEvalRunDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const fetchRuns = async () => {
    const res = await api.get("/policy/evals/runs");
    const data = await res.json();
    setRuns(data);
    if (!selected && data.length > 0) {
      await fetchDetail(data[0].id);
    }
  };

  const fetchDetail = async (id: number) => {
    const res = await api.get(`/policy/evals/runs/${id}`);
    setSelected(await res.json());
  };

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const res = await api.get("/policy/evals/runs");
        const data = await res.json();
        if (!active) return;
        setRuns(data);
        if (data.length > 0) {
          const detail = await api.get(`/policy/evals/runs/${data[0].id}`);
          if (active) setSelected(await detail.json());
        }
      } catch (err) {
        if (active) setMessage(`Không tải được eval runs: ${errorMessage(err)}`);
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, []);

  const runEval = async () => {
    setLoading(true);
    setMessage("");
    try {
      const res = await api.post("/policy/evals/runs", { name: `Policy eval ${new Date().toLocaleString()}` });
      const data = await res.json();
      setMessage(`Đã enqueue eval run #${data.run_id}: ${data.job_id}`);
      await fetchRuns();
      await fetchDetail(data.run_id);
    } catch (err) {
      setMessage(`Không chạy được eval: ${errorMessage(err)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#0B0F19] text-slate-100">
      <header className="border-b border-slate-800 bg-[#0F172A]/80">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link href="/" className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 flex items-center justify-center">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white">Policy RAG Evals</h1>
              <p className="text-xs text-slate-400">Chạy bộ câu hỏi chuẩn và kiểm tra answer, citation, expected source</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={fetchRuns} className="inline-flex items-center gap-2 rounded-lg border border-slate-700 hover:bg-slate-800 px-3 py-2 text-xs text-slate-300">
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
            <button onClick={runEval} disabled={loading} className="inline-flex items-center gap-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 px-3 py-2 text-xs font-semibold text-white">
              <Play className="w-4 h-4" />
              Run Eval
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6 space-y-4">
        {message && <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/10 px-3 py-2 text-sm text-cyan-200">{message}</div>}

        <section className="rounded-xl border border-slate-800 bg-slate-900/70 overflow-hidden">
          <div className="p-4 border-b border-slate-800">
            <h2 className="font-semibold text-white">Eval runs</h2>
          </div>
          <div className="divide-y divide-slate-800">
            {runs.length === 0 ? (
              <div className="p-8 text-center text-sm text-slate-500">Chưa có eval run nào.</div>
            ) : (
              runs.map((run) => (
                <button
                  key={run.id}
                  onClick={() => fetchDetail(run.id)}
                  className="w-full p-4 grid md:grid-cols-[1fr_120px_120px_140px] gap-3 text-left hover:bg-slate-800/60"
                >
                  <div>
                    <div className="font-medium text-white">#{run.id} {run.name}</div>
                    <div className="text-xs text-slate-500 mt-1">{new Date(run.created_at).toLocaleString()}</div>
                    {run.error && <div className="text-xs text-rose-300 mt-1">{run.error}</div>}
                  </div>
                  <div className="text-sm text-slate-300">{run.passed_questions}/{run.total_questions} pass</div>
                  <div className="text-sm font-semibold text-white">{run.score.toFixed(1)}%</div>
                  <div>
                    <span className={`inline-flex px-2.5 py-1 rounded-md border text-xs font-semibold ${statusClass[run.status] || "text-slate-300 bg-slate-800 border-slate-700"}`}>
                      {run.status}
                    </span>
                  </div>
                </button>
              ))
            )}
          </div>
        </section>

        {selected && (
          <section className="rounded-xl border border-slate-800 bg-slate-900/70 overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between gap-3">
              <div>
                <h2 className="font-semibold text-white">Chi tiết run #{selected.id}</h2>
                <p className="text-xs text-slate-400 mt-1">{selected.passed_questions}/{selected.total_questions} pass · score {selected.score.toFixed(1)}%</p>
              </div>
            </div>
            <div className="divide-y divide-slate-800">
              {selected.items.map((item) => (
                <article key={item.id} className="p-4 space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-white">{item.question}</div>
                      <div className="mt-1 flex flex-wrap gap-2 text-xs text-slate-400">
                        <span className="px-2 py-1 rounded-md border border-slate-700">source: {item.expected_source || "any"}</span>
                        <span className="px-2 py-1 rounded-md border border-slate-700">keywords: {item.expected_keywords.join(", ") || "none"}</span>
                        <span className="px-2 py-1 rounded-md border border-slate-700">{item.notes}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {item.passed ? <CheckCircle2 className="w-5 h-5 text-emerald-300" /> : <XCircle className="w-5 h-5 text-rose-300" />}
                      <span className="text-sm font-semibold text-white">{item.score.toFixed(1)}%</span>
                    </div>
                  </div>
                  <p className="text-sm text-slate-300 leading-6">{item.answer || "Chưa có câu trả lời."}</p>
                  <div className="grid md:grid-cols-2 gap-2">
                    {item.citations.slice(0, 4).map((citation, index) => (
                      <div key={`${citation.source}-${citation.chunk_id}-${index}`} className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                        <div className="text-xs font-semibold text-cyan-300 truncate">{citation.source}</div>
                        <div className="text-xs text-slate-500 mt-1">chunk {citation.chunk_id} · score {Number(citation.score || 0).toFixed(3)}</div>
                        <p className="text-xs text-slate-400 mt-2 line-clamp-3">{citation.snippet}</p>
                      </div>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
