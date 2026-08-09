<script setup lang="ts">
import { computed, ref } from "vue"

import ImportTaskCard from "./components/ImportTaskCard.vue"
import PipelineOverview from "./components/PipelineOverview.vue"
import UploadDropzone from "./components/UploadDropzone.vue"
import { useImportTasks } from "./composables/useImportTasks"

const {
  tasks,
  activeCount,
  completedCount,
  addFiles,
  retryTask,
  removeTask,
  clearFinished,
} = useImportTasks()

const notices = ref<string[]>([])
const hasFinished = computed(() =>
  tasks.value.some((task) => ["completed", "failed", "connection_error"].includes(task.status)),
)

function handleFiles(files: File[]): void {
  notices.value = addFiles(files)
}
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <a class="brand" href="#main" aria-label="掌柜智库首页">
        <span class="brand-mark">掌</span>
        <span>
          <strong>掌柜智库</strong>
          <small>SHOPKEEPER BRAIN</small>
        </span>
      </a>
      <nav aria-label="主导航">
        <a class="is-active" href="#main">文档导入</a>
        <span aria-disabled="true">知识问答 <small>即将开放</small></span>
      </nav>
      <div class="service-state">
        <i aria-hidden="true"></i>
        本地开发环境
      </div>
    </header>

    <main id="main">
      <section class="hero" aria-labelledby="page-title">
        <div class="hero-copy">
          <div class="eyebrow"><span></span> 企业文档智能入库</div>
          <h1 id="page-title">把产品手册，<br />变成<span>随时可问</span>的知识。</h1>
          <p>
            一次上传，自动完成解析、图片托管、语义切分、商品识别、混合向量化与知识入库。
          </p>
        </div>
        <div class="hero-metrics" aria-label="系统能力摘要">
          <div>
            <strong>8</strong>
            <span>最多处理节点</span>
          </div>
          <div>
            <strong>200<small>MB</small></strong>
            <span>单文件上限</span>
          </div>
          <div>
            <strong>2<small>路</small></strong>
            <span>混合向量检索</span>
          </div>
        </div>
      </section>

      <section class="workspace-grid">
        <UploadDropzone :active-count="activeCount" @selected="handleFiles" />
        <PipelineOverview />
      </section>

      <div v-if="notices.length" class="notice-stack" role="alert" aria-live="assertive">
        <div v-for="notice in notices" :key="notice" class="notice-item">
          <span>!</span>
          <p>{{ notice }}</p>
          <button type="button" aria-label="关闭提示" @click="notices = notices.filter((item) => item !== notice)">
            ×
          </button>
        </div>
      </div>

      <section class="tasks-section" aria-labelledby="tasks-title">
        <div class="tasks-heading">
          <div>
            <div class="section-kicker">03 / 导入任务</div>
            <h2 id="tasks-title">处理记录</h2>
          </div>
          <div class="tasks-summary">
            <span><b>{{ activeCount }}</b> 处理中</span>
            <span><b>{{ completedCount }}</b> 已完成</span>
            <button v-if="hasFinished" type="button" class="text-button" @click="clearFinished">
              清理已结束
            </button>
          </div>
        </div>

        <div v-if="tasks.length" class="task-list" aria-live="polite">
          <ImportTaskCard
            v-for="task in tasks"
            :key="task.localId"
            :task="task"
            @retry="retryTask"
            @remove="removeTask"
          />
        </div>

        <div v-else class="empty-state">
          <span class="empty-index">00</span>
          <div>
            <strong>还没有导入任务</strong>
            <p>选择上方文件后，节点进度和结果会在这里实时更新。</p>
          </div>
        </div>
      </section>
    </main>

    <footer class="page-footer">
      <span>掌柜智库 · RAG KNOWLEDGE WORKBENCH</span>
      <span>FastAPI / Vue 3 / Milvus</span>
    </footer>
  </div>
</template>
