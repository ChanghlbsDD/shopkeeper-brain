import { describe, expect, it } from "vitest"

import type { ImportTaskView } from "../types/imports"
import {
  fileKind,
  formatDuration,
  formatFileSize,
  pipelineFor,
  taskProgress,
  validateImportFile,
} from "./imports"

function task(overrides: Partial<ImportTaskView> = {}): ImportTaskView {
  return {
    localId: "local-1",
    file: new File(["# Manual"], "manual.md"),
    kind: "markdown",
    status: "processing",
    taskId: "task-1",
    statusUrl: "/api/imports/task-1",
    doneNodes: ["upload_file", "entry_node"],
    runningNode: "md_img_node",
    nodeDurationsMs: {},
    chunkCount: 0,
    itemName: "",
    collectionName: "",
    errorMessage: "",
    retryCount: 0,
    ...overrides,
  }
}

describe("import helpers", () => {
  it("builds different PDF and Markdown pipelines", () => {
    expect(pipelineFor("pdf")).toHaveLength(8)
    expect(pipelineFor("markdown")).toHaveLength(7)
    expect(pipelineFor("pdf").map((step) => step.id)).toContain("pdf_to_md_node")
    expect(pipelineFor("markdown").map((step) => step.id)).not.toContain("pdf_to_md_node")
  })

  it("recognizes allowed extensions without trusting MIME", () => {
    expect(fileKind(new File(["x"], "MANUAL.PDF", { type: "text/plain" }))).toBe("pdf")
    expect(fileKind(new File(["x"], "manual.markdown"))).toBe("markdown")
    expect(fileKind(new File(["x"], "manual.exe"))).toBeNull()
  })

  it("rejects empty, oversized and unsupported files", () => {
    expect(validateImportFile(new File([], "empty.md"))).toBe("文件内容为空")
    expect(validateImportFile(new File(["x"], "manual.txt"))).toContain("仅支持")
    const oversized = new File(["x"], "large.pdf")
    Object.defineProperty(oversized, "size", { value: 200 * 1024 * 1024 + 1 })
    expect(validateImportFile(oversized)).toContain("200 MB")
  })

  it("calculates branch-aware progress and caps active work at 95 percent", () => {
    expect(taskProgress(task())).toBe(35)
    expect(
      taskProgress(
        task({
          doneNodes: pipelineFor("markdown").map((step) => step.id),
          runningNode: "import_milvus_node",
        }),
      ),
    ).toBe(95)
    expect(taskProgress(task({ status: "completed" }))).toBe(100)
  })

  it("formats byte sizes and node durations", () => {
    expect(formatFileSize(512)).toBe("512 B")
    expect(formatFileSize(1536)).toBe("1.5 KB")
    expect(formatFileSize(2 * 1024 * 1024)).toBe("2.0 MB")
    expect(formatDuration(245)).toBe("245 ms")
    expect(formatDuration(2500)).toBe("2.5 秒")
    expect(formatDuration(65_000)).toBe("1 分 5 秒")
  })
})
