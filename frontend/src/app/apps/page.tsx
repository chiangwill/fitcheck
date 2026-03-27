"use client"

import { useEffect, useState } from "react"
import { Send, Plus, Loader2, Trash2, AlertTriangle } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import type { Application, Job } from "@/lib/types"

const STATUS: Record<string, { label: string; color: string }> = {
  pending:      { label: "Pending",      color: "#737370" },
  applied:      { label: "Applied",      color: "#3b82f6" },
  interviewing: { label: "Interviewing", color: "#f59e0b" },
  offer:        { label: "Offer",        color: "#22c55e" },
  rejected:     { label: "Rejected",     color: "#ef4444" },
}

function AppCard({ app, job, onUpdate, onDelete }: {
  app: Application
  job: Job | undefined
  onUpdate: (status: string, notes: string) => void
  onDelete: () => void
}) {
  const parsed = job?.parsed_json as Record<string, unknown> | null
  const title = (parsed?.title as string) ?? `Job #${app.job_id}`
  const company = parsed?.company as string | undefined
  const { label, color } = STATUS[app.status] ?? STATUS.pending
  const [notes, setNotes] = useState(app.notes ?? "")
  const [status, setStatus] = useState(app.status)

  return (
    <div className="rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className="w-2 h-2 rounded-full mt-1.5 shrink-0" style={{ background: color }} />
          <div>
            <p className="text-sm font-medium text-[#e8e8e6]">{title}</p>
            {company && <p className="text-xs text-[#737370] mt-0.5">{company}</p>}
            {app.applied_at && (
              <p className="text-xs text-[#3d3d3a] mt-0.5">Applied {app.applied_at.slice(0, 10)}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-[10px] px-2 py-0.5 rounded border font-medium" style={{ color, borderColor: `${color}40`, background: `${color}10` }}>
            {label}
          </span>
          <button onClick={onDelete} className="p-1.5 rounded text-[#3d3d3a] hover:text-[#ef4444] hover:bg-[#222222] transition-colors">
            <Trash2 size={13} />
          </button>
        </div>
      </div>

      {/* Stage progress */}
      <div className="flex gap-1">
        {Object.entries(STATUS).map(([k, v]) => (
          <button
            key={k}
            onClick={() => { setStatus(k); onUpdate(k, notes) }}
            className="flex-1 h-1 rounded-full transition-colors"
            style={{ background: k === status ? v.color : "#2a2a2a" }}
            title={v.label}
          />
        ))}
      </div>

      {/* Status + notes */}
      <div className="space-y-2">
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); onUpdate(e.target.value, notes) }}
          className="w-full bg-[#111111] border border-[#2a2a2a] rounded px-2.5 py-1.5 text-xs text-[#e8e8e6] focus:outline-none focus:border-[#f97316]/50"
        >
          {Object.entries(STATUS).map(([k, v]) => (
            <option key={k} value={k}>{v.label}</option>
          ))}
        </select>
        <div className="flex gap-2">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Notes, interview tips, contact..."
            rows={2}
            className="flex-1 bg-[#111111] border border-[#2a2a2a] rounded px-2.5 py-1.5 text-xs text-[#e8e8e6] placeholder:text-[#3d3d3a] focus:outline-none focus:border-[#f97316]/50 resize-none"
          />
          <button
            onClick={() => onUpdate(status, notes)}
            className="px-3 py-1.5 rounded bg-[#222222] text-xs text-[#737370] hover:text-[#e8e8e6] hover:bg-[#2a2a2a] transition-colors self-end"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  )
}

export default function AppsPage() {
  const [apps, setApps] = useState<Application[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedJob, setSelectedJob] = useState("")
  const [adding, setAdding] = useState(false)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const [a, j] = await Promise.all([api.applications.list(), api.jobs.list()])
      setApps(a)
      setJobs(j.filter((j) => j.parsed_json))
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const add = async () => {
    if (!selectedJob) return
    setAdding(true)
    try { await api.applications.create(parseInt(selectedJob)); await load() }
    finally { setAdding(false) }
  }

  const jobsMap = Object.fromEntries(jobs.map((j) => [j.id, j]))

  return (
    <div className="p-6 space-y-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-bold text-[#e8e8e6]">Applications</h1>
        <p className="text-sm text-[#737370] mt-0.5">Track every application · From sent to offer</p>
      </div>

      {/* Add */}
      <div className="rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Plus size={14} className="text-[#737370]" />
          <span className="text-sm font-medium text-[#e8e8e6]">Add application</span>
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
                return <option key={j.id} value={j.id}>{(p?.title as string) ?? j.title} · {p?.company as string ?? ""}</option>
              })}
            </select>
            <button
              onClick={add}
              disabled={adding || !selectedJob}
              className="px-4 py-2 rounded-md bg-[#f97316] text-white text-sm font-medium disabled:opacity-40 hover:bg-[#ea6c0a] transition-colors flex items-center gap-1.5"
            >
              {adding ? <Loader2 size={13} className="animate-spin" /> : <Plus size={13} />}
              Add
            </button>
          </div>
        )}
      </div>

      {/* List */}
      {loading ? (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] p-4 space-y-3">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <Skeleton className="w-2 h-2 rounded-full mt-1.5 shrink-0" />
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-40 rounded" />
                    <Skeleton className="h-3 w-28 rounded" />
                  </div>
                </div>
                <Skeleton className="h-5 w-20 rounded" />
              </div>
              <div className="flex gap-1">
                {[0, 1, 2, 3, 4].map((j) => <Skeleton key={j} className="flex-1 h-1 rounded-full" />)}
              </div>
              <Skeleton className="h-7 w-full rounded" />
              <Skeleton className="h-14 w-full rounded" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-12 gap-3 text-[#737370]">
          <AlertTriangle size={18} className="text-[#ef4444]" />
          <p className="text-sm">{error}</p>
          <button onClick={load} className="text-xs text-[#f97316] hover:underline">Retry</button>
        </div>
      ) : apps.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-[#3d3d3a] gap-2">
          <Send size={28} />
          <p className="text-sm">No applications yet</p>
        </div>
      ) : (
        <div className="space-y-2">
          {apps.map((a) => (
            <AppCard
              key={a.id}
              app={a}
              job={jobsMap[a.job_id]}
              onUpdate={(status, notes) => api.applications.update(a.id, { status, notes })}
              onDelete={async () => { await api.applications.delete(a.id); load() }}
            />
          ))}
        </div>
      )}
    </div>
  )
}
