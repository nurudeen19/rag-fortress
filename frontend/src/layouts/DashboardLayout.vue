<template>
  <div class="min-h-screen bg-fortress-950">
    <!-- Top Navigation Bar -->
    <nav class="bg-fortress-900 border-b border-fortress-800 fixed top-0 left-0 right-0 z-50">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <!-- Left: Logo & App Name -->
          <div class="flex items-center">
            <button
              @click="sidebarOpen = !sidebarOpen"
              class="lg:hidden mr-2 p-2 rounded-lg text-fortress-400 hover:text-fortress-100 hover:bg-fortress-800 transition-colors"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div class="flex items-center space-x-3">
              <div class="w-8 h-8 bg-secure/10 border border-secure/30 rounded-lg flex items-center justify-center">
                <svg class="w-5 h-5 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <span class="text-xl font-bold text-fortress-100">RAG Fortress</span>
            </div>
          </div>

          <!-- Right: User Menu -->
          <div class="flex items-center space-x-4">
            <!-- Notifications -->
            <button class="p-2 rounded-lg text-fortress-400 hover:text-fortress-100 hover:bg-fortress-800 transition-colors relative">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <span class="absolute top-1 right-1 w-2 h-2 bg-alert rounded-full"></span>
            </button>

            <!-- User Dropdown -->
            <div class="relative" v-if="authStore.user">
              <button
                @click="userMenuOpen = !userMenuOpen"
                class="flex items-center space-x-3 p-2 rounded-lg hover:bg-fortress-800 transition-colors"
              >
                <div class="w-8 h-8 bg-secure/20 border border-secure/30 rounded-full flex items-center justify-center">
                  <span class="text-sm font-medium text-secure">{{ userInitials }}</span>
                </div>
                <div class="hidden md:block text-left">
                  <p class="text-sm font-medium text-fortress-100">{{ authStore.fullName }}</p>
                  <p class="text-xs text-fortress-400">{{ authStore.user.email }}</p>
                </div>
                <svg class="w-4 h-4 text-fortress-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              <!-- Dropdown Menu -->
              <div
                v-show="userMenuOpen"
                @click.self="userMenuOpen = false"
                class="absolute right-0 mt-2 w-56 bg-fortress-900 border border-fortress-800 rounded-lg shadow-glow overflow-hidden animate-fade-in"
              >
                <div class="p-2">
                  <router-link
                    to="/profile"
                    class="block px-4 py-2 text-sm text-fortress-300 hover:bg-fortress-800 hover:text-fortress-100 rounded-lg transition-colors"
                  >
                    <svg class="w-4 h-4 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    Profile
                  </router-link>
                  <router-link
                    to="/settings"
                    class="block px-4 py-2 text-sm text-fortress-300 hover:bg-fortress-800 hover:text-fortress-100 rounded-lg transition-colors"
                  >
                    <svg class="w-4 h-4 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    Settings
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

    <div class="flex pt-16">
      <!-- Sidebar -->
      <aside
        :class="[
          'fixed lg:relative inset-y-0 left-0 z-40 w-64 bg-fortress-900 border-r border-fortress-800 pt-16 lg:pt-0 transform transition-transform duration-300',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        ]"
      >
        <nav class="h-full overflow-y-auto scrollbar-thin p-4 space-y-2">
          <router-link
            v-for="item in navigation"
            :key="item.name"
            :to="{ name: item.routeName }"
            :class="[
              'flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200',
              $route.name === item.routeName
                ? 'bg-secure/10 text-secure border border-secure/30'
                : 'text-fortress-400 hover:text-fortress-100 hover:bg-fortress-800'
            ]"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" v-html="svgPaths[item.icon]"></svg>
            <span class="font-medium">{{ item.name }}</span>
            <span v-if="item.badge" :class="[
              'ml-auto text-xs px-2 py-0.5 rounded-full',
              item.badgeColor || 'bg-secure/20 text-secure'
            ]">
              {{ item.badge }}
            </span>
          </router-link>
        </nav>
      </aside>

      <!-- Main Content -->
      <main class="flex-1 overflow-x-hidden">
        <div class="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <router-view />
        </div>
      </main>
    </div>

    <!-- Mobile Sidebar Overlay -->
    <div
      v-show="sidebarOpen"
      @click="sidebarOpen = false"
      class="fixed inset-0 bg-black/50 z-30 lg:hidden"
    ></div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const sidebarOpen = ref(false)
const userMenuOpen = ref(false)

const userInitials = computed(() => {
  if (!authStore.user) return '?'
  const first = authStore.user.first_name?.[0] || ''
  const last = authStore.user.last_name?.[0] || ''
  return (first + last).toUpperCase()
})

// SVG path maps for icons
const svgPaths = {
  dashboard: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-3m2 3l2-3m2 3l2-3m2 3l2-3m2 3l2-3M3 20h18a2 2 0 002-2V8a2 2 0 00-2-2H3a2 2 0 00-2 2v10a2 2 0 002 2z" />',
  chat: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />',
  documents: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z M13 3v5a2 2 0 002 2h5" />',
  users: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 12H9m4 5H8a4 4 0 00-4 4v2h16v-2a4 4 0 00-4-4h-1m-6-10a4 4 0 110 5.292M17 12h6m-3 5h-3a4 4 0 00-4 4v2h16v-2a4 4 0 00-4-4z" />',
  settings: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z" />',
  logs: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />',
}

function getSvgPath(iconName) {
  const path = svgPaths[iconName] || svgPaths.settings
  return {
    template: `<svg class="w-full h-full" stroke-linecap="round" stroke-linejoin="round" stroke-width="2">${path}</svg>`
  }
}

// Navigation items
const navigation = [
  {
    name: 'Dashboard',
    path: '/dashboard',
    routeName: 'dashboard',
    icon: 'dashboard',
  },
  {
    name: 'Chat',
    path: '/chat',
    routeName: 'chat',
    icon: 'chat',
    badge: '2',
  },
  {
    name: 'Documents',
    path: '/documents',
    routeName: 'documents',
    icon: 'documents',
  },
  {
    name: 'Users',
    path: '/access-control',
    routeName: 'access-control',
    icon: 'users',
  },
  {
    name: 'Configuration',
    path: '/configuration',
    routeName: 'configuration',
    icon: 'settings',
  },
  {
    name: 'Activity Logs',
    path: '/logs',
    routeName: 'logs',
    icon: 'logs',
  },
]

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>
