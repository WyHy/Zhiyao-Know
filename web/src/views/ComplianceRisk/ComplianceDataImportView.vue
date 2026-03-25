<template>
  <div class="di-page">
    <div class="di-card">
      <div class="di-head">
        <div class="di-title">数据导入</div>
        <div class="di-subtitle">选择导入类型并上传文件（第 3/4 步 UI 暂未开放）</div>
      </div>

      <a-steps :current="currentStep" class="di-steps" size="small">
        <a-step title="选择类型" />
        <a-step title="上传文件" />
        <a-step title="校验预览" />
        <a-step title="确认导入" />
      </a-steps>

      <div class="di-body">
        <template v-if="currentStep === 0">
          <div class="di-section-title">选择导入数据类型</div>
          <div class="di-type-grid">
            <div
              v-for="t in types"
              :key="t.key"
              class="di-type-card"
              :class="{ active: selectedType === t.key }"
              @click="selectedType = t.key"
            >
              <div class="di-type-top">
                <div class="di-type-icon" :class="`tone-${t.tone}`">{{ t.iconText }}</div>
                <div class="di-type-meta">
                  <div class="di-type-name">{{ t.name }}</div>
                  <div class="di-type-desc">{{ t.desc }}</div>
                </div>
              </div>
              <div class="di-type-hint">支持 CSV / Excel</div>
            </div>
          </div>
        </template>

        <template v-else-if="currentStep === 1">
          <div class="di-section-title">上传文件</div>
          <div class="di-upload-hint">
            <span class="label">已选择类型：</span>
            <a-tag color="blue">{{ currentTypeName }}</a-tag>
          </div>

          <a-upload-dragger
            v-model:fileList="fileList"
            :before-upload="beforeUpload"
            :multiple="false"
            :max-count="1"
            accept=".csv,.xlsx,.xls"
            class="di-uploader"
          >
            <p class="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p class="ant-upload-text">点击或拖拽文件到这里上传</p>
            <p class="ant-upload-hint">仅本地预览（假流程），不会实际上传到服务器</p>
          </a-upload-dragger>

          <div class="di-csv">
            <div class="di-section-title di-section-title-sm">CSV 格式说明</div>
            <div class="di-csv-desc">第一行必须是表头；UTF-8 编码；逗号分隔；不支持合并单元格。</div>
            <div class="di-csv-block">
              <div class="di-csv-subtitle">字段（按列顺序）</div>
              <div class="di-csv-fields">
                <a-tag v-for="f in csvSpec.fields" :key="f" class="di-field">{{ f }}</a-tag>
              </div>
              <div class="di-csv-subtitle">示例（表头 + 1 行）</div>
              <pre class="di-csv-pre">{{ csvSpec.example }}</pre>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="di-section-title">暂未开放</div>
          <div class="di-placeholder">
            第 {{ currentStep + 1 }} 步 UI 暂无，先空着；本页会禁用“下一步”。
          </div>
        </template>
      </div>

      <div class="di-footer">
        <a-button @click="handlePrev" :disabled="currentStep === 0">上一步</a-button>
        <div class="spacer"></div>
        <a-button v-if="currentStep <= 1" @click="handleNext" type="primary" :disabled="!canNext">
          下一步
        </a-button>
        <a-button v-else type="primary" disabled>下一步</a-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { message } from 'ant-design-vue'
import { InboxOutlined } from '@ant-design/icons-vue'

const currentStep = ref(0)
const selectedType = ref('')
const fileList = ref([])

const types = ref([
  {
    key: 'risk-library',
    name: '合规风险库',
    desc: '风险点、分级与管控措施',
    tone: 'red',
    iconText: '风'
  },
  {
    key: 'process-checklist',
    name: '流程管控清单',
    desc: '流程、风险描述与合规要点',
    tone: 'purple',
    iconText: '流'
  },
  {
    key: 'position-responsibility',
    name: '岗位职责清单',
    desc: '岗位职责与合规要点',
    tone: 'green',
    iconText: '岗'
  }
])

const currentTypeName = computed(() => {
  const hit = types.value.find((t) => t.key === selectedType.value)
  return hit?.name || '-'
})

