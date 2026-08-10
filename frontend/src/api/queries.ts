import type {
  QueryApiErrorPayload,
  QueryHistoryDeleteResponse,
  QueryHistoryResponse,
  QuerySearchRequest,
  QuerySearchResponse,
  QueryStreamEvent,
} from "../types/queries"

const apiBase = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "")

export class QueryApiError extends Error {
  readonly code: string
  readonly status: number

  constructor(message: string, code = "QUERY_API_ERROR", status = 0) {
    super(message)
    this.name = "QueryApiError"
    this.code = code
    this.status = status
  }
}

export async function searchQuery(
  request: QuerySearchRequest,
  signal?: AbortSignal,
): Promise<QuerySearchResponse> {
  const response = await fetch(`${apiBase}/api/queries/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal,
  })
  return parseJsonResponse<QuerySearchResponse>(response)
}

export async function streamQuery(
  request: QuerySearchRequest,
  onEvent: (event: QueryStreamEvent) => void,
  signal?: AbortSignal,
): Promise<QuerySearchResponse> {
  const response = await fetch(`${apiBase}/api/queries/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(request),
    signal,
  })
  if (!response.ok) {
    return parseJsonResponse<QuerySearchResponse>(response)
  }
  if (!response.body) {
    throw new QueryApiError("浏览器无法读取流式回答", "STREAM_NOT_SUPPORTED")
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  let finalResponse: QuerySearchResponse | null = null

  while (true) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value, { stream: !done }).replace(/\r\n/g, "\n")
    const frames = buffer.split("\n\n")
    buffer = frames.pop() || ""
    for (const frame of frames) {
      const parsed = parseSseFrame(frame)
      if (!parsed) continue
      onEvent(parsed)
      if (parsed.event === "error") {
        throw new QueryApiError(
          parsed.data.message || "知识查询失败",
          parsed.data.code || "QUERY_STREAM_FAILED",
          parsed.data.status_code || 0,
        )
      }
      if (parsed.event === "final") finalResponse = parsed.data
    }
    if (done) break
  }

  if (buffer.trim()) {
    const parsed = parseSseFrame(buffer)
    if (parsed) {
      onEvent(parsed)
      if (parsed.event === "error") {
        throw new QueryApiError(
          parsed.data.message || "知识查询失败",
          parsed.data.code || "QUERY_STREAM_FAILED",
          parsed.data.status_code || 0,
        )
      }
      if (parsed.event === "final") finalResponse = parsed.data
    }
  }
  if (!finalResponse) {
    throw new QueryApiError("流式回答提前结束", "INCOMPLETE_QUERY_STREAM")
  }
  return finalResponse
}

export async function getQueryHistory(
  sessionId: string,
  signal?: AbortSignal,
): Promise<QueryHistoryResponse> {
  const response = await fetch(
    `${apiBase}/api/queries/history/${encodeURIComponent(sessionId)}`,
    { signal },
  )
  return parseJsonResponse<QueryHistoryResponse>(response)
}

export async function clearQueryHistory(
  sessionId: string,
  signal?: AbortSignal,
): Promise<QueryHistoryDeleteResponse> {
  const response = await fetch(
    `${apiBase}/api/queries/history/${encodeURIComponent(sessionId)}`,
    { method: "DELETE", signal },
  )
  return parseJsonResponse<QueryHistoryDeleteResponse>(response)
}

function parseSseFrame(frame: string): QueryStreamEvent | null {
  if (!frame.trim() || frame.trimStart().startsWith(":")) return null
  let eventName = "message"
  const dataLines: string[] = []
  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) eventName = line.slice(6).trim()
    if (line.startsWith("data:")) dataLines.push(line.slice(5).trimStart())
  }
  if (!dataLines.length || !["progress", "delta", "final", "error"].includes(eventName)) {
    return null
  }
  try {
    return {
      event: eventName,
      data: JSON.parse(dataLines.join("\n")) as unknown,
    } as QueryStreamEvent
  } catch {
    throw new QueryApiError("服务器返回了损坏的流式数据", "INVALID_STREAM_EVENT")
  }
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  let payload: unknown
  try {
    payload = await response.json()
  } catch {
    throw new QueryApiError(
      response.ok ? "服务器返回了无法识别的数据" : "服务器暂时无法处理请求",
      "INVALID_API_RESPONSE",
      response.status,
    )
  }
  if (!response.ok) {
    const errorPayload = payload as QueryApiErrorPayload
    throw new QueryApiError(
      errorPayload.error?.message || `请求失败（HTTP ${response.status}）`,
      errorPayload.error?.code || "QUERY_REQUEST_FAILED",
      response.status,
    )
  }
  return payload as T
}
