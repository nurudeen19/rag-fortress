<template>
  <div class="min-h-screen bg-fortress-950">
    <!-- Top Navigation Bar -->
    <nav class="bg-fortress-900 border-b border-fortress-800 fixed top-0 left-0 right-0 z-50">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <!-- Left: Logo & Back Button -->
          <div class="flex items-center space-x-3">
            <button
              @click="exitChatMode"
              class="p-2 rounded-lg text-fortress-400 hover:text-fortress-100 hover:bg-fortress-800 transition-colors lg:hidden"
              title="Back to main navigation"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <div class="flex items-center space-x-2">
              <svg class="w-5 h-5 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <span class="text-lg font-semibold text-fortress-100 hidden sm:inline">Conversations</span>
            </div>
          </div>

          <!-- Right: User Menu & Settings -->
          <div class="flex items-center space-x-4">
            <!-- Chat Settings Button -->
            <button
              @click="chatSettingsOpen = !chatSettingsOpen"
              class="p-2 rounded-lg text-fortress-400 hover:text-fortress-100 hover:bg-fortress-800 transition-colors relative"
              title="Chat settings"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>

            <!-- User Menu -->
            <div class="relative" v-if="authStore.user">
              <button
                @click="userMenuOpen = !userMenuOpen"
                class="flex items-center space-x-2 p-2 rounded-lg hover:bg-fortress-800 transition-colors"
              >
                <div class="w-8 h-8 bg-secure/20 border border-secure/30 rounded-full flex items-center justify-center">
                  <span class="text-sm font-medium text-secure">{{ userInitials }}</span>
                </div>
                <svg class="w-4 h-4 text-fortress-400 hidden sm:block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              <!-- User Dropdown Menu -->
              <div
                v-show="userMenuOpen"
                @click.self="userMenuOpen = false"
                class="absolute right-0 mt-2 w-56 bg-fortress-900 border border-fortress-800 rounded-lg shadow-glow overflow-hidden animate-fade-in"
              >
                <div class="p-4 border-b border-fortress-800">
                  <p class="text-sm font-medium text-fortress-100">{{ authStore.fullName }}</p>
                  <p class="text-xs text-fortress-400 mt-1">{{ authStore.user.email }}</p>
                </div>
                <div class="p-2">
                  <router-link
                    to="/profile"
                    @click="userMenuOpen = false"
                    class="block px-4 py-2 text-sm text-fortress-300 hover:bg-fortress-800 hover:text-fortress-100 rounded-lg transition-colors"
                  >
                    <svg class="w-4 h-4 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    Profile
                  </router-link>
                </div>
                <div class="border-t border-fortress-800 p-2">
                  <button
                    @click="handleLogout"
                    class="w-full text-left px-4 py-2 text-sm text-alert hover:bg-alert/10 hover:text-alert-light rounded-lg transition-colors"
                  >
                    <svg class="w-4 h-4 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    Logout
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>

    <div class="flex pt-16 h-[calc(100vh-64px)]">
      <!-- Chat Sidebar -->
      <aside
        :class="[
          'fixed lg:relative inset-y-0 left-0 z-40 w-64 bg-fortress-900 border-r border-fortress-800 pt-16 lg:pt-0 transform transition-transform duration-300 flex flex-col',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        ]"
      >
        <!-- New Chat Button -->
        <div class="p-4 border-b border-fortress-800">
          <button
            @click="newChat"
            class="w-full bg-secure hover:bg-secure/90 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            <span>New Chat</span>
          </button>
        </div>

        <!-- Filters & Search -->
        <div class="px-4 py-3 border-b border-fortress-800 space-y-3">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search conversations..."
            class="w-full bg-fortress-800 border border-fortress-700 rounded-lg px-3 py-2 text-sm text-fortress-100 placeholder-fortress-500 focus:outline-none focus:border-secure transition-colors"
          />
          
          <!-- Category Filter -->
          <div class="flex items-center space-x-2 text-sm">
            <span class="text-fortress-400">Category:</span>
            <select
              v-model="selectedCategory"
              class="flex-1 bg-fortress-800 border border-fortress-700 rounded px-2 py-1 text-xs text-fortress-100 focus:outline-none focus:border-secure"
            >
              <option value="">All</option>
              <option value="general">General</option>
              <option value="research">Research</option>
              <option value="support">Support</option>
              <option value="analysis">Analysis</option>
            </select>
          </div>
        </div>

        <!-- Chat History Section -->
        <div class="flex-1 overflow-y-auto scrollbar-thin">
          <!-- Today -->
          <div v-if="todayChats.length > 0" class="px-2 py-4">
            <h3 class="text-xs font-semibold text-fortress-400 uppercase px-2 mb-2">Today</h3>
            <div class="space-y-1">
              <button
                v-for="chat in todayChats"
                :key="chat.id"
                @click="selectChat(chat)"
                :class="[
                  'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors truncate',
                  activeChat?.id === chat.id
                    ? 'bg-secure/20 text-secure border border-secure/30'
                    : 'text-fortress-300 hover:text-fortress-100 hover:bg-fortress-800'
                ]"
                :title="chat.title"
              >
                {{ chat.title }}
              </button>
            </div>
          </div>

          <!-- Yesterday -->
          <div v-if="yesterdayChats.length > 0" class="px-2 py-4 border-t border-fortress-800">
            <h3 class="text-xs font-semibold text-fortress-400 uppercase px-2 mb-2">Yesterday</h3>
            <div class="space-y-1">
              <button
                v-for="chat in yesterdayChats"
                :key="chat.id"
                @click="selectChat(chat)"
                :class="[
                  'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors truncate',
                  activeChat?.id === chat.id
                    ? 'bg-secure/20 text-secure border border-secure/30'
                    : 'text-fortress-300 hover:text-fortress-100 hover:bg-fortress-800'
                ]"
                :title="chat.title"
              >
                {{ chat.title }}
              </button>
            </div>
          </div>

          <!-- Previous 7 Days -->
          <div v-if="week7Chats.length > 0" class="px-2 py-4 border-t border-fortress-800">
            <h3 class="text-xs font-semibold text-fortress-400 uppercase px-2 mb-2">Previous 7 Days</h3>
            <div class="space-y-1">
              <button
                v-for="chat in week7Chats"
                :key="chat.id"
                @click="selectChat(chat)"
                :class="[
                  'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors truncate',
                  activeChat?.id === chat.id
                    ? 'bg-secure/20 text-secure border border-secure/30'
                    : 'text-fortress-300 hover:text-fortress-100 hover:bg-fortress-800'
                ]"
                :title="chat.title"
              >
                {{ chat.title }}
              </button>
            </div>
          </div>

          <!-- Older -->
          <div v-if="olderChats.length > 0" class="px-2 py-4 border-t border-fortress-800">
            <h3 class="text-xs font-semibold text-fortress-400 uppercase px-2 mb-2">Older</h3>
            <div class="space-y-1">
              <button
                v-for="chat in olderChats"
                :key="chat.id"
                @click="selectChat(chat)"
                :class="[
                  'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors truncate',
                  activeChat?.id === chat.id
                    ? 'bg-secure/20 text-secure border border-secure/30'
                    : 'text-fortress-300 hover:text-fortress-100 hover:bg-fortress-800'
                ]"
                :title="chat.title"
              >
                {{ chat.title }}
              </button>
            </div>
          </div>

          <!-- Empty State -->
          <div v-if="filteredChats.length === 0" class="p-4 text-center">
            <p class="text-fortress-500 text-sm">No conversations yet</p>
          </div>
        </div>

        <!-- Sidebar Footer - Back Button -->
        <div class="p-4 border-t border-fortress-800">
          <button
            @click="exitChatMode"
            class="w-full flex items-center justify-center space-x-2 px-4 py-2 text-sm text-fortress-400 hover:text-fortress-100 hover:bg-fortress-800 rounded-lg transition-colors"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span>Back to Main</span>
          </button>
        </div>
      </aside>

      <!-- Main Chat View -->
      <main class="flex-1 overflow-x-hidden overflow-y-auto">
        <router-view :key="activeChat?.id" />
      </main>

      <!-- Mobile Sidebar Overlay -->
      <div
        v-show="sidebarOpen"
        @click="sidebarOpen = false"
        class="fixed inset-0 bg-black/50 z-30 lg:hidden"
      ></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useChatHistory } from '../composables/useChatHistory'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { chats, activeChat, selectChat, createNewChat, loadChats } = useChatHistory()

