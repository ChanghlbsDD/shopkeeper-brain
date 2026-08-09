<script setup lang="ts">
import { computed } from "vue"

import { statusLabel } from "../composables/useImportTasks"
import type { ImportTaskView, PipelineStep } from "../types/imports"
import {
  formatDuration,
  formatFileSize,
  pipelineFor,
  taskProgress,
  totalDuration,
} from "../utils/imports"

const props = defineProps<{
  task: ImportTaskView
}>()

defineEmits<{
  retry: [task: ImportTaskView]
  remove: [task: ImportTaskView]
}>()

const steps = computed(() => pipelineFor(props.task.kind))
const progress = computed(() => taskProgress(props.task))
const elapsed = computed(() => totalDuration(props.task))
const canRetry = computed(() => ["failed", "connection_error"].includes(props.task.status))
const isTerminal = computed(() =>
  ["completed", "failed", "connection_error"].includes(props.task.status),
)

function stepState(step: PipelineStep): "done" | "running" | "pending" {
  if (props.task.doneNodes.includes(step.id)) return "done"
  if (props.task.runningNode === step.id) return "running"
  return "pending"
}
</script>

<template>
  <article class="task-card" :class="`status-${task.status}`">
    <header class="task-header">
      <div class="file-symbol" :class="task.kind" aria-hidden="true">
        {{ task.kind === "pdf" ? "PDF" : "MD" }}
      </div>
      <div class="task-title-group">
        <div class="task-title-line">
          <h3 :title="task.file.name">{{ task.file.name }}</h3>
          <span class="status-pill" :class="`status-${task.status}`">
            <span class="status-light" aria-hidden="true"></span>
            {{ statusLabel(task.status) }}
          </span>
        </div>
        <div class="file-meta">
          <span>{{ formatFileSize(task.file.size) }}</span>
          <span>{{ task.kind === "pdf" ? "PDF 解析路线" : "Markdown 直入路线" }}</span>
          <span v-if="task.taskId">任务 {{ task.taskId.slice(0, 8) }}</span>
        </div>
      </div>
    </header>

    <div class="progress-row">
      <div
        class="progress-track"
        role="progressbar"
        :aria-valuenow="progress"
        aria-valuemin="0"
        aria-valuemax="100"
        :aria-label="`${task.file.name} 导入进度`"
      >
        <span :style="{ width: `${progress}%` }"></span>
      </div>
      <strong>{{ progress }}%</strong>
    </div>

    <ol class="task-timeline" aria-label="导入节点">
      <li
        v-for="step in steps"
        :key="step.id"
        :class="`is-${stepState(step)}`"
      >
        <span class="timeline-node" aria-hidden="true">
          {{ stepState(step) === "done" ? "✓" : "" }}
        </span>
        <span class="timeline-copy">
          <strong>{{ step.shortLabel }}</strong>
          <small>{{ step.label }}</small>
        </span>
        <span v-if="task.nodeDurationsMs[step.id] !== undefined" class="duration-chip">
          {{ formatDuration(task.nodeDurationsMs[step.id]) }}
        </span>
      </li>
    </ol>

    <div v-if="task.status === 'completed'" class="task-result" aria-live="polite">
      <div>
        <span>识别结果</span>
        <strong>{{ task.itemName || "未返回商品名称" }}</strong>
      </div>
      <dl>
        <div>
          <dt>知识片段</dt>
          <dd>{{ task.chunkCount }}</dd>
        </div>
        <div>
          <dt>向量集合</dt>
          <dd>{{ task.collectionName || "—" }}</dd>
        </div>
        <div>
          <dt>节点耗时</dt>
          <dd>{{ formatDuration(elapsed) }}</dd>
        </div>
      </dl>
    </div>

    <div v-if="task.errorMessage" class="task-error" role="alert">
      <span aria-hidden="true">!</span>
      <p>{{ task.errorMessage }}</p>
    </div>

    <footer v-if="isTerminal" class="task-actions">
      <button v-if="canRetry" type="button" class="text-button is-accent" @click="$emit('retry', task)">
        重新导入
      </button>
      <button type="button" class="text-button" @click="$emit('remove', task)">移除记录</button>
    </footer>
  </article>
</template>
