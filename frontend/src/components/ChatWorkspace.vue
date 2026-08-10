<script setup lang="ts">
import { nextTick, onMounted, ref } from "vue"

import {
  clearQueryHistory,
  getQueryHistory,
  QueryApiError,
  searchQuery,
  streamQuery,
} from "../api/queries"
import type {
  QueryReference,
  QuerySearchResponse,
  QueryStreamEvent,
} from "../types/queries"

interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  pending?: boolean
  references?: QueryReference[]
  images?: string[]
  options?: string[]
}

const SESSION_KEY = "shopkeeper-brain-query-session"
const nodeLabels: Record<string, string> = {
  item_name_confirm_node: "确认商品",
  query_embedding_node: "问题向量化",
  vector_search_node: "知识库检索",
  hyde_search_node: "假设答案检索",
  web_search_node: "联网检索",
  rrf_node: "召回融合",
  rerank_node: "证据精排",
  answer_generation_node: "生成答案",
}

const sessionId = ref(loadOrCreateSessionId())
const messages = ref<ChatMessage[]>([])
const question = ref("")
const useStreaming = ref(true)
const busy = ref(false)
const loadingHistory = ref(true)
const statusText = ref("正在恢复会话…")
const listElement = ref<HTMLElement | null>(null)

function createSessionId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID().replaceAll("-", "")
  }
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
}

function loadOrCreateSessionId(): string {
  try {
    const stored = localStorage.getItem(SESSION_KEY)
    if (stored && /^[A-Za-z0-9_-]{1,64}$/.test(stored)) return stored
    const created = createSessionId()
    localStorage.setItem(SESSION_KEY, created)
    return created
  } catch {
    return createSessionId()
  }
}

function saveSessionId(value: string): void {
  try {
    localStorage.setItem(SESSION_KEY, value)
  } catch {
    // 隐私模式禁用 localStorage 时，本页会话仍然可用。
  }
}

async function restoreHistory(): Promise<void> {
  try {
    const history = await getQueryHistory(sessionId.value)
    messages.value = history.items.map((item) => ({
      id: item.message_id,
      role: item.role,
      content: item.content,
    }))
    statusText.value = history.items.length ? "已恢复历史会话" : "可以开始提问"
  } catch (error) {
    statusText.value = errorMessage(error)
  } finally {
    loadingHistory.value = false
    await scrollToLatest()
  }
}

async function submitQuestion(preset?: string): Promise<void> {
  const content = (preset ?? question.value).trim()
  if (!content || busy.value) return
  question.value = ""
  busy.value = true
  statusText.value = "正在理解问题…"
  const assistant: ChatMessage = {
    id: `assistant-${Date.now()}`,
    role: "assistant",
    content: "",
    pending: true,
  }
  messages.value.push(
    { id: `user-${Date.now()}`, role: "user", content },
    assistant,
  )
  await scrollToLatest()

  try {
    const request = { query: content, session_id: sessionId.value }
    let result: QuerySearchResponse
    if (useStreaming.value) {
      result = await streamQuery(request, (event) => handleStreamEvent(event, assistant))
    } else {
      result = await searchQuery(request)
    }
    applyFinalResponse(assistant, result)
    statusText.value = result.history_persisted
      ? "回答完成 · 已保存会话"
      : "回答完成 · 会话未保存"
  } catch (error) {
    const message = errorMessage(error)
    assistant.content = assistant.content
      ? `${assistant.content}\n\n回答中断：${message}`
      : `暂时无法回答：${message}`
    statusText.value = message
  } finally {
    assistant.pending = false
    busy.value = false
    await scrollToLatest()
  }
}

function handleStreamEvent(event: QueryStreamEvent, assistant: ChatMessage): void {
  if (event.event === "progress") {
    const node = event.data.node || ""
    statusText.value = `${nodeLabels[node] || "处理问题"}…`
  } else if (event.event === "delta" && event.data.text) {
    assistant.content += event.data.text
    void scrollToLatest()
  } else if (event.event === "final") {
    applyFinalResponse(assistant, event.data)
  }
}

function applyFinalResponse(message: ChatMessage, response: QuerySearchResponse): void {
  message.content = response.answer || response.clarification || "没有找到足够资料。"
  message.references = response.references
  message.images = response.images
  message.options = response.item_name_options
}

