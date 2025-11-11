<template>
  <div>
    <!-- Page Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-fortress-100 mb-2">Dashboard</h1>
      <p class="text-fortress-400">Welcome back, {{ authStore.fullName }}! Here's your knowledge fortress overview.</p>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <!-- Total Documents -->
      <div class="card hover:shadow-glow-sm transition-shadow duration-200">
        <div class="card-body">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-fortress-400 mb-1">Total Documents</p>
              <p class="text-2xl font-bold text-fortress-100">1,234</p>
              <p class="text-xs text-success mt-1">
                <span class="inline-block mr-1">↑</span>
                12% from last month
              </p>
            </div>
            <div class="w-12 h-12 bg-secure/10 border border-secure/30 rounded-lg flex items-center justify-center">
              <svg class="w-6 h-6 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Active Queries -->
      <div class="card hover:shadow-glow-sm transition-shadow duration-200">
        <div class="card-body">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-fortress-400 mb-1">Queries This Week</p>
              <p class="text-2xl font-bold text-fortress-100">856</p>
              <p class="text-xs text-success mt-1">
                <span class="inline-block mr-1">↑</span>
                8% from last week
              </p>
            </div>
            <div class="w-12 h-12 bg-success/10 border border-success/30 rounded-lg flex items-center justify-center">
              <svg class="w-6 h-6 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Vector Store Usage -->
      <div class="card hover:shadow-glow-sm transition-shadow duration-200">
        <div class="card-body">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-fortress-400 mb-1">Vector Store</p>
              <p class="text-2xl font-bold text-fortress-100">78%</p>
              <p class="text-xs text-warning mt-1">
                <span class="inline-block mr-1">⚠</span>
                Storage capacity
              </p>
            </div>
            <div class="w-12 h-12 bg-warning/10 border border-warning/30 rounded-lg flex items-center justify-center">
              <svg class="w-6 h-6 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- System Health -->
      <div class="card hover:shadow-glow-sm transition-shadow duration-200">
        <div class="card-body">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-fortress-400 mb-1">System Health</p>
              <p class="text-2xl font-bold text-success">Healthy</p>
              <p class="text-xs text-fortress-400 mt-1">
                All systems operational
              </p>
            </div>
            <div class="w-12 h-12 bg-success/10 border border-success/30 rounded-lg flex items-center justify-center">
              <svg class="w-6 h-6 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <!-- Recent Activity -->
      <div class="card">
        <div class="card-header">
          <h3 class="text-lg font-semibold text-fortress-100">Recent Activity</h3>
        </div>
        <div class="card-body">
          <div class="space-y-4">
            <div v-for="activity in recentActivities" :key="activity.id" class="flex items-start space-x-3 pb-4 border-b border-fortress-800 last:border-0 last:pb-0">
              <div :class="[
                'w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0',
                activity.type === 'upload' ? 'bg-secure/10 border border-secure/30' :
                activity.type === 'query' ? 'bg-success/10 border border-success/30' :
                'bg-warning/10 border border-warning/30'
              ]">
                <svg class="w-5 h-5" :class="[
                  activity.type === 'upload' ? 'text-secure' :
                  activity.type === 'query' ? 'text-success' :
                  'text-warning'
                ]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path v-if="activity.type === 'upload'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  <path v-else-if="activity.type === 'query'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm text-fortress-100 font-medium">{{ activity.title }}</p>
                <p class="text-xs text-fortress-400 mt-1">{{ activity.description }}</p>
                <p class="text-xs text-fortress-500 mt-1">{{ activity.time }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Top Queried Topics -->
      <div class="card">
        <div class="card-header">
          <h3 class="text-lg font-semibold text-fortress-100">Top Queried Topics</h3>
        </div>
        <div class="card-body">
          <div class="space-y-3">
            <div v-for="topic in topTopics" :key="topic.name" class="flex items-center justify-between">
              <div class="flex-1">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm text-fortress-300">{{ topic.name }}</span>
                  <span class="text-sm font-medium text-fortress-100">{{ topic.count }}</span>
                </div>
                <div class="w-full bg-fortress-800 rounded-full h-2">
                  <div
                    class="h-2 rounded-full transition-all duration-300"
                    :class="topic.color"
                    :style="{ width: `${topic.percentage}%` }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="card">
      <div class="card-header">
        <h3 class="text-lg font-semibold text-fortress-100">Quick Actions</h3>
      </div>
      <div class="card-body">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <router-link
            to="/chat"
            class="flex items-center space-x-3 p-4 rounded-lg border border-fortress-800 hover:border-secure hover:bg-secure/5 transition-all duration-200 group"
          >
            <div class="w-10 h-10 bg-secure/10 border border-secure/30 rounded-lg flex items-center justify-center group-hover:bg-secure/20 transition-colors">
              <svg class="w-5 h-5 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <div>
              <p class="text-sm font-medium text-fortress-100">Start Chat</p>
              <p class="text-xs text-fortress-400">Query knowledge base</p>
            </div>
          </router-link>

          <router-link
            to="/documents"
            class="flex items-center space-x-3 p-4 rounded-lg border border-fortress-800 hover:border-success hover:bg-success/5 transition-all duration-200 group"
          >
            <div class="w-10 h-10 bg-success/10 border border-success/30 rounded-lg flex items-center justify-center group-hover:bg-success/20 transition-colors">
              <svg class="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <div>
              <p class="text-sm font-medium text-fortress-100">Upload Document</p>
              <p class="text-xs text-fortress-400">Add to knowledge base</p>
            </div>
          </router-link>

          <router-link
            v-if="authStore.isAdmin"
            to="/access-control"
            class="flex items-center space-x-3 p-4 rounded-lg border border-fortress-800 hover:border-warning hover:bg-warning/5 transition-all duration-200 group"
          >
            <div class="w-10 h-10 bg-warning/10 border border-warning/30 rounded-lg flex items-center justify-center group-hover:bg-warning/20 transition-colors">
              <svg class="w-5 h-5 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <div>
              <p class="text-sm font-medium text-fortress-100">Manage Access</p>
              <p class="text-xs text-fortress-400">Control permissions</p>
            </div>
          </router-link>

          <router-link
            to="/logs"
            class="flex items-center space-x-3 p-4 rounded-lg border border-fortress-800 hover:border-fortress-600 hover:bg-fortress-800/50 transition-all duration-200 group"
          >
            <div class="w-10 h-10 bg-fortress-700 border border-fortress-600 rounded-lg flex items-center justify-center group-hover:bg-fortress-600 transition-colors">
              <svg class="w-5 h-5 text-fortress-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <div>
              <p class="text-sm font-medium text-fortress-100">View Logs</p>
              <p class="text-xs text-fortress-400">Activity history</p>
            </div>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

// Mock data - replace with API calls
const recentActivities = ref([
  {
    id: 1,
    type: 'upload',
    title: 'Document uploaded',
    description: 'Financial Report Q4 2024.pdf added to knowledge base',
    time: '2 minutes ago'
  },
  {
    id: 2,
    type: 'query',
    title: 'Query executed',
    description: 'User searched for "quarterly revenue analysis"',
    time: '15 minutes ago'
  },
  {
    id: 3,
    type: 'alert',
    title: 'Access attempt',
    description: 'User tried to access restricted document',
    time: '1 hour ago'
  },
])

const topTopics = ref([
  { name: 'Financial Reports', count: 234, percentage: 85, color: 'bg-secure' },
  { name: 'HR Policies', count: 189, percentage: 68, color: 'bg-success' },
  { name: 'Technical Documentation', count: 145, percentage: 52, color: 'bg-warning' },
  { name: 'Marketing Materials', count: 98, percentage: 35, color: 'bg-purple-500' },
])
</script>
