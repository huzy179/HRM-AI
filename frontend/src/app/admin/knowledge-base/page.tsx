"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  BookOpen,
  FileText,
  RefreshCw,
  RotateCw,
  Shield,
  BarChart3,
  Trash2,
  Upload,
} from "lucide-react";
import { api } from "@/lib/api";
import { PolicyDocument } from "@/types";

const statusClass: Record<string, string> = {
  OK: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  PENDING: "text-amber-300 bg-amber-500/10 border-amber-500/20",
  ERROR: "text-rose-400 bg-rose-500/10 border-rose-500/20",
};

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

export default function KnowledgeBaseAdminPage() {
  const [documents, setDocuments] = useState<PolicyDocument[]>([]);
  const [files, setFiles] = useState<FileList | null>(null);
  const [category, setCategory] = useState("hr-policy");
  const [visibility, setVisibility] = useState("employee");
  const [version, setVersion] = useState("1.0");
  const [status, setStatus] = useState("published");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [confirmClear, setConfirmClear] = useState(false);

  const fetchDocuments = async () => {
    const res = await api.get("/policy/documents");
    setDocuments(await res.json());
  };

  useEffect(() => {
    let active = true;
    async function loadDocuments() {
      try {
        const res = await api.get("/policy/documents");
        const data = await res.json();
        if (active) setDocuments(data);
      } catch (err: unknown) {
        if (active) setMessage(`Không tải được danh sách tài liệu: ${errorMessage(err)}`);
      }
    }
    void loadDocuments();
    return () => {
      active = false;
    };
  }, []);

  const uploadDocuments = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!files || files.length === 0) return;

    setLoading(true);
    setMessage("");
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }
    formData.append("category", category);
    formData.append("visibility", visibility);
    formData.append("version", version);
    formData.append("status", status);

    try {
      const res = await api.post("/policy/ingest", formData);
      const data = await res.json();
      setMessage(`Đã đưa ${data.doc_ids?.length || files.length} tài liệu vào hàng đợi ingest.`);
      setFiles(null);
      await fetchDocuments();
    } catch (err: unknown) {
      setMessage(`Upload lỗi: ${errorMessage(err)}`);
    } finally {
      setLoading(false);
    }
  };

  const rebuildIndex = async () => {
    setLoading(true);
    setMessage("");
    try {
      const res = await api.post("/policy/rebuild?confirm=true");
      const data = await res.json();
      setMessage(`Đã enqueue rebuild index: ${data.job_id}`);
    } catch (err: unknown) {
      setMessage(`Rebuild lỗi: ${errorMessage(err)}`);
    } finally {
      setLoading(false);
    }
  };

  const clearIndex = async () => {
    if (!confirmClear) return;
    setLoading(true);
    setMessage("");
    try {
      const res = await api.post("/policy/clear?confirm=true");
      const data = await res.json();
      setMessage(`Đã enqueue clear index: ${data.job_id}`);
      setConfirmClear(false);
    } catch (err: unknown) {
      setMessage(`Clear lỗi: ${errorMessage(err)}`);
    } finally {
      setLoading(false);
    }
  };

  const readyCount = documents.filter((doc) => doc.ingest_status === "OK").length;
  const pendingCount = documents.filter((doc) => doc.ingest_status === "PENDING").length;
  const failedCount = documents.filter((doc) => doc.ingest_status === "ERROR").length;

  return (
    <main className="min-h-screen bg-[#0B0F19] text-slate-100">
      <header className="border-b border-slate-800 bg-[#0F172A]/80">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link href="/" className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 flex items-center justify-center">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white">Knowledge Base Admin</h1>
              <p className="text-xs text-slate-400">Upload, publish và vận hành tài liệu nội bộ cho Policy Chatbot</p>
            </div>
          </div>
          <Link href="/policy-chat" className="inline-flex items-center gap-2 text-xs px-3 py-2 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800">
            <BookOpen className="w-4 h-4" />
            Mở chatbot
          </Link>
          <Link href="/admin/evals" className="inline-flex items-center gap-2 text-xs px-3 py-2 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800">
            <BarChart3 className="w-4 h-4" />
            Eval
          </Link>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6 grid lg:grid-cols-[360px_1fr] gap-6">
        <aside className="space-y-4">
          <section className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
            <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
              <Upload className="w-4 h-4 text-cyan-300" />
              Upload tài liệu
            </h2>
            <form onSubmit={uploadDocuments} className="space-y-4">
              <label className="block rounded-xl border border-dashed border-slate-700 hover:border-cyan-500/60 bg-slate-950 p-4 cursor-pointer">
                <input
                  type="file"
                  multiple
                  accept=".pdf,.txt,.docx,.md"
                  className="hidden"
                  onChange={(event) => setFiles(event.target.files)}
                />
                <div className="text-sm text-slate-300 font-medium">Chọn PDF, DOCX, TXT hoặc MD</div>
                <div className="text-xs text-slate-500 mt-1">
                  {files && files.length > 0 ? `${files.length} file đã chọn` : "Dùng cho policy, handbook, onboarding, benefit"}
                </div>
              </label>

              <div className="grid grid-cols-2 gap-3">
                <label className="space-y-1">
                  <span className="text-xs text-slate-400">Category</span>
                  <input value={category} onChange={(e) => setCategory(e.target.value)} className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-sm outline-none focus:border-cyan-500" />
                </label>
                <label className="space-y-1">
                  <span className="text-xs text-slate-400">Version</span>
                  <input value={version} onChange={(e) => setVersion(e.target.value)} className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-sm outline-none focus:border-cyan-500" />
                </label>
                <label className="space-y-1">
                  <span className="text-xs text-slate-400">Visibility</span>
                  <select value={visibility} onChange={(e) => setVisibility(e.target.value)} className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-sm outline-none focus:border-cyan-500">
                    <option value="employee">employee</option>
                    <option value="hr">hr</option>
                    <option value="admin">admin</option>
                  </select>
                </label>
                <label className="space-y-1">
                  <span className="text-xs text-slate-400">Status</span>
                  <select value={status} onChange={(e) => setStatus(e.target.value)} className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-sm outline-none focus:border-cyan-500">
                    <option value="published">published</option>
                    <option value="draft">draft</option>
                    <option value="archived">archived</option>
                  </select>
                </label>
              </div>

              <button disabled={!files || loading} className="w-full rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 px-4 py-2.5 text-sm font-semibold text-white">
                {loading ? "Đang xử lý..." : "Upload và ingest"}
              </button>
            </form>
          </section>

          <section className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-3">
            <h2 className="font-semibold text-white">Index operations</h2>
            <button onClick={rebuildIndex} disabled={loading} className="w-full inline-flex items-center justify-center gap-2 rounded-lg border border-slate-700 hover:bg-slate-800 px-4 py-2.5 text-sm text-slate-200">
              <RefreshCw className="w-4 h-4" />
              Rebuild index
            </button>
            <label className="flex items-center gap-2 text-xs text-slate-400">
              <input type="checkbox" checked={confirmClear} onChange={(e) => setConfirmClear(e.target.checked)} />
              Xác nhận clear vector index
            </label>
            <button onClick={clearIndex} disabled={!confirmClear || loading} className="w-full inline-flex items-center justify-center gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 hover:bg-rose-600 disabled:opacity-40 px-4 py-2.5 text-sm text-rose-300 hover:text-white">
              <Trash2 className="w-4 h-4" />
              Clear index
            </button>
          </section>
        </aside>

        <section className="rounded-xl border border-slate-800 bg-slate-900/70 overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-semibold text-white">Tài liệu nội bộ</h2>
              <p className="text-xs text-slate-400 mt-1">Ready {readyCount} · Pending {pendingCount} · Failed {failedCount}</p>
            </div>
            <button onClick={fetchDocuments} className="inline-flex items-center gap-2 rounded-lg border border-slate-700 hover:bg-slate-800 px-3 py-2 text-xs text-slate-300">
              <RotateCw className="w-4 h-4" />
              Refresh
            </button>
          </div>

          {message && (
            <div className="m-4 rounded-lg border border-cyan-500/20 bg-cyan-500/10 px-3 py-2 text-sm text-cyan-200">
              {message}
            </div>
          )}

          <div className="divide-y divide-slate-800">
            {documents.length === 0 ? (
              <div className="p-10 text-center text-slate-500 text-sm">Chưa có tài liệu nào. Upload tài liệu để chatbot có tri thức nội bộ.</div>
            ) : (
              documents.map((doc) => (
                <div key={doc.id} className="p-4 grid md:grid-cols-[1fr_auto] gap-3">
                  <div className="min-w-0 flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-center text-slate-400 shrink-0">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                      <div className="font-medium text-white truncate">{doc.filename}</div>
                      <div className="mt-1 flex flex-wrap gap-2 text-xs">
                        <span className="px-2 py-1 rounded-md border border-slate-700 text-slate-300">{doc.category}</span>
                        <span className="px-2 py-1 rounded-md border border-slate-700 text-slate-300">v{doc.version}</span>
                        <span className="px-2 py-1 rounded-md border border-slate-700 text-slate-300">{doc.visibility}</span>
                        <span className="px-2 py-1 rounded-md border border-slate-700 text-slate-300">{doc.status}</span>
                      </div>
                      {doc.error && <div className="mt-2 text-xs text-rose-300">{doc.error}</div>}
                    </div>
                  </div>
                  <div className="flex md:justify-end items-start">
                    <span className={`px-2.5 py-1 rounded-md border text-xs font-semibold ${statusClass[doc.ingest_status] || "text-slate-300 bg-slate-800 border-slate-700"}`}>
                      {doc.ingest_status}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