async function clearConversation(): Promise<void> {
  if (busy.value || !window.confirm("确定清空当前会话记录吗？")) return
  try {
    await clearQueryHistory(sessionId.value)
    messages.value = []
    sessionId.value = createSessionId()
    saveSessionId(sessionId.value)
    statusText.value = "会话已清空，可以重新提问"
  } catch (error) {
    statusText.value = errorMessage(error)
  }
}

function errorMessage(error: unknown): string {
  if (error instanceof QueryApiError) return error.message
  return "网络连接失败，请确认后端服务已经启动"
}

async function scrollToLatest(): Promise<void> {
  await nextTick()
  listElement.value?.scrollTo({ top: listElement.value.scrollHeight, behavior: "smooth" })
}

onMounted(restoreHistory)
</script>

<template>
  <section class="chat-page" aria-labelledby="chat-title">
    <header class="chat-intro">
      <div>
        <div class="eyebrow"><span></span> RAG 企业知识问答</div>
        <h1 id="chat-title">问产品，也问方法。</h1>
        <p>系统会确认商品、检索本地知识与网页资料、融合精排，并在答案后标出来源。</p>
      </div>
      <div class="chat-session-card">
        <small>当前会话</small>
        <code>{{ sessionId.slice(0, 12) }}</code>
        <button type="button" :disabled="busy" @click="clearConversation">清空记录</button>
      </div>
    </header>

    <div class="chat-workspace">
      <aside class="chat-guide">
        <div class="section-kicker">回答流程</div>
        <ol>
          <li v-for="(label, node) in nodeLabels" :key="node">
            <span>{{ String(Object.keys(nodeLabels).indexOf(node) + 1).padStart(2, "0") }}</span>
            {{ label }}
          </li>
        </ol>
        <p>答案中的 <b>[1]</b> 等编号，对应回答下方的证据来源。</p>
      </aside>

      <div class="chat-panel">
        <div ref="listElement" class="message-list" aria-live="polite">
          <div v-if="loadingHistory" class="chat-empty">正在读取 MongoDB 会话历史…</div>
          <div v-else-if="!messages.length" class="chat-empty">
            <span>?</span>
            <strong>从一个具体问题开始</strong>
            <p>例如：RS-12 数字万用表怎么测量直流电压？</p>
          </div>

          <article
            v-for="message in messages"
            :key="message.id"
            class="message"
            :class="`is-${message.role}`"
          >
            <div class="message-role">{{ message.role === "user" ? "你" : "掌柜智库" }}</div>
            <div class="message-body">
              <p :class="{ 'is-waiting': message.pending && !message.content }">
                {{ message.content || "正在组织答案…" }}
              </p>
              <div v-if="message.options?.length" class="clarification-options">
                <button
                  v-for="option in message.options"
                  :key="option"
                  type="button"
                  :disabled="busy"
                  @click="submitQuestion(option)"
                >
                  {{ option }}
                </button>
              </div>
              <div v-if="message.images?.length" class="answer-images">
                <a
                  v-for="image in message.images"
                  :key="image"
                  :href="image"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <img :src="image" alt="知识文档中的相关图片" loading="lazy" />
                </a>
              </div>
              <ol v-if="message.references?.length" class="answer-references">
                <li v-for="reference in message.references" :key="reference.reference_id">
                  <b>[{{ reference.reference_id }}]</b>
                  <a
                    v-if="reference.source === 'web' && reference.url"
                    :href="reference.url"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {{ reference.title }}
                  </a>
                  <span v-else>
                    {{ reference.title }}
                    <small v-if="reference.chunk_id !== null">
                      · 知识片段 {{ reference.chunk_id }}
                    </small>
                  </span>
                </li>
              </ol>
            </div>
          </article>
        </div>

        <form class="question-box" @submit.prevent="submitQuestion()">
          <div class="query-state">
            <span :class="{ 'is-busy': busy }"></span>
            {{ statusText }}
          </div>
          <textarea
            v-model="question"
            rows="3"
            maxlength="2000"
            placeholder="输入产品名称和你的问题…"
            :disabled="busy || loadingHistory"
            @keydown.enter.exact.prevent="submitQuestion()"
          ></textarea>
          <div class="question-actions">
            <label>
              <input v-model="useStreaming" type="checkbox" :disabled="busy" />
              流式显示回答
            </label>
            <span>{{ question.length }} / 2000</span>
            <button type="submit" class="primary-button" :disabled="!question.trim() || busy">
              {{ busy ? "回答中…" : "发送问题" }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </section>
</template>
