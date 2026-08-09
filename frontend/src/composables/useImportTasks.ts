import { computed, onBeforeUnmount, ref } from "vue"

import { getImportTask, ImportApiError, uploadImportFile } from "../api/imports"
import type {
  ImportTaskResponse,
  ImportTaskView,
  ImportViewStatus,
} from "../types/imports"
import { fileKind, validateImportFile } from "../utils/imports"

const POLL_INTERVAL_MS = 1500
const MAX_POLL_FAILURES = 5

export function useImportTasks() {
  const tasks = ref<ImportTaskView[]>([])
  const controllers = new Map<string, AbortController>()

  const activeCount = computed(
    () =>
      tasks.value.filter((task) =>
        ["uploading", "queued", "processing", "connection_error"].includes(task.status),
      ).length,
  )
  const completedCount = computed(
    () => tasks.value.filter((task) => task.status === "completed").length,
  )

  function addFiles(files: File[]): string[] {
    const errors: string[] = []
    for (const file of files) {
      const validationError = validateImportFile(file)
      if (validationError) {
        errors.push(`${file.name || "未命名文件"}：${validationError}`)
        continue
      }
      void createTask(file)
    }
    return errors
  }

  async function createTask(file: File): Promise<void> {
    const kind = fileKind(file)
    if (!kind) return

    const localId = createLocalId()
    const task: ImportTaskView = {
      localId,
      file,
      kind,
      status: "uploading",
      taskId: "",
      statusUrl: "",
      doneNodes: [],
      runningNode: null,
      nodeDurationsMs: {},
      chunkCount: 0,
      itemName: "",
      collectionName: "",
      errorMessage: "",
      retryCount: 0,
    }
    tasks.value.unshift(task)

    const controller = new AbortController()
    controllers.set(localId, controller)
    try {
      const accepted = await uploadImportFile(file, controller.signal)
      task.taskId = accepted.task_id
      task.statusUrl = accepted.status_url
      task.status = accepted.status
      task.doneNodes = ["upload_file"]
      await pollTask(task, controller.signal)
    } catch (error) {
      if (isAbortError(error)) return
      task.status = "failed"
      task.errorMessage = readableError(error, "文件上传失败，请确认后端服务已启动")
    } finally {
      controllers.delete(localId)
    }
  }

  async function pollTask(task: ImportTaskView, signal: AbortSignal): Promise<void> {
    while (!signal.aborted) {
      try {
        const result = await getImportTask(task.taskId, signal)
        applyTaskResult(task, result)
        task.retryCount = 0
        if (result.status === "completed" || result.status === "failed") return
      } catch (error) {
        if (isAbortError(error)) return
        task.retryCount += 1
        if (task.retryCount >= MAX_POLL_FAILURES) {
          task.status = "connection_error"
          task.errorMessage = "连续 5 次无法查询任务状态，请确认后端服务后重新导入"
          return
        }
        task.status = "connection_error"
        task.errorMessage = `状态连接暂时中断，正在重试（${task.retryCount}/${MAX_POLL_FAILURES}）`
      }
      await delay(POLL_INTERVAL_MS, signal)
    }
  }

  function applyTaskResult(task: ImportTaskView, result: ImportTaskResponse): void {
    task.status = result.status
    task.doneNodes = [...result.done_nodes]
    task.runningNode = result.running_node
    task.nodeDurationsMs = { ...result.node_durations_ms }
    task.chunkCount = result.chunk_count
    task.itemName = result.item_name
    task.collectionName = result.milvus_collection_name
    task.errorMessage = result.error?.message || ""
  }

  function retryTask(task: ImportTaskView): void {
    void createTask(task.file)
  }

  function removeTask(task: ImportTaskView): void {
    controllers.get(task.localId)?.abort()
    controllers.delete(task.localId)
    tasks.value = tasks.value.filter((candidate) => candidate.localId !== task.localId)
  }

  function clearFinished(): void {
    tasks.value = tasks.value.filter((task) =>
      ["uploading", "queued", "processing"].includes(task.status),
    )
  }

  function stopAll(): void {
    controllers.forEach((controller) => controller.abort())
    controllers.clear()
  }

  onBeforeUnmount(stopAll)

  return {
    tasks,
    activeCount,
    completedCount,
    addFiles,
    retryTask,
    removeTask,
    clearFinished,
    stopAll,
  }
}

function createLocalId(): string {
  return globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`
}

function readableError(error: unknown, fallback: string): string {
  if (error instanceof ImportApiError) return error.message
  if (error instanceof Error && error.message) return error.message
  return fallback
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError"
}

function delay(milliseconds: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    const timer = window.setTimeout(resolve, milliseconds)
    signal.addEventListener(
      "abort",
      () => {
        window.clearTimeout(timer)
        resolve()
      },
      { once: true },
    )
  })
}

export function statusLabel(status: ImportViewStatus): string {
  return {
    uploading: "正在上传",
    queued: "等待处理",
    processing: "正在处理",
    completed: "导入完成",
    failed: "导入失败",
    connection_error: "连接中断",
  }[status]
}
