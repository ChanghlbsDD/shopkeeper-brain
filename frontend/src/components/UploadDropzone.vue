<script setup lang="ts">
import { ref } from "vue"

defineProps<{
  activeCount: number
}>()

const emit = defineEmits<{
  selected: [files: File[]]
}>()

const input = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)

function chooseFiles(): void {
  input.value?.click()
}

function onInput(event: Event): void {
  const element = event.target as HTMLInputElement
  submitFiles(element.files)
  element.value = ""
}

function onDrop(event: DragEvent): void {
  isDragging.value = false
  submitFiles(event.dataTransfer?.files || null)
}

function submitFiles(fileList: FileList | null): void {
  if (!fileList?.length) return
  emit("selected", Array.from(fileList))
}
</script>

<template>
  <section class="upload-panel" aria-labelledby="upload-title">
    <div class="section-kicker">01 / 添加资料</div>
    <div class="upload-copy">
      <div>
        <h2 id="upload-title">导入一份产品资料</h2>
        <p>原始文档将私有归档，解析后的知识片段进入混合向量库。</p>
      </div>
      <span v-if="activeCount" class="active-count">{{ activeCount }} 项处理中</span>
    </div>

    <div
      class="dropzone"
      :class="{ 'is-dragging': isDragging }"
      @dragenter.prevent="isDragging = true"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="onDrop"
    >
      <input
        ref="input"
        class="visually-hidden"
        type="file"
        accept=".pdf,.md,.markdown"
        multiple
        aria-label="选择 PDF 或 Markdown 文档"
        @change="onInput"
      />
      <div class="dropzone-mark" aria-hidden="true">
        <span class="paper-corner"></span>
        <span class="upload-arrow">↑</span>
      </div>
      <div class="dropzone-content">
        <strong>{{ isDragging ? "松开即可开始导入" : "拖放文档到这里" }}</strong>
        <span>支持 PDF、MD、Markdown，单个文件不超过 200 MB</span>
      </div>
      <button class="primary-button" type="button" @click="chooseFiles">选择文件</button>
    </div>

    <div class="upload-notes" aria-label="上传说明">
      <span><i class="note-dot is-private"></i> 原件私有保存</span>
      <span><i class="note-dot is-cloud"></i> AI 推理走云端 API</span>
      <span><i class="note-dot is-vector"></i> 稠密 + 稀疏检索</span>
    </div>
  </section>
</template>
