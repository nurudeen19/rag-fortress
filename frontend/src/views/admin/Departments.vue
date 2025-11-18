<template>
  <div class="min-h-screen bg-fortress-950 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-fortress-100 mb-2">Departments Management</h1>
        <p class="text-fortress-400">Create, edit, and manage departments and their assignments</p>
      </div>

      <!-- Notifications -->
      <div v-if="notification.show" class="mb-4 p-4 rounded-lg" :class="notification.type === 'success' ? 'bg-secure/10 text-secure border border-secure/30' : 'bg-alert/10 text-alert border border-alert/30'">
        {{ notification.message }}
      </div>

      <!-- Create Department Button -->
      <div class="mb-6 flex justify-between items-center">
        <h2 class="text-xl font-semibold text-fortress-100">Departments</h2>
        <button
          @click="showCreateForm = true"
          class="btn btn-primary"
        >
          + Create Department
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12">
        <p class="text-fortress-400">Loading departments...</p>
      </div>

      <!-- Departments Table -->
      <div v-else-if="departments.length > 0" class="bg-fortress-900 rounded-lg border border-fortress-700 overflow-hidden">
        <table class="w-full">
          <thead class="bg-fortress-800 border-b border-fortress-700">
            <tr>
              <th class="px-6 py-3 text-left text-sm font-semibold text-fortress-200">Name</th>
              <th class="px-6 py-3 text-left text-sm font-semibold text-fortress-200">Code</th>
              <th class="px-6 py-3 text-left text-sm font-semibold text-fortress-200">Manager</th>
              <th class="px-6 py-3 text-left text-sm font-semibold text-fortress-200">Members</th>
              <th class="px-6 py-3 text-left text-sm font-semibold text-fortress-200">Status</th>
              <th class="px-6 py-3 text-right text-sm font-semibold text-fortress-200">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-fortress-700">
            <tr v-for="dept in departments" :key="dept.id" class="hover:bg-fortress-800/50 transition-colors">
              <td class="px-6 py-4 text-sm text-fortress-100">
                <div class="font-medium">{{ dept.name }}</div>
                <p v-if="dept.description" class="text-xs text-fortress-400 mt-1">{{ dept.description }}</p>
              </td>
              <td class="px-6 py-4 text-sm text-fortress-300">{{ dept.code }}</td>
              <td class="px-6 py-4 text-sm text-fortress-300">
                {{ dept.manager_name || 'Unassigned' }}
              </td>
              <td class="px-6 py-4 text-sm text-fortress-300">
                <button
                  @click="openMembersModal(dept)"
                  class="text-secure hover:underline"
                >
                  View Members
                </button>
              </td>
              <td class="px-6 py-4 text-sm">
                <span :class="dept.is_active ? 'text-secure' : 'text-fortress-400'">
                  {{ dept.is_active ? 'Active' : 'Inactive' }}
                </span>
              </td>
              <td class="px-6 py-4 text-sm text-right space-x-2">
                <button
                  @click="editDept = dept; showEditForm = true"
                  class="text-secure hover:text-secure/80 transition-colors"
                  title="Edit"
                >
                  Edit
                </button>
                <button
                  @click="setManagerModal(dept)"
                  class="text-fortress-400 hover:text-fortress-300 transition-colors"
                  title="Set Manager"
                >
                  Set Manager
                </button>
                <button
                  @click="deleteDept(dept.id)"
                  class="text-alert hover:text-alert/80 transition-colors"
                  title="Delete"
                >
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Empty State -->
      <div v-else class="bg-fortress-900 rounded-lg border border-fortress-700 p-12 text-center">
        <p class="text-fortress-400 mb-4">No departments created yet</p>
        <button
          @click="showCreateForm = true"
          class="btn btn-primary"
        >
          Create First Department
        </button>
      </div>

      <!-- Create Department Modal -->
      <div v-if="showCreateForm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div class="bg-fortress-900 rounded-lg max-w-md w-full border border-fortress-700">
          <div class="p-6 border-b border-fortress-700">
            <h3 class="text-xl font-bold text-fortress-100">Create Department</h3>
          </div>
          <div class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-fortress-300 mb-2">
                Department Name <span class="text-alert">*</span>
              </label>
              <input
                v-model="formData.name"
                type="text"
                placeholder="e.g., Engineering"
                class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure outline-none transition-colors"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-fortress-300 mb-2">
                Department Code <span class="text-alert">*</span>
              </label>
              <input
                v-model="formData.code"
                type="text"
                placeholder="e.g., ENG"
                class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure outline-none transition-colors"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-fortress-300 mb-2">
                Description
              </label>
              <textarea
                v-model="formData.description"
                placeholder="Optional description..."
                class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure outline-none transition-colors resize-none"
                rows="3"
              />
            </div>
          </div>
          <div class="p-6 border-t border-fortress-700 flex justify-end gap-2">
            <button
              @click="showCreateForm = false; formData = {}"
              class="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              @click="createDept"
              :disabled="!formData.name || !formData.code"
              class="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Create
            </button>
          </div>
        </div>
      </div>

      <!-- Edit Department Modal -->
      <div v-if="showEditForm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div class="bg-fortress-900 rounded-lg max-w-md w-full border border-fortress-700">
          <div class="p-6 border-b border-fortress-700">
            <h3 class="text-xl font-bold text-fortress-100">Edit Department</h3>
          </div>
          <div class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-fortress-300 mb-2">
                Department Name <span class="text-alert">*</span>
              </label>
              <input
                v-model="editDept.name"
                type="text"
                class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure outline-none transition-colors"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-fortress-300 mb-2">
                Department Code <span class="text-alert">*</span>
              </label>
              <input
                v-model="editDept.code"
                type="text"
                class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure outline-none transition-colors"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-fortress-300 mb-2">
                Description
              </label>
              <textarea
                v-model="editDept.description"
                class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 placeholder-fortress-500 focus:border-secure outline-none transition-colors resize-none"
                rows="3"
              />
            </div>
            <div class="flex items-center gap-3">
              <input
                v-model="editDept.is_active"
                type="checkbox"
                id="edit-active"
                class="w-4 h-4 rounded border-fortress-600 bg-fortress-800 text-secure focus:ring-secure cursor-pointer"
              />
              <label for="edit-active" class="text-sm text-fortress-300 cursor-pointer">
                Active
              </label>
            </div>
          </div>
          <div class="p-6 border-t border-fortress-700 flex justify-end gap-2">
            <button
              @click="showEditForm = false; editDept = {}"
              class="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              @click="updateDept"
              :disabled="!editDept.name || !editDept.code"
              class="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Save Changes
            </button>
          </div>
        </div>
      </div>

      <!-- Set Manager Modal -->
      <div v-if="showManagerModal && managerDept" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div class="bg-fortress-900 rounded-lg max-w-md w-full border border-fortress-700">
          <div class="p-6 border-b border-fortress-700">
            <h3 class="text-xl font-bold text-fortress-100">Set Manager for {{ managerDept.name }}</h3>
          </div>
          <div class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-medium text-fortress-300 mb-2">
                Select Manager
              </label>
              <select
                v-model="selectedManagerId"
                class="w-full px-3 py-2 bg-fortress-800 border border-fortress-700 rounded-lg text-fortress-100 focus:border-secure outline-none transition-colors"
              >
                <option value="">Remove Manager</option>
                <option
                  v-for="user in availableUsers"
                  :key="user.id"
                  :value="user.id"
                >
                  {{ user.email }}
                </option>
              </select>
            </div>
          </div>
          <div class="p-6 border-t border-fortress-700 flex justify-end gap-2">
            <button
              @click="showManagerModal = false; managerDept = null"
              class="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              @click="setManager"
              class="btn btn-primary"
            >
              Save
            </button>
          </div>
        </div>
      </div>

      <!-- Members Modal -->
      <div v-if="showMembersModal && selectedDept" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div class="bg-fortress-900 rounded-lg max-w-2xl w-full border border-fortress-700 max-h-[80vh] overflow-y-auto">
          <div class="p-6 border-b border-fortress-700 sticky top-0 bg-fortress-900">
            <h3 class="text-xl font-bold text-fortress-100">Members of {{ selectedDept.name }}</h3>
          </div>
          <div class="p-6">
            <div v-if="deptMembers.length > 0" class="space-y-2">
              <div
                v-for="member in deptMembers"
                :key="member.id"
                class="flex items-center justify-between p-3 bg-fortress-800 rounded-lg"
              >
                <div>
                  <p class="text-fortress-100 font-medium">{{ member.email }}</p>
                  <p class="text-xs text-fortress-400">{{ member.full_name || 'No name' }}</p>
                </div>
                <button
                  @click="removeMember(selectedDept.id, member.id)"
                  class="text-alert hover:text-alert/80 transition-colors text-sm"
                >
                  Remove
                </button>
              </div>
            </div>
            <p v-else class="text-fortress-400 text-center py-8">No members in this department</p>
          </div>
          <div class="p-6 border-t border-fortress-700 flex justify-end">
            <button
              @click="closeMembersModal"
              class="btn btn-secondary"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../services/api'

