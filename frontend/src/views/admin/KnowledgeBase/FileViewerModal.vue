<template>
  <transition name="modal">
    <div v-if="isOpen" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-[60] flex items-center justify-center p-4">
      <div class="bg-fortress-800 rounded-lg border border-fortress-700 w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl">
        <!-- Header -->
        <div class="sticky top-0 flex items-center justify-between p-6 border-b border-fortress-700 bg-fortress-800">
          <div>
            <h2 class="text-xl font-semibold text-fortress-100">File Viewer</h2>
            <p class="text-sm text-fortress-400 mt-1 truncate">{{ fileName }}</p>
          </div>
          <button
            @click="closeViewer"
            class="p-1 hover:bg-fortress-700 rounded-lg transition-colors"
          >
            <svg class="w-6 h-6 text-fortress-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="p-12 text-center">
          <svg class="w-8 h-8 animate-spin mx-auto text-secure mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <p class="text-fortress-400">Loading file...</p>
        </div>

        <!-- Error -->
        <div v-else-if="error" class="p-12 text-center">
          <svg class="w-12 h-12 text-alert mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="text-alert">{{ error }}</p>
          <button
            @click="closeViewer"
            class="mt-4 px-4 py-2 bg-fortress-700 hover:bg-fortress-600 text-fortress-100 rounded-lg"
          >
            Close
          </button>
        </div>

        <!-- Not Viewable - Offer Download -->
        <div v-else-if="notViewable" class="p-12 text-center">
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
          <button
            @click="closeViewer"
            class="ml-2 px-6 py-2 bg-fortress-700 hover:bg-fortress-600 text-fortress-100 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>

        <!-- Content -->
        <div v-else class="p-6 space-y-4">
          <!-- PDF Viewer -->
          <div v-if="fileType === 'pdf'" class="space-y-4">
            <canvas ref="pdfCanvas" class="w-full border border-fortress-700 rounded bg-black"></canvas>
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

          <!-- Excel/CSV Table -->
          <div v-else-if="fileType === 'xlsx' || fileType === 'xls' || fileType === 'csv'" class="overflow-x-auto border border-fortress-700 rounded">
            <table class="w-full border-collapse">
              <thead>
                <tr class="bg-fortress-900">
                  <th
                    v-for="(header, i) in excelHeaders"
                    :key="i"
                    class="px-4 py-2 text-left text-fortress-100 font-semibold border border-fortress-700 text-sm"
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
                    class="px-4 py-2 text-fortress-300 border-r border-fortress-700 text-sm"
                  >
                    {{ cell }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Markdown Viewer -->
          <div
            v-else-if="fileType === 'md' || fileType === 'markdown'"
            class="bg-fortress-900 p-4 rounded border border-fortress-700 prose prose-invert max-w-none"
            v-html="markdownContent"
          ></div>

          <!-- JSON Viewer -->
          <div v-else-if="fileType === 'json'" class="bg-fortress-900 p-4 rounded overflow-x-auto border border-fortress-700">
            <pre class="text-fortress-300 text-sm whitespace-pre-wrap break-words font-mono">{{ jsonContent }}</pre>
          </div>

          <!-- Text Viewer -->
          <div v-else-if="fileType === 'txt'" class="bg-fortress-900 p-4 rounded overflow-x-auto border border-fortress-700">
            <pre class="text-fortress-300 text-sm whitespace-pre-wrap break-words font-mono">{{ textContent }}</pre>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { marked } from 'marked'
import Papa from 'papaparse'
import * as pdfjsLib from 'pdfjs-dist'
import { Workbook } from 'exceljs'
import api from '../../../services/api'

// Set up pdfjs worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`

// Props
const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  fileId: {
    type: Number,
    default: null
  },
  fileName: {
    type: String,
    default: 'File'
  }
})

// Emits
const emit = defineEmits(['close'])

// State
const loading = ref(false)
const error = ref(null)
const notViewable = ref(false)
const notViewableMessage = ref('')
const fileTypeDisplay = ref('')
const fileType = ref(null)

// PDF specific
const pdfCanvas = ref(null)
const currentPage = ref(1)
const pdfPageCount = ref(0)
let pdfDoc = null

// Excel specific
const excelHeaders = ref([])
const excelRows = ref([])

// Markdown specific
const markdownContent = ref('')

// JSON specific
const jsonContent = ref('')

// Text specific
const textContent = ref('')