const sidebarOpen = ref(false)
const userMenuOpen = ref(false)
const chatSettingsOpen = ref(false)
const searchQuery = ref('')
const selectedCategory = ref('')

const userInitials = computed(() => {
  if (!authStore.user) return '?'
  const first = authStore.user.first_name?.[0] || ''
  const last = authStore.user.last_name?.[0] || ''
  return (first + last).toUpperCase()
})

// Filter chats based on search and category
const filteredChats = computed(() => {
  return chats.value.filter(chat => {
    const matchesSearch = chat.title.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesCategory = !selectedCategory.value || chat.category === selectedCategory.value
    return matchesSearch && matchesCategory
  })
})

// Group chats by time period
const now = new Date()
const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
const yesterday = new Date(today.getTime() - 86400000)
const sevenDaysAgo = new Date(today.getTime() - 604800000)

const todayChats = computed(() => 
  filteredChats.value.filter(c => {
    const chatDate = new Date(c.created_at)
    return chatDate >= today
  })
)

const yesterdayChats = computed(() =>
  filteredChats.value.filter(c => {
    const chatDate = new Date(c.created_at)
    return chatDate >= yesterday && chatDate < today
  })
)

const week7Chats = computed(() =>
  filteredChats.value.filter(c => {
    const chatDate = new Date(c.created_at)
    return chatDate >= sevenDaysAgo && chatDate < yesterday
  })
)

const olderChats = computed(() =>
  filteredChats.value.filter(c => {
    const chatDate = new Date(c.created_at)
    return chatDate < sevenDaysAgo
  })
)

// Close sidebar on route change
watch(() => route.path, () => {
  sidebarOpen.value = false
  userMenuOpen.value = false
})

const newChat = async () => {
  await createNewChat()
  sidebarOpen.value = false
}

const exitChatMode = () => {
  router.push('/dashboard')
}

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}

onMounted(() => {
  loadChats()
})
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.2s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