const departments = ref([])
const availableUsers = ref([])
const deptMembers = ref([])
const loading = ref(false)
const showCreateForm = ref(false)
const showEditForm = ref(false)
const showManagerModal = ref(false)
const showMembersModal = ref(false)
const notification = ref({ show: false, message: '', type: 'success' })
const formData = ref({})
const editDept = ref({})
const selectedDept = ref(null)
const managerDept = ref(null)
const selectedManagerId = ref('')

onMounted(async () => {
  await loadDepartments()
  await loadUsers()
})

async function loadDepartments() {
  loading.value = true
  try {
    const response = await api.get('/v1/admin/departments')
    departments.value = response.departments || []
  } catch (err) {
    showNotification('Failed to load departments', 'error')
  } finally {
    loading.value = false
  }
}

async function loadUsers() {
  try {
    const response = await api.get('/v1/admin/users?limit=1000')
    availableUsers.value = response.users || []
  } catch (err) {
    console.error('Failed to load users:', err)
  }
}

async function createDept() {
  try {
    await api.post('/v1/admin/departments', {
      name: formData.value.name,
      code: formData.value.code,
      description: formData.value.description || null
    })
    showNotification(`Department "${formData.value.name}" created successfully`, 'success')
    showCreateForm.value = false
    formData.value = {}
    await loadDepartments()
  } catch (err) {
    showNotification(err.response?.data?.detail || 'Failed to create department', 'error')
  }
}

