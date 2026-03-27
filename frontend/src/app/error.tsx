"use client"

import { useEffect } from "react"
import { AlertTriangle } from "lucide-react"

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center h-64 gap-3 text-[#737370]">
      <AlertTriangle size={20} className="text-[#ef4444]" />
      <p className="text-sm">Something went wrong.</p>
      <button
        onClick={reset}
        className="text-xs text-[#f97316] hover:underline"
      >
        Try again
      </button>
    </div>
  )
}
