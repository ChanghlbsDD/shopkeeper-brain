import type {
  ApiErrorPayload,
  ImportAcceptedResponse,
  ImportTaskResponse,
} from "../types/imports"

const apiBase = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "")

export class ImportApiError extends Error {
  readonly code: string
  readonly status: number

  constructor(message: string, code = "IMPORT_API_ERROR", status = 0) {
    super(message)
    this.name = "ImportApiError"
    this.code = code
    this.status = status
  }
}

export async function uploadImportFile(
  file: File,
  signal?: AbortSignal,
): Promise<ImportAcceptedResponse> {
  const formData = new FormData()
  formData.append("file", file)
  const response = await fetch(`${apiBase}/api/imports`, {
    method: "POST",
    body: formData,
    signal,
  })
  return parseResponse<ImportAcceptedResponse>(response)
}

export async function getImportTask(
  taskId: string,
  signal?: AbortSignal,
): Promise<ImportTaskResponse> {
  const response = await fetch(`${apiBase}/api/imports/${encodeURIComponent(taskId)}`, {
    signal,
  })
  return parseResponse<ImportTaskResponse>(response)
}

async function parseResponse<T>(response: Response): Promise<T> {
  let payload: unknown
  try {
    payload = await response.json()
  } catch {
    throw new ImportApiError(
      response.ok ? "服务器返回了无法识别的数据" : "服务器暂时无法处理请求",
      "INVALID_API_RESPONSE",
      response.status,
    )
  }

  if (!response.ok) {
    const errorPayload = payload as ApiErrorPayload
    throw new ImportApiError(
      errorPayload.error?.message || `请求失败（HTTP ${response.status}）`,
      errorPayload.error?.code || "IMPORT_REQUEST_FAILED",
      response.status,
    )
  }
  return payload as T
}