const csvSpec = computed(() => {
  const key = selectedType.value
  if (key === 'process-checklist') {
    return {
      fields: ['code', 'title', 'department', 'owner', 'risk_desc', 'compliance_points', 'measures'],
      example: [
        'code,title,department,owner,risk_desc,compliance_points,measures',
        'LC-001,招标采购审批流程,物资部,采购主管,存在规避招标风险,"采购金额超限触发招标|招标文件综合合规审查|评标委员会资质审核",审查立项资料->确认招标方式->组织公开招标'
      ].join('\n')
    }
  }
  if (key === 'position-responsibility') {
    return {
      fields: ['code', 'title', 'department', 'compliance_type', 'level', 'responsibilities', 'compliance_points', 'related_risks'],
      example: [
        'code,title,department,compliance_type,level,responsibilities,compliance_points,related_risks',
        'GW-001,合规管理专员,合规管理部,法律合规,专员,"制度宣贯|风险识别评估|合规审查留痕","重大事项书面意见|关键节点留痕可追溯","FX-001|FX-005"'
      ].join('\n')
    }
  }
  // 默认：合规风险库
  return {
    fields: ['code', 'level', 'category', 'title', 'desc', 'chips', 'department', 'owner', 'basis', 'measures'],
    example: [
      'code,level,category,title,desc,chips,department,owner,basis,measures',
      'FX-001,高风险,法律合规,采购项目立项,未按规定履行招标程序,"招标采购|采购项目立项|物资部",物资部,采购主管,《招标投标法》…,"严格执行制度|建立审查机制|定期培训"'
    ].join('\n')
  }
})

const canNext = computed(() => {
  if (currentStep.value === 0) return !!selectedType.value
  if (currentStep.value === 1) return fileList.value.length > 0
  return false
})

const handlePrev = () => {
  if (currentStep.value === 0) return
  currentStep.value -= 1
}

const handleNext = () => {
  if (!canNext.value) return
  if (currentStep.value === 0) {
    currentStep.value = 1
    return
  }
  if (currentStep.value === 1) {
    currentStep.value = 2
    message.info('第 3/4 步暂未开放（已进入占位页）')
  }
}

const beforeUpload = (file) => {
  // 阻止自动上传：仅做本地“已选择文件”的演示
  const isAllowed = /\.(csv|xlsx|xls)$/i.test(file.name)
  if (!isAllowed) {
    message.error('仅支持 CSV / Excel 文件')
    return false
  }
  return false
}
</script>

<style scoped lang="less">
.di-page {
  width: 100%;
}

.di-card {
  background: var(--gray-0);
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  padding: 16px;
}

.di-head {
  margin-bottom: 12px;
}

.di-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--gray-1000);
}

.di-subtitle {
  margin-top: 6px;
  font-size: 12px;
  color: var(--gray-600);
}

.di-steps {
  margin-top: 10px;
}

.di-body {
  margin-top: 16px;
}

.di-section-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--gray-1000);
  margin-bottom: 12px;
}

.di-type-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.di-type-card {
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  background: var(--gray-0);
  transition: background-color 0.15s ease, border-color 0.15s ease;

  &:hover {
    background: var(--gray-25);
  }

  &.active {
    border-color: rgba(59, 130, 246, 0.45);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
  }
}

.di-type-top {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.di-type-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex: 0 0 auto;

  &.tone-red {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }
  &.tone-purple {
    background: rgba(168, 85, 247, 0.1);
    color: #a855f7;
  }
  &.tone-green {
    background: rgba(34, 197, 94, 0.1);
    color: #22c55e;
  }
}

.di-type-meta {
  min-width: 0;
}

.di-type-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--gray-1000);
}

.di-type-desc {
  margin-top: 4px;
  font-size: 12px;
  color: var(--gray-600);
}

.di-type-hint {
  margin-top: 10px;
  font-size: 12px;
  color: var(--gray-500);
}

.di-upload-hint {
  margin-bottom: 10px;
  font-size: 12px;
  color: var(--gray-600);
  display: flex;
  align-items: center;
  gap: 8px;

  .label {
    color: var(--gray-600);
  }
}

.di-uploader {
  border-radius: 12px;
}

.di-section-title-sm {
  margin-top: 14px;
  margin-bottom: 8px;
}

.di-csv {
  margin-top: 10px;
}

.di-csv-desc {
  font-size: 12px;
  color: var(--gray-600);
  margin-bottom: 10px;
}

.di-csv-block {
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  padding: 12px;
  background: var(--gray-0);
}

.di-csv-subtitle {
  font-size: 12px;
  font-weight: 700;
  color: var(--gray-900);
  margin-bottom: 8px;
}

.di-csv-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.di-field {
  background: rgba(59, 130, 246, 0.08);
  color: var(--gray-700);
  border: none;
  border-radius: 10px;
}

.di-csv-pre {
  margin: 0;
  padding: 10px 12px;
  background: var(--gray-25);
  border: 1px solid var(--gray-200);
  border-radius: 10px;
  font-size: 12px;
  color: var(--gray-900);
  overflow: auto;
  white-space: pre;
}

.di-placeholder {
  border: 1px dashed var(--gray-200);
  border-radius: 12px;
  padding: 18px;
  color: var(--gray-600);
  background: var(--gray-25);
}

.di-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--gray-100);
}

.spacer {
  flex: 1 1 auto;
}

@media (max-width: 1024px) {
  .di-type-grid {
    grid-template-columns: 1fr;
  }
}
</style>