// Categorize file types
const viewableTypes = ['pdf', 'txt', 'md', 'markdown', 'json', 'csv', 'xlsx', 'xls']
const downloadOnlyTypes = ['docx', 'doc', 'pptx', 'xls', 'zip', 'rar', 'exe']

const isViewable = (type) => viewableTypes.includes(type?.toLowerCase())
const isDownloadOnly = (type) => downloadOnlyTypes.includes(type?.toLowerCase())

// Get file type from response
const getFileTypeFromResponse = (response) => {
  return response.file_type?.toLowerCase() || null
}

// Detect file type from filename
const detectFileType = (filename) => {
  const ext = filename.toLowerCase().split('.').pop()
  return ext || 'unknown'
}

// Load file from backend
const loadFile = async () => {
  if (!props.fileId) return

  loading.value = true
  error.value = null
  notViewable.value = false

  try {
    // Get file as blob
    const response = await api.get(`/v1/files/${props.fileId}/content`, {
      responseType: 'blob'
    })

    fileType.value = detectFileType(props.fileName)

    // Check if file is viewable or download-only
    if (isDownloadOnly(fileType.value)) {
      notViewable.value = true
      notViewableMessage.value = `${fileType.value.toUpperCase()} files cannot be viewed in browser. Please download to view.`
      fileTypeDisplay.value = fileType.value.toUpperCase()
      return
    }

    if (!isViewable(fileType.value)) {
      notViewable.value = true
      notViewableMessage.value = `File type ".${fileType.value}" is not supported for preview. Please download to view.`
      fileTypeDisplay.value = fileType.value.toUpperCase()
      return
    }

    // Get the blob - when responseType is 'blob', the entire response is the blob
    const blob = response.data || response

    // File is viewable - process based on type
    switch (fileType.value) {
      case 'pdf':
        await loadPDF(blob)
        break
      case 'xlsx':
      case 'xls':
        await loadExcel(blob)
        break
      case 'csv':
        await loadCSV(blob)
        break
      case 'md':
      case 'markdown':
        await loadMarkdown(blob)
        break
      case 'json':
        await loadJSON(blob)
        break
      case 'txt':
        await loadText(blob)
        break
      default:
        error.value = `File type ".${fileType.value}" not supported for preview`
    }
  } catch (err) {
    console.error('Failed to load file:', err)
    error.value = err.response?.data?.detail || 'Failed to load file. Please try again.'
  } finally {
    loading.value = false
  }
}

// PDF loading
const loadPDF = async (blob) => {
  try {
    if (!blob) {
      error.value = 'No file content received'
      return
    }
    if (!(blob instanceof Blob)) {
      error.value = 'Invalid file format received'
      return
    }
    const arrayBuffer = await blob.arrayBuffer()
    if (!arrayBuffer || arrayBuffer.byteLength === 0) {
      error.value = 'PDF file is empty'
      return
    }
    pdfDoc = await pdfjsLib.getDocument({ data: arrayBuffer }).promise
    if (!pdfDoc) {
      error.value = 'Failed to parse PDF document'
      return
    }
    pdfPageCount.value = pdfDoc.numPages
    currentPage.value = 1
    
    await nextTick()
    await renderPDFPage(1)
  } catch (err) {
    console.error('PDF loading error:', err)
    error.value = `Failed to load PDF: ${err.message || 'Unknown error'}`
  }
}

const renderPDFPage = async (pageNum) => {
  if (!pdfDoc || !pdfCanvas.value) return

  try {
    const page = await pdfDoc.getPage(pageNum)
    const scale = 1.5
    const viewport = page.getViewport({ scale })

    pdfCanvas.value.width = viewport.width
    pdfCanvas.value.height = viewport.height

    const context = pdfCanvas.value.getContext('2d')
    await page.render({
      canvasContext: context,
      viewport: viewport
    }).promise
  } catch (err) {
    console.error('Page render error:', err)
  }
}

const nextPage = () => {
  if (currentPage.value < pdfPageCount.value) {
    currentPage.value++
    renderPDFPage(currentPage.value)
  }
}

const previousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    renderPDFPage(currentPage.value)
  }
}

