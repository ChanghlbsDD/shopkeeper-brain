import type {
  ImportFileKind,
  ImportTaskView,
  PipelineStep,
} from "../types/imports"

export const MAX_IMPORT_BYTES = 200 * 1024 * 1024

const COMMON_STEPS: PipelineStep[] = [
  { id: "upload_file", label: "文件上传与私有归档", shortLabel: "上传文件" },
  { id: "entry_node", label: "检查文件并选择处理分支", shortLabel: "检查文件" },
]

const TAIL_STEPS: PipelineStep[] = [
  { id: "md_img_node", label: "上传正文图片并替换链接", shortLabel: "处理图片" },
  { id: "document_split_node", label: "按标题与语义切分文档", shortLabel: "切分文档" },
  {
    id: "item_name_recognition_node",
    label: "识别核心商品或设备名称",
    shortLabel: "识别商品",
  },
  { id: "bge_embedding_node", label: "生成稠密与稀疏向量", shortLabel: "生成向量" },
  { id: "import_milvus_node", label: "写入 Milvus 混合向量库", shortLabel: "写入知识库" },
]

export function pipelineFor(kind: ImportFileKind): PipelineStep[] {
  const branch =
    kind === "pdf"
      ? [{ id: "pdf_to_md_node", label: "使用 MinerU 解析 PDF", shortLabel: "解析 PDF" }]
      : []
  return [...COMMON_STEPS, ...branch, ...TAIL_STEPS]
}

export function fileKind(file: File): ImportFileKind | null {
  const lowerName = file.name.toLowerCase()
  if (lowerName.endsWith(".pdf")) return "pdf"
  if (lowerName.endsWith(".md") || lowerName.endsWith(".markdown")) return "markdown"
  return null
}

export function validateImportFile(file: File): string | null {
  if (!fileKind(file)) return "仅支持 PDF、MD 或 Markdown 文件"
  if (file.size === 0) return "文件内容为空"
  if (file.size > MAX_IMPORT_BYTES) return "单个文件不能超过 200 MB"
  return null
}

export function taskProgress(task: ImportTaskView): number {
  if (task.status === "completed") return 100
  if (task.status === "uploading") return 4
  const total = pipelineFor(task.kind).length
  const knownDone = task.doneNodes.filter((node) =>
    pipelineFor(task.kind).some((step) => step.id === node),
  ).length
  const runningCredit = task.runningNode ? 0.45 : 0
  return Math.min(95, Math.round(((knownDone + runningCredit) / total) * 100))
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function formatDuration(milliseconds: number): string {
  if (milliseconds < 1000) return `${Math.round(milliseconds)} ms`
  const seconds = milliseconds / 1000
  if (seconds < 60) return `${seconds.toFixed(seconds < 10 ? 1 : 0)} 秒`
  const minutes = Math.floor(seconds / 60)
  return `${minutes} 分 ${Math.round(seconds % 60)} 秒`
}

export function totalDuration(task: ImportTaskView): number {
  return Object.values(task.nodeDurationsMs).reduce((total, value) => total + value, 0)
}
