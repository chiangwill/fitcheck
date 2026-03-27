import { KanbanBoard } from "@/components/kanban/board"

export default function HomePage() {
  return (
    <div className="flex flex-col h-screen p-6 gap-4">
      <div>
        <h1 className="text-xl font-bold text-[#e8e8e6]">Pipeline</h1>
        <p className="text-sm text-[#737370] mt-0.5">
          Drag jobs across stages · AI scores your fit
        </p>
      </div>

      <div className="flex-1 min-h-0">
        <KanbanBoard />
      </div>
    </div>
  )
}
