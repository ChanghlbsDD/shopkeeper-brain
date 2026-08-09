<script setup lang="ts">
const stages = [
  { number: "01", title: "接收与解析", detail: "原件归档 · PDF 转换" },
  { number: "02", title: "整理与切分", detail: "图片托管 · 章节切片" },
  { number: "03", title: "理解与向量化", detail: "商品识别 · 混合向量" },
  { number: "04", title: "建立知识索引", detail: "Milvus 批量入库" },
]
</script>

<template>
  <aside class="pipeline-panel" aria-labelledby="pipeline-title">
    <div class="section-kicker">02 / 处理路线</div>
    <div class="pipeline-heading">
      <div>
        <h2 id="pipeline-title">从文件到知识，只走一条清晰路线</h2>
        <p>PDF 共 8 步，Markdown 自动跳过解析节点，共 7 步。</p>
      </div>
      <span class="pipeline-seal" aria-label="混合检索已启用">HYBRID</span>
    </div>

    <ol class="overview-list">
      <li v-for="stage in stages" :key="stage.number">
        <span class="overview-number">{{ stage.number }}</span>
        <span class="overview-line" aria-hidden="true"></span>
        <span class="overview-copy">
          <strong>{{ stage.title }}</strong>
          <small>{{ stage.detail }}</small>
        </span>
      </li>
    </ol>

    <div class="pipeline-footnote">
      <span class="pulse-light" aria-hidden="true"></span>
      <span>节点状态每 1.5 秒更新一次</span>
    </div>
  </aside>
</template>
