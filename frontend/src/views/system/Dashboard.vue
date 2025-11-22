<template>
  <div>
    <!-- Page Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-fortress-100 mb-2">Dashboard</h1>
      <p class="text-fortress-400">Welcome back, {{ authStore.fullName }}! Here's your {{ authStore.isAdmin ? 'admin' : 'knowledge fortress' }} overview.</p>
      <p v-if="cacheStatus" class="text-xs text-fortress-500 mt-2">Data {{ cacheStatus === 'cached' ? '(cached)' : '(live)' }}</p>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center py-12">
      <div class="text-center">
        <svg class="w-8 h-8 text-secure animate-spin mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <p class="text-fortress-400">Loading metrics...</p>
      </div>
    </div>

    <!-- Admin Dashboard -->
    <div v-else-if="authStore.isAdmin" class="space-y-8">
      <!-- Key Metrics Grid -->
      <div>
        <h2 class="text-lg font-semibold text-fortress-100 mb-4">Key Metrics</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          <!-- Total Documents -->
          <div class="card hover:shadow-glow-sm transition-shadow duration-200">
            <div class="card-body">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-fortress-400 mb-1">Total Documents</p>
                  <p class="text-2xl font-bold text-fortress-100">{{ adminMetrics.total_documents.toLocaleString() }}</p>
                  <p class="text-xs text-success mt-1" v-if="adminMetrics.approved_documents > 0">
                    <span class="inline-block mr-1">✓</span>{{ adminMetrics.approved_documents }} approved
                  </p>
                </div>
                <div class="w-10 h-10 bg-secure/10 border border-secure/30 rounded-lg flex items-center justify-center">
                  <svg class="w-5 h-5 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <!-- Pending Approval -->
          <div class="card hover:shadow-glow-sm transition-shadow duration-200">
            <div class="card-body">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-fortress-400 mb-1">Pending Approval</p>
                  <p class="text-2xl font-bold text-warning">{{ adminMetrics.pending_documents }}</p>
                  <p class="text-xs text-fortress-400 mt-1">
                    Awaiting review
                  </p>
                </div>
                <div class="w-10 h-10 bg-warning/10 border border-warning/30 rounded-lg flex items-center justify-center">
                  <svg class="w-5 h-5 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <!-- Jobs Processed -->
          <div class="card hover:shadow-glow-sm transition-shadow duration-200">
            <div class="card-body">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-fortress-400 mb-1">Jobs Processed</p>
                  <p class="text-2xl font-bold text-success">{{ adminMetrics.jobs_processed.toLocaleString() }}</p>
                  <p class="text-xs text-fortress-400 mt-1">
                    Success rate: {{ adminComputed.jobSuccessRate }}%
                  </p>
                </div>
                <div class="w-10 h-10 bg-success/10 border border-success/30 rounded-lg flex items-center justify-center">
                  <svg class="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <!-- Failed Jobs -->
          <div class="card hover:shadow-glow-sm transition-shadow duration-200">
            <div class="card-body">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-fortress-400 mb-1">Failed Jobs</p>
                  <p class="text-2xl font-bold text-danger">{{ adminMetrics.jobs_failed }}</p>
                  <p class="text-xs text-fortress-400 mt-1">
                    Require attention
                  </p>
                </div>
                <div class="w-10 h-10 bg-danger/10 border border-danger/30 rounded-lg flex items-center justify-center">
                  <svg class="w-5 h-5 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4v2m0 0v2M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
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
                  <p class="text-2xl font-bold text-success">{{ adminMetrics.system_health === 'healthy' ? 'Healthy' : 'Warning' }}</p>
                  <p class="text-xs text-fortress-400 mt-1">
                    {{ adminMetrics.total_users }} users active
                  </p>
                </div>
                <div class="w-10 h-10 bg-success/10 border border-success/30 rounded-lg flex items-center justify-center">
                  <svg class="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Secondary Metrics -->
      <div>
        <h2 class="text-lg font-semibold text-fortress-100 mb-4">Activity Overview</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <!-- Total Users -->
          <div class="card">
            <div class="card-body">
              <p class="text-sm text-fortress-400 mb-2">Total Users</p>
              <p class="text-xl font-bold text-fortress-100">{{ adminMetrics.total_users }}</p>
              <p class="text-xs text-fortress-500 mt-2">Active members</p>
            </div>
          </div>

          <!-- Notifications -->
          <div class="card">
            <div class="card-body">
              <p class="text-sm text-fortress-400 mb-2">Unread Notifications</p>
              <p class="text-xl font-bold text-info">{{ adminMetrics.unread_notifications }}</p>
              <p class="text-xs text-fortress-500 mt-2">From {{ adminMetrics.total_notifications }} total</p>
            </div>
          </div>

          <!-- Jobs In Progress -->
          <div class="card">
            <div class="card-body">
              <p class="text-sm text-fortress-400 mb-2">Jobs In Progress</p>
              <p class="text-xl font-bold text-warning">{{ adminMetrics.jobs_in_progress }}</p>
              <p class="text-xs text-fortress-500 mt-2">Currently processing</p>
            </div>
          </div>

          <!-- Pending Jobs -->
          <div class="card">
            <div class="card-body">
              <p class="text-sm text-fortress-400 mb-2">Jobs Pending</p>
              <p class="text-xl font-bold text-warning">{{ adminMetrics.jobs_pending }}</p>
              <p class="text-xs text-fortress-500 mt-2">Queued for processing</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Admin Quick Actions -->
      <div class="card">
        <div class="card-header">
          <h3 class="text-lg font-semibold text-fortress-100">Quick Actions</h3>
        </div>
        <div class="card-body">
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <router-link
              to="/knowledge-base"
              class="flex flex-col items-center space-y-2 p-4 rounded-lg border border-fortress-800 hover:border-secure hover:bg-secure/5 transition-all duration-200 group text-center"
            >
              <div class="w-10 h-10 bg-secure/10 border border-secure/30 rounded-lg flex items-center justify-center group-hover:bg-secure/20 transition-colors">
                <svg class="w-5 h-5 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-fortress-100">Review Files</p>
                <p class="text-xs text-fortress-400">{{ adminMetrics.pending_documents }} pending</p>
              </div>
            </router-link>

            <router-link
              to="/activity-logs"
              class="flex flex-col items-center space-y-2 p-4 rounded-lg border border-fortress-800 hover:border-info hover:bg-info/5 transition-all duration-200 group text-center"
            >
              <div class="w-10 h-10 bg-info/10 border border-info/30 rounded-lg flex items-center justify-center group-hover:bg-info/20 transition-colors">
                <svg class="w-5 h-5 text-info" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-fortress-100">Activity Logs</p>
                <p class="text-xs text-fortress-400">System audit</p>
              </div>
            </router-link>

            <router-link
              to="/system-settings"
              class="flex flex-col items-center space-y-2 p-4 rounded-lg border border-fortress-800 hover:border-warning hover:bg-warning/5 transition-all duration-200 group text-center"
            >
              <div class="w-10 h-10 bg-warning/10 border border-warning/30 rounded-lg flex items-center justify-center group-hover:bg-warning/20 transition-colors">
                <svg class="w-5 h-5 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-fortress-100">Settings</p>
                <p class="text-xs text-fortress-400">Configure system</p>
              </div>
            </router-link>

            <router-link
              to="/access-control"
              class="flex flex-col items-center space-y-2 p-4 rounded-lg border border-fortress-800 hover:border-success hover:bg-success/5 transition-all duration-200 group text-center"
            >
              <div class="w-10 h-10 bg-success/10 border border-success/30 rounded-lg flex items-center justify-center group-hover:bg-success/20 transition-colors">
                <svg class="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-fortress-100">Access Control</p>
                <p class="text-xs text-fortress-400">Manage permissions</p>
              </div>
            </router-link>

            <router-link
              to="/chat"
              class="flex flex-col items-center space-y-2 p-4 rounded-lg border border-fortress-800 hover:border-fortress-600 hover:bg-fortress-800/50 transition-all duration-200 group text-center"
            >
              <div class="w-10 h-10 bg-fortress-700 border border-fortress-600 rounded-lg flex items-center justify-center group-hover:bg-fortress-600 transition-colors">
                <svg class="w-5 h-5 text-fortress-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-fortress-100">Chat</p>
                <p class="text-xs text-fortress-400">Test knowledge base</p>
              </div>
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- User Dashboard -->
    <div v-else class="space-y-8">
      <!-- User Metrics Grid -->
      <div>
        <h2 class="text-lg font-semibold text-fortress-100 mb-4">Your Progress</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <!-- My Documents -->
          <div class="card hover:shadow-glow-sm transition-shadow duration-200">
            <div class="card-body">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-fortress-400 mb-1">My Documents</p>
                  <p class="text-2xl font-bold text-fortress-100">{{ userMetrics.my_documents }}</p>
                  <p class="text-xs text-success mt-1" v-if="userMetrics.approved_documents > 0">
                    <span class="inline-block mr-1">✓</span>{{ userMetrics.approved_documents }} approved
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

          <!-- Pending Approval -->
          <div class="card hover:shadow-glow-sm transition-shadow duration-200">
            <div class="card-body">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-fortress-400 mb-1">Pending Approval</p>
                  <p class="text-2xl font-bold text-warning">{{ userMetrics.pending_approval }}</p>
                  <p class="text-xs text-fortress-400 mt-1">
                    Awaiting review
                  </p>
                </div>
                <div class="w-12 h-12 bg-warning/10 border border-warning/30 rounded-lg flex items-center justify-center">
                  <svg class="w-6 h-6 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <!-- Approval Rate -->
          <div class="card hover:shadow-glow-sm transition-shadow duration-200">
            <div class="card-body">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-fortress-400 mb-1">Approval Rate</p>
                  <p class="text-2xl font-bold text-success">{{ userComputed.approvalRate }}%</p>
                  <p class="text-xs text-fortress-400 mt-1">
                    Of your uploads
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

          <!-- Unread Notifications -->
          <div class="card hover:shadow-glow-sm transition-shadow duration-200">
            <div class="card-body">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-fortress-400 mb-1">Unread Messages</p>
                  <p class="text-2xl font-bold text-info">{{ userMetrics.my_unread_notifications }}</p>
                  <p class="text-xs text-fortress-400 mt-1">
                    New notifications
                  </p>
                </div>
                <div class="w-12 h-12 bg-info/10 border border-info/30 rounded-lg flex items-center justify-center">
                  <svg class="w-6 h-6 text-info" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Knowledge Base Stats -->
      <div>
        <h2 class="text-lg font-semibold text-fortress-100 mb-4">Knowledge Base</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="card">
            <div class="card-body">
              <p class="text-sm text-fortress-400 mb-2">Total Documents Available</p>
              <p class="text-2xl font-bold text-fortress-100">{{ userMetrics.total_documents.toLocaleString() }}</p>
              <p class="text-xs text-fortress-500 mt-2">Approved documents you can query</p>
            </div>
          </div>

          <div class="card">
            <div class="card-body">
              <p class="text-sm text-fortress-400 mb-2">Available Knowledge</p>
              <p class="text-2xl font-bold text-success">{{ userMetrics.total_approved_documents.toLocaleString() }}</p>
              <p class="text-xs text-fortress-500 mt-2">Documents ready for RAG queries</p>
            </div>
          </div>
        </div>
      </div>

      <!-- User Quick Actions -->
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
              to="/upload"
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
              to="/uploads"
              class="flex items-center space-x-3 p-4 rounded-lg border border-fortress-800 hover:border-info hover:bg-info/5 transition-all duration-200 group"
            >
              <div class="w-10 h-10 bg-info/10 border border-info/30 rounded-lg flex items-center justify-center group-hover:bg-info/20 transition-colors">
                <svg class="w-5 h-5 text-info" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-fortress-100">My Uploads</p>
                <p class="text-xs text-fortress-400">View your documents</p>
              </div>
            </router-link>

            <router-link
              to="/notifications"
              v-if="userMetrics.my_unread_notifications > 0"
              class="flex items-center space-x-3 p-4 rounded-lg border border-fortress-800 hover:border-warning hover:bg-warning/5 transition-all duration-200 group"
            >
              <div class="w-10 h-10 bg-warning/10 border border-warning/30 rounded-lg flex items-center justify-center group-hover:bg-warning/20 transition-colors">
                <svg class="w-5 h-5 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-fortress-100">Notifications</p>
                <p class="text-xs text-fortress-400">{{ userMetrics.my_unread_notifications }} unread</p>
              </div>
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '../../stores/auth'
import { useDashboardMetrics } from '../../composables/useDashboardMetrics'

const authStore = useAuthStore()
const {
  adminMetrics,
  userMetrics,
  isLoading,
  error,
  cacheStatus,
  loadMetrics,
  adminComputed,
  userComputed,
} = useDashboardMetrics()
</script>
