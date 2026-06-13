"use client";

import Link from "next/link";
import { 
  Users, 
  FileText, 
  MessageSquare, 
  ChevronRight, 
  Sparkles, 
  TrendingUp, 
  CheckCircle,
  Clock
} from "lucide-react";

export default function Home() {
  return (
    <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-12 md:py-20 flex flex-col justify-center">
      {/* Hero Section */}
      <div className="text-center max-w-3xl mx-auto mb-16 space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-sm font-medium animate-pulse">
          <Sparkles className="w-4 h-4" />
          <span>Local Ollama & Offline-First Recruiter Suite</span>
        </div>
        <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-white font-sans bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-400 to-emerald-400 leading-tight">
          HRM AI Recruitment Suite
        </h1>
        <p className="text-lg text-slate-400 leading-relaxed max-w-2xl mx-auto">
          Hệ thống quản lý tuyển dụng thông minh. Sử dụng AI để sàng lọc hồ sơ CV chính xác và chatbot tra cứu chính sách công ty tự động.
        </p>
      </div>

      {/* Feature Cards Grid */}
      <div className="grid md:grid-cols-2 gap-8 mb-16">
        {/* CV Screening Card */}
        <div className="glass-card rounded-2xl p-8 flex flex-col justify-between group">
          <div className="space-y-6">
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20 text-blue-400 group-hover:scale-110 transition-transform">
              <Users className="w-6 h-6" />
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-white group-hover:text-blue-400 transition-colors">
                CV Screening & Ranking
              </h2>
              <p className="text-slate-400 text-sm leading-relaxed">
                Phân tích, OCR và chấm điểm CV dựa trên độ tương thích kỹ năng với JD. Tích hợp vẽ biểu đồ Radar Match & sinh thư mời/từ chối tự động bằng Llama3.
              </p>
            </div>
            <ul className="space-y-3 text-slate-400 text-sm">
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span>Radar skill matching chart</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span>AI response Email automation</span>
              </li>
            </ul>
          </div>
          <Link 
            href="/cv-screening"
            className="mt-8 inline-flex items-center justify-center gap-2 px-5 py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition-all group-hover:shadow-[0_0_20px_rgba(59,130,246,0.3)]"
          >
            <span>Bắt đầu sàng lọc CV</span>
            <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        {/* Policy Chatbot Card */}
        <div className="glass-card rounded-2xl p-8 flex flex-col justify-between group">
          <div className="space-y-6">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20 text-emerald-400 group-hover:scale-110 transition-transform">
              <MessageSquare className="w-6 h-6" />
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-white group-hover:text-emerald-400 transition-colors">
                HR Policy Chatbot
              </h2>
              <p className="text-slate-400 text-sm leading-relaxed">
                Trò chuyện và tra cứu chính sách công ty tự động bằng RAG. Nhận diện tài liệu đa dạng (.pdf, .txt, .docx, .md), hỗ trợ bộ lọc và phản hồi dạng streaming.
              </p>
            </div>
            <ul className="space-y-3 text-slate-400 text-sm">
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span>SSE streaming response with citations</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span>Source document filtering</span>
              </li>
            </ul>
          </div>
          <Link 
            href="/policy-chat"
            className="mt-8 inline-flex items-center justify-center gap-2 px-5 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium transition-all group-hover:shadow-[0_0_20px_rgba(16,185,129,0.3)]"
          >
            <span>Mở Policy Chatbot</span>
            <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </div>

      {/* Footer Info */}
      <div className="flex flex-wrap justify-center items-center gap-8 text-xs text-slate-500 border-t border-slate-800 pt-8 max-w-4xl mx-auto w-full">
        <div className="flex items-center gap-1.5">
          <Clock className="w-4 h-4" />
          <span>Local Llama3 & Nomic Embed Text</span>
        </div>
        <div className="flex items-center gap-1.5">
          <FileText className="w-4 h-4" />
          <span>Supports: PDF, DOCX, TXT, MD</span>
        </div>
        <div className="flex items-center gap-1.5">
          <TrendingUp className="w-4 h-4" />
          <span>Hybrid dense-sparse reranking</span>
        </div>
      </div>
    </main>
  );
}
