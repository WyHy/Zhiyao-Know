<template>
  <div class="share-config-form">
    <div class="share-config-content">
      <div class="share-mode">
        <a-radio-group v-model:value="config.is_shared" class="share-mode-radio">
          <a-radio :value="true">全员共享</a-radio>
          <a-radio :value="false">指定部门</a-radio>
        </a-radio-group>
      </div>
      <p class="share-hint">
        {{ config.is_shared ? '所有用户都可以访问' : '只有指定部门的用户可以访问' }}
      </p>
      <!-- 部门选择 - 改用树形选择器 -->
      <div v-if="!config.is_shared" class="dept-selection">
        <a-tree-select
          v-model:value="config.accessible_department_ids"
          :tree-data="departmentTreeData"
          tree-checkable
          :show-checked-strategy="SHOW_PARENT"
          placeholder="请选择可访问的部门"
          style="width: 100%"
          :tree-default-expand-all="false"
          :max-tag-count="3"
          allow-clear
        />
        <p class="dept-hint">支持选择多个部门，包含子部门会自动包含</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { TreeSelect } from 'ant-design-vue'
import { useUserStore } from '@/stores/user'
import { getDepartments } from '@/apis/department_api'

const SHOW_PARENT = TreeSelect.SHOW_PARENT

const userStore = useUserStore()
const departmentTree = ref([])

const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
    default: () => ({
      is_shared: true,
      accessible_department_ids: []
    })
  },
  // 是否自动选中当前用户所在部门
  autoSelectUserDept: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

// 本地状态
const config = reactive({
  is_shared: true,
  accessible_department_ids: []
})

// 初始化 config
const initConfig = () => {
  const sourceDepts =
    props.modelValue.accessible_department_ids ?? props.modelValue.accessible_departments ?? []
  config.is_shared = props.modelValue.is_shared ?? true
  config.accessible_department_ids = sourceDepts.map((id) => Number(id))
  console.log('[ShareConfigForm] initConfig:', JSON.stringify(config))
}

// 递归构建树形数据
const buildTreeData = (nodes) => {
  if (!Array.isArray(nodes)) {
    console.warn('[ShareConfigForm] buildTreeData 收到非数组数据:', nodes)
    return []
  }
  
  return nodes.map((node) => {
    const treeNode = {
      title: node.name,
      value: node.id,
      key: `dept_${node.id}`,
      selectable: false,
      checkable: true
    }
    
    if (node.children && Array.isArray(node.children) && node.children.length > 0) {
      treeNode.children = buildTreeData(node.children)
    }
    
    return treeNode
  })
}

// 部门树形数据
const departmentTreeData = computed(() => {
  if (!departmentTree.value || departmentTree.value.length === 0) {
    return []
  }
  return buildTreeData(departmentTree.value)
})

// 获取所有部门ID（扁平化）
const getAllDepartmentIds = (tree) => {
  const ids = []
  const traverse = (nodes) => {
    nodes.forEach((node) => {
      ids.push(node.id)
      if (node.children && node.children.length > 0) {
        traverse(node.children)
      }
    })
  }
  traverse(tree)
  return ids
}

// 尝试自动选中用户所在部门
const tryAutoSelectUserDept = () => {
  const userDeptId = userStore.departmentId
  if (userDeptId) {
    const allDeptIds = getAllDepartmentIds(departmentTree.value)
    if (allDeptIds.includes(userDeptId)) {
      config.accessible_department_ids = [Number(userDeptId)]
    }
  }
}

// 加载部门树
const loadDepartments = async () => {
  try {
    const res = await getDepartments()
    // getDepartments 返回的是数组，不是包含 data 的对象
    departmentTree.value = Array.isArray(res) ? res : (res?.data || [])
    console.log('[ShareConfigForm] 加载部门树，节点数:', departmentTree.value.length)

    if (
      props.autoSelectUserDept &&
      !config.is_shared &&
      config.accessible_department_ids.length === 0
    ) {
      tryAutoSelectUserDept()
    }
  } catch (e) {
    console.error('加载部门列表失败:', e)
    departmentTree.value = []
  }
}

// 监听本地 config 变化，同步到父组件
watch(
  config,
  (newVal) => {
    console.log('[ShareConfigForm] config 变化，emit:', JSON.stringify(newVal))
    emit('update:modelValue', {
      is_shared: newVal.is_shared,
      accessible_department_ids: newVal.accessible_department_ids
    })
  },
  { deep: true }
)

// 监听共享模式变化
watch(
  () => config.is_shared,
  (newVal) => {
    if (!newVal && props.autoSelectUserDept && config.accessible_department_ids.length === 0) {
      tryAutoSelectUserDept()
    }
  }
)

// 监听用户部门变化
watch(
  () => userStore.departmentId,
  (newDeptId) => {
    if (
      props.autoSelectUserDept &&
      !config.is_shared &&
      config.accessible_department_ids.length === 0 &&
      newDeptId
    ) {
      tryAutoSelectUserDept()
    }
  }
)

// 组件挂载时初始化
onMounted(async () => {
  initConfig()
  await loadDepartments()
})

// 验证
const validate = () => {
  if (config.is_shared) {
    return { valid: true, message: '' }
  }

  const userDeptId = userStore.departmentId
  if (!userDeptId) {
    return {
      valid: false,
      message: '您不属于任何部门，无法使用指定部门共享模式'
    }
  }

  if (!config.accessible_department_ids.includes(userDeptId)) {
    return {
      valid: false,
      message: '您所在的部门必须在可访问部门范围内'
    }
  }

  return { valid: true, message: '' }
}

// 暴露方法给父组件
defineExpose({
  config,
  validate
})
</script>

<style lang="less" scoped>
.share-config-form {
  h3 {
    margin-top: 20px;
    margin-bottom: 12px;
  }

  .share-config-content {
    background: var(--gray-25);
    border-radius: 8px;
    padding: 16px;
    border: 1px solid var(--gray-150);

    .share-mode {
      .share-mode-radio {
        display: flex;
        gap: 24px;
      }
    }

    .share-hint {
      font-size: 13px;
      color: var(--gray-600);
      margin: 8px 0 0 0;
    }

    .dept-selection {
      margin-top: 12px;

      .dept-hint {
        font-size: 12px;
        color: var(--gray-500);
        margin: 6px 0 0 0;
      }
    }
  }
}
</style>
