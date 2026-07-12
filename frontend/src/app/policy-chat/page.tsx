"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Bot,
  BookOpen,
  Check,
  MessageSquare,
  Send,
  ThumbsDown,
  ThumbsUp,
  UserRound,
} from "lucide-react";
import { api } from "@/lib/api";
import { ChatMessage } from "@/types";

const suggestedPrompts = [
  "Quy định nghỉ phép năm như thế nào?",
  "Thử việc có được hưởng bảo hiểm không?",
  "Quy trình xin nghỉ ốm ra sao?",
  "Chính sách làm remote hiện tại là gì?",
];

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

export default function PolicyChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState<Record<number, string>>({});

  const sendMessage = async (text: string) => {
    const clean = text.trim();
    if (!clean || loading) return;

    const userMessage: ChatMessage = { role: "user", content: clean };
    const historyPayload = messages.map((msg) => ({
      role: msg.role,
      content: msg.content,
    }));

    setMessages((prev) => [...prev, userMessage, { role: "assistant", content: "" }]);
    setQuery("");
    setLoading(true);

    try {
      let fullContent = "";
      await api.readStream(
        "/policy/chat/stream",
        {
          query: clean,
          k: 5,
          history: historyPayload,
          doc_ids: null,
        },
        (chunk) => {
          fullContent += chunk;
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.role === "assistant") {
              last.content = fullContent;
            }
            return updated;
          });
        },
        (citations) => {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.role === "assistant") {
              last.citations = citations;
            }
            return updated;
          });
        }
      );
    } catch (err: unknown) {
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last?.role === "assistant") {
          last.content = `Không thể kết nối chatbot: ${errorMessage(err)}`;
        }
        return updated;
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await sendMessage(query);
  };

  const sendFeedback = async (messageIndex: number, rating: "up" | "down") => {
    const answer = messages[messageIndex]?.content || "";
    const previousUser = [...messages]
      .slice(0, messageIndex)
      .reverse()
      .find((msg) => msg.role === "user");
    try {
      await api.post("/policy/feedback", {
        query: previousUser?.content || "",
        answer,
        rating,
      });
      setFeedbackSent((prev) => ({ ...prev, [messageIndex]: rating }));
    } catch (err) {
      console.error("Failed to send feedback", err);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-slate-100 flex flex-col">
      <header className="border-b border-slate-800 bg-[#0F172A]/80">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link href="/" className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white">HR Policy Chatbot</h1>
              <p className="text-xs text-slate-400">Hỏi đáp chính sách nội bộ dựa trên tài liệu đã được HR/Admin publish</p>
            </div>
          </div>
          <Link href="/admin/knowledge-base" className="hidden sm:inline-flex items-center gap-2 text-xs px-3 py-2 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800">
            <BookOpen className="w-4 h-4" />
            Admin KB
          </Link>
        </div>
      </header>

      <main className="flex-1 w-full max-w-5xl mx-auto px-4 py-6 flex flex-col">
        {messages.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="max-w-2xl w-full text-center space-y-8">
              <div className="space-y-3">
                <div className="mx-auto w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                  <MessageSquare className="w-8 h-8" />
                </div>
                <h2 className="text-2xl font-bold text-white">Bạn muốn hỏi gì về chính sách công ty?</h2>
                <p className="text-sm text-slate-400">
                  Chatbot chỉ trả lời dựa trên tài liệu nội bộ đã được admin upload và index.
                </p>
              </div>
              <div className="grid sm:grid-cols-2 gap-3 text-left">
                {suggestedPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => sendMessage(prompt)}
                    className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-emerald-500/50 text-sm text-slate-300 hover:text-white transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 space-y-6 pb-6">
            {messages.map((msg, idx) => {
              const isUser = msg.role === "user";
              return (
                <div key={idx} className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
                  {!isUser && (
                    <div className="mt-1 w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}
                  <div className={`max-w-[78%] space-y-3 ${isUser ? "items-end" : "items-start"}`}>
                    <div
                      className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                        isUser
                          ? "bg-blue-600 text-white rounded-br-sm"
                          : "bg-slate-900 border border-slate-800 text-slate-100 rounded-bl-sm"
                      }`}
                    >
                      {msg.content || (
                        <span className="inline-flex items-center gap-1 text-slate-400">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-bounce" />
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-bounce delay-100" />
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-bounce delay-200" />
                        </span>
                      )}
                    </div>

                    {!isUser && msg.content && (
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <button
                          onClick={() => sendFeedback(idx, "up")}
                          className="p-1.5 rounded-md hover:bg-slate-800 hover:text-emerald-400"
                          title="Câu trả lời hữu ích"
                        >
                          {feedbackSent[idx] === "up" ? <Check className="w-4 h-4 text-emerald-400" /> : <ThumbsUp className="w-4 h-4" />}
                        </button>
                        <button
                          onClick={() => sendFeedback(idx, "down")}
                          className="p-1.5 rounded-md hover:bg-slate-800 hover:text-rose-400"
                          title="Câu trả lời chưa đúng"
                        >
                          {feedbackSent[idx] === "down" ? <Check className="w-4 h-4 text-rose-400" /> : <ThumbsDown className="w-4 h-4" />}
                        </button>
                      </div>
                    )}

                    {!isUser && msg.citations && msg.citations.length > 0 && (
                      <div className="grid gap-2">
                        {msg.citations.map((cit, citIdx) => (
                          <div key={citIdx} className="rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-400">
                            <div className="flex items-center justify-between gap-3 mb-1">
                              <span className="font-semibold text-slate-300 truncate">{cit.source}</span>
                              <span className="text-emerald-400 shrink-0">{Math.round(cit.score * 100)}%</span>
                            </div>
                            <p className="line-clamp-2">{cit.snippet}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  {isUser && (
                    <div className="mt-1 w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-300 flex items-center justify-center shrink-0">
                      <UserRound className="w-4 h-4" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </main>

      <footer className="border-t border-slate-800 bg-[#0F172A]/80">
        <form onSubmit={handleSubmit} className="max-w-5xl mx-auto px-4 py-4 flex gap-3">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
            placeholder={loading ? "Đang trả lời..." : "Nhập câu hỏi về chính sách nội bộ..."}
            className="flex-1 bg-slate-900 border border-slate-800 focus:border-emerald-500 rounded-xl px-4 py-3 text-sm outline-none text-slate-100 placeholder:text-slate-500"
          />
          <button
            type="submit"
            disabled={!query.trim() || loading}
            className="px-4 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </footer>
    </div>
  );
}
