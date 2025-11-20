<template>
  <div class="space-y-4">
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-96">
      <div class="text-center">
        <svg class="w-8 h-8 animate-spin mx-auto text-secure mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <p class="text-fortress-400">Loading file...</p>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center p-12">
      <svg class="w-12 h-12 text-alert mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p class="text-alert">{{ error }}</p>
    </div>

    <!-- Not Viewable -->
    <div v-else-if="notViewable" class="text-center p-12">
      <svg class="w-12 h-12 text-fortress-500 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
      </svg>
      <p class="text-fortress-300 mb-2">{{ notViewableMessage }}</p>
      <p class="text-fortress-400 text-sm mb-6">File type: <span class="font-semibold">{{ fileTypeDisplay }}</span></p>
      <button
        @click="downloadFile"
        class="px-6 py-2 bg-secure hover:bg-secure/80 text-white rounded-lg font-medium transition-colors"
      >
        Download File
      </button>
    </div>

    <!-- Universal Viewer -->
    <div v-else class="space-y-4">
      <!-- PDF with navigation controls -->
      <div v-if="fileType === 'pdf'" class="space-y-4">
        <div class="border border-fortress-700 rounded bg-black overflow-auto overflow-x-auto max-h-screen max-w-full flex items-center justify-center">
          <canvas ref="pdfCanvas" class="flex-shrink-0"></canvas>
        </div>
        <div class="flex items-center justify-between">
          <button
            @click="previousPage"
            :disabled="currentPage === 1"
            class="px-4 py-2 bg-fortress-700 hover:bg-fortress-600 disabled:opacity-50 text-fortress-100 rounded"
          >
            ← Previous
          </button>
          <span class="text-fortress-300">Page {{ currentPage }} of {{ pdfPageCount }}</span>
          <button
            @click="nextPage"
            :disabled="currentPage === pdfPageCount"
            class="px-4 py-2 bg-fortress-700 hover:bg-fortress-600 disabled:opacity-50 text-fortress-100 rounded"
          >
            Next →
          </button>
        </div>
      </div>

      <!-- All other content types -->
      <div v-else class="border border-fortress-700 rounded bg-fortress-900/50 overflow-auto overflow-x-auto max-h-screen max-w-full">
        <!-- Table for Excel/CSV -->
        <table v-if="fileType === 'xlsx' || fileType === 'xls' || fileType === 'csv'" class="w-full border-collapse">
          <thead class="sticky top-0 bg-fortress-900">
            <tr>
              <th
                v-for="(header, i) in excelHeaders"
                :key="i"
                class="px-4 py-2 text-left text-fortress-100 font-semibold border border-fortress-700 text-sm whitespace-nowrap"
              >
                {{ header }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, i) in excelRows"
              :key="i"
              class="hover:bg-fortress-900/30 border-b border-fortress-700"
            >
              <td
                v-for="(cell, j) in row"
                :key="j"
                class="px-4 py-2 text-fortress-300 border-r border-fortress-700 text-sm whitespace-nowrap cursor-grab"
              >
                {{ cell }}
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Markdown -->
        <div
          v-else-if="fileType === 'md' || fileType === 'markdown'"
          class="p-4 prose prose-invert max-w-none"
          v-html="markdownContent"
        ></div>

        <!-- JSON -->
        <pre v-else-if="fileType === 'json'" class="p-4 text-fortress-300 text-sm whitespace-pre-wrap break-words font-mono">{{ jsonContent }}</pre>

        <!-- Text -->
        <pre v-else class="p-4 text-fortress-300 text-sm whitespace-pre-wrap break-words font-mono">{{ textContent }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import * as XLSX from 'exceljs'
import Papa from 'papaparse'
import { marked } from 'marked'
import api from '../../../services/api'

// Set PDF worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`

const props = defineProps({
  fileId: {
    type: String,
    required: true
  },
  fileName: {
    type: String,
    required: true
  },
  autoLoad: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['loaded'])

// State
const loading = ref(false)
const error = ref(null)
const fileType = ref(null)
const notViewable = ref(false)
const notViewableMessage = ref('')
const fileTypeDisplay = ref('')

// PDF
const pdfCanvas = ref(null)
const pdfDoc = ref(null)
const pdfPageCount = ref(0)
const currentPage = ref(1)

// Excel/CSV
const excelHeaders = ref([])
const excelRows = ref([])

// Markdown/JSON/Text
const markdownContent = ref('')
const jsonContent = ref('')
const textContent = ref('')

// Helper functions
const detectFileType = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase() || 'unknown'
  return ext
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const downloadFile = async () => {
  try {
    const response = await api.get(`/v1/files/${props.fileId}/content`, {
      responseType: 'blob'
    })

    const blob = response.data || response
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', props.fileName)
    document.body.appendChild(link)
    link.click()
    link.parentNode.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (err) {
    console.error('Download failed:', err)
    error.value = 'Failed to download file'
  }
}

// PDF loading
const loadPDF = async (blob) => {
  try {
    const pdf = await pdfjsLib.getDocument(new Uint8Array(await blob.arrayBuffer())).promise
    pdfDoc.value = pdf
    pdfPageCount.value = pdf.numPages
    currentPage.value = 1
    await renderPDFPage(1)
  } catch (err) {
    console.error('PDF loading error:', err)
    error.value = 'Failed to load PDF file'
  }
}

const renderPDFPage = async (pageNum) => {
  if (!pdfDoc.value) return
  try {
    const page = await pdfDoc.value.getPage(pageNum)
    const scale = 2
    const viewport = page.getViewport({ scale })

    if (!pdfCanvas.value) return
    pdfCanvas.value.width = viewport.width
    pdfCanvas.value.height = viewport.height

    const renderContext = {
      canvasContext: pdfCanvas.value.getContext('2d'),
      viewport: viewport
    }
    await page.render(renderContext).promise
  } catch (err) {
    console.error('PDF rendering error:', err)
    error.value = 'Failed to render PDF page'
  }
}

const nextPage = async () => {
  if (currentPage.value < pdfPageCount.value) {
    currentPage.value++
    await renderPDFPage(currentPage.value)
  }
}

const previousPage = async () => {
  if (currentPage.value > 1) {
    currentPage.value--
    await renderPDFPage(currentPage.value)
  }
}

// Excel loading
const loadExcel = async (blob) => {
  try {
    const workbook = new XLSX.Workbook()
    await workbook.xlsx.load(blob)
    const worksheet = workbook.worksheets[0]
    if (!worksheet) {
      error.value = 'No worksheet found'
      return
    }

    const rows = worksheet.getSheetValues()
    if (rows && rows.length > 0) {
      excelHeaders.value = rows[1] || []
      excelRows.value = rows.slice(2).filter(row => row && row.length > 0) || []
    } else {
      error.value = 'No data found in Excel file'
    }
  } catch (err) {
    console.error('Excel loading error:', err)
    error.value = 'Failed to load Excel file'
  }
}

// CSV loading
const loadCSV = async (blob) => {
  try {
    const text = await blob.text()
    return new Promise((resolve, reject) => {
      Papa.parse(text, {
        header: false,
        skipEmptyLines: true,
        complete: (results) => {
          try {
            if (results.data && results.data.length > 0) {
              excelHeaders.value = results.data[0] || []
              excelRows.value = results.data.slice(1) || []
            } else {
              error.value = 'No data found in CSV file'
            }
            resolve()
          } catch (e) {
            reject(e)
          }
        },
        error: (err) => {
          reject(err)
        }
      })
    })
  } catch (err) {
    console.error('CSV loading error:', err)
    error.value = 'Failed to load CSV file'
  }
}

// Markdown loading
const loadMarkdown = async (blob) => {
  try {
    const text = await blob.text()
    markdownContent.value = marked.parse(text)
  } catch (err) {
    console.error('Markdown loading error:', err)
    error.value = 'Failed to load Markdown file'
  }
}

// JSON loading
const loadJSON = async (blob) => {
  try {
    const text = await blob.text()
    const json = JSON.parse(text)
    jsonContent.value = JSON.stringify(json, null, 2)
  } catch (err) {
    console.error('JSON loading error:', err)
    error.value = 'Invalid JSON file'
  }
}

// Text loading
const loadText = async (blob) => {
  try {
    textContent.value = await blob.text()
  } catch (err) {
    console.error('Text loading error:', err)
    error.value = 'Failed to load text file'
  }
}

// Main load function
const loadFile = async () => {
  loading.value = true
  error.value = null
  notViewable.value = false

  try {
    const ext = detectFileType(props.fileName)
    fileType.value = ext
    fileTypeDisplay.value = ext.toUpperCase()

    const response = await api.get(`/v1/files/${props.fileId}/content`, {
      responseType: 'blob'
    })

    const blob = response.data || response

    if (!(blob instanceof Blob)) {
      throw new Error('Response is not a valid Blob')
    }

    // Determine file type and load accordingly
    const viewableTypes = ['pdf', 'txt', 'md', 'markdown', 'json', 'csv', 'xlsx', 'xls']

    if (!viewableTypes.includes(ext)) {
      notViewable.value = true
      notViewableMessage.value = `${ext.toUpperCase()} files must be downloaded to view`
      loading.value = false
      return
    }

    // Load based on type
    if (ext === 'pdf') {
      await loadPDF(blob)
    } else if (ext === 'xlsx' || ext === 'xls') {
      await loadExcel(blob)
    } else if (ext === 'csv') {
      await loadCSV(blob)
    } else if (ext === 'md' || ext === 'markdown') {
      await loadMarkdown(blob)
    } else if (ext === 'json') {
      await loadJSON(blob)
    } else if (ext === 'txt') {
      await loadText(blob)
    }

    emit('loaded')
  } catch (err) {
    console.error('File loading error:', err)
    error.value = err.message || 'Failed to load file'
  } finally {
    loading.value = false
  }
}

// Watch for fileId changes
watch(() => props.fileId, () => {
  if (props.autoLoad) {
    loadFile()
  }
}, { immediate: props.autoLoad })

// Expose loadFile for parent components
defineExpose({
  loadFile
})
</script>

<style scoped>
.prose {
  --tw-prose-body: rgb(209, 213, 219);
  --tw-prose-headings: rgb(243, 244, 246);
  --tw-prose-code: rgb(209, 213, 219);
}
</style>
