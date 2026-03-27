export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded bg-[#222222] ${className ?? ""}`} />
  )
}
