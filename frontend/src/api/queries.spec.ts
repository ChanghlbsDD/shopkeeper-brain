import { afterEach, describe, expect, it, vi } from "vitest"

import { clearQueryHistory, getQueryHistory, streamQuery } from "./queries"

afterEach(() => {
  vi.unstubAllGlobals()
})

function streamResponse(chunks: string[]): Response {
  const encoder = new TextEncoder()
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk))
      controller.close()
    },
  })
  return new Response(body, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  })
}

describe("query API client", () => {
  it("parses SSE events even when JSON is split across network chunks", async () => {
    const final = {
      session_id: "session-1",
      status: "retrieved",
      history_persisted: true,
      original_query: "怎么用？",
      rewritten_query: "RS-12 怎么用？",
      item_names: ["RS-12"],
      item_name_options: [],
      clarification: "",
      answer: "先选择档位。[1]",
      references: [],
      images: [],
      completed_nodes: [],
      node_durations_ms: {},
    }
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        streamResponse([
          'event: progress\ndata: {"node":"rerank',
          '_node"}\n\nevent: delta\ndata: {"text":"先选择"}\n\n',
          `event: final\ndata: ${JSON.stringify(final)}\n\n`,
        ]),
      ),
    )
    const events: string[] = []

    const result = await streamQuery({ query: "怎么用？" }, (event) => {
      events.push(event.event)
    })

    expect(events).toEqual(["progress", "delta", "final"])
    expect(result.answer).toBe("先选择档位。[1]")
  })

  it("turns an SSE error into a typed query error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        streamResponse([
          'event: error\ndata: {"code":"QUERY_AI_NOT_CONFIGURED","message":"未配置 Token","status_code":503}\n\n',
        ]),
      ),
    )

    await expect(streamQuery({ query: "问题" }, () => undefined)).rejects.toMatchObject({
      code: "QUERY_AI_NOT_CONFIGURED",
      message: "未配置 Token",
      status: 503,
    })
  })

  it("loads and clears only the encoded session", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ session_id: "a/b", items: [] }), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ session_id: "a/b", deleted_count: 2 }), {
          status: 200,
        }),
      )
    vi.stubGlobal("fetch", fetchMock)

    await getQueryHistory("a/b")
    await clearQueryHistory("a/b")

    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/queries/history/a%2Fb", {
      signal: undefined,
    })
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/queries/history/a%2Fb", {
      method: "DELETE",
      signal: undefined,
    })
  })
})
