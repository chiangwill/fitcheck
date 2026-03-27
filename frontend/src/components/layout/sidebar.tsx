"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Home, FileText, Search, BarChart2, Send } from "lucide-react"

const NAV = [
  { href: "/",        icon: Home,      label: "Pipeline" },
  { href: "/resume",  icon: FileText,  label: "Resume" },
  { href: "/jobs",    icon: Search,    label: "Jobs" },
  { href: "/match",   icon: BarChart2, label: "Analysis" },
  { href: "/apps",    icon: Send,      label: "Applications" },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-52 shrink-0 flex flex-col h-screen sticky top-0 border-r border-[#1f1f1f] bg-[#141414]">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-[#1f1f1f]">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-[#f97316] flex items-center justify-center">
            <span className="text-white text-xs font-black">T</span>
          </div>
          <span className="font-bold text-sm text-[#e8e8e6] tracking-wide">Tobira</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-3 space-y-0.5">
        {NAV.map(({ href, icon: Icon, label }) => {
          const active = pathname === href
          return (
            <Link
              key={href}
              href={href}
              className={`
                flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium
                transition-colors duration-100
                ${active
                  ? "bg-[#222222] text-[#e8e8e6]"
                  : "text-[#737370] hover:text-[#e8e8e6] hover:bg-[#1a1a1a]"
                }
              `}
            >
              <Icon
                size={15}
                className={active ? "text-[#f97316]" : ""}
              />
              {label}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-[#1f1f1f]">
        <p className="text-xs text-[#3d3d3a]">Japan Job Pipeline</p>
      </div>
    </aside>
  )
}
