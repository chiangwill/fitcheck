"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { ArrowLeft, CheckCircle2, XCircle, Lightbulb, FileEdit, Loader2, Copy, Check, AlertTriangle } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import type { Match, Job } from "@/lib/types"

function scoreColor(s: number) {
  if (s >= 7) return "#22c55e"
  if (s >= 4) return "#f59e0b"
  return "#ef4444"
}

function ScoreHero({ score }: { score: number }) {
  const color = scoreColor(score)
  const label = score >= 7 ? "Good fit" : score >= 4 ? "Partial fit" : "Low fit"
  const circ = 2 * Math.PI * 38
  const pct = (score / 10) * circ

  return (
    <div className="flex items-center gap-5">
      <div className="relative w-24 h-24">
        <svg width={96} height={96} className="-rotate-90">
          <circle cx={48} cy={48} r={38} fill="none" stroke="#2a2a2a" strokeWidth={5} />
          <circle cx={48} cy={48} r={38} fill="none" stroke={color} strokeWidth={5}
            strokeLinecap="round" strokeDasharray={circ}
            strokeDashoffset={circ - pct} style={{ transition: "stroke-dashoffset 0.8s ease" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-black" style={{ color }}>{score.toFixed(1)}</span>
          <span className="text-[10px] text-[#737370]">/ 10</span>
        </div>
      </div>
      <div>
        <p className="text-lg font-bold" style={{ color }}>{label}</p>
        <p className="text-sm text-[#737370] mt-0.5">AI match score</p>
      </div>
    </div>
  )
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000) }}
      className="flex items-center gap-1.5 text-xs text-[#737370] hover:text-[#e8e8e6] transition-colors"
    >
      {copied ? <Check size={12} className="text-[#22c55e]" /> : <Copy size={12} />}
      {copied ? "Copied" : "Copy"}
    </button>
  )
}