async function updateDept() {
  try {
    await api.put(`/v1/admin/departments/${editDept.value.id}`, {
      name: editDept.value.name,
      code: editDept.value.code,
      description: editDept.value.description || null,
      is_active: editDept.value.is_active
    })
    showNotification('Department updated successfully', 'success')
    showEditForm.value = false
    editDept.value = {}
    await loadDepartments()
  } catch (err) {
    showNotification(err.response?.data?.detail || 'Failed to update department', 'error')
  }
}

async function deleteDept(deptId) {
  if (!confirm('Are you sure you want to delete this department?')) return
  
  try {
    await api.delete(`/v1/admin/departments/${deptId}`)
    showNotification('Department deleted successfully', 'success')
    await loadDepartments()
  } catch (err) {
    showNotification(err.response?.data?.detail || 'Failed to delete department', 'error')
  }
}

function setManagerModal(dept) {
  managerDept.value = dept
  selectedManagerId.value = dept.manager_id || ''
  showManagerModal.value = true
}

async function setManager() {
  try {
    if (selectedManagerId.value) {
      await api.post(`/v1/admin/departments/${managerDept.value.id}/manager`, {
        user_id: parseInt(selectedManagerId.value)
      })
    } else {
      await api.delete(`/v1/admin/departments/${managerDept.value.id}/manager`)
    }
    showNotification('Manager updated successfully', 'success')
    showManagerModal.value = false
    managerDept.value = null
    await loadDepartments()
  } catch (err) {
    showNotification(err.response?.data?.detail || 'Failed to update manager', 'error')
  }
}

async function loadDeptMembers(deptId) {
  try {
    const response = await api.get(`/v1/admin/departments/${deptId}/users`)
    deptMembers.value = response.users || []
  } catch (err) {
    showNotification('Failed to load department members', 'error')
  }
}

async function removeMember(deptId, userId) {
  if (!confirm('Are you sure you want to remove this member?')) return
  
  try {
    await api.delete(`/v1/admin/departments/${deptId}/users/${userId}`)
    showNotification('Member removed successfully', 'success')
    await loadDeptMembers(deptId)
  } catch (err) {
    showNotification(err.response?.data?.detail || 'Failed to remove member', 'error')
  }
}

function closeMembersModal() {
  showMembersModal.value = false
  selectedDept.value = null
  deptMembers.value = []
}

async function openMembersModal(dept) {
  selectedDept.value = dept
  showMembersModal.value = true
  await loadDeptMembers(dept.id)
}

function showNotification(message, type = 'success') {
  notification.value = { show: true, message, type }
  setTimeout(() => {
    notification.value.show = false
  }, 3000)
}
</script>
