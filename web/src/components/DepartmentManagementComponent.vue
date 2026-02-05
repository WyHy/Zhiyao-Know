<template>
  <div class="department-management">
    <!-- 头部区域 -->
    <div class="header-section">
      <div class="header-content">
        <h3 class="title">部门管理</h3>
        <p class="description">管理系统部门，部门下的用户会被隔离管理。</p>
      </div>
      <a-button type="primary" @click="showAddDepartmentModal" class="add-btn">
        <template #icon><PlusOutlined /></template>
        添加部门
      </a-button>
    </div>

    <!-- 主内容区域 -->
    <div class="content-section">
      <a-spin :spinning="departmentManagement.loading">
        <div v-if="departmentManagement.error" class="error-message">
          <a-alert type="error" :message="departmentManagement.error" show-icon />
        </div>

        <template v-if="departmentManagement.departments.length > 0">
          <a-table
            :dataSource="departmentManagement.departments"
            :columns="columns"
            :rowKey="(record) => record.id"
            :pagination="false"
            :defaultExpandAllRows="false"
            :expandedRowKeys="expandedRowKeys"
            @expand="handleExpand"
            class="department-table"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'name'">
                <div class="department-name">
                  <!-- 层级缩进 -->
                  <span
                    v-for="i in record.displayLevel"
                    :key="'indent-' + i"
                    class="level-indent"
                  ></span>
                  <!-- 层级指示器 -->
                  <span v-if="record.displayLevel > 0" class="level-indicator">└─</span>
                  <!-- 部门名称 -->
                  <span class="name-text">{{ record.name }}</span>
                  <!-- 层级标签 -->
                  <a-tag v-if="record.level" :color="getLevelColor(record.level)" size="small" class="level-tag">
                    L{{ record.level }}
                  </a-tag>
                </div>
              </template>
              <template v-if="column.key === 'description'">
                <span class="description-text">{{ record.description || '-' }}</span>
              </template>
              <template v-if="column.key === 'userCount'">
                <span>{{ record.user_count ?? 0 }} 人</span>
              </template>
              <template v-if="column.key === 'action'">
                <a-space>
                  <a-tooltip title="编辑部门">
                    <a-button
                      type="text"
                      size="small"
                      @click="showEditDepartmentModal(record)"
                      class="action-btn"
                    >
                      <EditOutlined />
                    </a-button>
                  </a-tooltip>
                  <a-tooltip title="删除部门">
                    <a-button
                      type="text"
                      size="small"
                      danger
                      @click="confirmDeleteDepartment(record)"
                      :disabled="record.user_count > 0 || record.hasChildren"
                      class="action-btn"
                    >
                      <DeleteOutlined />
                    </a-button>
                  </a-tooltip>
                </a-space>
              </template>
            </template>
          </a-table>
        </template>

        <div v-else class="empty-state">
          <a-empty description="暂无部门数据" />
        </div>
      </a-spin>
    </div>

    <!-- 部门表单模态框 -->
    <a-modal
      v-model:open="departmentManagement.modalVisible"
      :title="departmentManagement.modalTitle"
      @ok="handleDepartmentFormSubmit"
      :confirmLoading="departmentManagement.loading"
      @cancel="departmentManagement.modalVisible = false"
      :maskClosable="false"
      width="520px"
      class="department-modal"
    >
      <a-form layout="vertical" class="department-form">
        <a-form-item label="上级部门" class="form-item">
          <a-tree-select
            v-model:value="departmentManagement.form.parent_id"
            :tree-data="departmentTreeData"
            placeholder="请选择上级部门（可选，不选则为顶级部门）"
            allow-clear
            :field-names="{ label: 'name', value: 'id', children: 'children' }"
            tree-default-expand-all
            size="large"
          />
          <div class="help-text">不选择则创建为顶级部门</div>
        </a-form-item>

        <a-form-item label="部门名称" required class="form-item">
          <a-input
            v-model:value="departmentManagement.form.name"
            placeholder="请输入部门名称"
            size="large"
            :maxlength="50"
          />
        </a-form-item>

        <a-form-item label="部门描述" class="form-item">
          <a-textarea
            v-model:value="departmentManagement.form.description"
            placeholder="请输入部门描述（可选）"
            :rows="3"
            :maxlength="255"
            show-count
          />
        </a-form-item>

        <a-form-item label="排序顺序" class="form-item">
          <a-input-number
            v-model:value="departmentManagement.form.sort_order"
            placeholder="数字越小越靠前"
            :min="0"
            :max="9999"
            size="large"
            style="width: 100%"
          />
          <div class="help-text">同级部门按此值排序，数字越小越靠前</div>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { reactive, onMounted, computed, ref } from 'vue'
import { notification, Modal } from 'ant-design-vue'
import { departmentApi } from '@/apis'
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons-vue'

