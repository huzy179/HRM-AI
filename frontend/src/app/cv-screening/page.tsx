"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { 
  ArrowLeft, 
  Plus, 
  Upload, 
  RefreshCw, 
  Sliders, 
  SlidersHorizontal,
  ChevronDown,
  ChevronUp, 
  Sparkles,
  Download,
  Mail,
  User,
  Radar,
  Award,
  CheckCircle,
  FileText
} from "lucide-react";
import { api } from "@/lib/api";
import { Campaign, Candidate, ScreeningResult } from "@/types";

export default function CVScreeningPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState<number | null>(null);
  const [newCampaignName, setNewCampaignName] = useState("Backend Developer - Tháng 7/2026");
  const [creatingCampaign, setCreatingCampaign] = useState(false);

  // File uploads
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [cvFiles, setCvFiles] = useState<FileList | null>(null);
  const [uploadingJd, setUploadingJd] = useState(false);
  const [uploadingCvs, setUploadingCvs] = useState(false);

  // Polling Job Status
  const [lastJobId, setLastJobId] = useState("");
  const [jobStatus, setJobStatus] = useState<any>(null);
  const [polling, setPolling] = useState(false);

  // Candidates & Settings
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [wEmbed, setWEmbed] = useState(0.7);
  const [skillsOverride, setSkillsOverride] = useState("");
  const [minYears, setMinYears] = useState(0.0);
  const [savingSettings, setSavingSettings] = useState(false);

  // Screening & Ranking
  const [screening, setScreening] = useState(false);
  const [ranking, setRanking] = useState<ScreeningResult[]>([]);
  const [showErrors, setShowErrors] = useState(true);
  const [minTotalScore, setMinTotalScore] = useState(0);

  // Drilldown Candidate details
  const [drillCandidateId, setDrillCandidateId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<"evidence" | "rules" | "review" | "profile" | "email">("evidence");
  const [reviewData, setReviewData] = useState<any>(null);
  const [profileData, setProfileData] = useState<any>(null);
  const [loadingReview, setLoadingReview] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(false);

  // Email Automation
  const [emailType, setEmailType] = useState<"interview" | "offer" | "rejection">("interview");
  const [emailSubject, setEmailSubject] = useState("");
  const [emailContent, setEmailContent] = useState("");
  const [generatingEmail, setGeneratingEmail] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(false);

  useEffect(() => {
    fetchCampaigns();
  }, []);

  useEffect(() => {
    if (selectedCampaignId) {
      fetchCandidates();
      fetchSettings();
      // Clear ranking / drilldown states on campaign change
      setRanking([]);
      setDrillCandidateId(null);
    }
  }, [selectedCampaignId]);

  useEffect(() => {
    if (drillCandidateId) {
      setReviewData(null);
      setProfileData(null);
      setEmailSubject("");
      setEmailContent("");
      setActiveTab("evidence");
    }
  }, [drillCandidateId]);

  const fetchCampaigns = async () => {
    try {
      const res = await api.get("/campaigns");
      const data = await res.json();
      setCampaigns(data);
      if (data.length > 0 && !selectedCampaignId) {
        setSelectedCampaignId(data[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchCandidates = async () => {
    if (!selectedCampaignId) return;
    try {
      const res = await api.get(`/campaigns/${selectedCampaignId}/candidates`);
      const data = await res.json();
      setCandidates(data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchSettings = async () => {
    if (!selectedCampaignId) return;
    try {
      const res = await api.get(`/campaigns/${selectedCampaignId}/settings`);
      const data = await res.json();
      setWEmbed(data.w_embed || 0.7);
      setMinYears(data.min_years_override || 0.0);
      setSkillsOverride((data.required_skills || []).join(", "));
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateCampaign = async () => {
    if (!newCampaignName.trim()) return;
    setCreatingCampaign(true);
    try {
      const res = await api.post("/campaigns", { name: newCampaignName });
      const data = await res.json();
      await fetchCampaigns();
      setSelectedCampaignId(data.id);
      setNewCampaignName("Backend Developer - Tháng 7/2026");
    } catch (e: any) {
      alert(e.message);
    } finally {
      setCreatingCampaign(false);
    }
  };

  const handleUploadJd = async () => {
    if (!jdFile || !selectedCampaignId) return;
    setUploadingJd(true);
    const formData = new FormData();
    formData.append("file", jdFile);
    try {
      const res = await api.post(`/campaigns/${selectedCampaignId}/jd`, formData);
      const data = await res.json();
      setLastJobId(data.job_id);
      pollJobStatus(data.job_id);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setUploadingJd(false);
    }
  };

  const handleUploadCvs = async () => {
    if (!cvFiles || cvFiles.length === 0 || !selectedCampaignId) return;
    setUploadingCvs(true);
    const formData = new FormData();
    for (let i = 0; i < cvFiles.length; i++) {
      formData.append("files", cvFiles[i]);
    }
    try {
      const res = await api.post(`/campaigns/${selectedCampaignId}/cvs`, formData);
      const data = await res.json();
      setLastJobId(data.job_id);
      pollJobStatus(data.job_id);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setUploadingCvs(false);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    setPolling(true);
    const interval = setInterval(async () => {
      try {
        const res = await api.get(`/jobs/${jobId}`);
        const data = await res.json();
        setJobStatus(data);
        if (data.status === "DONE" || data.status === "FAILED") {
          clearInterval(interval);
          setPolling(false);
          fetchCandidates();
        }
      } catch (e) {
        clearInterval(interval);
        setPolling(false);
      }
    }, 1500);
  };

  const handleSaveSettings = async () => {
    if (!selectedCampaignId) return;
    setSavingSettings(true);
    const skills = skillsOverride.split(",").map(s => s.trim().toLowerCase()).filter(Boolean);
    try {
      await api.put(`/campaigns/${selectedCampaignId}/settings`, {
        w_embed: wEmbed,
        required_skills: skills,
        min_years_override: minYears
      });
      alert("Đã lưu cấu hình campaign!");
    } catch (e: any) {
      alert(e.message);
    } finally {
      setSavingSettings(false);
    }
  };

  const handleStartScreening = async () => {
    if (!selectedCampaignId) return;
    setScreening(true);
    try {
      const res = await api.post(`/campaigns/${selectedCampaignId}/screen`);
      const data = await res.json();
      setLastJobId(data.job_id);
      pollJobStatus(data.job_id);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setScreening(false);
    }
  };

  const handleGetRanking = async () => {
    if (!selectedCampaignId) return;
    try {
      const res = await api.get(`/campaigns/${selectedCampaignId}/ranking`);
      const data = await res.json();
      setRanking(data.results || []);
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleStartReview = async () => {
    if (!selectedCampaignId || !drillCandidateId) return;
    setLoadingReview(true);
    try {
      const res = await api.post(`/campaigns/${selectedCampaignId}/candidates/${drillCandidateId}/review`);
      const data = await res.json();
      pollJobStatus(data.job_id);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoadingReview(false);
    }
  };

  const handleGetReview = async () => {
    if (!selectedCampaignId || !drillCandidateId) return;
    setLoadingReview(true);
    try {
      const res = await api.get(`/campaigns/${selectedCampaignId}/candidates/${drillCandidateId}/review`);
      const data = await res.json();
      setReviewData(data);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoadingReview(false);
    }
  };

  const handleStartProfile = async () => {
    if (!selectedCampaignId || !drillCandidateId) return;
    setLoadingProfile(true);
    try {
      const res = await api.post(`/campaigns/${selectedCampaignId}/candidates/${drillCandidateId}/profile`);
      const data = await res.json();
      pollJobStatus(data.job_id);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoadingProfile(false);
    }
  };

  const handleGetProfile = async () => {
    if (!selectedCampaignId || !drillCandidateId) return;
    setLoadingProfile(true);
    try {
      const res = await api.get(`/campaigns/${selectedCampaignId}/candidates/${drillCandidateId}/profile`);
      const data = await res.json();
      setProfileData(data);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setLoadingProfile(false);
    }
  };

  const handleUpdateStatus = async (newStatus: string) => {
    if (!drillCandidateId) return;
    setUpdatingStatus(true);
    try {
      await api.put(`/automation/candidates/${drillCandidateId}/status`, {
        pipeline_status: newStatus
      });
      fetchCandidates();
      alert("Đã cập nhật trạng thái ứng viên!");
    } catch (e: any) {
      alert(e.message);
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleGenerateEmail = async () => {
    if (!selectedCampaignId || !drillCandidateId) return;
    setGeneratingEmail(true);
    try {
      const res = await api.post("/automation/generate-email", {
        campaign_id: selectedCampaignId,
        candidate_id: drillCandidateId,
        email_type: emailType
      });
      const data = await res.json();
      setEmailSubject(data.email_subject || "");
      setEmailContent(data.email_content || "");
    } catch (e: any) {
      alert(e.message);
    } finally {
      setGeneratingEmail(false);
    }
  };

  // Filters for Ranking Dashboard
  const filteredRanking = ranking.filter(row => {
    if (row.score_total < minTotalScore) return false;
    if (!showErrors && row.parse_status && row.parse_status !== "OK") return false;
    return true;
  });

  const drilldownCandidate = candidates.find(c => c.id === drillCandidateId);
  const drilldownRankingRow = ranking.find(r => r.candidate_id === drillCandidateId);

  return (
    <div className="min-h-screen bg-[#0B0F19] text-slate-100 flex flex-col">
      {/* Header Navigation */}
      <header className="border-b border-slate-800 bg-[#0F172A] p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/" className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <Award className="w-5 h-5 text-blue-400" />
              <span>Job Opening Screening</span>
            </h1>
            <p className="text-xs text-slate-400">Mỗi đợt tuyển dụng gồm 1 JD và toàn bộ CV ứng tuyển vị trí đó</p>
          </div>
        </div>
        
        {/* Polling/Job status tag */}
        {polling && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/30 text-blue-400 rounded-full text-xs">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            <span>Đang xử lý job: {lastJobId.slice(0, 8)}... ({jobStatus?.status || "RUNNING"})</span>
          </div>
        )}
      </header>

      <div className="flex-1 max-w-7xl w-full mx-auto px-4 py-8 grid lg:grid-cols-12 gap-8">
        
        {/* LEFT COLUMN - Settings & Uploads (4 Cols) */}
        <section className="lg:col-span-4 space-y-6">
          {/* Campaign Select Card */}
          <div className="glass-card rounded-xl p-5 space-y-4">
            <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider">1) Job Opening</h2>
            <div className="space-y-3">
              <select
                value={selectedCampaignId || ""}
                onChange={(e) => setSelectedCampaignId(Number(e.target.value) || null)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 text-slate-200"
              >
                <option value="">(Tạo đợt tuyển dụng mới)</option>
                {campaigns.map(c => (
                  <option key={c.id} value={c.id}>{c.id}: {c.name}</option>
                ))}
              </select>

              {!selectedCampaignId && (
                <div className="space-y-2 pt-2 border-t border-slate-800">
                  <input
                    type="text"
                    value={newCampaignName}
                    onChange={(e) => setNewCampaignName(e.target.value)}
                    placeholder="Ví dụ: Backend Developer - Tháng 7/2026"
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs focus:outline-none text-slate-200"
                  />
                  <button
                    onClick={handleCreateCampaign}
                    disabled={creatingCampaign}
                    className="w-full text-xs py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors disabled:opacity-40"
                  >
                    Tạo Job Opening mới
                  </button>
                </div>
              )}
            </div>
          </div>

          {selectedCampaignId && (
            <>
              {/* JD & CV Upload Card */}
              <div className="glass-card rounded-xl p-5 space-y-5">
                <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider">2) JD & Candidate CVs</h2>
                
                {/* JD Upload */}
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-300">JD cho vị trí này (1 file, upload lại sẽ thay JD cũ):</label>
                  <div className="flex gap-2">
                    <input
                      type="file"
                      onChange={(e) => setJdFile(e.target.files?.[0] || null)}
                      accept=".pdf,.txt,.docx,.md"
                      className="flex-1 text-xs bg-slate-900 border border-slate-800 rounded-lg px-2 py-1.5 file:hidden text-slate-300 cursor-pointer"
                    />
                    <button
                      onClick={handleUploadJd}
                      disabled={!jdFile || uploadingJd}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs rounded-lg font-medium transition-colors disabled:opacity-40 shrink-0"
                    >
                      {uploadingJd ? "Uploading..." : "Upload / Replace JD"}
                    </button>
                  </div>
                </div>

                {/* CVs Upload */}
                <div className="space-y-2 pt-3 border-t border-slate-800">
                  <label className="text-xs font-medium text-slate-300">CV ứng tuyển vị trí này (upload nhiều file):</label>
                  <div className="flex gap-2">
                    <input
                      type="file"
                      multiple
                      onChange={(e) => setCvFiles(e.target.files)}
                      accept=".pdf,.docx"
                      className="flex-1 text-xs bg-slate-900 border border-slate-800 rounded-lg px-2 py-1.5 file:hidden text-slate-300 cursor-pointer"
                    />
                    <button
                      onClick={handleUploadCvs}
                      disabled={!cvFiles || cvFiles.length === 0 || uploadingCvs}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-xs rounded-lg font-medium transition-colors disabled:opacity-40 shrink-0"
                    >
                      {uploadingCvs ? "Uploading..." : "Upload CVs"}
                    </button>
                  </div>
                </div>
              </div>

              {/* Campaign settings Card */}
              <div className="glass-card rounded-xl p-5 space-y-4">
                <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider">3) Scoring Settings</h2>
                <div className="space-y-3 text-xs">
                  {/* Slider for wEmbed */}
                  <div className="space-y-1.5">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Trọng số Embed (w_embed)</span>
                      <span className="font-bold text-blue-400">{wEmbed}</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={wEmbed}
                      onChange={(e) => setWEmbed(Number(e.target.value))}
                      className="w-full accent-blue-500"
                    />
                  </div>

                  {/* Required skills override */}
                  <div className="space-y-1">
                    <label className="text-slate-400">Các kỹ năng yêu cầu (ngăn cách bằng dấu phẩy):</label>
                    <input
                      type="text"
                      value={skillsOverride}
                      onChange={(e) => setSkillsOverride(e.target.value)}
                      placeholder="e.g. Python, Docker, React"
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-blue-500 text-slate-200"
                    />
                  </div>

                  {/* Min years override */}
                  <div className="space-y-1">
                    <label className="text-slate-400">Kinh nghiệm tối thiểu (năm):</label>
                    <input
                      type="number"
                      step="0.5"
                      min="0"
                      value={minYears}
                      onChange={(e) => setMinYears(Number(e.target.value) || 0)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-blue-500 text-slate-200"
                    />
                  </div>

                  <button
                    onClick={handleSaveSettings}
                    disabled={savingSettings}
                    className="w-full text-xs py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors disabled:opacity-40"
                  >
                    {savingSettings ? "Saving..." : "Lưu cấu hình"}
                  </button>
                </div>
              </div>
            </>
          )}
        </section>

        {/* RIGHT COLUMN - Dashboard, Ranking, Drilldown (8 Cols) */}
        <main className="lg:col-span-8 space-y-6">
          {!selectedCampaignId ? (
            <div className="h-96 glass-card rounded-2xl flex flex-col items-center justify-center text-center max-w-md mx-auto p-6 space-y-4">
              <Sparkles className="w-12 h-12 text-blue-400 animate-pulse" />
                <h3 className="text-lg font-bold text-white">Bắt đầu một đợt tuyển dụng</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                Tạo Job Opening, upload 1 JD và các CV ứng tuyển cùng vị trí để chạy ranking.
                </p>
            </div>
          ) : (
            <>
              {/* Screening & Action Controls */}
              <div className="glass-card rounded-xl p-5 flex flex-wrap items-center justify-between gap-4">
                <div className="space-y-1">
                  <h3 className="font-bold text-white text-sm">Chạy ranking cho Job Opening này</h3>
                  <p className="text-xs text-slate-400">So khớp toàn bộ CV trong đợt tuyển dụng với JD hiện tại</p>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleStartScreening}
                    disabled={screening}
                    className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition-all disabled:opacity-40 hover:shadow-[0_0_15px_rgba(59,130,246,0.3)]"
                  >
                    🚀 Bắt đầu Sàng Lọc
                  </button>
                  <button
                    onClick={handleGetRanking}
                    className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg text-xs font-bold transition-colors"
                  >
                    Xem Xếp Hạng
                  </button>
                </div>
              </div>

              {/* Ranking Dashboard */}
              {ranking.length > 0 && (
                <div className="glass-card rounded-xl p-5 space-y-5">
                  <div className="flex justify-between items-center">
                    <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Bảng Xếp Hạng Ứng Viên</h2>
                    
                    {/* Filters bar */}
                    <div className="flex items-center gap-4 text-xs">
                      <div className="flex items-center gap-1.5">
                        <input
                          type="checkbox"
                          id="showErr"
                          checked={showErrors}
                          onChange={(e) => setShowErrors(e.target.checked)}
                          className="rounded border-slate-700 bg-slate-900 text-blue-500 focus:ring-blue-500/20"
                        />
                        <label htmlFor="showErr" className="text-slate-400 cursor-pointer">Hiển thị lỗi/Quality</label>
                      </div>
                      
                      <div className="flex items-center gap-1.5">
                        <span className="text-slate-400">Min Score:</span>
                        <input
                          type="number"
                          value={minTotalScore}
                          onChange={(e) => setMinTotalScore(Number(e.target.value) || 0)}
                          className="w-12 bg-slate-900 border border-slate-800 rounded px-1.5 py-0.5 text-center text-slate-200"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Table View */}
                  <div className="overflow-x-auto border border-slate-800/80 rounded-lg">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="bg-slate-900/60 border-b border-slate-800 text-slate-400 uppercase tracking-wider font-bold">
                          <th className="p-3">ID</th>
                          <th className="p-3">File CV</th>
                          <th className="p-3 text-center">Score Total</th>
                          <th className="p-3 text-center">Embed match</th>
                          <th className="p-3 text-center">Rule match</th>
                          <th className="p-3 text-center">Trạng thái</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800 bg-slate-900/20">
                        {filteredRanking.map((row) => (
                          <tr 
                            key={row.candidate_id} 
                            onClick={() => setDrillCandidateId(row.candidate_id)}
                            className={`hover:bg-slate-800/40 cursor-pointer transition-colors ${
                              drillCandidateId === row.candidate_id ? "bg-blue-500/10" : ""
                            }`}
                          >
                            <td className="p-3 text-slate-400 font-bold">{row.candidate_id}</td>
                            <td className="p-3 font-semibold text-slate-200 truncate max-w-[200px]">{row.filename}</td>
                            <td className="p-3 text-center text-blue-400 font-extrabold">{row.score_total}</td>
                            <td className="p-3 text-center text-slate-400">{row.score_embed}</td>
                            <td className="p-3 text-center text-slate-400">{row.score_rules}</td>
                            <td className="p-3 text-center">
                              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                                row.pipeline_status === "Rejected" ? "bg-rose-500/10 text-rose-400" :
                                row.pipeline_status === "Offered" ? "bg-emerald-500/10 text-emerald-400" :
                                "bg-blue-500/10 text-blue-400"
                              }`}>
                                {row.pipeline_status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Candidate Drill-down (Review/Radar/Evidence Tabs) */}
              {drillCandidateId && drilldownCandidate && (
                <div className="glass-card rounded-xl p-5 space-y-6">
                  {/* Candidate header */}
                  <div className="flex justify-between items-start border-b border-slate-800 pb-4">
                    <div>
                      <h3 className="text-lg font-bold text-white">{drilldownCandidate.filename}</h3>
                      <p className="text-xs text-slate-400">ID Ứng Viên: {drillCandidateId} | Trạng thái: {drilldownCandidate.pipeline_status}</p>
                    </div>
                    {drilldownRankingRow && (
                      <div className="flex items-center gap-6">
                        <div className="text-center">
                          <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Total Score</p>
                          <p className="text-2xl font-black text-blue-400">{drilldownRankingRow.score_total}</p>
                        </div>
                        <div className="text-center">
                          <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Quality Score</p>
                          <p className="text-2xl font-black text-slate-300">{drilldownCandidate.quality_score}</p>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Tabs controller */}
                  <div className="flex border-b border-slate-800 text-xs">
                    {(["evidence", "rules", "review", "profile", "email"] as const).map(tab => (
                      <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`px-4 py-2.5 font-bold transition-all border-b-2 capitalize ${
                          activeTab === tab 
                            ? "border-blue-500 text-blue-400" 
                            : "border-transparent text-slate-400 hover:text-slate-200"
                        }`}
                      >
                        {tab === "email" ? "📧 Email Automation" : tab}
                      </button>
                    ))}
                  </div>

                  {/* Tab contents */}
                  <div className="pt-2">
                    {activeTab === "evidence" && (
                      <div className="space-y-4">
                        <h4 className="text-xs font-bold text-slate-400 uppercase">Evidence Chunks from CV</h4>
                        {drilldownRankingRow?.evidence && drilldownRankingRow.evidence.length > 0 ? (
                          drilldownRankingRow.evidence.map((chunk, cIdx) => (
                            <textarea
                              key={cIdx}
                              readOnly
                              value={chunk}
                              rows={5}
                              className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-xs text-slate-300 font-mono focus:outline-none"
                            />
                          ))
                        ) : (
                          <p className="text-xs text-slate-500">Không có evidence.</p>
                        )}
                      </div>
                    )}

                    {activeTab === "rules" && (
                      <div className="space-y-3">
                        <h4 className="text-xs font-bold text-slate-400 uppercase">Match Rules Checklist</h4>
                        <pre className="bg-slate-900 border border-slate-800 p-4 rounded-lg text-xs font-mono text-emerald-400 overflow-x-auto">
                          {JSON.stringify(drilldownRankingRow?.rules || {}, null, 2)}
                        </pre>
                      </div>
                    )}

                    {activeTab === "review" && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <h4 className="text-xs font-bold text-slate-400 uppercase">LLM Llama3 Review Details</h4>
                          <div className="flex gap-2">
                            <button
                              onClick={handleStartReview}
                              disabled={loadingReview}
                              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold rounded-md transition-colors"
                            >
                              Khởi chạy Review
                            </button>
                            <button
                              onClick={handleGetReview}
                              disabled={loadingReview}
                              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-[10px] font-bold rounded-md transition-colors"
                            >
                              Lấy Kết Quả Review
                            </button>
                          </div>
                        </div>

                        {reviewData ? (
                          <div className="space-y-3 bg-slate-900/60 border border-slate-800 rounded-lg p-4 text-xs">
                            <div>
                              <p className="font-bold text-blue-400 uppercase text-[10px]">LLM Match Score</p>
                              <p className="text-lg font-black text-white">{reviewData.score_llm}/100</p>
                            </div>
                            <div>
                              <p className="font-bold text-slate-400 uppercase text-[10px]">Tóm tắt thế mạnh (Strengths)</p>
                              <p className="text-slate-300 italic">
                                {typeof reviewData.strengths_json === 'string' ? reviewData.strengths_json : JSON.stringify(reviewData.strengths_json)}
                              </p>
                            </div>
                            <div>
                              <p className="font-bold text-slate-400 uppercase text-[10px]">Điểm hạn chế (Gaps)</p>
                              <p className="text-slate-300 italic">
                                {typeof reviewData.gaps_json === 'string' ? reviewData.gaps_json : JSON.stringify(reviewData.gaps_json)}
                              </p>
                            </div>
                          </div>
                        ) : (
                          <p className="text-xs text-slate-500">Chưa có dữ liệu review. Nhấn nút để lấy dữ liệu.</p>
                        )}
                      </div>
                    )}

                    {activeTab === "profile" && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <h4 className="text-xs font-bold text-slate-400 uppercase">Radar match & Candidate Profile</h4>
                          <div className="flex gap-2">
                            <button
                              onClick={handleStartProfile}
                              disabled={loadingProfile}
                              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold rounded-md transition-colors"
                            >
                              Bóc tách Profile
                            </button>
                            <button
                              onClick={handleGetProfile}
                              disabled={loadingProfile}
                              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-[10px] font-bold rounded-md transition-colors"
                            >
                              Lấy Kết Quả & Radar Chart
                            </button>
                          </div>
                        </div>

                        {profileData ? (
                          <div className="grid md:grid-cols-2 gap-4">
                            <div className="space-y-3 bg-slate-900/60 border border-slate-800 rounded-lg p-4 text-xs">
                              <h5 className="font-bold text-slate-300 mb-2 border-b border-slate-800 pb-1.5">Thông tin Profile</h5>
                              <p><span className="text-slate-500">Họ và tên:</span> <strong className="text-white">{profileData.name}</strong></p>
                              <p><span className="text-slate-500">Email:</span> <span className="text-slate-300">{profileData.email}</span></p>
                              <p><span className="text-slate-500">Số điện thoại:</span> <span className="text-slate-300">{profileData.phone}</span></p>
                              <p><span className="text-slate-500">Kinh nghiệm:</span> <strong className="text-white">{profileData.years_experience} năm</strong></p>
                              <p><span className="text-slate-500">Học vấn:</span> <span className="text-slate-300">{profileData.education}</span></p>
                            </div>
                            <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-4 text-xs flex flex-col items-center justify-center text-center">
                              <Radar className="w-8 h-8 text-blue-400 mb-2 animate-pulse" />
                              <h5 className="font-bold text-slate-300 mb-1">Radar Chart Match</h5>
                              <p className="text-slate-500 text-[10px] leading-relaxed max-w-[200px]">
                                So khớp kỹ năng ứng viên so với yêu cầu của JD chi tiết.
                              </p>
                            </div>
                          </div>
                        ) : (
                          <p className="text-xs text-slate-500">Chưa có hồ sơ profile chi tiết.</p>
                        )}
                      </div>
                    )}

                    {activeTab === "email" && (
                      <div className="space-y-4">
                        <div className="grid sm:grid-cols-2 gap-4">
                          {/* Left Panel: Status update & Type selector */}
                          <div className="space-y-4">
                            <div className="space-y-1.5">
                              <label className="text-xs font-bold text-slate-400 uppercase">Cập nhật Trạng thái Ứng Viên</label>
                              <div className="flex gap-2">
                                <select
                                  value={drilldownCandidate.pipeline_status}
                                  onChange={(e) => handleUpdateStatus(e.target.value)}
                                  disabled={updatingStatus}
                                  className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none"
                                >
                                  <option value="Applied">Applied</option>
                                  <option value="Shortlisted">Shortlisted</option>
                                  <option value="Interviewing">Interviewing</option>
                                  <option value="Offered">Offered</option>
                                  <option value="Rejected">Rejected</option>
                                </select>
                              </div>
                            </div>

                            <div className="space-y-1.5">
                              <label className="text-xs font-bold text-slate-400 uppercase">Chọn loại Thư Phản Hồi</label>
                              <select
                                value={emailType}
                                onChange={(e) => setEmailType(e.target.value as any)}
                                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none"
                              >
                                <option value="interview">Mời phỏng vấn (Interview Invite)</option>
                                <option value="offer">Thư mời nhận việc (Job Offer)</option>
                                <option value="rejection">Thư từ chối (Rejection Letter)</option>
                              </select>
                            </div>

                            <button
                              onClick={handleGenerateEmail}
                              disabled={generatingEmail}
                              className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition-all hover:shadow-[0_0_12px_rgba(59,130,246,0.3)] disabled:opacity-40"
                            >
                              {generatingEmail ? "Đang soạn thư..." : "Soạn Email bằng AI"}
                            </button>
                          </div>

                          {/* Right Panel: Content preview */}
                          <div className="space-y-3 bg-slate-900/60 border border-slate-800 rounded-lg p-4 text-xs">
                            <h5 className="font-bold text-slate-300 border-b border-slate-800 pb-1.5 flex items-center gap-1.5">
                              <Mail className="w-4 h-4 text-blue-400" />
                              <span>Bản nháp email tuyển dụng</span>
                            </h5>
                            
                            <div className="space-y-2">
                              <div>
                                <span className="text-slate-500 block text-[10px]">Tiêu đề:</span>
                                <input
                                  type="text"
                                  readOnly
                                  value={emailSubject}
                                  placeholder="Tiêu đề thư mời..."
                                  className="w-full bg-slate-950 border border-slate-800 rounded-md p-1.5 text-xs text-slate-200 focus:outline-none"
                                />
                              </div>
                              <div>
                                <span className="text-slate-500 block text-[10px]">Nội dung thư:</span>
                                <textarea
                                  readOnly
                                  value={emailContent}
                                  placeholder="Nội dung thư tuyển dụng tự động tạo sẽ xuất hiện ở đây..."
                                  rows={8}
                                  className="w-full bg-slate-950 border border-slate-800 rounded-md p-2 text-xs text-slate-300 focus:outline-none"
                                />
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </main>

      </div>
    </div>
  );
}
