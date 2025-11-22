<template>
  <div class="h-full flex flex-col">
    <h1 class="text-2xl font-bold text-fortress-100 mb-2">System Settings</h1>
    <p class="text-fortress-400 mb-6">Configure custom application settings and manage system jobs</p>
    
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Application Settings Card -->
      <div class="card p-6">
        <div class="flex items-center gap-3 mb-4">
          <svg class="w-6 h-6 text-secure" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
          <h2 class="text-lg font-semibold text-fortress-100">Application Settings</h2>
        </div>
        <p class="text-fortress-400 text-sm mb-6">
          Configure custom application settings that will be enforced across the system. These settings control system behavior and defaults.
        </p>
        <button class="px-4 py-2 bg-secure hover:bg-secure/90 text-white rounded-lg font-medium transition-colors">
          Configure Settings
        </button>
      </div>

      <!-- Job Management Card -->
      <div class="card p-6">
        <div class="flex items-center gap-3 mb-4">
          <svg class="w-6 h-6 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
          </svg>
          <h2 class="text-lg font-semibold text-fortress-100">Job Management</h2>
        </div>
        <p class="text-fortress-400 text-sm mb-6">
          Manage system jobs including restarting failed jobs, processing pending jobs, and monitoring job status.
        </p>
        <button class="px-4 py-2 bg-warning hover:bg-warning/90 text-black rounded-lg font-medium transition-colors">
          Manage Jobs
        </button>
      </div>
    </div>

    <!-- Coming Soon Info -->
    <div class="mt-8 card p-6 bg-fortress-800/30">
      <div class="flex items-start gap-4">
        <svg class="w-6 h-6 text-info flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <div>
          <h3 class="font-semibold text-fortress-100 mb-1">Under Development</h3>
          <p class="text-fortress-400 text-sm">
            These features are currently being developed. More configuration options and management tools will be available soon. 
            You can also view your system status in the <router-link to="/activity-logs" class="text-secure hover:text-secure-light">Activity Logs</router-link>.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// System settings interface
// Future implementation will include:
// - Custom application settings storage and retrieval
// - Application setting validation and enforcement
// - Job queue management (restart failed, process pending)
// - System status monitoring
</script>

<style scoped>
.card {
  background: linear-gradient(135deg, rgba(17, 24, 39, 0.5) 0%, rgba(31, 41, 55, 0.5) 100%);
  border: 1px solid rgba(75, 85, 99, 0.3);
  border-radius: 0.5rem;
}
</style>