import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from 'react'
import axios from 'axios'

import type { Conversation, ExtractedTask, ThreadMessage } from '../types'
import { formatDateTime, truncateText } from '../utils'

type StreamPayload =
  | { type: 'delta'; text?: string }
  | { type: 'done'; text?: string; conversation_id?: number; message_id?: number; memories_used?: number }
  | { type: 'error'; error?: string }

const EMPTY_ASSISTANT_ID = 'assistant-stream'

export default function Chat() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null)
  const [messages, setMessages] = useState<ThreadMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingConversationId, setLoadingConversationId] = useState<number | null>(null)
  const [taskLoading, setTaskLoading] = useState(false)
  const [tasks, setTasks] = useState<ExtractedTask[]>([])
  const [error, setError] = useState('')
  const [statusText, setStatusText] = useState('Memories are captured automatically when a message looks like a preference, project fact, or deadline.')
  const endRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    void refreshConversations()
  }, [])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages])

  async function refreshConversations(preferredId?: number | null) {
    const response = await axios.get<Conversation[]>('/api/conversations')
    const items = response.data
    setConversations(items)

    const targetId =
      preferredId ??
      (activeConversationId && items.some((item) => item.id === activeConversationId) ? activeConversationId : null) ??
      items[0]?.id ??
      null

    if (targetId) {
      await loadConversation(targetId)
      return
    }

    setActiveConversationId(null)
    setMessages([])
    setTasks([])
  }

  async function loadConversation(conversationId: number) {
    setLoadingConversationId(conversationId)
    setError('')
    try {
      const response = await axios.get<Conversation>(`/api/conversations/${conversationId}`)
      setActiveConversationId(response.data.id)
      setMessages(response.data.messages || [])
      setTasks([])
    } catch (err) {
      console.error(err)
      setError('Failed to load the selected conversation.')
    } finally {
      setLoadingConversationId(null)
    }
  }

  function startNewConversation() {
    setActiveConversationId(null)
    setMessages([])
    setTasks([])
    setError('')
    setStatusText('Starting a fresh session. The next message will create a new conversation.')
  }

  async function deleteConversation(conversationId: number) {
    try {
      await axios.delete(`/api/conversations/${conversationId}`)
      const nextId = activeConversationId === conversationId ? null : activeConversationId
      await refreshConversations(nextId)
      setStatusText('Conversation deleted.')
    } catch (err) {
      console.error(err)
      setError('Failed to delete the conversation.')
    }
  }

  function updateStreamingAssistant(content: string) {
    setMessages((previous) => {
      const next = [...previous]
      const index = next.findIndex((message) => message.id === EMPTY_ASSISTANT_ID)
      if (index >= 0) {
        next[index] = { ...next[index], content }
      } else {
        next.push({ id: EMPTY_ASSISTANT_ID, role: 'assistant', content })
      }
      return next
    })
  }

  async function sendMessage(event?: FormEvent) {
    event?.preventDefault()
    const prompt = input.trim()
    if (!prompt || loading) return

    const userMessage: ThreadMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: prompt,
    }

    setMessages((previous) => [...previous, userMessage, { id: EMPTY_ASSISTANT_ID, role: 'assistant', content: '' }])
    setInput('')
    setLoading(true)
    setError('')
    setStatusText('Streaming reply from the local model...')

    let nextConversationId = activeConversationId
    let assembled = ''
    let buffer = ''

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          conversation_id: activeConversationId,
        }),
      })

      if (!response.ok || !response.body) {
        throw new Error('Unable to reach the chat endpoint.')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''

        for (const part of parts) {
          const line = part
            .split('\n')
            .map((entry) => entry.trim())
            .find((entry) => entry.startsWith('data:'))

          if (!line) continue

          const rawPayload = line.replace(/^data:\s*/, '')
          let payload: StreamPayload | null = null

          try {
            payload = JSON.parse(rawPayload) as StreamPayload
          } catch {
            assembled += rawPayload
            updateStreamingAssistant(assembled)
            continue
          }

          if (payload.type === 'delta') {
            assembled += payload.text || ''
            updateStreamingAssistant(assembled)
          }

          if (payload.type === 'done') {
            assembled = payload.text || assembled
            nextConversationId = payload.conversation_id ?? nextConversationId
            updateStreamingAssistant(assembled)
            setStatusText(
              payload.memories_used
                ? `Reply completed with ${payload.memories_used} memory item${payload.memories_used === 1 ? '' : 's'} in scope.`
                : 'Reply completed.',
            )
          }

          if (payload.type === 'error') {
            throw new Error(payload.error || 'Streaming failed.')
          }
        }

        if (done) break
      }

      await refreshConversations(nextConversationId)
    } catch (err) {
      console.error(err)
      setError(err instanceof Error ? err.message : 'Failed to send the message.')
      updateStreamingAssistant('The backend could not complete this response. Check that Ollama and the backend are both running.')
    } finally {
      setLoading(false)
    }
  }

  async function extractTasks() {
    if (!activeConversationId) return
    setTaskLoading(true)
    setError('')
    try {
      const response = await axios.post<{ tasks: ExtractedTask[] }>(`/api/tasks/from_conversation/${activeConversationId}`)
      setTasks(response.data.tasks || [])
      setStatusText(
        response.data.tasks?.length
          ? `Extracted ${response.data.tasks.length} potential action item${response.data.tasks.length === 1 ? '' : 's'}.`
          : 'No action items were detected in this conversation.',
      )
    } catch (err) {
      console.error(err)
      setError('Task extraction failed for this conversation.')
    } finally {
      setTaskLoading(false)
    }
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      void sendMessage()
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
      <section className="rounded-[28px] border border-stone-200/80 bg-white/85 p-4 shadow-[0_20px_60px_rgba(59,45,18,0.08)] backdrop-blur">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">Sessions</p>
            <h2 className="mt-1 text-xl font-semibold text-stone-900">Conversation History</h2>
          </div>
          <button
            onClick={startNewConversation}
            className="rounded-full bg-stone-950 px-3 py-2 text-xs font-semibold text-white transition hover:bg-stone-800"
          >
            New Chat
          </button>
        </div>

        <div className="mt-4 space-y-2">
          {conversations.length === 0 && (
            <div className="rounded-2xl border border-dashed border-stone-300 bg-stone-50 px-4 py-5 text-sm text-stone-500">
              No saved conversations yet. Send a message to start one.
            </div>
          )}

          {conversations.map((conversation) => {
            const active = conversation.id === activeConversationId
            return (
              <div
                key={conversation.id}
                className={`rounded-2xl border px-3 py-3 transition ${
                  active ? 'border-stone-900 bg-stone-950 text-stone-50' : 'border-stone-200 bg-stone-50/80 text-stone-800'
                }`}
              >
                <button className="w-full text-left" onClick={() => void loadConversation(conversation.id)}>
                  <div className="text-sm font-semibold">{truncateText(conversation.title || 'Untitled conversation', 46)}</div>
                  <div className={`mt-1 text-xs ${active ? 'text-stone-300' : 'text-stone-500'}`}>
                    {formatDateTime(conversation.updated_at)}
                  </div>
                  <div className={`mt-2 text-xs ${active ? 'text-stone-300' : 'text-stone-500'}`}>
                    {conversation.messages.length} message{conversation.messages.length === 1 ? '' : 's'}
                  </div>
                </button>
                <button
                  onClick={() => void deleteConversation(conversation.id)}
                  className={`mt-3 text-xs font-semibold ${active ? 'text-amber-300' : 'text-amber-700'}`}
                >
                  Delete
                </button>
              </div>
            )
          })}
        </div>
      </section>

      <section className="rounded-[28px] border border-stone-200/80 bg-white/85 p-5 shadow-[0_20px_60px_rgba(59,45,18,0.08)] backdrop-blur">
        <div className="flex flex-col gap-3 border-b border-stone-200 pb-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">Assistant</p>
            <h2 className="mt-1 text-2xl font-semibold text-stone-900">Working Chat Loop</h2>
            <p className="mt-2 text-sm text-stone-600">{statusText}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => void extractTasks()}
              disabled={!activeConversationId || taskLoading}
              className="rounded-full border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 transition hover:border-amber-400 hover:bg-amber-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {taskLoading ? 'Extracting...' : 'Extract Action Items'}
            </button>
          </div>
        </div>

        <div className="mt-4 grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
          <div className="min-w-0">
            <div className="h-[420px] overflow-y-auto rounded-[24px] border border-stone-200 bg-stone-50/70 p-4">
              {loadingConversationId ? (
                <div className="text-sm text-stone-500">Loading conversation...</div>
              ) : messages.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-stone-300 bg-white/80 px-4 py-6 text-sm text-stone-500">
                  Ask AstraOS to remember something about you, summarize a decision, or help with your next step.
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[85%] rounded-[22px] px-4 py-3 text-sm shadow-sm ${
                          message.role === 'user'
                            ? 'bg-stone-950 text-stone-50'
                            : 'bg-white text-stone-800 ring-1 ring-stone-200'
                        }`}
                      >
                        <div className="whitespace-pre-wrap leading-6">{message.content || (loading ? '...' : '')}</div>
                        {message.timestamp && (
                          <div className={`mt-2 text-[11px] ${message.role === 'user' ? 'text-stone-300' : 'text-stone-400'}`}>
                            {formatDateTime(message.timestamp)}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  <div ref={endRef} />
                </div>
              )}
            </div>

            <form onSubmit={(event) => void sendMessage(event)} className="mt-4 space-y-3">
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={handleComposerKeyDown}
                rows={4}
                className="w-full rounded-[22px] border border-stone-300 bg-white px-4 py-3 text-sm text-stone-900 shadow-sm outline-none transition focus:border-amber-400 focus:ring-4 focus:ring-amber-100"
                placeholder="Message AstraOS. Try: Remember that I prefer concise, technical explanations."
              />
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <p className="text-xs text-stone-500">
                  Shift+Enter adds a new line. Enter sends the message.
                </p>
                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className="rounded-full bg-amber-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-amber-500 disabled:cursor-not-allowed disabled:bg-amber-300"
                >
                  {loading ? 'Sending...' : 'Send Message'}
                </button>
              </div>
            </form>

            {error && <div className="mt-3 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
          </div>

          <aside className="rounded-[24px] border border-stone-200 bg-stone-50/70 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">Derived Output</p>
            <h3 className="mt-1 text-lg font-semibold text-stone-900">Action Items</h3>
            <p className="mt-2 text-sm text-stone-600">
              Pull task-like lines from the active conversation so the assistant starts feeling like a workspace, not just a chat box.
            </p>

            <div className="mt-4 space-y-3">
              {tasks.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-stone-300 bg-white px-4 py-5 text-sm text-stone-500">
                  No extracted items yet. Run task extraction on a conversation that includes TODOs, deadlines, or checklist lines.
                </div>
              ) : (
                tasks.map((task, index) => (
                  <div key={`${task.text}-${index}`} className="rounded-2xl bg-white px-4 py-3 shadow-sm ring-1 ring-stone-200">
                    <div className="text-sm font-medium text-stone-900">{task.text}</div>
                    <div className="mt-1 text-xs text-stone-500">
                      {task.line ? `Line ${task.line}` : 'Checklist item'} - matched "{task.match}"
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
