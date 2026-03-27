"use client"

import { useEffect, useState } from "react"
import { Link2, Briefcase, Loader2, ChevronRight, ExternalLink, AlertTriangle } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import type { Job } from "@/lib/types"

function JobRow({ job, onClick }: { job: Job; onClick: () => void }) {
  const parsed = job.parsed_json as Record<string, unknown> | null
  const title = (parsed?.title as string) ?? job.title ?? "Parsing..."
  const company = (parsed?.company as string) ?? job.company ?? ""
  const skills = (parsed?.required_skills as string[] | undefined) ?? []
  const isParsed = !!parsed

  return (
    <div
      onClick={onClick}
      className="flex items-center gap-4 p-4 rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] hover:border-[#3a3a3a] hover:bg-[#1e1e1e] transition-colors cursor-pointer group"
    >
      <div className={`w-8 h-8 rounded-md flex items-center justify-center shrink-0 ${isParsed ? "bg-[#3b82f6]/10" : "bg-[#222222]"}`}>
        <Briefcase size={14} className={isParsed ? "text-[#3b82f6]" : "text-[#3d3d3a]"} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium text-[#e8e8e6] truncate">{title}</p>
          {!isParsed && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#f59e0b]/10 text-[#f59e0b] border border-[#f59e0b]/20 shrink-0">
              parsing
            </span>
          )}
        </div>
        {company && <p className="text-xs text-[#737370] mt-0.5">{company}</p>}
        {skills.length > 0 && (
          <div className="flex gap-1 mt-1.5 flex-wrap">
            {skills.slice(0, 4).map((s) => (
              <span key={s} className="text-[10px] px-1.5 py-0.5 rounded bg-[#222222] text-[#737370] border border-[#2a2a2a]">{s}</span>
            ))}
            {skills.length > 4 && <span className="text-[10px] text-[#3d3d3a]">+{skills.length - 4}</span>}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 shrink-0">
        <a
          href={job.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="p-1.5 rounded text-[#3d3d3a] hover:text-[#737370] transition-colors"
        >
          <ExternalLink size={13} />
        </a>
        <ChevronRight size={14} className="text-[#3d3d3a] group-hover:text-[#737370] transition-colors" />
      </div>
    </div>
  )
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [url, setUrl] = useState("")
  const [parsing, setParsing] = useState(false)
  const [selected, setSelected] = useState<Job | null>(null)

  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try { setJobs(await api.jobs.list()) }
    catch (e) { setError(e instanceof Error ? e.message : "Failed to load") }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const parse = async () => {
    if (!url.trim()) return
    setParsing(true)
    try {
      await api.jobs.parse(url.trim())
      setUrl("")
      await load()
    } finally {
      setParsing(false)
    }
  }

  const parsed = selected?.parsed_json as Record<string, unknown> | null

  return (
    <div className="p-6 space-y-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-bold text-[#e8e8e6]">Jobs</h1>
        <p className="text-sm text-[#737370] mt-0.5">Paste a URL · Gemini extracts the details</p>
      </div>

      {/* URL input */}
      <div className="flex gap-2">
        <div className="flex-1 flex items-center gap-2 bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-3 focus-within:border-[#f97316]/50">
          <Link2 size={14} className="text-[#3d3d3a] shrink-0" />
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && parse()}
            placeholder="https://jobs.example.com/..."
            className="flex-1 bg-transparent py-2.5 text-sm text-[#e8e8e6] placeholder:text-[#3d3d3a] focus:outline-none"
          />
        </div>
        <button
          onClick={parse}
          disabled={parsing || !url.trim()}
          className="px-4 py-2.5 rounded-lg bg-[#f97316] text-white text-sm font-medium disabled:opacity-40 hover:bg-[#ea6c0a] transition-colors flex items-center gap-1.5"
        >
          {parsing ? <Loader2 size={13} className="animate-spin" /> : null}
          Parse
        </button>
      </div>

      {/* Job detail panel */}
      {selected && (
        <div className="rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] p-4 space-y-3">
          <div className="flex items-start justify-between">
            <div>
              <p className="font-semibold text-[#e8e8e6]">{(parsed?.title as string) ?? selected.title}</p>
              {!!parsed?.company && <p className="text-sm text-[#737370]">{String(parsed.company)}</p>}
            </div>
            <button onClick={() => setSelected(null)} className="text-xs text-[#3d3d3a] hover:text-[#737370]">✕</button>
          </div>
          <div className="flex gap-3 flex-wrap text-xs text-[#737370]">
            {!!parsed?.salary && <span>💰 {String(parsed.salary)}</span>}
            {!!parsed?.location && <span>📍 {String(parsed.location)}</span>}
            {!!parsed?.remote_policy && <span>🖥 {String(parsed.remote_policy)}</span>}
          </div>
          {!!parsed?.required_skills && (
            <div>
              <p className="text-[10px] uppercase tracking-wider text-[#3d3d3a] mb-1.5">Required skills</p>
              <div className="flex gap-1 flex-wrap">
                {(parsed.required_skills as string[]).map((s) => (
                  <span key={s} className="text-[10px] px-2 py-0.5 rounded bg-[#222222] text-[#f59e0b] border border-[#f59e0b]/20">{s}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* List */}
      {loading ? (
        <div className="space-y-2">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-4 p-4 rounded-lg border border-[#2a2a2a] bg-[#1a1a1a]">
              <Skeleton className="w-8 h-8 rounded-md shrink-0" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-48 rounded" />
                <Skeleton className="h-3 w-32 rounded" />
                <div className="flex gap-1">
                  {[0, 1, 2].map((j) => <Skeleton key={j} className="h-5 w-16 rounded" />)}
                </div>
              </div>
              <Skeleton className="w-5 h-5 rounded shrink-0" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-12 gap-3 text-[#737370]">
          <AlertTriangle size={18} className="text-[#ef4444]" />
          <p className="text-sm">{error}</p>
          <button onClick={load} className="text-xs text-[#f97316] hover:underline">Retry</button>
        </div>
      ) : jobs.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-[#3d3d3a] gap-2">
          <Briefcase size={28} />
          <p className="text-sm">No jobs yet — paste a URL above</p>
        </div>
      ) : (
        <div className="space-y-2">
          {jobs.map((j) => (
            <JobRow key={j.id} job={j} onClick={() => setSelected(j)} />
          ))}
        </div>
      )}
    </div>
  )
}