// Excel loading
const loadExcel = async (blob) => {
  try {
    if (!blob) {
      error.value = 'No file content received'
      return
    }
    if (!(blob instanceof Blob)) {
      error.value = 'Invalid file format received'
      return
    }
    const arrayBuffer = await blob.arrayBuffer()
    if (!arrayBuffer || arrayBuffer.byteLength === 0) {
      error.value = 'Excel file is empty'
      return
    }
    const workbook = new Workbook()
    await workbook.xlsx.load(arrayBuffer)
    
    const worksheet = workbook.worksheets[0]
    if (!worksheet) {
      error.value = 'No data found in Excel file'
      return
    }

    // Get headers from first row
    const firstRow = worksheet.getRow(1)
    excelHeaders.value = firstRow.values.slice(1) || []

    // Get data rows (limit to 1000 for performance)
    const data = []
    const maxRows = Math.min(1000, worksheet.rowCount)
    
    for (let i = 2; i <= maxRows; i++) {
      const row = worksheet.getRow(i)
      data.push(row.values.slice(1) || [])
    }
    
    excelRows.value = data
  } catch (err) {
    console.error('Excel loading error:', err)
    error.value = `Failed to load Excel file: ${err.message || 'Unknown error'}`
  }
}

// CSV loading
const loadCSV = async (blob) => {
  try {
    if (!blob) {
      error.value = 'No file content received'
      return
    }
    if (!(blob instanceof Blob)) {
      error.value = 'Invalid file format received'
      return
    }
    const text = await blob.text()
    if (!text) {
      error.value = 'CSV file is empty'
      return
    }
    
    // Use a promise to properly wait for Papa.parse callback
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
    error.value = `Failed to load CSV file: ${err.message || 'Unknown error'}`
  }
}

// Markdown loading
const loadMarkdown = async (blob) => {
  try {
    if (!blob) {
      error.value = 'No file content received'
      return
    }
    if (!(blob instanceof Blob)) {
      error.value = 'Invalid file format received'
      return
    }
    const text = await blob.text()
    if (!text) {
      error.value = 'Markdown file is empty'
      return
    }
    if (typeof marked.parse !== 'function') {
      error.value = 'Markdown parser not available'
      return
    }
    markdownContent.value = marked.parse(text)
  } catch (err) {
    console.error('Markdown loading error:', err)
    error.value = `Failed to load Markdown file: ${err.message || 'Unknown error'}`
  }
}

// JSON loading
const loadJSON = async (blob) => {
  try {
    if (!blob) {
      error.value = 'No file content received'
      return
    }
    if (!(blob instanceof Blob)) {
      error.value = 'Invalid file format received'
      return
    }
    const text = await blob.text()
    if (!text) {
      error.value = 'JSON file is empty'
      return
    }
    const json = JSON.parse(text)
    jsonContent.value = JSON.stringify(json, null, 2)
  } catch (err) {
    console.error('JSON loading error:', err)
    error.value = `Invalid JSON file: ${err.message || 'Unknown error'}`
  }
}

// Text loading
const loadText = async (blob) => {
  try {
    if (!blob) {
      error.value = 'No file content received'
      return
    }
    if (!(blob instanceof Blob)) {
      error.value = 'Invalid file format received'
      return
    }
    const text = await blob.text()
    if (text === undefined || text === null) {
      error.value = 'Text file is empty'
      return
    }
    textContent.value = text
  } catch (err) {
    console.error('Text loading error:', err)
    error.value = `Failed to load text file: ${err.message || 'Unknown error'}`
  }
}

const closeViewer = () => {
  emit('close')
  currentPage.value = 1
  pdfDoc = null
  pdfPageCount.value = 0
  error.value = null
  notViewable.value = false
}

// Download file
const downloadFile = async () => {
  try {
    loading.value = true
    const response = await api.get(`/v1/files/${props.fileId}/content`, {
      responseType: 'blob'
    })
    
    // When responseType is 'blob', response.data is the blob
    const blob = response.data || response
    
    // Create download link from blob
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
  } finally {
    loading.value = false
  }
}

// Watch for open/close
watch(
  () => props.isOpen,
  (newVal) => {
    if (newVal) {
      loadFile()
    }
  }
)
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: all 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

/* Prose styling for markdown */
.prose {
  color: #d1d5db;
}

.prose strong {
  color: #f3f4f6;
}

.prose code {
  background: #374151;
  color: #fca5a5;
  padding: 0.2em 0.4em;
  border-radius: 0.25em;
}

.prose pre {
  background: #1f2937;
  color: #9ca3af;
}

.prose a {
  color: #60a5fa;
}

.prose h1,
.prose h2,
.prose h3,
.prose h4 {
  color: #f3f4f6;
}
</style>
