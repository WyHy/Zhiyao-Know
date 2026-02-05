<template>
  <div class="chat-view">
    <!-- 顶部标签栏 -->
    <div class="chat-header-tabs">
      <div class="tab-item" :class="{ active: activeTab === 'model' }" @click="activeTab = 'model'">
        大模型名称
      </div>
      <div class="tab-item" :class="{ active: activeTab === 'knowledge' }" @click="activeTab = 'knowledge'">
        知识库名称
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="chat-main-container">
      <!-- 左侧主内容区 -->
      <div class="chat-content">
        <!-- 欢迎区域 -->
        <div class="welcome-section">
          <div class="welcome-emoji">👋</div>
          <h1 class="welcome-greeting">{{ greeting }}</h1>
          <p class="welcome-intro">我是你的智能合规管控小助手,请问现在能帮您做什么?</p>
          
          <!-- 建议操作按钮 -->
          <div class="suggested-actions">
            <div class="action-button" @click="handleSuggestionClick('解析一下xxx文件的内容,形成摘要')">
              <span>解析一下xxx文件的内容,形成摘要</span>
              <span class="arrow-icon">→</span>
            </div>
            <div class="action-button" @click="handleSuggestionClick('帮我生成一份关于xxx的报告')">
              <span>帮我生成一份关于xxx的报告</span>
              <span class="arrow-icon">→</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧边栏 -->
      <div class="chat-sidebar">
        <div class="sidebar-header">
          <span class="clock-icon">🕐</span>
          <h3 class="sidebar-title">最近对话</h3>
        </div>
        <p class="sidebar-hint">
          最近的对话记录会显示在这里
        </p>
        <div class="conversation-list">
          <!-- 暂时为空，显示提示 -->
          <div class="empty-conversations">
            <p>暂无对话记录</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部输入区域 -->
    <div class="chat-input-wrapper">
      <div class="chat-input-area">
        <div class="input-icons">
          <div class="input-icon" title="AI助手">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div class="input-icon" title="文档">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
          </div>
          <div class="input-icon" title="文件夹">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
        </div>
        <input
          v-model="inputText"
          type="text"
          class="chat-input"
          placeholder="请输入您的问题..."
          @keyup.enter="handleSend"
        />
        <button class="send-button" @click="handleSend" :disabled="!inputText.trim()">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const activeTab = ref('model')
const inputText = ref('')

// 根据时间获取问候语
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) {
    return '上午好'
  } else if (hour < 18) {
    return '下午好'
  } else {
    return '晚上好'
  }
})

// 处理建议按钮点击
const handleSuggestionClick = (text) => {
  inputText.value = text
  // 这里可以触发发送
  console.log('建议内容:', text)
}

// 处理发送
const handleSend = () => {
  if (!inputText.value.trim()) return
  console.log('发送消息:', inputText.value)
  // TODO: 实现发送逻辑
  inputText.value = ''
}
</script>

<style lang="less" scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
}

// 顶部标签栏
.chat-header-tabs {
  display: flex;
  gap: 8px;
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: #ffffff;

  .tab-item {
    padding: 8px 20px;
    border-radius: 8px;
    background: #f5f5f5;
    color: #666;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;

    &:hover {
      background: #e8e8e8;
    }

    &.active {
      background: #1890ff;
      color: #ffffff;
    }
  }
}

// 主内容容器
.chat-main-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

// 左侧主内容区
.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  overflow-y: auto;
}

.welcome-section {
  text-align: center;
  max-width: 600px;
}

.welcome-emoji {
  font-size: 80px;
  margin-bottom: 24px;
  animation: wave 2s ease-in-out infinite;
}

@keyframes wave {
  0%, 100% {
    transform: rotate(0deg);
  }
  25% {
    transform: rotate(20deg);
  }
  75% {
    transform: rotate(-20deg);
  }
}

.welcome-greeting {
  font-size: 32px;
  font-weight: 600;
  color: #262626;
  margin: 0 0 16px 0;
}

.welcome-intro {
  font-size: 16px;
  color: #595959;
  margin: 0 0 32px 0;
  line-height: 1.6;
}

.suggested-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 32px;
}

.action-button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: #f5f5f5;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  color: #262626;

  &:hover {
    background: #e8e8e8;
    transform: translateX(4px);
  }

  .arrow-icon {
    color: #8c8c8c;
    font-size: 18px;
  }
}

// 右侧边栏
.chat-sidebar {
  width: 320px;
  border-left: 1px solid #f0f0f0;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  padding: 24px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;

  .clock-icon {
    font-size: 18px;
  }

  .sidebar-title {
    font-size: 16px;
    font-weight: 600;
    color: #262626;
    margin: 0;
  }
}

.sidebar-hint {
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.5;
  margin: 0 0 24px 0;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
}

.empty-conversations {
  text-align: center;
  padding: 40px 20px;
  color: #bfbfbf;
  font-size: 14px;
}

// 底部输入区域包装器
.chat-input-wrapper {
  display: flex;
  justify-content: center;
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
  background: #ffffff;
}

// 底部输入区域
.chat-input-area {
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 800px;
  width: 100%;
}

.input-icons {
  display: flex;
  gap: 12px;
}

.input-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  color: #8c8c8c;
  cursor: pointer;
  transition: color 0.2s;

  &:hover {
    color: #1890ff;
  }
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 24px;
  font-size: 14px;
  outline: none;
  transition: all 0.2s;

  &:focus {
    border-color: #1890ff;
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
  }

  &::placeholder {
    color: #bfbfbf;
  }
}

.send-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #1890ff;
  color: #ffffff;
  border: none;
  cursor: pointer;
  transition: all 0.2s;

  &:hover:not(:disabled) {
    background: #40a9ff;
    transform: scale(1.05);
  }

  &:disabled {
    background: #d9d9d9;
    cursor: not-allowed;
  }
}
</style>