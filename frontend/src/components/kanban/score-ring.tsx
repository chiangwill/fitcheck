"use client"

import { useEffect, useRef, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"

interface ScoreRingProps {
  score: number | null
  size?: number
}

function scoreColor(score: number | null) {
  if (score === null) return { stroke: "#2a2a2a", text: "#3d3d3a" }
  if (score >= 7)     return { stroke: "#22c55e", text: "#22c55e" }
  if (score >= 4)     return { stroke: "#f59e0b", text: "#f59e0b" }
  return               { stroke: "#ef4444",  text: "#ef4444"  }
}

export function ScoreRing({ score, size = 38 }: ScoreRingProps) {
  const r     = (size - 5) / 2
  const circ  = 2 * Math.PI * r
  const pct   = score !== null ? (score / 10) * circ : 0
  const { stroke, text } = scoreColor(score)

  // pulse once when score arrives
  const prev       = useRef<number | null>(null)
  const [pulse, setPulse] = useState(false)
  useEffect(() => {
    if (prev.current === null && score !== null) {
      setPulse(true)
      const t = setTimeout(() => setPulse(false), 700)
      return () => clearTimeout(t)
    }
    prev.current = score
  }, [score])

  return (
    <motion.div
      animate={pulse ? { scale: [1, 1.18, 1] } : { scale: 1 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="relative shrink-0"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="-rotate-90">
        {/* track */}
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1f1f1f" strokeWidth={3} />
        {/* progress */}
        <motion.circle
          cx={size/2} cy={size/2} r={r}
          fill="none"
          stroke={stroke}
          strokeWidth={3}
          strokeLinecap="round"
          strokeDasharray={circ}
          animate={{ strokeDashoffset: circ - pct, stroke }}
          initial={{ strokeDashoffset: circ }}
          transition={{ duration: 0.7, ease: "easeOut" }}
        />
      </svg>

      {/* number */}
      <div className="absolute inset-0 flex items-center justify-center">
        <AnimatePresence mode="wait">
          <motion.span
            key={score ?? "empty"}
            initial={{ opacity: 0, scale: 0.6 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.6 }}
            transition={{ duration: 0.25 }}
            className="text-[10px] font-bold tabular-nums"
            style={{ color: text }}
          >
            {score !== null ? score.toFixed(1) : "—"}
          </motion.span>
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
