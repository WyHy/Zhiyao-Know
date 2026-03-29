<template>
  <div class="di-page">
    <div class="di-card">
      <div class="di-head">
        <div class="di-title">数据导入</div>
        <div class="di-subtitle">选择导入类型并上传 Excel，系统会解析并写入数据库</div>
      </div>

      <a-steps :current="currentStep" class="di-steps" size="small">
        <a-step title="选择类型" />
        <a-step title="上传文件" />
        <a-step title="导入结果" />
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
              <div class="di-type-hint">支持 Excel（.xlsx / .xlsm）</div>
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
            accept=".xlsx,.xlsm"
            class="di-uploader"
          >
            <p class="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p class="ant-upload-text">点击或拖拽 Excel 到这里上传</p>
            <p class="ant-upload-hint">上传后会直接调用后端 API 导入</p>
          </a-upload-dragger>

          <div class="di-csv">
            <div class="di-section-title di-section-title-sm">关键字段参考</div>
            <div class="di-csv-desc">请确保表头中至少包含下列关键字段。</div>
            <div class="di-csv-block">
              <div class="di-csv-fields">
                <a-tag v-for="f in csvSpec.fields" :key="f" class="di-field">{{ f }}</a-tag>
              </div>
            </div>
          </div>

          <div class="di-import-actions">
            <a-switch v-model:checked="replaceExisting" />
            <span class="di-import-label">覆盖该类型已有数据</span>
            <a-button type="primary" :loading="importing" :disabled="fileList.length === 0" @click="handleImport">
              开始导入
            </a-button>
          </div>
        </template>

        <template v-else>
          <div class="di-section-title">导入结果</div>
          <div class="di-result" v-if="importResult">
            <div class="row"><span>导入类型：</span><b>{{ currentTypeName }}</b></div>
            <div class="row"><span>解析总行数：</span><b>{{ importResult.total }}</b></div>
            <div class="row"><span>新增行数：</span><b>{{ importResult.imported }}</b></div>
            <div class="row"><span>更新行数：</span><b>{{ importResult.updated }}</b></div>
          </div>
          <div class="di-placeholder" v-else>暂无导入结果，请先上传并执行导入。</div>
        </template>
      </div>

      <div class="di-footer">
        <a-button @click="handlePrev" :disabled="currentStep === 0">上一步</a-button>
        <div class="spacer"></div>
        <a-button v-if="currentStep === 0" @click="currentStep = 1" type="primary" :disabled="!selectedType">下一步</a-button>
        <a-button v-else-if="currentStep === 2" type="primary" @click="currentStep = 1">继续导入</a-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { message } from 'ant-design-vue'
import { InboxOutlined } from '@ant-design/icons-vue'
import { complianceApi } from '@/apis/compliance_api'

const currentStep = ref(0)
const selectedType = ref('')
const fileList = ref([])
const replaceExisting = ref(true)
const importing = ref(false)
const importResult = ref(null)

const types = ref([
  { key: 'risk-library', name: '合规风险库', desc: '风险点、分级与管控措施', tone: 'red', iconText: '风' },
  { key: 'process-checklist', name: '流程管控清单', desc: '流程、风险描述与合规要点', tone: 'purple', iconText: '流' },
  { key: 'position-responsibility', name: '岗位职责清单', desc: '岗位职责与合规要点', tone: 'green', iconText: '岗' }
])

const currentTypeName = computed(() => {
  const hit = types.value.find((t) => t.key === selectedType.value)
  return hit?.name || '-'
})

const csvSpec = computed(() => {
  if (selectedType.value === 'process-checklist') {
    return { fields: ['末级流程编号', '末级流程名称', '合规重要环节', '合规审查内容', '合规审查责任部门'] }
  }
  if (selectedType.value === 'position-responsibility') {
    return { fields: ['部门名称', '岗位名称', '风险内控合规职责', '合规底线清单', '底线标准与处罚'] }
  }
  return { fields: ['风险行为编号', '合规风险名称', '风险行为描述', '风险等级', '风险控制措施', '归口部门'] }
})

const beforeUpload = (file) => {
  if (!/\.(xlsx|xlsm)$/i.test(file.name)) {
    message.error('仅支持 .xlsx/.xlsm 文件')
    return false
  }
  return false
}

const handlePrev = () => {
  if (currentStep.value === 0) return
  currentStep.value -= 1
}

const handleImport = async () => {
  const firstFile = fileList.value[0]
  const rawFile = firstFile?.originFileObj || firstFile
  if (!selectedType.value) {
    message.warning('请先选择导入类型')
    return
  }
  if (!rawFile) {
    message.warning('请先选择 Excel 文件')
    return
  }

  importing.value = true
  try {
    const res = await complianceApi.importExcel(selectedType.value, rawFile, replaceExisting.value)
    importResult.value = res
    currentStep.value = 2
    message.success('导入成功')
  } catch (error) {
    message.error(error.message || '导入失败')
  } finally {
    importing.value = false
  }
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
}

.di-uploader {
  border-radius: 12px;
}

.di-csv {
  margin-top: 12px;
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

.di-csv-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.di-field {
  background: rgba(59, 130, 246, 0.08);
  color: var(--gray-700);
  border: none;
  border-radius: 10px;
}

.di-import-actions {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.di-import-label {
  font-size: 12px;
  color: var(--gray-700);
}

.di-result {
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  background: var(--gray-0);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;

  .row {
    font-size: 13px;
    color: var(--gray-800);
  }
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
