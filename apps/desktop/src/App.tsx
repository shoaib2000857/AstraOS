import { useState } from 'react'

import Chat from './components/Chat'
import Documents from './components/Documents'
import Memories from './components/Memories'
import QA from './components/QA'
import Sidebar from './components/Sidebar'
import type { AppView } from './types'

export default function App() {
  const [view, setView] = useState<AppView>('chat')

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-6 rounded-[28px] border border-stone-200/80 bg-white/80 p-6 shadow-[0_20px_60px_rgba(59,45,18,0.08)] backdrop-blur">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">AstraOS</p>
          <div className="mt-3 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h1 className="text-3xl font-semibold tracking-tight text-stone-900 md:text-4xl">
                Memory-augmented personal AI workspace
              </h1>
              <p className="mt-2 max-w-3xl text-sm text-stone-600 md:text-base">
                Chat with a local assistant, keep durable memories, ingest files, and ground answers in your own
                workspace context.
              </p>
            </div>
            <div className="rounded-2xl bg-stone-950 px-4 py-3 text-sm text-stone-100">
              Local-first stack: FastAPI, Ollama, SQLite, Qdrant, React
            </div>
          </div>
        </header>

        <div className="grid gap-6 lg:grid-cols-[260px_minmax(0,1fr)]">
          <Sidebar view={view} onView={setView} />
          <main className="min-w-0">
            {view === 'chat' && <Chat />}
            {view === 'memories' && <Memories />}
            {view === 'documents' && <Documents />}
            {view === 'qa' && <QA />}
          </main>
        </div>
      </div>
    </div>
  )
}
