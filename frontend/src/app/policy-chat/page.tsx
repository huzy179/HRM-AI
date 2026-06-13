"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { 
  MessageSquare, 
  Upload, 
  ArrowLeft, 
  Trash2, 
  RotateCw, 
  Send,
  FileText,
  AlertTriangle,
  ChevronDown,
  BookOpen
} from "lucide-react";
import { api } from "@/lib/api";
import { ChatMessage, PolicyDocument } from "@/types";

export default function PolicyChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  
  // Document states
  const [documents, setDocuments] = useState<PolicyDocument[]>([]);
  const [selectedDocs, setSelectedDocs] = useState<number[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  // Danger zone confirmations
  const [confirmClear, setConfirmClear] = useState(false);
  const [confirmRebuild, setConfirmRebuild] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await api.get("/policy/documents");
      const data = await res.json();
      setDocuments(data);
    } catch (err) {
      console.error("Failed to load documents", err);
    }
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    setUploadSuccess(null);
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }

    try {
      await api.post("/policy/ingest", formData);
      setUploadSuccess("Đã xếp hàng tài liệu vào hàng đợi xử lý!");
      setTimeout(() => setUploadSuccess(null), 5000);
      fetchDocuments();
    } catch (err: any) {
      alert(`Lỗi upload: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files);
    }
  };

  const toggleDocSelection = (id: number) => {
    setSelectedDocs(prev => 
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
    );
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userMessage: ChatMessage = { role: "user", content: query };
    setMessages(prev => [...prev, userMessage]);
    setQuery("");
    setLoading(true);

    const historyPayload = messages.map(msg => ({
      role: msg.role,
      content: msg.content
    }));

    // Add empty placeholder assistant message
    const placeholderMsg: ChatMessage = { role: "assistant", content: "" };
    setMessages(prev => [...prev, placeholderMsg]);

    try {
      let fullContent = "";
      await api.readStream(
        "/policy/chat/stream",
        {
          query: userMessage.content,
          k: 5,
          history: historyPayload,
          doc_ids: selectedDocs.length > 0 ? selectedDocs.map(String) : null
        },
        (chunk) => {
          fullContent += chunk;
          setMessages(prev => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.role === "assistant") {
              last.content = fullContent;
            }
            return updated;
          });
        },
        (citations) => {
          setMessages(prev => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.role === "assistant") {
              last.citations = citations;
            }
            return updated;
          });
        }
      );
    } catch (err: any) {
      setMessages(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last && last.role === "assistant") {
          last.content = `Lỗi kết nối API: ${err.message}`;
        }
        return updated;
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClearIndex = async () => {
    if (!confirmClear) return;
    try {
      await api.post("/policy/clear?confirm=true");
      alert("Đã gửi lệnh xóa Vector Index chính sách!");
      setConfirmClear(false);
      setMessages([]);
      fetchDocuments();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleRebuildIndex = async () => {
    if (!confirmRebuild) return;
    try {
      await api.post("/policy/rebuild?confirm=true");
      alert("Đã gửi lệnh rebuild Vector Index!");
      setConfirmRebuild(false);
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="flex h-screen bg-[#0B0F19] text-slate-100 overflow-hidden">
      {/* Sidebar - Document Management */}
      <aside className="w-80 border-r border-slate-800 bg-[#0F172A] flex flex-col shrink-0">
        {/* Sidebar Header */}
        <div className="p-4 border-b border-slate-800 flex items-center gap-3">
          <Link href="/" className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div className="flex items-center gap-2 text-emerald-400">
            <BookOpen className="w-5 h-5" />
            <span className="font-bold text-white tracking-wide">Tài liệu Chính sách</span>
          </div>
        </div>

        {/* Drag & Drop Upload */}
        <div className="p-4 border-b border-slate-800">
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`relative border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors ${
              dragActive ? "border-emerald-500 bg-emerald-500/5" : "border-slate-700 hover:border-slate-600 bg-slate-900/50"
            }`}
          >
            <input
              type="file"
              multiple
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              onChange={(e) => handleFileUpload(e.target.files)}
              accept=".pdf,.txt,.docx,.md"
              disabled={uploading}
            />
            <Upload className={`w-8 h-8 mx-auto mb-2 text-slate-400 ${uploading ? "animate-bounce text-emerald-400" : ""}`} />
            <p className="text-xs text-slate-300 font-medium">Kéo thả tài liệu vào đây</p>
            <p className="text-[10px] text-slate-500 mt-1">Hỗ trợ PDF, DOCX, TXT, MD</p>
          </div>
          {uploadSuccess && (
            <div className="mt-2 text-xs bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 p-2 rounded-lg">
              {uploadSuccess}
            </div>
          )}
        </div>

        {/* Ingested Documents List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Danh sách tài liệu</span>
            <button onClick={fetchDocuments} className="text-slate-400 hover:text-white transition-colors p-1 rounded-md hover:bg-slate-800">
              <RotateCw className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-2">
            {documents.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-4">Chưa có tài liệu nào.</p>
            ) : (
              documents.map((doc) => {
                const isSelected = selectedDocs.includes(doc.id);
                return (
                  <div
                    key={doc.id}
                    onClick={() => toggleDocSelection(doc.id)}
                    className={`flex items-center justify-between p-2.5 rounded-lg border cursor-pointer transition-all ${
                      isSelected 
                        ? "bg-emerald-500/10 border-emerald-500/40 text-white" 
                        : "bg-slate-900/40 border-slate-800 hover:border-slate-700 text-slate-300"
                    }`}
                  >
                    <div className="flex items-center gap-2 overflow-hidden pr-2">
                      <FileText className={`w-4 h-4 shrink-0 ${isSelected ? "text-emerald-400" : "text-slate-400"}`} />
                      <span className="text-xs font-medium truncate leading-none">{doc.filename}</span>
                    </div>
                    <span className="text-[10px] uppercase font-bold shrink-0 text-slate-500">
                      {doc.ingest_status === "OK" ? "🟢" : doc.ingest_status === "PENDING" ? "🟡" : "🔴"}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Danger Zone */}
        <div className="p-4 border-t border-slate-800 bg-[#0c1222] space-y-3">
          <div className="flex items-center gap-1.5 text-rose-400 text-xs font-bold uppercase tracking-wider">
            <AlertTriangle className="w-4 h-4" />
            <span>Danger Zone</span>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <input 
                type="checkbox" 
                id="checkClear" 
                checked={confirmClear} 
                onChange={(e) => setConfirmClear(e.target.checked)}
                className="rounded border-slate-700 bg-slate-900 text-rose-500 focus:ring-rose-500/20"
              />
              <label htmlFor="checkClear" className="text-[10px] text-slate-400 cursor-pointer">Xác nhận xóa Index</label>
            </div>
            <button
              onClick={handleClearIndex}
              disabled={!confirmClear}
              className="w-full text-xs py-2 bg-rose-600/10 hover:bg-rose-600 border border-rose-500/30 hover:border-rose-500 text-rose-400 hover:text-white rounded-lg transition-all disabled:opacity-40 disabled:hover:bg-rose-600/10 disabled:hover:text-rose-400"
            >
              Clear Vector Index
            </button>

            <div className="flex items-center gap-2 pt-1">
              <input 
                type="checkbox" 
                id="checkRebuild" 
                checked={confirmRebuild} 
                onChange={(e) => setConfirmRebuild(e.target.checked)}
                className="rounded border-slate-700 bg-slate-900 text-emerald-500 focus:ring-emerald-500/20"
              />
              <label htmlFor="checkRebuild" className="text-[10px] text-slate-400 cursor-pointer">Xác nhận Rebuild</label>
            </div>
            <button
              onClick={handleRebuildIndex}
              disabled={!confirmRebuild}
              className="w-full text-xs py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg transition-all disabled:opacity-40"
            >
              Rebuild Index
            </button>
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col min-w-0 bg-[#0B0F19]">
        {/* Chat Header */}
        <header className="p-4 border-b border-slate-800 flex justify-between items-center bg-[#0F172A]/50">
          <div>
            <h1 className="text-lg font-bold text-white leading-tight">HR Policy Assistant</h1>
            <p className="text-xs text-slate-400">Trò chuyện và tra cứu quy chế nội bộ tự động</p>
          </div>
          {messages.length > 0 && (
            <button 
              onClick={() => setMessages([])} 
              className="text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-slate-300 transition-colors"
            >
              Xóa lịch sử chat
            </button>
          )}
        </header>

        {/* Message Panel */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-4">
              <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <MessageSquare className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-bold text-white">Bạn cần trợ giúp gì về chính sách?</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Hãy tải lên tài liệu chính sách ở cột bên trái (như quy chế làm việc, bảo hiểm, nghỉ phép...) rồi đặt câu hỏi để nhận câu trả lời đối chiếu chính xác.
              </p>
            </div>
          ) : (
            messages.map((msg, idx) => {
              const isUser = msg.role === "user";
              return (
                <div key={idx} className={`flex flex-col ${isUser ? "items-end" : "items-start"} space-y-2`}>
                  {/* Chat bubble */}
                  <div 
                    className={`max-w-[80%] rounded-2xl p-4 text-sm leading-relaxed ${
                      isUser 
                        ? "bg-gradient-to-br from-blue-600 to-indigo-600 text-white rounded-br-none shadow-lg shadow-blue-500/15" 
                        : "bg-slate-900 border border-slate-800 text-slate-100 rounded-bl-none"
                    }`}
                  >
                    {msg.content || (
                      <span className="inline-flex gap-1 items-center">
                        <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce"></span>
                        <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce delay-100"></span>
                        <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce delay-200"></span>
                      </span>
                    )}
                  </div>

                  {/* Citations panel */}
                  {!isUser && msg.citations && msg.citations.length > 0 && (
                    <div className="w-full max-w-[85%] mt-2 pl-4">
                      <div className="text-xs font-bold text-slate-400 flex items-center gap-1.5 mb-2">
                        <BookOpen className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Tài liệu tham khảo nguồn ({msg.citations.length})</span>
                      </div>
                      <div className="grid sm:grid-cols-2 gap-3">
                        {msg.citations.map((cit, cIdx) => (
                          <div key={cIdx} className="bg-slate-900/60 border border-slate-800/80 rounded-lg p-3 text-xs text-slate-400 relative overflow-hidden group">
                            <div className="flex justify-between items-center mb-1 bg-slate-800/40 px-2 py-0.5 rounded border border-slate-800/50">
                              <span className="font-bold text-slate-300 truncate max-w-[120px]">{cit.source}</span>
                              <span className="text-[10px] text-emerald-400 font-bold shrink-0">{Math.round(cit.score * 100)}% Match</span>
                            </div>
                            <p className="italic text-slate-300 leading-normal line-clamp-3">"{cit.snippet}"</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Input panel */}
        <footer className="p-4 border-t border-slate-800 bg-[#0F172A]/40">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto flex gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={loading ? "Đang chuẩn bị câu trả lời..." : "Đặt câu hỏi về chính sách quy chế tại đây..."}
              disabled={loading}
              className="flex-1 bg-slate-900 hover:bg-slate-900/80 border border-slate-800 focus:border-emerald-500 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 text-slate-100 placeholder-slate-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!query.trim() || loading}
              className="p-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white rounded-xl transition-all shadow-lg shadow-emerald-600/20 hover:shadow-emerald-500/30"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </footer>
      </main>
    </div>
  );
}