// 表格列定义
const columns = [
  {
    title: '部门名称',
    dataIndex: 'name',
    key: 'name',
    width: 200
  },
  {
    title: '描述',
    dataIndex: 'description',
    key: 'description',
    ellipsis: true
  },
  {
    title: '用户数量',
    dataIndex: 'user_count',
    key: 'userCount',
    width: 100,
    align: 'center'
  },
  {
    title: '操作',
    key: 'action',
    width: 120,
    align: 'center'
  }
]

// 展开的行
const expandedRowKeys = ref([])

// 扁平化部门列表（用于选择上级部门）
const flattenDepartmentsForSelect = (deptList, result = [], excludeId = null, level = 0) => {
  deptList.forEach(dept => {
    if (dept.id !== excludeId) {
      result.push({
        value: dept.id,
        label: '  '.repeat(level) + dept.name,
        level: dept.level
      })
      if (dept.children && dept.children.length > 0) {
        flattenDepartmentsForSelect(dept.children, result, excludeId, level + 1)
      }
    }
  })
  return result
}

// 上级部门选项
const parentDepartmentOptions = computed(() => {
  if (!departmentManagement.departments.length) return []
  const excludeId = departmentManagement.editMode ? departmentManagement.editDepartmentId : null
  return flattenDepartmentsForSelect(departmentManagement.departments, [], excludeId)
})

// 获取级别颜色
const getLevelColor = (level) => {
  const colors = {
    1: 'blue',
    2: 'green',
    3: 'orange',
    4: 'red',
    5: 'purple'
  }
  return colors[level] || 'default'
}

// 切换展开/收起
const toggleExpand = (id) => {
  const index = expandedRowKeys.value.indexOf(id)
  if (index > -1) {
    expandedRowKeys.value.splice(index, 1)
  } else {
    expandedRowKeys.value.push(id)
  }
}

// 处理展开事件
const handleExpand = (expanded, record) => {
  if (expanded) {
    if (!expandedRowKeys.value.includes(record.id)) {
      expandedRowKeys.value.push(record.id)
    }
  } else {
    const index = expandedRowKeys.value.indexOf(record.id)
    if (index > -1) {
      expandedRowKeys.value.splice(index, 1)
    }
  }
}

// 部门管理状态
const departmentManagement = reactive({
  loading: false,
  departments: [],
  departmentTree: [], // 存储原始树形数据
  error: null,
  modalVisible: false,
  modalTitle: '添加部门',
  editMode: false,
  editDepartmentId: null,
  form: {
    name: '',
    parent_id: null,
    description: '',
    sort_order: 0
  }
})

// 计算属性：用于树形选择器的数据
const departmentTreeData = computed(() => {
  // 如果是编辑模式，需要过滤掉当前部门及其子部门（避免循环引用）
  if (departmentManagement.editMode && departmentManagement.editDepartmentId) {
    return filterDepartmentTree(
      departmentManagement.departmentTree,
      departmentManagement.editDepartmentId
    )
  }
  return departmentManagement.departmentTree
})

// 过滤部门树，排除指定部门及其子部门
const filterDepartmentTree = (tree, excludeId) => {
  return tree
    .filter((node) => node.id !== excludeId)
    .map((node) => ({
      ...node,
      children: node.children ? filterDepartmentTree(node.children, excludeId) : []
    }))
}

// 将树形结构扁平化为列表
const flattenDepartmentTree = (tree, level = 0) => {
  const result = []
  
  tree.forEach((node) => {
    // 添加当前节点，带层级信息
    result.push({
      ...node,
      displayLevel: level,
      hasChildren: node.children && node.children.length > 0
    })
    
    // 递归处理子节点
    if (node.children && node.children.length > 0) {
      const childNodes = flattenDepartmentTree(node.children, level + 1)
      result.push(...childNodes)
    }
  })
  
  return result
}

// 获取部门列表
const fetchDepartments = async () => {
  try {
    departmentManagement.loading = true
    departmentManagement.error = null
    const response = await departmentApi.getDepartments()
    
    // 后端返回格式: { success: true, data: [...] }
    const treeData = response.data || response
    
    // 保存原始树形数据（用于父部门选择器）
    departmentManagement.departmentTree = treeData
    
    // 将树形结构扁平化（用于表格显示）
    const flatDepartments = flattenDepartmentTree(treeData)
    
    departmentManagement.departments = flatDepartments
  } catch (error) {
    console.error('获取部门列表失败:', error)
    departmentManagement.error = '获取部门列表失败'
  } finally {
    departmentManagement.loading = false
  }
}

// 打开添加部门模态框
const showAddDepartmentModal = () => {
  departmentManagement.modalTitle = '添加部门'
  departmentManagement.editMode = false
  departmentManagement.editDepartmentId = null
  departmentManagement.form = {
    name: '',
    parent_id: null,
    description: '',
    sort_order: 0
  }
  departmentManagement.modalVisible = true
}

