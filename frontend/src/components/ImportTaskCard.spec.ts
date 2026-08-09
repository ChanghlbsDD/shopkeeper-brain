import { mount } from "@vue/test-utils"
import { describe, expect, it } from "vitest"

import type { ImportTaskView } from "../types/imports"
import ImportTaskCard from "./ImportTaskCard.vue"

function completedTask(): ImportTaskView {
  return {
    localId: "local-1",
    file: new File(["# Manual"], "RS-12 产品手册.md"),
    kind: "markdown",
    status: "completed",
    taskId: "1234567890",
    statusUrl: "/api/imports/1234567890",
    doneNodes: [
      "upload_file",
      "entry_node",
      "md_img_node",
      "document_split_node",
      "item_name_recognition_node",
      "bge_embedding_node",
      "import_milvus_node",
    ],
    runningNode: null,
    nodeDurationsMs: { entry_node: 12.5, import_milvus_node: 250 },
    chunkCount: 18,
    itemName: "RS-12 数字万用表",
    collectionName: "knowledge_chunks",
    errorMessage: "",
    retryCount: 0,
  }
}

describe("ImportTaskCard", () => {
  it("renders the completed result without vectors or paths", () => {
    const wrapper = mount(ImportTaskCard, { props: { task: completedTask() } })

    expect(wrapper.text()).toContain("导入完成")
    expect(wrapper.text()).toContain("RS-12 数字万用表")
    expect(wrapper.text()).toContain("18")
    expect(wrapper.text()).toContain("knowledge_chunks")
    expect(wrapper.find('[role="progressbar"]').attributes("aria-valuenow")).toBe("100")
    expect(wrapper.text()).not.toContain("dense_vector")
  })

  it("shows safe failures and emits retry", async () => {
    const task = {
      ...completedTask(),
      status: "failed" as const,
      errorMessage: "文档没有有效内容",
    }
    const wrapper = mount(ImportTaskCard, { props: { task } })

    expect(wrapper.get('[role="alert"]').text()).toContain("文档没有有效内容")
    await wrapper.get("button.is-accent").trigger("click")
    expect(wrapper.emitted("retry")?.[0]).toEqual([task])
  })
})
