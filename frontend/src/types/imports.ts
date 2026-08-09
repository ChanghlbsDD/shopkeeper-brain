export type BackendImportStatus = "queued" | "processing" | "completed" | "failed"
export type ImportViewStatus = "uploading" | BackendImportStatus | "connection_error"
export type ImportFileKind = "pdf" | "markdown"

export interface ImportAcceptedResponse {
  message: string
  task_id: string
  status: BackendImportStatus
  filename: string
  status_url: string
}

export interface ImportTaskError {
  node: string | null
  message: string
}

export interface ImportTaskResponse {
  task_id: string
  filename: string
  status: BackendImportStatus
  done_nodes: string[]
  running_node: string | null
  node_durations_ms: Record<string, number>
  chunk_count: number
  item_name: string
  milvus_collection_name: string
  error: ImportTaskError | null
  created_at: string
  updated_at: string
}

export interface ImportTaskView {
  localId: string
  file: File
  kind: ImportFileKind
  status: ImportViewStatus
  taskId: string
  statusUrl: string
  doneNodes: string[]
  runningNode: string | null
  nodeDurationsMs: Record<string, number>
  chunkCount: number
  itemName: string
  collectionName: string
  errorMessage: string
  retryCount: number
}

export interface PipelineStep {
  id: string
  label: string
  shortLabel: string
}

export interface ApiErrorPayload {
  error?: {
    code?: string
    message?: string
  }
}