// 打开编辑部门模态框
const showEditDepartmentModal = (department) => {
  departmentManagement.modalTitle = '编辑部门'
  departmentManagement.editMode = true
  departmentManagement.editDepartmentId = department.id
  departmentManagement.form = {
    name: department.name,
    parent_id: department.parent_id,
    description: department.description || '',
    sort_order: department.sort_order || 0
  }
  departmentManagement.modalVisible = true
}

// 处理部门表单提交
const handleDepartmentFormSubmit = async () => {
  try {
    // 验证部门名称
    if (!departmentManagement.form.name.trim()) {
      notification.error({ message: '部门名称不能为空' })
      return
    }

    if (departmentManagement.form.name.trim().length < 2) {
      notification.error({ message: '部门名称至少2个字符' })
      return
    }

    departmentManagement.loading = true

    const formData = {
      name: departmentManagement.form.name.trim(),
      description: departmentManagement.form.description.trim() || undefined,
      parent_id: departmentManagement.form.parent_id || null,
      sort_order: departmentManagement.form.sort_order || 0
    }

    if (departmentManagement.editMode) {
      // 更新部门
      await departmentApi.updateDepartment(departmentManagement.editDepartmentId, {
        name: departmentManagement.form.name.trim(),
        description: departmentManagement.form.description.trim() || null,
        sort_order: departmentManagement.form.sort_order
      })
      notification.success({ message: '部门更新成功' })
    } else {
      // 创建部门
      await departmentApi.createDepartment({
        name: departmentManagement.form.name.trim(),
        parent_id: departmentManagement.form.parent_id || null,
        description: departmentManagement.form.description.trim() || null,
        sort_order: departmentManagement.form.sort_order
      })
      notification.success({ message: '部门创建成功' })
    }

    // 重新获取部门列表
    await fetchDepartments()
    departmentManagement.modalVisible = false
  } catch (error) {
    console.error('部门操作失败:', error)
    notification.error({
      message: '操作失败',
      description: error.message || '请稍后重试'
    })
  } finally {
    departmentManagement.loading = false
  }
}

// 删除部门
const confirmDeleteDepartment = (department) => {
  Modal.confirm({
    title: '确认删除部门',
    content: `确定要删除部门 "${department.name}" 吗？此操作不可撤销。部门下必须没有用户才能删除。`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      try {
        departmentManagement.loading = true
        await departmentApi.deleteDepartment(department.id)
        notification.success({ message: '部门删除成功' })
        // 重新获取部门列表
        await fetchDepartments()
      } catch (error) {
        console.error('删除部门失败:', error)
        notification.error({
          message: '删除失败',
          description: error.message || '请稍后重试'
        })
      } finally {
        departmentManagement.loading = false
      }
    }
  })
}

// 在组件挂载时获取部门列表
onMounted(() => {
  fetchDepartments()
})
</script>

<style lang="less" scoped>
.department-management {
  margin-top: 12px;
  min-height: 50vh;

  .header-section {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;

    .header-content {
      flex: 1;

      .description {
        font-size: 14px;
        color: var(--gray-600);
        margin: 0;
        line-height: 1.4;
      }
    }
  }

  .content-section {
    overflow: hidden;

    .error-message {
      padding: 16px 24px;
    }

    .empty-state {
      padding: 60px 20px;
      text-align: center;
    }

    .department-table {
      :deep(.ant-table-thead > tr > th) {
        background: var(--gray-50);
        font-weight: 500;
        padding: 8px 12px;
      }

      :deep(.ant-table-tbody > tr > td) {
        padding: 8px 12px;
      }

      .department-name {
        display: flex;
        align-items: center;
        
        .level-indent {
          display: inline-block;
          width: 24px;
        }
        
        .level-indicator {
          color: var(--gray-400);
          margin-right: 8px;
          font-size: 12px;
        }
        
        .name-text {
          font-weight: 500;
          color: var(--gray-900);
        }
        
        .level-tag {
          margin-left: 8px;
          font-size: 11px;
          padding: 0 6px;
          line-height: 18px;
        }
      }

      .description-text {
        color: var(--gray-600);
      }

      .action-btn {
        padding: 4px 8px;
        border-radius: 6px;
        transition: all 0.2s ease;

        &:hover {
          background: var(--gray-25);
        }
      }
    }
  }
}

.department-modal {
  :deep(.ant-modal-header) {
    padding: 20px 24px;
    border-bottom: 1px solid var(--gray-150);

    .ant-modal-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--gray-900);
    }
  }

  :deep(.ant-modal-body) {
    padding: 24px;
  }

  .department-form {
    .form-item {
      margin-bottom: 20px;

      :deep(.ant-form-item-label) {
        padding-bottom: 4px;

        label {
          font-weight: 500;
          color: var(--gray-900);
        }
      }
    }
  }

  .error-text {
    color: var(--color-error-500);
    font-size: 12px;
    margin-top: 4px;
    line-height: 1.3;
  }

  .help-text {
    color: var(--gray-600);
    font-size: 12px;
    margin-top: 4px;
    line-height: 1.3;
  }
}
</style>
