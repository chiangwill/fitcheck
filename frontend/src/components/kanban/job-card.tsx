"use client"

import { ScoreRing } from "./score-ring"
import type { CrawlerJob, JobScore } from "@/lib/types"

function fmtSalary(min: number | null, max: number | null): string {
  if (min && max) {
    const lo = Math.round(min / 1_000_000)
    const hi = Math.round(max / 1_000_000)
    if (lo && hi) return `¥${lo}–${hi}M`
  }
  if (min) {
    const lo = Math.round(min / 1_000_000)
    return lo ? `¥${lo}M+` : `¥${min.toLocaleString()}+`
  }
  return ""
}

interface JobCardProps {
  job: CrawlerJob
  score: JobScore | null
  isDragging?: boolean
  isOverlay?: boolean
}

export function JobCard({ job, score, isDragging, isOverlay }: JobCardProps) {
  const salary  = fmtSalary(job.salary_min, job.salary_max)
  const missing = score?.missing_skills?.[0] ?? null

  return (
    <div
      className={`
        bg-[#1a1a1a] border rounded-lg p-3 select-none
        transition-colors duration-100
        ${isOverlay
          ? "border-[#f97316]/40 shadow-lg shadow-black/40 rotate-1 scale-105"
          : isDragging
          ? "border-[#2a2a2a] opacity-30"
          : "border-[#2a2a2a] hover:border-[#3a3a3a] hover:bg-[#1e1e1e]"
        }
      `}
    >
      <div className="flex items-start gap-3">
        <ScoreRing score={score?.score ?? null} size={38} />

        <div className="flex-1 min-w-0">
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => { if (isDragging || isOverlay) e.preventDefault() }}
            className="text-sm font-medium text-[#e8e8e6] hover:text-[#f97316] transition-colors line-clamp-1"
          >
            {job.title ?? "Untitled"}
          </a>

          {job.company && (
            <p className="text-xs text-[#737370] mt-0.5 line-clamp-1">{job.company}</p>
          )}

          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
            {job.remote_level && (
              <span className="text-[10px] text-[#737370] bg-[#222222] px-1.5 py-0.5 rounded">
                {job.remote_level}
              </span>
            )}
            {salary && (
              <span className="text-[10px] text-[#737370]">{salary}</span>
            )}
          </div>

          {missing && (
            <p className="text-[10px] text-[#f59e0b] mt-1 line-clamp-1">↑ {missing}</p>
          )}
        </div>
      </div>
    </div>
  )
}
