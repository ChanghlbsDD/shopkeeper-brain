import { flushPromises, mount } from "@vue/test-utils"
import { defineComponent, h } from "vue"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { useImportTasks } from "./useImportTasks"

const apiMocks = vi.hoisted(() => ({
  upload: vi.fn(),
  getTask: vi.fn(),
}))

vi.mock("../api/imports", () => {
  class ImportApiError extends Error {}
  return {
    ImportApiError,
    uploadImportFile: apiMocks.upload,
    getImportTask: apiMocks.getTask,
  }
})

function mountComposable() {
  let state: ReturnType<typeof useImportTasks> | undefined
  const wrapper = mount(
    defineComponent({
      setup() {
        state = useImportTasks()
        return () => h("div")
      },
    }),
  )
  if (!state) throw new Error("composable was not initialized")
  return { wrapper, state }
}

beforeEach(() => {
  apiMocks.upload.mockReset()
  apiMocks.getTask.mockReset()
})

afterEach(() => {
  vi.useRealTimers()
})

describe("useImportTasks", () => {
  it("uploads, polls and stores only the result summary", async () => {
    apiMocks.upload.mockResolvedValue({
      task_id: "task-1",
      status: "queued",
      status_url: "/api/imports/task-1",
      filename: "manual.md",
      message: "accepted",
    })
    apiMocks.getTask.mockResolvedValue({
      task_id: "task-1",
      filename: "manual.md",
      status: "completed",
      done_nodes: ["upload_file", "entry_node", "import_milvus_node"],
      running_node: null,
      node_durations_ms: { entry_node: 2.5 },
      chunk_count: 6,
      item_name: "RS-12 数字万用表",
      milvus_collection_name: "knowledge_chunks",
      error: null,
      created_at: "2026-08-09T00:00:00Z",
      updated_at: "2026-08-09T00:00:01Z",
    })
    const { wrapper, state } = mountComposable()

    expect(state.addFiles([new File(["# Manual"], "manual.md")])).toEqual([])
    await flushPromises()

    expect(apiMocks.upload).toHaveBeenCalledOnce()
    expect(apiMocks.getTask).toHaveBeenCalledWith("task-1", expect.any(AbortSignal))
    expect(state.tasks.value[0]).toMatchObject({
      status: "completed",
      chunkCount: 6,
      itemName: "RS-12 数字万用表",
      collectionName: "knowledge_chunks",
    })
    expect(state.completedCount.value).toBe(1)
    wrapper.unmount()
  })

  it("stops after five consecutive status connection failures", async () => {
    vi.useFakeTimers()
    apiMocks.upload.mockResolvedValue({
      task_id: "task-2",
      status: "queued",
      status_url: "/api/imports/task-2",
      filename: "manual.md",
      message: "accepted",
    })
    apiMocks.getTask.mockRejectedValue(new TypeError("network unavailable"))
    const { wrapper, state } = mountComposable()

    state.addFiles([new File(["# Manual"], "manual.md")])
    await flushPromises()
    for (let index = 0; index < 4; index += 1) {
      await vi.advanceTimersByTimeAsync(1500)
      await flushPromises()
    }

    expect(apiMocks.getTask).toHaveBeenCalledTimes(5)
    expect(state.tasks.value[0].status).toBe("connection_error")
    expect(state.tasks.value[0].errorMessage).toContain("连续 5 次")
    wrapper.unmount()
  })
})
