import { FormEvent, useEffect, useState } from 'react'
import axios from 'axios'

import type { MemoryItem } from '../types'
import { formatDateTime } from '../utils'

const categories = ['profile', 'preference', 'project', 'deadline']

export default function Memories() {
  const [items, setItems] = useState<MemoryItem[]>([])
  const [text, setText] = useState('')
  const [category, setCategory] = useState('profile')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editingText, setEditingText] = useState('')
  const [editingCategory, setEditingCategory] = useState('profile')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [statusText, setStatusText] = useState('You can create memories manually here, and chat also auto-captures memory-worthy user facts.')

  useEffect(() => {
    void fetchMemories()
  }, [])

  async function fetchMemories() {
    setLoading(true)
    try {
      const response = await axios.get<MemoryItem[]>('/api/memories')
      setItems(response.data)
    } catch (err) {
      console.error(err)
      setError('Failed to load memories.')
    } finally {
      setLoading(false)
    }
  }

  async function createMemory(event: FormEvent) {
    event.preventDefault()
    if (!text.trim()) return
    setSaving(true)
    setError('')
    try {
      await axios.post('/api/memories', {
        text,
        category,
      })
      setText('')
      setCategory('profile')
      setStatusText('Memory saved.')
      await fetchMemories()
    } catch (err) {
      console.error(err)
      setError('Failed to save the memory.')
    } finally {
      setSaving(false)
    }
  }

  function startEditing(item: MemoryItem) {
    setEditingId(item.id)
    setEditingText(item.text)
    setEditingCategory(item.category)
  }

  async function updateMemory(id: number) {
    if (!editingText.trim()) return
    setSaving(true)
    setError('')
    try {
      await axios.put(`/api/memories/${id}`, {
        text: editingText,
        category: editingCategory,
      })
      setEditingId(null)
      setStatusText('Memory updated.')
      await fetchMemories()
    } catch (err) {
      console.error(err)
      setError('Failed to update the memory.')
    } finally {
      setSaving(false)
    }
  }

  async function deleteMemory(id: number) {
    setError('')
    try {
      await axios.delete(`/api/memories/${id}`)
      if (editingId === id) {
        setEditingId(null)
      }
      setStatusText('Memory deleted.')
      await fetchMemories()
    } catch (err) {
      console.error(err)
      setError('Failed to delete the memory.')
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
      <section className="rounded-[28px] border border-stone-200/80 bg-white/85 p-5 shadow-[0_20px_60px_rgba(59,45,18,0.08)] backdrop-blur">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">Capture</p>
        <h2 className="mt-1 text-2xl font-semibold text-stone-900">Memory Editor</h2>
        <p className="mt-2 text-sm text-stone-600">{statusText}</p>

        <form onSubmit={createMemory} className="mt-5 space-y-4">
          <div>
            <label className="mb-2 block text-sm font-medium text-stone-700">Memory Text</label>
            <textarea
              value={text}
              onChange={(event) => setText(event.target.value)}
              rows={5}
              className="w-full rounded-[22px] border border-stone-300 bg-white px-4 py-3 text-sm shadow-sm outline-none transition focus:border-amber-400 focus:ring-4 focus:ring-amber-100"
              placeholder="Example: I prefer concise and technical summaries."
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-stone-700">Category</label>
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              className="w-full rounded-2xl border border-stone-300 bg-white px-4 py-3 text-sm shadow-sm outline-none transition focus:border-amber-400 focus:ring-4 focus:ring-amber-100"
            >
              {categories.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={saving || !text.trim()}
            className="w-full rounded-full bg-amber-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-amber-500 disabled:cursor-not-allowed disabled:bg-amber-300"
          >
            {saving ? 'Saving...' : 'Save Memory'}
          </button>
        </form>

        {error && <div className="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
      </section>

      <section className="rounded-[28px] border border-stone-200/80 bg-white/85 p-5 shadow-[0_20px_60px_rgba(59,45,18,0.08)] backdrop-blur">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">Timeline</p>
            <h2 className="mt-1 text-2xl font-semibold text-stone-900">What AstraOS Remembers</h2>
          </div>
          <button
            onClick={() => void fetchMemories()}
            className="rounded-full border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 transition hover:border-amber-400 hover:bg-amber-50"
          >
            Refresh
          </button>
        </div>

        <div className="mt-5 space-y-3">
          {loading ? (
            <div className="rounded-2xl border border-dashed border-stone-300 bg-stone-50 px-4 py-6 text-sm text-stone-500">
              Loading memories...
            </div>
          ) : items.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-stone-300 bg-stone-50 px-4 py-6 text-sm text-stone-500">
              Nothing is stored yet. Add a memory here or tell the assistant to remember something in chat.
            </div>
          ) : (
            items.map((item) => {
              const editing = editingId === item.id
              return (
                <div key={item.id} className="rounded-[24px] border border-stone-200 bg-stone-50/80 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-amber-800">
                      {item.category}
                    </span>
                    <span className="text-xs text-stone-500">{formatDateTime(item.updated_at || item.created_at)}</span>
                  </div>

                  {editing ? (
                    <div className="mt-3 space-y-3">
                      <textarea
                        value={editingText}
                        onChange={(event) => setEditingText(event.target.value)}
                        rows={4}
                        className="w-full rounded-2xl border border-stone-300 bg-white px-4 py-3 text-sm shadow-sm outline-none transition focus:border-amber-400 focus:ring-4 focus:ring-amber-100"
                      />
                      <select
                        value={editingCategory}
                        onChange={(event) => setEditingCategory(event.target.value)}
                        className="w-full rounded-2xl border border-stone-300 bg-white px-4 py-3 text-sm shadow-sm outline-none transition focus:border-amber-400 focus:ring-4 focus:ring-amber-100"
                      >
                        {categories.map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                      <div className="flex gap-2">
                        <button
                          onClick={() => void updateMemory(item.id)}
                          className="rounded-full bg-stone-950 px-4 py-2 text-sm font-semibold text-white"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => setEditingId(null)}
                          className="rounded-full border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-stone-800">{item.text}</p>
                      {item.source && <p className="mt-2 text-xs text-stone-500">Source: {item.source}</p>}
                      <div className="mt-4 flex gap-2">
                        <button
                          onClick={() => startEditing(item)}
                          className="rounded-full border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700 transition hover:border-amber-400 hover:bg-amber-50"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => void deleteMemory(item.id)}
                          className="rounded-full border border-rose-200 px-4 py-2 text-sm font-semibold text-rose-700 transition hover:bg-rose-50"
                        >
                          Delete
                        </button>
                      </div>
                    </>
                  )}
                </div>
              )
            })
          )}
        </div>
      </section>
    </div>
  )
}
