export type QueryStatus = "retrieved" | "needs_clarification" | "unrecognized"
export type QuerySource = "local" | "web"

export interface QueryReference {
  reference_id: string
  source: QuerySource
  title: string
  chunk_id: number | null
  url: string
  rerank_score: number | null
}

export interface QuerySearchRequest {
  query: string
  session_id?: string
  limit?: number
}

export interface QuerySearchResponse {
  session_id: string
  status: QueryStatus
  history_persisted: boolean
  original_query: string
  rewritten_query: string
  item_names: string[]
  item_name_options: string[]
  clarification: string
  answer: string
  references: QueryReference[]
  images: string[]
  completed_nodes: string[]
  node_durations_ms: Record<string, number>
}

export interface QueryHistoryMessage {
  message_id: string
  role: "user" | "assistant"
  content: string
  rewritten_query: string
  item_names: string[]
  created_at: string
}

export interface QueryHistoryResponse {
  session_id: string
  items: QueryHistoryMessage[]
}

export interface QueryHistoryDeleteResponse {
  session_id: string
  deleted_count: number
}

export type QueryStreamEvent =
  | { event: "progress"; data: { node?: string; duration_ms?: number } }
  | { event: "delta"; data: { text?: string } }
  | { event: "final"; data: QuerySearchResponse }
  | {
      event: "error"
      data: { code?: string; message?: string; status_code?: number }
    }

export interface QueryApiErrorPayload {
  error?: {
    code?: string
    message?: string
  }
}
