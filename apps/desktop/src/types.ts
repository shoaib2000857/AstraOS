export type AppView = 'chat' | 'memories' | 'documents' | 'qa'

export type ThreadMessage = {
  id: number | string
  role: string
  content: string
  timestamp?: string
}

export type Conversation = {
  id: number
  title: string | null
  created_at: string
  updated_at: string
  messages: ThreadMessage[]
}

export type MemoryItem = {
  id: number
  text: string
  category: string
  source?: string | null
  created_at: string
  updated_at: string
}

export type DocumentListItem = {
  id: number
  title: string
  file_path: string
  summary?: string | null
  checksum?: string | null
  imported_at: string
  chunk_count: number
}

export type DocumentChunk = {
  id: number
  index: number
  text: string
  vector_id?: string | null
}

export type DocumentDetail = {
  id: number
  title: string
  file_path: string
  summary?: string | null
  checksum?: string | null
  chunks: DocumentChunk[]
}

export type SearchSource = {
  id: string | number
  score: number | null
  document_id?: number | null
  title?: string | null
  text?: string | null
  payload?: {
    chunk_id?: number
    chunk_index?: number
    document_id?: number
    source?: string | null
    text?: string | null
    title?: string | null
  }
  search_mode?: 'vector' | 'lexical' | string
}

export type ExtractedTask = {
  line: number | null
  text: string
  match: string
}
