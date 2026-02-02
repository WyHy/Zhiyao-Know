<template>
  <div class="user-management">
    <!-- 头部区域 -->
    <div class="header-section">
      <div class="header-content">
        <h3 class="title">用户管理</h3>
        <p class="description">管理系统用户，请谨慎操作。删除用户后该用户将无法登录系统。</p>
      </div>
      <a-button type="primary" @click="showAddUserModal" class="add-btn">
        <template #icon><PlusOutlined /></template>
        添加用户
      </a-button>
    </div>

    <!-- 搜索和筛选区域 -->
    <div class="filter-section">
      <a-space size="middle" wrap>
        <!-- 搜索框 -->
        <a-input-search
          v-model:value="filterState.searchKeyword"
          placeholder="搜索用户名、ID或手机号"
          style="width: 280px"
          size="large"
          allow-clear
          @search="handleSearch"
        >
          <template #prefix>
            <SearchOutlined />
          </template>
        </a-input-search>

        <!-- 角色筛选 -->
        <a-select
          v-model:value="filterState.roleFilter"
          placeholder="筛选角色"
          style="width: 150px"
          size="large"
          allow-clear
          @change="handleFilter"
        >
          <a-select-option value="">全部角色</a-select-option>
          <a-select-option value="superadmin">超级管理员</a-select-option>
          <a-select-option value="admin">管理员</a-select-option>
          <a-select-option value="user">普通用户</a-select-option>
        </a-select>

        <!-- 部门筛选 -->
        <a-tree-select
          v-if="userStore.isSuperAdmin"
          v-model:value="filterState.departmentFilter"
          :tree-data="departmentTreeData"
          placeholder="筛选部门"
          style="width: 200px"
          size="large"
          allow-clear
          :field-names="{ label: 'name', value: 'id', children: 'children' }"
          @change="handleFilter"
        />

        <!-- 重置按钮 -->
        <a-button @click="resetFilters" size="large">
          重置
        </a-button>
      </a-space>
    </div>

    <!-- 主内容区域 - 表格 -->
    <div class="content-section">
      <a-spin :spinning="userManagement.loading">
        <div v-if="userManagement.error" class="error-message">
          <a-alert type="error" :message="userManagement.error" show-icon />
        </div>

        <a-table
          :dataSource="filteredUsers"
          :columns="columns"
          :rowKey="(record) => record.id"
          :pagination="{
            total: filteredUsers.length,
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个用户`
          }"
          class="user-table"
        >
          <template #bodyCell="{ column, record }">
            <!-- 用户信息列 -->
            <template v-if="column.key === 'user'">
              <div class="user-cell">
                <div class="user-avatar-small">
                  <img
                    v-if="record.avatar"
                    :src="record.avatar"
                    :alt="record.username"
                    class="avatar-img"
                  />
                  <div v-else class="avatar-placeholder">
                    {{ record.username.charAt(0).toUpperCase() }}
                  </div>
                </div>
                <div class="user-info">
                  <div class="user-name">{{ record.username }}</div>
                  <div class="user-id-text">ID: {{ record.user_id }}</div>
                </div>
              </div>
            </template>

            <!-- 角色列 -->
            <template v-if="column.key === 'role'">
              <a-tag :color="getRoleColor(record.role)">
                <template #icon>
                  <UserLock v-if="record.role === 'superadmin'" :size="12" />
                  <UserStar v-else-if="record.role === 'admin'" :size="12" />
                  <User v-else :size="12" />
                </template>
                {{ getRoleText(record.role) }}
              </a-tag>
            </template>

            <!-- 部门列 -->
            <template v-if="column.key === 'department'">
              <span>{{ record.department_name || '-' }}</span>
            </template>

            <!-- 手机号列 -->
            <template v-if="column.key === 'phone'">
              <span>{{ record.phone_number || '-' }}</span>
            </template>

            <!-- 最后登录列 -->
            <template v-if="column.key === 'lastLogin'">
              <span class="time-text">{{ formatTime(record.last_login) }}</span>
            </template>

            <!-- 操作列 -->
            <template v-if="column.key === 'action'">
              <a-space>
                <a-tooltip title="编辑用户">
                  <a-button
                    type="link"
                    size="small"
                    @click="showEditUserModal(record)"
                  >
                    <EditOutlined />
                  </a-button>
                </a-tooltip>
                <a-tooltip title="删除用户">
                  <a-button
                    type="link"
                    size="small"
                    danger
                    @click="confirmDeleteUser(record)"
                    :disabled="
                      record.id === userStore.userId ||
                      (record.role === 'superadmin' && userStore.userRole !== 'superadmin')
                    "
                  >
                    <DeleteOutlined />
                  </a-button>
                </a-tooltip>
              </a-space>
            </template>
          </template>

          <template #emptyText>
            <a-empty description="暂无用户数据" />
          </template>
        </a-table>
      </a-spin>
    </div>

    <!-- 用户表单模态框 -->
    <a-modal
      v-model:open="userManagement.modalVisible"
      :title="userManagement.modalTitle"
      @ok="handleUserFormSubmit"
      :confirmLoading="userManagement.loading"
      @cancel="userManagement.modalVisible = false"
      :maskClosable="false"
      width="480px"
      class="user-modal"
    >
      <a-form layout="vertical" class="user-form">
        <a-form-item label="用户名" required class="form-item">
          <a-input
            v-model:value="userManagement.form.username"
            placeholder="请输入用户名（2-20个字符）"
            size="large"
            @blur="validateAndGenerateUserId"
            :maxlength="20"
          />
          <div v-if="userManagement.form.usernameError" class="error-text">
            {{ userManagement.form.usernameError }}
          </div>
        </a-form-item>

        <!-- 显示自动生成的用户ID -->
        <a-form-item
          v-if="userManagement.form.generatedUserId || userManagement.editMode"
          label="用户ID"
          class="form-item"
        >
          <a-input
            :value="userManagement.form.generatedUserId"
            placeholder="自动生成"
            size="large"
            disabled
            :addon-before="userManagement.editMode ? '已存在ID' : '登录ID'"
          />
          <div v-if="!userManagement.editMode" class="help-text">
            此ID将用于登录，根据用户名自动生成
          </div>
          <div v-else class="help-text">编辑模式下不能修改用户ID</div>
        </a-form-item>

        <!-- 手机号字段 -->
        <a-form-item label="手机号" class="form-item">
          <a-input
            v-model:value="userManagement.form.phoneNumber"
            placeholder="请输入手机号（可选，可用于登录）"
            size="large"
            :maxlength="11"
          />
          <div v-if="userManagement.form.phoneError" class="error-text">
            {{ userManagement.form.phoneError }}
          </div>
        </a-form-item>

        <template v-if="userManagement.editMode">
          <div class="password-toggle">
            <a-checkbox v-model:checked="userManagement.displayPasswordFields">
              修改密码
            </a-checkbox>
          </div>
        </template>

        <template v-if="!userManagement.editMode || userManagement.displayPasswordFields">
          <a-form-item label="密码" required class="form-item">
            <a-input-password
              v-model:value="userManagement.form.password"
              placeholder="请输入密码"
              size="large"
            />
          </a-form-item>

          <a-form-item label="确认密码" required class="form-item">
            <a-input-password
              v-model:value="userManagement.form.confirmPassword"
              placeholder="请再次输入密码"
              size="large"
            />
          </a-form-item>
        </template>

        <a-form-item
          v-if="userManagement.editMode && userManagement.form.role === 'superadmin'"
          label="角色"
          class="form-item"
        >
          <a-input value="超级管理员" size="large" disabled />
          <div class="help-text">超级管理员账户无法修改角色</div>
        </a-form-item>
        <a-form-item v-else label="角色" class="form-item">
          <a-select v-model:value="userManagement.form.role" size="large">
            <a-select-option value="user">普通用户</a-select-option>
            <a-select-option value="admin" v-if="userStore.isSuperAdmin">管理员</a-select-option>
          </a-select>
        </a-form-item>

        <!-- 部门选择器（仅超级管理员可见） -->
        <a-form-item v-if="userStore.isSuperAdmin" label="主部门" class="form-item">
          <a-tree-select
            v-model:value="userManagement.form.departmentId"
            :tree-data="departmentTreeData"
            placeholder="请选择主部门"
            allow-clear
            :field-names="{ label: 'name', value: 'id', children: 'children' }"
            tree-default-expand-all
            size="large"
          />
          <div class="help-text">用户的主要归属部门</div>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { reactive, onMounted, watch, computed } from 'vue'
import { notification, Modal } from 'ant-design-vue'
import { useUserStore } from '@/stores/user'
import { departmentApi } from '@/apis'
import { DeleteOutlined, EditOutlined, PlusOutlined, SearchOutlined } from '@ant-design/icons-vue'
import { User, UserLock, UserStar } from 'lucide-vue-next'
import { formatDateTime } from '@/utils/time'

const userStore = useUserStore()

// 表格列定义
const columns = [
  {
    title: '用户',
    key: 'user',
    width: 220,
    fixed: 'left'
  },
  {
    title: '角色',
    key: 'role',
    width: 120,
    filters: [
      { text: '超级管理员', value: 'superadmin' },
      { text: '管理员', value: 'admin' },
      { text: '普通用户', value: 'user' }
    ],
    onFilter: (value, record) => record.role === value
  },
  {
    title: '部门',
    key: 'department',
    width: 180,
    ellipsis: true
  },
  {
    title: '手机号',
    key: 'phone',
    width: 130
  },
  {
    title: '最后登录',
    key: 'lastLogin',
    width: 180,
    sorter: (a, b) => {
      const timeA = a.last_login ? new Date(a.last_login).getTime() : 0
      const timeB = b.last_login ? new Date(b.last_login).getTime() : 0
      return timeA - timeB
    }
  },
  {
    title: '操作',
    key: 'action',
    width: 100,
    fixed: 'right',
    align: 'center'
  }
]

// 筛选状态
const filterState = reactive({
  searchKeyword: '',
  roleFilter: '',
  departmentFilter: null
})

// 用户管理相关状态
const userManagement = reactive({
  loading: false,
  users: [],
  error: null,
  modalVisible: false,
  modalTitle: '添加用户',
  editMode: false,
  editUserId: null,
  form: {
    username: '',
    generatedUserId: '', // 自动生成的user_id
    phoneNumber: '', // 手机号
    password: '',
    confirmPassword: '',
    role: 'user', // 默认角色
    departmentId: null, // 部门ID
    usernameError: '', // 用户名错误信息
    phoneError: '' // 手机号错误信息
  },
  displayPasswordFields: true // 编辑时是否显示密码字段
})

// 部门列表（仅超级管理员使用）
const departmentManagement = reactive({
  departments: [],
  departmentTree: [] // 存储树形数据
})

// 计算属性：用于树形选择器的数据
const departmentTreeData = computed(() => {
  return departmentManagement.departmentTree
})

// 计算属性：筛选后的用户列表
const filteredUsers = computed(() => {
  let users = userManagement.users

  // 搜索关键词筛选
  if (filterState.searchKeyword) {
    const keyword = filterState.searchKeyword.toLowerCase()
    users = users.filter((user) => {
      return (
        user.username?.toLowerCase().includes(keyword) ||
        user.user_id?.toLowerCase().includes(keyword) ||
        user.phone_number?.includes(keyword)
      )
    })
  }

  // 角色筛选
  if (filterState.roleFilter) {
    users = users.filter((user) => user.role === filterState.roleFilter)
  }

  // 部门筛选
  if (filterState.departmentFilter) {
    users = users.filter((user) => user.department_id === filterState.departmentFilter)
  }

  return users
})

// 获取部门列表
const fetchDepartments = async () => {
  if (!userStore.isSuperAdmin) return // 普通管理员不需要获取所有部门列表
  try {
    const response = await departmentApi.getDepartments()
    // 后端返回格式: { success: true, data: [...] }
    const treeData = response.data || response
    
    // 保存原始树形数据
    departmentManagement.departmentTree = treeData
    
    // 同时也保存扁平化列表（如果其他地方需要）
    departmentManagement.departments = flattenDepartments(treeData)
  } catch (error) {
    console.error('获取部门列表失败:', error)
  }
}

// 扁平化部门树（辅助函数）
const flattenDepartments = (tree) => {
  const result = []
  tree.forEach((node) => {
    result.push(node)
    if (node.children && node.children.length > 0) {
      result.push(...flattenDepartments(node.children))
    }
  })
  return result
}

// 添加验证用户名并生成user_id的函数
const validateAndGenerateUserId = async () => {
  const username = userManagement.form.username.trim()

  // 清空之前的错误和生成的ID
  userManagement.form.usernameError = ''
  userManagement.form.generatedUserId = ''

  if (!username) {
    return
  }

  // 在编辑模式下，不需要重新生成user_id
  if (userManagement.editMode) {
    return
  }

  try {
    const result = await userStore.validateUsernameAndGenerateUserId(username)
    userManagement.form.generatedUserId = result.user_id
  } catch (error) {
    userManagement.form.usernameError = error.message || '用户名验证失败'
  }
}

// 验证手机号格式
const validatePhoneNumber = (phone) => {
  if (!phone) {
    return true // 手机号可选
  }

  // 中国大陆手机号格式验证
  const phoneRegex = /^1[3-9]\d{9}$/
  return phoneRegex.test(phone)
}

// 监听密码字段显示状态变化
watch(
  () => userManagement.displayPasswordFields,
  (newVal) => {
    // 当取消显示密码字段时，清空密码输入
    if (!newVal) {
      userManagement.form.password = ''
      userManagement.form.confirmPassword = ''
    }
  }
)

// 监听手机号输入变化
watch(
  () => userManagement.form.phoneNumber,
  (newPhone) => {
    userManagement.form.phoneError = ''

    if (newPhone && !validatePhoneNumber(newPhone)) {
      userManagement.form.phoneError = '请输入正确的手机号格式'
    }
  }
)

// 格式化时间显示
const formatTime = (timeStr) => formatDateTime(timeStr)

// 获取用户列表
const fetchUsers = async () => {
  try {
    userManagement.loading = true
    const users = await userStore.getUsers()
    userManagement.users = users
    userManagement.error = null
  } catch (error) {
    console.error('获取用户列表失败:', error)
    userManagement.error = '获取用户列表失败'
  } finally {
    userManagement.loading = false
  }
}

// 打开添加用户模态框
const showAddUserModal = () => {
  userManagement.modalTitle = '添加用户'
  userManagement.editMode = false
  userManagement.editUserId = null
  userManagement.form = {
    username: '',
    generatedUserId: '',
    phoneNumber: '',
    password: '',
    confirmPassword: '',
    role: 'user', // 默认角色为普通用户
    departmentId: null,
    usernameError: '',
    phoneError: ''
  }
  userManagement.displayPasswordFields = true
  userManagement.modalVisible = true
}

// 打开编辑用户模态框
const showEditUserModal = (user) => {
  userManagement.modalTitle = '编辑用户'
  userManagement.editMode = true
  userManagement.editUserId = user.id
  userManagement.form = {
    username: user.username,
    generatedUserId: user.user_id || '', // 编辑模式显示现有的user_id
    phoneNumber: user.phone_number || '',
    password: '',
    confirmPassword: '',
    role: user.role,
    departmentId: user.department_id || null,
    usernameError: '',
    phoneError: ''
  }
  userManagement.displayPasswordFields = false // 默认不显示密码字段
  userManagement.modalVisible = true
}

// 处理用户表单提交
const handleUserFormSubmit = async () => {
  try {
    // 简单验证
    if (!userManagement.form.username.trim()) {
      notification.error({ message: '用户名不能为空' })
      return
    }

    // 验证用户名长度
    if (
      userManagement.form.username.trim().length < 2 ||
      userManagement.form.username.trim().length > 20
    ) {
      notification.error({ message: '用户名长度必须在 2-20 个字符之间' })
      return
    }

    // 验证手机号
    if (userManagement.form.phoneNumber && !validatePhoneNumber(userManagement.form.phoneNumber)) {
      notification.error({ message: '请输入正确的手机号格式' })
      return
    }

    if (userManagement.displayPasswordFields) {
      if (!userManagement.form.password) {
        notification.error({ message: '密码不能为空' })
        return
      }

      if (userManagement.form.password !== userManagement.form.confirmPassword) {
        notification.error({ message: '两次输入的密码不一致' })
        return
      }
    }

    userManagement.loading = true

    // 根据模式决定创建还是更新用户
    if (userManagement.editMode) {
      // 创建更新数据对象
      const updateData = {
        username: userManagement.form.username.trim(),
        role: userManagement.form.role
      }

      // 添加手机号字段
      if (userManagement.form.phoneNumber) {
        updateData.phone_number = userManagement.form.phoneNumber
      }

      // 超级管理员可以修改部门
      if (userStore.isSuperAdmin && userManagement.form.departmentId) {
        updateData.department_id = userManagement.form.departmentId
      }

      // 如果显示了密码字段并且填写了密码，才更新密码
      if (userManagement.displayPasswordFields && userManagement.form.password) {
        updateData.password = userManagement.form.password
      }

      await userStore.updateUser(userManagement.editUserId, updateData)
      notification.success({ message: '用户更新成功' })
    } else {
      // 创建新用户
      const createData = {
        username: userManagement.form.username.trim(),
        password: userManagement.form.password,
        role: userManagement.form.role
      }

      // 超级管理员可以指定部门
      if (userStore.isSuperAdmin && userManagement.form.departmentId) {
        createData.department_id = userManagement.form.departmentId
      }

      // 添加手机号字段（如果填写了）
      if (userManagement.form.phoneNumber) {
        createData.phone_number = userManagement.form.phoneNumber
      }

      await userStore.createUser(createData)
      notification.success({ message: '用户创建成功' })
    }

    // 重新获取用户列表
    await fetchUsers()
    userManagement.modalVisible = false
  } catch (error) {
    console.error('用户操作失败:', error)
    notification.error({
      message: '操作失败',
      description: error.message || '请稍后重试'
    })
  } finally {
    userManagement.loading = false
  }
}

// 删除用户
const confirmDeleteUser = (user) => {
  // 自己不能删除自己
  if (user.id === userStore.userId) {
    notification.error({ message: '不能删除自己的账户' })
    return
  }

  // 确认对话框
  Modal.confirm({
    title: '确认删除用户',
    content: `确定要删除用户 "${user.username}" 吗？此操作不可撤销。`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      try {
        userManagement.loading = true
        await userStore.deleteUser(user.id)
        notification.success({ message: '用户删除成功' })
        // 重新获取用户列表
        await fetchUsers()
      } catch (error) {
        console.error('删除用户失败:', error)
        notification.error({
          message: '删除失败',
          description: error.message || '请稍后重试'
        })
      } finally {
        userManagement.loading = false
      }
    }
  })
}

// 搜索处理
const handleSearch = () => {
  // 搜索逻辑已在 computed 中处理
}

// 筛选处理
const handleFilter = () => {
  // 筛选逻辑已在 computed 中处理
}

// 重置筛选
const resetFilters = () => {
  filterState.searchKeyword = ''
  filterState.roleFilter = ''
  filterState.departmentFilter = null
}

// 角色相关辅助函数
const getRoleText = (role) => {
  const roleMap = {
    superadmin: '超级管理员',
    admin: '管理员',
    user: '普通用户'
  }
  return roleMap[role] || role
}

const getRoleColor = (role) => {
  const colorMap = {
    superadmin: 'red',
    admin: 'blue',
    user: 'default'
  }
  return colorMap[role] || 'default'
}

// 在组件挂载时获取用户列表
onMounted(async () => {
  await fetchUsers()
  await fetchDepartments()
})
</script>

<style lang="less" scoped>
.user-management {
  margin-top: 12px;
  min-height: 50vh;

  .header-section {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;

    .header-content {
      flex: 1;

      .description {
        font-size: 14px;
        color: var(--gray-600);
        margin: 0;
        line-height: 1.4;
        margin-bottom: 16px;
      }
    }
  }

  .content-section {
    overflow: hidden;

    .error-message {
      padding: 16px 24px;
    }

    .cards-container {
      .empty-state {
        padding: 60px 20px;
        text-align: center;
      }

      .user-cards-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 16px;
        // padding: 16px;

        .user-card {
          background: var(--gray-0);
          border: 1px solid var(--gray-150);
          border-radius: 8px;
          padding: 12px;
          padding-bottom: 6px;

          transition: all 0.2s ease;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

          &:hover {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            border-color: var(--gray-200);
          }

          .card-header {
            margin-bottom: 10px;

            .user-info-main {
              display: flex;
              gap: 12px;
              align-items: center;

              .user-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: var(--gray-50);
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
                flex-shrink: 0;

                .avatar-img {
                  width: 100%;
                  height: 100%;
                  object-fit: cover;
                }

                .avatar-placeholder {
                  color: var(--gray-600);
                  font-weight: 500;
                  font-size: 14px;
                }
              }

              .user-info-content {
                flex: 1;
                min-width: 0;

                .name-tag-row {
                  display: flex;
                  align-items: center;
                  justify-content: space-between;
                  gap: 8px;
                  margin-bottom: 2px;
                  flex-wrap: wrap;

                  .username {
                    margin: 0;
                    font-size: 15px;
                    font-weight: 600;
                    color: var(--gray-900);
                    line-height: 1.2;
                    flex-shrink: 0;
                  }

                  .role-dept-badge {
                    display: inline-flex;
                    align-items: center;
                    gap: 4px;
                    padding: 2px 8px 2px 4px;
                    background: var(--gray-50);
                    border-radius: 4px;

                    .role-icon-wrapper {
                      display: flex;
                      align-items: center;
                      justify-content: center;
                      width: 16px;
                      height: 16px;

                      &.role-superadmin {
                        color: var(--color-error-700);
                      }
                      &.role-admin {
                        color: var(--color-info-700);
                      }
                      &.role-user {
                        color: var(--color-success-700);
                      }
                    }

                    .dept-text {
                      font-size: 12px;
                      color: var(--gray-700);
                      font-weight: 500;
                    }
                  }
                }

                .user-id-row {
                  font-size: 12px;
                  color: var(--gray-500);
                  font-family: 'Monaco', 'Consolas', monospace;
                  line-height: 1.2;
                }
              }
            }
          }

          .card-content {
            .info-item {
              display: flex;
              justify-content: space-between;
              align-items: center;
              padding: 2px 0;
              border-bottom: 1px solid var(--gray-25);

              &:last-child {
                border-bottom: none;
              }

              .info-label {
                font-size: 12px;
                color: var(--gray-600);
                font-weight: 500;
                min-width: 70px;
              }

              .info-value {
                font-size: 12px;
                color: var(--gray-900);
                text-align: right;
                flex: 1;

                &.time-text {
                  color: var(--gray-700);
                }

                &.phone-text {
                  font-family: 'Monaco', 'Consolas', monospace;
                }
              }
            }
          }

          .card-actions {
            display: flex;
            justify-content: flex-end;
            gap: 6px;
            padding-top: 6px;
            border-top: 1px solid var(--gray-25);

            .action-btn {
              display: flex;
              align-items: center;
              gap: 4px;
              padding: 4px 8px;
              border-radius: 6px;
              transition: all 0.2s ease;
              font-size: 12px;

              span {
                font-size: 12px;
              }

              &:hover {
                background: var(--gray-25);
              }

              &.ant-btn-dangerous:hover {
                background: var(--gray-25);
                border-color: var(--color-error-500);
                color: var(--color-error-500);
              }
            }
          }
        }
      }
    }
  }

  .time-text {
    font-size: 13px;
    color: var(--gray-700);
  }

  .phone-text,
  .user-id-text {
    font-size: 13px;
    color: var(--gray-900);
    font-family: 'Monaco', 'Consolas', monospace;
  }

  // 新增：筛选区域样式
  .filter-section {
    margin-bottom: 16px;
    padding: 16px;
    background: var(--gray-0);
    border: 1px solid var(--gray-150);
    border-radius: 8px;
  }

  // 新增：表格样式
  .user-table {
    :deep(.ant-table) {
      background: var(--gray-0);
    }

    :deep(.ant-table-thead > tr > th) {
      background: var(--gray-50);
      font-weight: 500;
      padding: 12px 16px;
      border-bottom: 2px solid var(--gray-200);
    }

    :deep(.ant-table-tbody > tr > td) {
      padding: 12px 16px;
    }

    :deep(.ant-table-tbody > tr:hover > td) {
      background: var(--gray-25);
    }

    .user-cell {
      display: flex;
      align-items: center;
      gap: 12px;

      .user-avatar-small {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        overflow: hidden;
        flex-shrink: 0;

        .avatar-img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .avatar-placeholder {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--color-primary-100);
          color: var(--color-primary-600);
          font-weight: 600;
          font-size: 16px;
        }
      }

      .user-info {
        flex: 1;
        min-width: 0;

        .user-name {
          font-weight: 500;
          color: var(--gray-900);
          font-size: 14px;
          margin-bottom: 2px;
        }

        .user-id-text {
          font-size: 12px;
          color: var(--gray-500);
        }
      }
    }
  }
}

.user-modal {
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

  .user-form {
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

    .password-toggle {
      margin-bottom: 16px;

      :deep(.ant-checkbox-wrapper) {
        font-weight: 500;
        color: var(--gray-600);
      }
    }
  }
}
</style>
