"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { BarChart2, PlayCircle, Loader2, ChevronRight, AlertTriangle } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import type { Match, Job } from "@/lib/types"

function scoreColor(score: number) {
  if (score >= 7) return "#22c55e"
  if (score >= 4) return "#f59e0b"
  return "#ef4444"
}

function scoreLabel(score: number) {
  if (score >= 7) return "Good fit"
  if (score >= 4) return "Partial fit"
  return "Low fit"
}

function MatchRow({ match, job, onClick }: { match: Match; job: Job | undefined; onClick: () => void }) {
  const parsed = job?.parsed_json as Record<string, unknown> | null
  const title = (parsed?.title as string) ?? `Job #${match.job_id}`
  const company = parsed?.company as string | undefined
  const color = scoreColor(match.score)

  return (
    <div
      onClick={onClick}
      className="flex items-center gap-4 p-4 rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] hover:border-[#3a3a3a] hover:bg-[#1e1e1e] transition-colors cursor-pointer group"
    >
      <div className="w-10 h-10 rounded-full border-2 flex items-center justify-center shrink-0" style={{ borderColor: color }}>
        <span className="text-xs font-bold" style={{ color }}>{match.score.toFixed(1)}</span>
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-[#e8e8e6] truncate">{title}</p>
        <div className="flex items-center gap-2 mt-0.5">
          {company && <span className="text-xs text-[#737370]">{company}</span>}
          <span className="text-xs" style={{ color }}>{scoreLabel(match.score)}</span>
        </div>
      </div>

      <ChevronRight size={14} className="text-[#3d3d3a] group-hover:text-[#737370] transition-colors shrink-0" />
    </div>
  )
}

export default function MatchPage() {
  const router = useRouter()
  const [matches, setMatches] = useState<Match[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [selectedJob, setSelectedJob] = useState<string>("")

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const [m, j] = await Promise.all([api.match.list(), api.jobs.list()])
      setMatches(m)
      setJobs(j.filter((j) => j.parsed_json))
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const run = async () => {
    if (!selectedJob) return
    setRunning(true)
    try {
      const result = await api.match.run(parseInt(selectedJob))
      router.push(`/match/${result.id}`)
    } finally {
      setRunning(false)
    }
  }

  const jobsMap = Object.fromEntries(jobs.map((j) => [j.id, j]))

  return (
    <div className="p-6 space-y-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-bold text-[#e8e8e6]">Analysis</h1>
        <p className="text-sm text-[#737370] mt-0.5">AI scores your resume against each job</p>
      </div>

      {/* Run match */}
      <div className="rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] p-4 space-y-3">
        <div className="flex items-center gap-2">
          <PlayCircle size={14} className="text-[#737370]" />
          <span className="text-sm font-medium text-[#e8e8e6]">New analysis</span>
        </div>
        {jobs.length === 0 ? (
          <p className="text-xs text-[#737370]">Add jobs first → <a href="/jobs" className="text-[#f97316] hover:underline">Jobs page</a></p>
        ) : (
          <div className="flex gap-2">
            <select
              value={selectedJob}
              onChange={(e) => setSelectedJob(e.target.value)}
              className="flex-1 bg-[#111111] border border-[#2a2a2a] rounded-md px-3 py-2 text-sm text-[#e8e8e6] focus:outline-none focus:border-[#f97316]/50"
            >
              <option value="">Select a job...</option>
              {jobs.map((j) => {
                const p = j.parsed_json as Record<string, unknown> | null
                const label = `${p?.title ?? j.title ?? "Untitled"} · ${p?.company ?? ""}`
                return <option key={j.id} value={j.id}>{label}</option>
              })}
            </select>
            <button
              onClick={run}
              disabled={running || !selectedJob}
              className="px-4 py-2 rounded-md bg-[#f97316] text-white text-sm font-medium disabled:opacity-40 hover:bg-[#ea6c0a] transition-colors flex items-center gap-1.5"
            >
              {running ? <Loader2 size={13} className="animate-spin" /> : null}
              Run
            </button>
          </div>
        )}
      </div>

      {/* History */}
      {loading ? (
        <div className="space-y-2">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-4 p-4 rounded-lg border border-[#2a2a2a] bg-[#1a1a1a]">
              <Skeleton className="w-10 h-10 rounded-full shrink-0" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-44 rounded" />
                <Skeleton className="h-3 w-28 rounded" />
              </div>
              <Skeleton className="w-4 h-4 rounded shrink-0" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-12 gap-3 text-[#737370]">
          <AlertTriangle size={18} className="text-[#ef4444]" />
          <p className="text-sm">{error}</p>
          <button onClick={load} className="text-xs text-[#f97316] hover:underline">Retry</button>
        </div>
      ) : matches.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-[#3d3d3a] gap-2">
          <BarChart2 size={28} />
          <p className="text-sm">No analyses yet</p>
        </div>
      ) : (
        <div className="space-y-2">
          {matches.map((m) => (
            <MatchRow
              key={m.id}
              match={m}
              job={jobsMap[m.job_id]}
              onClick={() => router.push(`/match/${m.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
