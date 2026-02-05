<template>
  <div class="data-extraction-view">
    <div class="page-header">
      <h2>数据提取</h2>
      <p class="page-description">查看和管理已提取的数据</p>
    </div>
    <div class="empty-state">
      <p>数据提取功能待实现</p>
    </div>
  </div>
</template>

<script setup>
</script>

<style lang="less" scoped>
.data-extraction-view {
  padding: 24px;
  background: #ffffff;
  height: 100%;
  overflow-y: auto;
}

.page-header {
  margin-bottom: 24px;

  h2 {
    margin: 0 0 8px 0;
    font-size: 20px;
    font-weight: 600;
    color: #262626;
  }

  .page-description {
    margin: 0;
    color: #8c8c8c;
    font-size: 14px;
  }
}

.empty-state {
  text-align: center;
  padding: 100px 20px;
  color: #bfbfbf;
}
</style>