import type { AppView } from '../types'

const items: Array<{ view: AppView; label: string; blurb: string }> = [
  { view: 'chat', label: 'Chat', blurb: 'Persistent conversations with memory-aware context.' },
  { view: 'memories', label: 'Memories', blurb: 'Inspect, edit, and curate long-term user facts.' },
  { view: 'documents', label: 'Documents', blurb: 'Upload files, inspect chunks, and extract actions.' },
  { view: 'qa', label: 'Q&A', blurb: 'Ask grounded questions across documents and stored memory.' },
]

type SidebarProps = {
  view: AppView
  onView: (view: AppView) => void
}

export default function Sidebar({ view, onView }: SidebarProps) {
  return (
    <aside className="rounded-[28px] border border-stone-200/80 bg-white/80 p-4 shadow-[0_20px_60px_rgba(59,45,18,0.08)] backdrop-blur">
      <div className="mb-4 rounded-2xl bg-gradient-to-br from-amber-100 via-orange-50 to-white p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">Workspace</p>
        <h2 className="mt-2 text-xl font-semibold text-stone-900">Prototype Control Deck</h2>
        <p className="mt-2 text-sm text-stone-600">
          Focus on the core loops first: working chat, usable memory, correct ingestion, grounded answers.
        </p>
      </div>

      <nav className="space-y-2">
        {items.map((item) => {
          const active = item.view === view
          return (
            <button
              key={item.view}
              onClick={() => onView(item.view)}
              className={`w-full rounded-2xl border px-4 py-3 text-left transition ${
                active
                  ? 'border-stone-900 bg-stone-950 text-stone-50 shadow-[0_14px_30px_rgba(28,25,23,0.22)]'
                  : 'border-stone-200 bg-stone-50/80 text-stone-800 hover:border-amber-300 hover:bg-amber-50'
              }`}
            >
              <div className="text-sm font-semibold">{item.label}</div>
              <div className={`mt-1 text-xs ${active ? 'text-stone-300' : 'text-stone-500'}`}>{item.blurb}</div>
            </button>
          )
        })}
      </nav>
    </aside>
  )
}
