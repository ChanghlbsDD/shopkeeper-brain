import { afterEach, describe, expect, it, vi } from "vitest"

import { getImportTask, ImportApiError, uploadImportFile } from "./imports"

afterEach(() => {
  vi.unstubAllGlobals()
})

describe("import API client", () => {
  it("uploads one file as multipart form data", async () => {
    const accepted = {
      message: "accepted",
      task_id: "task-1",
      status: "queued",
      filename: "manual.md",
      status_url: "/api/imports/task-1",
    }
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(accepted), {
        status: 202,
        headers: { "Content-Type": "application/json" },
      }),
    )
    vi.stubGlobal("fetch", fetchMock)
    const file = new File(["# Manual"], "manual.md", { type: "text/markdown" })

    const result = await uploadImportFile(file)

    expect(result).toEqual(accepted)
    expect(fetchMock).toHaveBeenCalledOnce()
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe("/api/imports")
    expect(options.method).toBe("POST")
    expect(options.body).toBeInstanceOf(FormData)
    expect((options.body as FormData).get("file")).toBe(file)
    expect(options.headers).toBeUndefined()
  })

  it("queries a task using an encoded id", async () => {
    const payload = { task_id: "task/1", status: "processing" }
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    )
    vi.stubGlobal("fetch", fetchMock)

    await getImportTask("task/1")

    expect(fetchMock).toHaveBeenCalledWith("/api/imports/task%2F1", { signal: undefined })
  })

  it("uses the backend unified error message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ error: { code: "UNSUPPORTED_IMPORT_FILE", message: "不支持" } }),
          { status: 415, headers: { "Content-Type": "application/json" } },
        ),
      ),
    )

    const promise = uploadImportFile(new File(["x"], "manual.txt"))

    await expect(promise).rejects.toEqual(
      expect.objectContaining<Partial<ImportApiError>>({
        message: "不支持",
        code: "UNSUPPORTED_IMPORT_FILE",
        status: 415,
      }),
    )
  })

  it("reports invalid JSON without exposing response content", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("gateway", { status: 502 })))

    await expect(getImportTask("task-1")).rejects.toMatchObject({
      code: "INVALID_API_RESPONSE",
      status: 502,
    })
  })
})
