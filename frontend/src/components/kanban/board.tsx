"use client"

import { useState, useEffect, useCallback, useMemo } from "react"
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  useDroppable,
  useDraggable,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core"
import { AnimatePresence, motion } from "framer-motion"
import { Loader2, RefreshCw, Zap, X } from "lucide-react"
import { JobCard } from "./job-card"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import type { CrawlerJob, JobScore, JobStatus } from "@/lib/types"

const COLUMNS: { id: JobStatus | "none"; label: string; color: string }[] = [
  { id: "none",       label: "Unsorted",   color: "#737370" },
  { id: "interested", label: "Interested", color: "#3b82f6" },
  { id: "applied",    label: "Applied",    color: "#22c55e" },
  { id: "rejected",   label: "Pass",       color: "#ef4444" },
]

// ── Draggable card wrapper ────────────────────────────────────────────────────
function DraggableCard({
  job,
  score,
}: {
  job: CrawlerJob
  score: JobScore | null
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: job.id,
  })

  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      className="cursor-grab active:cursor-grabbing touch-none"
    >
      <JobCard job={job} score={score} isDragging={isDragging} />
    </div>
  )
}

// ── Droppable column ──────────────────────────────────────────────────────────
function DroppableColumn({
  col,
  jobs,
  scores,
}: {
  col: (typeof COLUMNS)[number]
  jobs: CrawlerJob[]
  scores: Record<string, JobScore>
}) {
  const { setNodeRef, isOver } = useDroppable({ id: col.id })

  return (
    <div className="flex flex-col gap-2 min-h-0">
      {/* Header */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full" style={{ background: col.color }} />
          <span className="text-xs font-medium text-[#737370]">{col.label}</span>
        </div>
        <span
          className="text-xs font-bold tabular-nums"
          style={{ color: jobs.length ? col.color : "#3d3d3a" }}
        >
          {jobs.length}
        </span>
      </div>

      {/* Drop zone */}
      <div
        ref={setNodeRef}
        className={`
          flex-1 flex flex-col gap-2 overflow-y-auto p-2 rounded-lg border min-h-[160px]
          transition-colors duration-150
          ${isOver ? "border-[#f97316]/30 bg-[#f97316]/5" : "border-[#1f1f1f]"}
        `}
      >
        <AnimatePresence mode="popLayout" initial={false}>
          {jobs.length === 0 ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center justify-center h-20 text-xs text-[#3d3d3a]"
            >
              {isOver ? "Release to drop" : "Drop here"}
            </motion.div>
          ) : (
            jobs.map((job) => (
              <motion.div
                key={job.id}
                layout
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.15 }}
              >
                <DraggableCard job={job} score={scores[job.id] ?? null} />
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

// ── Filter chip ──────────────────────────────────────────────────────────────
function FilterChip({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`text-[10px] px-2 py-1 rounded border transition-colors whitespace-nowrap ${
        active
          ? "border-[#f97316]/50 bg-[#f97316]/10 text-[#f97316]"
          : "border-[#2a2a2a] text-[#737370] hover:border-[#3a3a3a] hover:text-[#e8e8e6]"
      }`}
    >
      {label}
    </button>
  )
}

// ── Main board ────────────────────────────────────────────────────────────────
export function KanbanBoard() {
  const [jobs, setJobs]       = useState<CrawlerJob[]>([])
  const [scores, setScores]   = useState<Record<string, JobScore>>({})
  const [statuses, setStatuses] = useState<Record<string, JobStatus>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)
  const [allTime, setAllTime] = useState(false)
  const [activeId, setActiveId] = useState<string | null>(null)
  const [bulkLoading, setBulkLoading] = useState(false)
  const [bulkProgress, setBulkProgress] = useState<{ done: number; total: number } | null>(null)

  const [filterRemote, setFilterRemote]   = useState<Set<string>>(new Set())
  const [filterJapanese, setFilterJapanese] = useState<Set<string>>(new Set())
  const [filterVisa, setFilterVisa]       = useState(false)
  const [filterScored, setFilterScored]   = useState(false)

  const remoteOptions = useMemo(
    () => [...new Set(jobs.map((j) => j.remote_level).filter(Boolean) as string[])].sort(),
    [jobs],
  )
  const japaneseOptions = useMemo(
    () => [...new Set(jobs.map((j) => j.japanese_level).filter(Boolean) as string[])].sort(),
    [jobs],
  )

  const filteredJobs = useMemo(() => {
    return jobs.filter((j) => {
      if (filterRemote.size > 0 && !filterRemote.has(j.remote_level ?? "")) return false
      if (filterJapanese.size > 0 && !filterJapanese.has(j.japanese_level ?? "")) return false
      if (filterVisa && !j.sponsors_visas) return false
      if (filterScored && !scores[j.id]) return false
      return true
    })
  }, [jobs, scores, filterRemote, filterJapanese, filterVisa, filterScored])

  const anyFilter = filterRemote.size > 0 || filterJapanese.size > 0 || filterVisa || filterScored

  const clearFilters = () => {
    setFilterRemote(new Set())
    setFilterJapanese(new Set())
    setFilterVisa(false)
    setFilterScored(false)
  }

  const toggleSet = (set: Set<string>, value: string): Set<string> => {
    const next = new Set(set)
    if (next.has(value)) next.delete(value)
    else next.add(value)
    return next
  }

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
  )

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.crawlerJobs.list(allTime)
      setJobs(data)
      if (data.length > 0) {
        const ids = data.map((j) => j.id)
        const [sc, st] = await Promise.all([
          api.crawlerJobs.batchScores(ids),
          api.crawlerJobs.statuses(ids),
        ])
        setScores(sc)
        setStatuses(st)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load")
    } finally {
      setLoading(false)
    }
  }, [allTime])

  useEffect(() => { load() }, [load])

  const colJobs = (colId: string) =>
    filteredJobs.filter((j) => (statuses[j.id] ?? "none") === colId)

  const moveJob = async (jobId: string, newStatus: JobStatus | "none") => {
    const prev = statuses[jobId] ?? "none"
    if (prev === newStatus) return
    setStatuses((s) => ({ ...s, [jobId]: newStatus as JobStatus }))
    try {
      if (newStatus === "none") await api.crawlerJobs.clearStatus(jobId)
      else await api.crawlerJobs.setStatus(jobId, newStatus)
    } catch {
      setStatuses((s) => ({ ...s, [jobId]: prev as JobStatus }))
    }
  }

  const onDragStart = ({ active }: DragStartEvent) =>
    setActiveId(active.id as string)

  const onDragEnd = ({ active, over }: DragEndEvent) => {
    setActiveId(null)
    if (!over) return
    moveJob(active.id as string, over.id as JobStatus | "none")
  }

  const bulkScore = async () => {
    const unscored = jobs.filter((j) => !scores[j.id])
    if (!unscored.length) return
    setBulkLoading(true)
    setBulkProgress({ done: 0, total: unscored.length })
    for (let i = 0; i < unscored.length; i++) {
      try {
        const result = await api.crawlerJobs.score(unscored[i].id)
        setScores((s) => ({ ...s, [unscored[i].id]: result }))
      } catch {}
      setBulkProgress({ done: i + 1, total: unscored.length })
      if (i < unscored.length - 1) await new Promise((r) => setTimeout(r, 4000))
    }
    setBulkLoading(false)
    setBulkProgress(null)
  }

  const activeJob = activeId ? jobs.find((j) => j.id === activeId) ?? null : null

  if (loading) {
    return (
      <div className="flex flex-col gap-4 h-full">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Skeleton className="w-24 h-7 rounded-md" />
            <Skeleton className="w-14 h-4 rounded" />
          </div>
          <Skeleton className="w-20 h-7 rounded-md" />
        </div>
        <div className="grid grid-cols-4 gap-3 flex-1 min-h-0">
          {COLUMNS.map((col) => (
            <div key={col.id} className="flex flex-col gap-2 min-h-0">
              <div className="flex items-center justify-between px-1">
                <Skeleton className="w-16 h-3 rounded" />
                <Skeleton className="w-4 h-3 rounded" />
              </div>
              <div className="flex flex-col gap-2 p-2 rounded-lg border border-[#1f1f1f] min-h-[160px]">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg p-3">
                    <div className="flex items-start gap-3">
                      <Skeleton className="w-[38px] h-[38px] rounded-full shrink-0" />
                      <div className="flex-1 space-y-2">
                        <Skeleton className="h-3.5 w-full rounded" />
                        <Skeleton className="h-3 w-2/3 rounded" />
                        <Skeleton className="h-3 w-1/3 rounded" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <p className="text-sm text-[#737370]">{error}</p>
        <button onClick={load} className="text-xs text-[#f97316] hover:underline">Retry</button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAllTime((v) => !v)}
            className="flex items-center gap-1.5 text-xs text-[#737370] hover:text-[#e8e8e6] transition-colors px-2.5 py-1.5 rounded-md border border-[#2a2a2a] hover:border-[#3a3a3a]"
          >
            <RefreshCw size={12} />
            {allTime ? "Last 7 days" : "All time"}
          </button>
          <span className="text-xs text-[#3d3d3a]">
            {anyFilter ? `${filteredJobs.length} / ${jobs.length}` : jobs.length} jobs
          </span>
        </div>

        <button
          onClick={bulkScore}
          disabled={bulkLoading}
          className="flex items-center gap-1.5 text-xs text-[#f97316] hover:text-[#ea6c0a] transition-colors px-2.5 py-1.5 rounded-md border border-[#2a2a2a] hover:border-[#f97316]/30 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {bulkLoading ? <Loader2 size={12} className="animate-spin" /> : <Zap size={12} />}
          {bulkProgress
            ? `Scoring ${bulkProgress.done}/${bulkProgress.total}…`
            : "Score all"}
        </button>
      </div>

      {/* Filters */}
      {jobs.length > 0 && (remoteOptions.length > 0 || japaneseOptions.length > 0) && (
        <div className="flex items-center gap-2 flex-wrap">
          {remoteOptions.map((opt) => (
            <FilterChip
              key={opt}
              label={opt}
              active={filterRemote.has(opt)}
              onClick={() => setFilterRemote(toggleSet(filterRemote, opt))}
            />
          ))}

          {remoteOptions.length > 0 && japaneseOptions.length > 0 && (
            <span className="w-px h-4 bg-[#2a2a2a]" />
          )}

          {japaneseOptions.map((opt) => (
            <FilterChip
              key={opt}
              label={opt}
              active={filterJapanese.has(opt)}
              onClick={() => setFilterJapanese(toggleSet(filterJapanese, opt))}
            />
          ))}

          <span className="w-px h-4 bg-[#2a2a2a]" />

          <FilterChip label="Visa sponsor" active={filterVisa} onClick={() => setFilterVisa((v) => !v)} />
          <FilterChip label="Scored" active={filterScored} onClick={() => setFilterScored((v) => !v)} />

          {anyFilter && (
            <button
              onClick={clearFilters}
              className="flex items-center gap-1 text-[10px] text-[#737370] hover:text-[#e8e8e6] transition-colors ml-1"
            >
              <X size={10} />
              Clear
            </button>
          )}
        </div>
      )}

      {/* Board */}
      <DndContext sensors={sensors} onDragStart={onDragStart} onDragEnd={onDragEnd}>
        <div className="grid grid-cols-4 gap-3 flex-1 min-h-0">
          {COLUMNS.map((col) => (
            <DroppableColumn
              key={col.id}
              col={col}
              jobs={colJobs(col.id)}
              scores={scores}
            />
          ))}
        </div>

        <DragOverlay dropAnimation={{ duration: 180, easing: "ease" }}>
          {activeJob && (
            <JobCard
              job={activeJob}
              score={scores[activeJob.id] ?? null}
              isOverlay
            />
          )}
        </DragOverlay>
      </DndContext>
    </div>
  )
}