export default function MatchDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [match, setMatch] = useState<Match | null>(null)
  const [job, setJob] = useState<Job | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [tone, setTone] = useState("正式")
  const [tab, setTab] = useState<"zh" | "en">("zh")

  useEffect(() => {
    const load = async () => {
      setError(null)
      try {
        const m = await api.match.get(parseInt(id))
        setMatch(m)
        const j = await api.jobs.get(m.job_id)
        setJob(j)
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  const generate = async () => {
    if (!match) return
    setGenerating(true)
    try {
      await api.generate.coverLetter(match.id, tone)
      const updated = await api.match.get(match.id)
      setMatch(updated)
    } finally {
      setGenerating(false)
    }
  }

  if (loading) {
    return (
      <div className="p-6 space-y-5 max-w-2xl">
        <Skeleton className="h-4 w-28 rounded" />
        <div className="rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] p-5 space-y-4">
          <Skeleton className="h-5 w-56 rounded" />
          <Skeleton className="h-3 w-32 rounded" />
          <div className="flex items-center gap-5 mt-4">
            <Skeleton className="w-24 h-24 rounded-full shrink-0" />
            <div className="space-y-2">
              <Skeleton className="h-5 w-24 rounded" />
              <Skeleton className="h-3 w-28 rounded" />
            </div>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {[0, 1].map((i) => (
            <div key={i} className="rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] p-4 space-y-2">
              <Skeleton className="h-4 w-24 rounded" />
              {[0, 1, 2, 3].map((j) => <Skeleton key={j} className="h-3 w-full rounded" />)}
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 flex flex-col items-center justify-center h-64 gap-3 text-[#737370]">
        <AlertTriangle size={18} className="text-[#ef4444]" />
        <p className="text-sm">{error}</p>
        <button onClick={() => router.push("/match")} className="text-xs text-[#f97316] hover:underline">
          Back to Analysis
        </button>
      </div>
    )
  }

  if (!match) {
    return <div className="p-6 text-sm text-[#737370]">Match not found.</div>
  }

  const parsed = job?.parsed_json as Record<string, unknown> | null
  const title = (parsed?.title as string) ?? `Job #${match.job_id}`
  const company = parsed?.company as string | undefined

  return (
    <div className="p-6 space-y-5 max-w-2xl">
      {/* Back */}
      <button
        onClick={() => router.push("/match")}
        className="flex items-center gap-1.5 text-xs text-[#737370] hover:text-[#e8e8e6] transition-colors"
      >
        <ArrowLeft size={13} />
        Back to Analysis
      </button>

      {/* Header */}
      <div className="rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] p-5">
        <p className="text-lg font-bold text-[#e8e8e6]">{title}</p>
        {company && <p className="text-sm text-[#737370] mt-0.5">{company}</p>}
        <div className="mt-4">
          <ScoreHero score={match.score} />
        </div>
      </div>

      {/* Skills */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] p-4 space-y-2">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 size={13} className="text-[#22c55e]" />
            <span className="text-xs font-medium text-[#e8e8e6]">Matched ({match.matched_skills?.length ?? 0})</span>
          </div>
          {match.matched_skills?.map((s) => (
            <div key={s} className="flex items-start gap-1.5">
              <div className="w-1 h-1 rounded-full bg-[#22c55e] mt-1.5 shrink-0" />
              <span className="text-xs text-[#737370]">{s}</span>
            </div>
          ))}
        </div>

        <div className="rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] p-4 space-y-2">
          <div className="flex items-center gap-1.5">
            <XCircle size={13} className="text-[#ef4444]" />
            <span className="text-xs font-medium text-[#e8e8e6]">Missing ({match.missing_skills?.length ?? 0})</span>
          </div>
          {match.missing_skills?.map((s) => (
            <div key={s} className="flex items-start gap-1.5">
              <div className="w-1 h-1 rounded-full bg-[#ef4444] mt-1.5 shrink-0" />
              <span className="text-xs text-[#737370]">{s}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Suggestion */}
      {match.suggestion && (
        <div className="rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] p-4 space-y-2">
          <div className="flex items-center gap-1.5">
            <Lightbulb size={13} className="text-[#f59e0b]" />
            <span className="text-xs font-medium text-[#e8e8e6]">Suggestion</span>
          </div>
          <p className="text-xs text-[#737370] leading-relaxed whitespace-pre-wrap">{match.suggestion}</p>
        </div>
      )}

      {/* Cover letter */}
      <div className="rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <FileEdit size={13} className="text-[#737370]" />
            <span className="text-xs font-medium text-[#e8e8e6]">Cover Letter</span>
          </div>
          {!match.cover_letter && (
            <div className="flex items-center gap-2">
              <select
                value={tone}
                onChange={(e) => setTone(e.target.value)}
                className="bg-[#111111] border border-[#2a2a2a] rounded px-2 py-1 text-xs text-[#737370] focus:outline-none"
              >
                <option value="正式">Formal</option>
                <option value="活潑">Casual</option>
              </select>
              <button
                onClick={generate}
                disabled={generating}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#f97316] text-white text-xs font-medium disabled:opacity-40 hover:bg-[#ea6c0a] transition-colors"
              >
                {generating ? <Loader2 size={11} className="animate-spin" /> : null}
                Generate
              </button>
            </div>
          )}
        </div>

        {match.cover_letter ? (
          <>
            <div className="flex gap-3 border-b border-[#2a2a2a] pb-2">
              {(["zh", "en"] as const).map((t) => (
                <button key={t} onClick={() => setTab(t)} className={`text-xs pb-1 transition-colors ${tab === t ? "text-[#e8e8e6] border-b border-[#f97316]" : "text-[#737370]"}`}>
                  {t === "zh" ? "Chinese" : "English"}
                </button>
              ))}
            </div>
            <div className="space-y-2">
              {tab === "zh" && match.cover_letter && (
                <>
                  <p className="text-xs text-[#737370] leading-loose whitespace-pre-wrap">{match.cover_letter}</p>
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] text-[#3d3d3a]">{match.cover_letter.length} chars</span>
                    <CopyButton text={match.cover_letter} />
                  </div>
                </>
              )}
              {tab === "en" && (
                match.cover_letter_en
                  ? <>
                      <p className="text-xs text-[#737370] leading-loose whitespace-pre-wrap">{match.cover_letter_en}</p>
                      <div className="flex items-center justify-between pt-1">
                        <span className="text-[10px] text-[#3d3d3a]">{match.cover_letter_en.split(" ").length} words</span>
                        <CopyButton text={match.cover_letter_en} />
                      </div>
                    </>
                  : <p className="text-xs text-[#3d3d3a]">English version not available.</p>
              )}
            </div>
          </>
        ) : (
          <p className="text-xs text-[#3d3d3a]">No cover letter yet — generate one above.</p>
        )}
      </div>
    </div>
  )
}
