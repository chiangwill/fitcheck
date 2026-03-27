"use client"

import { useEffect, useRef, useState } from "react"
import { FileText, Upload, CheckCircle, Trash2, ChevronDown, ChevronUp, Loader2, AlertTriangle } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import type { Resume } from "@/lib/types"

function SkillBadge({ label }: { label: string }) {
  return (
    <span className="text-[10px] px-2 py-0.5 rounded bg-[#222222] text-[#737370] border border-[#2a2a2a]">
      {label}
    </span>
  )
}

function ResumeCard({
  resume,
  onSetActive,
  onDelete,
}: {
  resume: Resume
  onSetActive: () => void
  onDelete: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const parsed = resume.parsed_json as Record<string, unknown> | null
  const skills = (parsed?.skills as string[] | undefined) ?? []
  const yoe = parsed?.years_of_experience as number | undefined

  return (
    <div className={`rounded-lg border transition-colors ${resume.is_active ? "border-[#f97316]/40 bg-[#1a1a1a]" : "border-[#2a2a2a] bg-[#1a1a1a]"}`}>
      <div className="flex items-start justify-between p-4">
        <div className="flex items-start gap-3">
          <div className={`mt-0.5 w-8 h-8 rounded-md flex items-center justify-center shrink-0 ${resume.is_active ? "bg-[#f97316]/10" : "bg-[#222222]"}`}>
            <FileText size={14} className={resume.is_active ? "text-[#f97316]" : "text-[#737370]"} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-[#e8e8e6]">{resume.version_name}</span>
              {resume.is_active && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#f97316]/10 text-[#f97316] border border-[#f97316]/20 font-medium">
                  active
                </span>
              )}
            </div>
            <p className="text-xs text-[#737370] mt-0.5">{resume.created_at.slice(0, 10)}</p>
            {yoe !== undefined && (
              <p className="text-xs text-[#737370] mt-0.5">{yoe} yrs exp</p>
            )}
            {skills.length > 0 && (
              <div className="flex gap-1 flex-wrap mt-2">
                {skills.slice(0, 5).map((s) => <SkillBadge key={s} label={s} />)}
                {skills.length > 5 && (
                  <span className="text-[10px] text-[#3d3d3a]">+{skills.length - 5}</span>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1">
          {parsed && (
            <button
              onClick={() => setExpanded((v) => !v)}
              className="p-1.5 rounded text-[#737370] hover:text-[#e8e8e6] hover:bg-[#222222] transition-colors"
            >
              {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
          )}
          {!resume.is_active && (
            <button
              onClick={onSetActive}
              className="p-1.5 rounded text-[#737370] hover:text-[#22c55e] hover:bg-[#222222] transition-colors"
              title="Set as active"
            >
              <CheckCircle size={14} />
            </button>
          )}
          <button
            onClick={onDelete}
            className="p-1.5 rounded text-[#737370] hover:text-[#ef4444] hover:bg-[#222222] transition-colors"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {expanded && parsed && (
        <div className="px-4 pb-4 border-t border-[#2a2a2a] pt-3 space-y-3">
          {!!parsed.summary && (
            <p className="text-xs text-[#737370] leading-relaxed">{String(parsed.summary)}</p>
          )}
          {(parsed.work_history as unknown[])?.length > 0 && (
            <div className="space-y-2">
              <p className="text-[10px] uppercase tracking-wider text-[#3d3d3a] font-medium">Experience</p>
              {(parsed.work_history as Record<string, string>[]).map((w, i) => (
                <div key={i} className="flex items-start justify-between">
                  <div>
                    <p className="text-xs font-medium text-[#e8e8e6]">{w.title}</p>
                    <p className="text-xs text-[#737370]">{w.company}</p>
                  </div>
                  <p className="text-xs text-[#3d3d3a] shrink-0 ml-4">{w.duration}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function ResumePage() {
  const [resumes, setResumes] = useState<Resume[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [versionName, setVersionName] = useState("")
  const fileRef = useRef<HTMLInputElement>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      setResumes(await api.resume.list())
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleUpload = async () => {
    const file = fileRef.current?.files?.[0]
    if (!file || !versionName.trim()) return
    setUploading(true)
    const form = new FormData()
    form.append("file", file)
    try {
      const res = await fetch(
        `http://localhost:8000/resume/upload?version_name=${encodeURIComponent(versionName)}`,
        { method: "POST", body: form }
      )
      if (res.ok) {
        setVersionName("")
        if (fileRef.current) fileRef.current.value = ""
        await load()
      }
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-bold text-[#e8e8e6]">Resume</h1>
        <p className="text-sm text-[#737370] mt-0.5">Manage versions · Set one as active for scoring</p>
      </div>

      {/* Upload */}
      <div className="rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Upload size={14} className="text-[#737370]" />
          <span className="text-sm font-medium text-[#e8e8e6]">Upload PDF</span>
        </div>
        <input
          type="text"
          placeholder="Version name (e.g. Backend v2)"
          value={versionName}
          onChange={(e) => setVersionName(e.target.value)}
          className="w-full bg-[#111111] border border-[#2a2a2a] rounded-md px-3 py-2 text-sm text-[#e8e8e6] placeholder:text-[#3d3d3a] focus:outline-none focus:border-[#f97316]/50"
        />
        <div className="flex items-center gap-3">
          <input ref={fileRef} type="file" accept=".pdf" className="text-xs text-[#737370] file:mr-3 file:py-1 file:px-3 file:rounded file:border file:border-[#2a2a2a] file:bg-[#222222] file:text-[#737370] file:text-xs file:cursor-pointer" />
          <button
            onClick={handleUpload}
            disabled={uploading || !versionName.trim()}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#f97316] text-white text-xs font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#ea6c0a] transition-colors shrink-0"
          >
            {uploading ? <Loader2 size={12} className="animate-spin" /> : <Upload size={12} />}
            Upload
          </button>
        </div>
      </div>

      {/* List */}
      {loading ? (
        <div className="space-y-2">
          {[0, 1].map((i) => (
            <div key={i} className="rounded-lg border border-[#2a2a2a] bg-[#1a1a1a] p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <Skeleton className="w-8 h-8 rounded-md shrink-0" />
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-36 rounded" />
                    <Skeleton className="h-3 w-20 rounded" />
                    <div className="flex gap-1 mt-2">
                      {[0, 1, 2].map((j) => <Skeleton key={j} className="h-5 w-14 rounded" />)}
                    </div>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Skeleton className="w-7 h-7 rounded" />
                  <Skeleton className="w-7 h-7 rounded" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-12 gap-3 text-[#737370]">
          <AlertTriangle size={18} className="text-[#ef4444]" />
          <p className="text-sm">{error}</p>
          <button onClick={load} className="text-xs text-[#f97316] hover:underline">Retry</button>
        </div>
      ) : resumes.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-[#3d3d3a] gap-2">
          <FileText size={28} />
          <p className="text-sm">No resumes yet</p>
        </div>
      ) : (
        <div className="space-y-2">
          {resumes.map((r) => (
            <ResumeCard
              key={r.id}
              resume={r}
              onSetActive={async () => { await api.resume.setActive(r.id); load() }}
              onDelete={async () => { await api.resume.delete(r.id); load() }}
            />
          ))}
        </div>
      )}
    </div>
  )
}
