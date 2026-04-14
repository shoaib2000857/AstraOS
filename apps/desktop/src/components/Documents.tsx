import { FormEvent, useEffect, useState } from 'react'
import axios from 'axios'

import type { DocumentDetail, DocumentListItem, ExtractedTask } from '../types'
import { formatDateTime, truncateText } from '../utils'

type UploadResponse = {
  status: string
  document_id: number
  summary?: string | null
  indexing?: {
    status: string
    chunks?: number
    search_mode?: string
  }
}

export default function Documents() {
  const [docs, setDocs] = useState<DocumentListItem[]>([])
  const [selected, setSelected] = useState<DocumentDetail | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [taskLoading, setTaskLoading] = useState(false)
  const [tasks, setTasks] = useState<ExtractedTask[]>([])
  const [error, setError] = useState('')
  const [statusText, setStatusText] = useState('Upload text or PDF files to chunk and index them for search and grounded QA.')

  useEffect(() => {
    void fetchDocs()
  }, [])

  async function fetchDocs(preferredId?: number) {
    setLoading(true)
    try {
      const response = await axios.get<DocumentListItem[]>('/api/documents')
      setDocs(response.data)
      const targetId = preferredId ?? selected?.id ?? response.data[0]?.id
      if (targetId) {
        await viewDoc(targetId)
      } else {
        setSelected(null)
        setTasks([])
      }
    } catch (err) {
      console.error(err)
      setError('Failed to load documents.')
    } finally {
      setLoading(false)
    }
  }

  async function viewDoc(id: number) {
    try {
      const response = await axios.get<DocumentDetail>(`/api/documents/${id}`)
      setSelected(response.data)
      setTasks([])
    } catch (err) {
      console.error(err)
      setError('Failed to load the selected document.')
    }
  }

  async function handleUpload(event: FormEvent) {
    event.preventDefault()
    if (!selectedFile) return

    const formData = new FormData()
    formData.append('file', selectedFile)

    setUploading(true)
    setError('')
    try {
      const response = await axios.post<UploadResponse>('/api/ingest/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setSelectedFile(null)
      setStatusText(
        `Uploaded document ${response.data.document_id}. Indexing status: ${response.data.indexing?.status || 'unknown'}.`,
      )
      await fetchDocs(response.data.document_id)
    } catch (err) {
      console.error(err)
      setError('Upload failed. Check that the backend is running and the file type is supported.')
    } finally {
      setUploading(false)
    }
  }

  async function deleteDocument(id: number) {
    setError('')
    try {
      await axios.delete(`/api/documents/${id}`)
      setStatusText('Document removed.')
      await fetchDocs()
    } catch (err) {
      console.error(err)
      setError('Failed to delete the document.')
    }
  }

  async function extractTasks() {
    if (!selected) return
    setTaskLoading(true)
    setError('')
    try {
      const response = await axios.post<{ tasks: ExtractedTask[] }>(`/api/tasks/from_document/${selected.id}`)
      setTasks(response.data.tasks || [])
      setStatusText(
        response.data.tasks?.length
          ? `Found ${response.data.tasks.length} potential action item${response.data.tasks.length === 1 ? '' : 's'} in this document.`
          : 'No task-like lines were found in this document.',
      )
    } catch (err) {
      console.error(err)
      setError('Task extraction failed for this document.')
    } finally {
      setTaskLoading(false)
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[340px_minmax(0,1fr)]">
      <section className="space-y-6">
        <div className="rounded-[28px] border border-stone-200/80 bg-white/85 p-5 shadow-[0_20px_60px_rgba(59,45,18,0.08)] backdrop-blur">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">Ingestion</p>
          <h2 className="mt-1 text-2xl font-semibold text-stone-900">Upload Documents</h2>
          <p className="mt-2 text-sm text-stone-600">{statusText}</p>

          <form onSubmit={handleUpload} className="mt-5 space-y-4">
            <label className="block rounded-[24px] border border-dashed border-stone-300 bg-stone-50/80 px-4 py-6 text-sm text-stone-600">
              <span className="font-medium text-stone-800">Select a file</span>
              <span className="mt-1 block text-xs text-stone-500">TXT, Markdown, code files, JSON, CSV, and PDF are supported.</span>
              <input
                type="file"
                className="mt-4 block w-full text-sm text-stone-700"
                onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
              />
            </label>
            <button
              type="submit"
              disabled={!selectedFile || uploading}
              className="w-full rounded-full bg-amber-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-amber-500 disabled:cursor-not-allowed disabled:bg-amber-300"
            >
              {uploading ? 'Uploading...' : 'Upload and Index'}
            </button>
          </form>
        </div>

        <div className="rounded-[28px] border border-stone-200/80 bg-white/85 p-5 shadow-[0_20px_60px_rgba(59,45,18,0.08)] backdrop-blur">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">Library</p>
              <h2 className="mt-1 text-2xl font-semibold text-stone-900">Indexed Files</h2>
            </div>
            <button
              onClick={() => void fetchDocs()}
              className="rounded-full border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 transition hover:border-amber-400 hover:bg-amber-50"
            >
              Refresh
            </button>
          </div>

          <div className="mt-5 space-y-3">
            {loading ? (
              <div className="rounded-2xl border border-dashed border-stone-300 bg-stone-50 px-4 py-6 text-sm text-stone-500">
                Loading documents...
              </div>
            ) : docs.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-stone-300 bg-stone-50 px-4 py-6 text-sm text-stone-500">
                No files uploaded yet.
              </div>
            ) : (
              docs.map((doc) => (
                <div
                  key={doc.id}
                  className={`rounded-[24px] border px-4 py-4 transition ${
                    selected?.id === doc.id ? 'border-stone-900 bg-stone-950 text-stone-50' : 'border-stone-200 bg-stone-50/80 text-stone-800'
                  }`}
                >
                  <button className="w-full text-left" onClick={() => void viewDoc(doc.id)}>
                    <div className="text-sm font-semibold">{truncateText(doc.title, 48)}</div>
                    <div className={`mt-1 text-xs ${selected?.id === doc.id ? 'text-stone-300' : 'text-stone-500'}`}>
                      {formatDateTime(doc.imported_at)} - {doc.chunk_count} chunk{doc.chunk_count === 1 ? '' : 's'}
                    </div>
                    {doc.summary && (
                      <div className={`mt-2 text-xs leading-5 ${selected?.id === doc.id ? 'text-stone-300' : 'text-stone-500'}`}>
                        {truncateText(doc.summary, 120)}
                      </div>
                    )}
                  </button>
                  <button
                    onClick={() => void deleteDocument(doc.id)}
                    className={`mt-3 text-xs font-semibold ${selected?.id === doc.id ? 'text-amber-300' : 'text-amber-700'}`}
                  >
                    Delete
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </section>

      <section className="rounded-[28px] border border-stone-200/80 bg-white/85 p-5 shadow-[0_20px_60px_rgba(59,45,18,0.08)] backdrop-blur">
        <div className="flex flex-col gap-3 border-b border-stone-200 pb-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">Inspector</p>
            <h2 className="mt-1 text-2xl font-semibold text-stone-900">Document Detail</h2>
          </div>
          <button
            onClick={() => void extractTasks()}
            disabled={!selected || taskLoading}
            className="rounded-full border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 transition hover:border-amber-400 hover:bg-amber-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {taskLoading ? 'Extracting...' : 'Extract Action Items'}
          </button>
        </div>

        {selected ? (
          <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
            <div className="min-w-0">
              <div className="rounded-[24px] bg-stone-50/80 p-4 ring-1 ring-stone-200">
                <h3 className="text-lg font-semibold text-stone-900">{selected.title}</h3>
                <p className="mt-2 text-sm text-stone-600">{selected.summary || 'No summary available yet.'}</p>
                <p className="mt-3 break-all text-xs text-stone-500">{selected.file_path}</p>
              </div>

              <div className="mt-4 max-h-[520px] space-y-3 overflow-y-auto rounded-[24px] border border-stone-200 bg-stone-50/80 p-4">
                {selected.chunks.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-stone-300 bg-white px-4 py-5 text-sm text-stone-500">
                    No text chunks were created for this file.
                  </div>
                ) : (
                  selected.chunks.map((chunk) => (
                    <div key={chunk.id} className="rounded-2xl bg-white px-4 py-4 shadow-sm ring-1 ring-stone-200">
                      <div className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-amber-700">Chunk {chunk.index + 1}</div>
                      <div className="whitespace-pre-wrap text-sm leading-6 text-stone-800">{chunk.text}</div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <aside className="rounded-[24px] border border-stone-200 bg-stone-50/80 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">Tasks</p>
              <h3 className="mt-1 text-lg font-semibold text-stone-900">Extracted Action Items</h3>
              <div className="mt-4 space-y-3">
                {tasks.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-stone-300 bg-white px-4 py-5 text-sm text-stone-500">
                    Run task extraction to scan the current document for TODOs, deadlines, and checklist entries.
                  </div>
                ) : (
                  tasks.map((task, index) => (
                    <div key={`${task.text}-${index}`} className="rounded-2xl bg-white px-4 py-3 shadow-sm ring-1 ring-stone-200">
                      <div className="text-sm font-medium text-stone-900">{task.text}</div>
                      <div className="mt-1 text-xs text-stone-500">
                        {task.line ? `Line ${task.line}` : 'Checklist item'}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </aside>
          </div>
        ) : (
          <div className="mt-5 rounded-2xl border border-dashed border-stone-300 bg-stone-50 px-4 py-6 text-sm text-stone-500">
            Select a document to inspect its summary and chunked text.
          </div>
        )}

        {error && <div className="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
      </section>
    </div>
  )
}
