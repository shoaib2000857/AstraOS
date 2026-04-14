import { FormEvent, useEffect, useState } from 'react'
import axios from 'axios'

import type { Conversation, SearchSource } from '../types'
import { truncateText } from '../utils'

type QAResponse = {
  answer: string
  sources: SearchSource[]
  memories_used: number
}

export default function QA() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState<SearchSource[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [conversationId, setConversationId] = useState<number | ''>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [statusText, setStatusText] = useState('Ask grounded questions against indexed document chunks and any relevant stored memory.')

  useEffect(() => {
    void loadConversations()
  }, [])

  async function loadConversations() {
    try {
      const response = await axios.get<Conversation[]>('/api/conversations')
      setConversations(response.data)
    } catch (err) {
      console.error(err)
    }
  }

  async function askQuestion(event: FormEvent) {
    event.preventDefault()
    if (!question.trim()) return

    setLoading(true)
    setError('')
    try {
      const response = await axios.post<QAResponse>('/api/qa/answer', {
        question,
        conversation_id: conversationId || undefined,
      })
      setAnswer(response.data.answer)
      setSources(response.data.sources || [])
      setStatusText(
        response.data.memories_used
          ? `Answer generated with ${response.data.memories_used} memory item${response.data.memories_used === 1 ? '' : 's'} in scope.`
          : 'Answer generated without extra memory matches.',
      )
    } catch (err) {
      console.error(err)
      setError('Failed to generate an answer. Make sure the backend and local model are running.')
      setAnswer('')
      setSources([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[380px_minmax(0,1fr)]">
      <section className="rounded-[28px] border border-stone-200/80 bg-white/85 p-5 shadow-[0_20px_60px_rgba(59,45,18,0.08)] backdrop-blur">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">Grounding</p>
        <h2 className="mt-1 text-2xl font-semibold text-stone-900">Ask Workspace Questions</h2>
        <p className="mt-2 text-sm text-stone-600">{statusText}</p>

        <form onSubmit={askQuestion} className="mt-5 space-y-4">
          <div>
            <label className="mb-2 block text-sm font-medium text-stone-700">Question</label>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={6}
              className="w-full rounded-[22px] border border-stone-300 bg-white px-4 py-3 text-sm shadow-sm outline-none transition focus:border-amber-400 focus:ring-4 focus:ring-amber-100"
              placeholder="Try: What did I say about my project focus, and which file is most relevant?"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-stone-700">Optional conversation context</label>
            <select
              value={conversationId}
              onChange={(event) => setConversationId(event.target.value ? Number(event.target.value) : '')}
              className="w-full rounded-2xl border border-stone-300 bg-white px-4 py-3 text-sm shadow-sm outline-none transition focus:border-amber-400 focus:ring-4 focus:ring-amber-100"
            >
              <option value="">None</option>
              {conversations.map((conversation) => (
                <option key={conversation.id} value={conversation.id}>
                  {truncateText(conversation.title || `Conversation ${conversation.id}`, 72)}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="w-full rounded-full bg-amber-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-amber-500 disabled:cursor-not-allowed disabled:bg-amber-300"
          >
            {loading ? 'Asking...' : 'Ask AstraOS'}
          </button>
        </form>

        {error && <div className="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
      </section>

      <section className="rounded-[28px] border border-stone-200/80 bg-white/85 p-5 shadow-[0_20px_60px_rgba(59,45,18,0.08)] backdrop-blur">
        <div className="border-b border-stone-200 pb-4">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">Answer</p>
          <h2 className="mt-1 text-2xl font-semibold text-stone-900">Grounded Response</h2>
        </div>

        <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
          <div className="min-w-0">
            <div className="min-h-[240px] rounded-[24px] bg-stone-50/80 p-5 ring-1 ring-stone-200">
              {loading ? (
                <div className="text-sm text-stone-500">Generating answer...</div>
              ) : answer ? (
                <div className="whitespace-pre-wrap text-sm leading-7 text-stone-800">{answer}</div>
              ) : (
                <div className="text-sm text-stone-500">
                  Ask a question to see a grounded answer built from stored documents and memory context.
                </div>
              )}
            </div>
          </div>

          <aside className="rounded-[24px] border border-stone-200 bg-stone-50/80 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">Sources</p>
            <h3 className="mt-1 text-lg font-semibold text-stone-900">Retrieved Context</h3>
            <div className="mt-4 space-y-3">
              {sources.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-stone-300 bg-white px-4 py-5 text-sm text-stone-500">
                  No supporting chunks shown yet.
                </div>
              ) : (
                sources.map((source) => (
                  <div key={`${source.id}-${source.payload?.chunk_index ?? 0}`} className="rounded-2xl bg-white px-4 py-4 shadow-sm ring-1 ring-stone-200">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-semibold text-stone-900">
                        {source.title || source.payload?.title || `Document ${source.document_id ?? 'chunk'}`}
                      </div>
                      <span className="rounded-full bg-amber-100 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-amber-800">
                        {source.search_mode || 'search'}
                      </span>
                    </div>
                    <div className="mt-2 text-xs text-stone-500">
                      Score: {typeof source.score === 'number' ? source.score.toFixed(3) : 'n/a'}
                    </div>
                    <div className="mt-3 text-sm leading-6 text-stone-700">
                      {truncateText(source.text || source.payload?.text || 'No snippet available.', 220)}
                    </div>
                  </div>
                ))
              )}
            </div>
          </aside>
        </div>
      </section>
    </div>
  )
}
