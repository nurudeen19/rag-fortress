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
          <div v-else-if="fileType === 'excel' || fileType === 'csv'" class="overflow-x-auto border border-fortress-700 rounded">
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

          <!-- DOCX Viewer -->
          <div
            v-else-if="fileType === 'docx'"
            class="bg-fortress-900 p-4 rounded border border-fortress-700 max-w-full overflow-x-auto"
            ref="docxContainer"
          ></div>

          <!-- Markdown Viewer -->
          <div
            v-else-if="fileType === 'markdown'"
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
import * as XLSX from 'xlsx'
import { marked } from 'marked'
import api from '../../../services/api'

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
const fileType = ref(null)

// PDF specific
const pdfCanvas = ref(null)
const currentPage = ref(1)
const pdfPageCount = ref(0)
let pdfDoc = null

// Excel specific
const excelHeaders = ref([])
const excelRows = ref([])

// DOCX specific
const docxContainer = ref(null)

// Markdown specific
const markdownContent = ref('')

// JSON specific
const jsonContent = ref('')

// Text specific
const textContent = ref('')

// Detect file type from filename
const detectFileType = (filename) => {
  const ext = filename.toLowerCase().split('.').pop()
  const typeMap = {
    pdf: 'pdf',
    xlsx: 'excel',
    xls: 'excel',
    csv: 'csv',
    docx: 'docx',
    md: 'markdown',
    markdown: 'markdown',
    txt: 'txt',
    json: 'json'
  }
  return typeMap[ext] || 'unknown'
}

// Load file from backend
const loadFile = async () => {
  if (!props.fileId) return

  loading.value = true
  error.value = null

  try {
    const response = await api.get(`/v1/files/${props.fileId}/content`, {
      responseType: 'blob'
    })

    fileType.value = detectFileType(props.fileName)

    // Process based on file type
    switch (fileType.value) {
      case 'pdf':
        await loadPDF(response)
        break
      case 'excel':
        await loadExcel(response)
        break
      case 'csv':
        await loadCSV(response)
        break
      case 'docx':
        await loadDOCX(response)
        break
      case 'markdown':
        await loadMarkdown(response)
        break
      case 'json':
        await loadJSON(response)
        break
      case 'txt':
        await loadText(response)
        break
      default:
        error.value = 'File type not supported for preview'
    }
  } catch (err) {
    console.error('Failed to load file:', err)
    error.value = 'Failed to load file. Please try again.'
  } finally {
    loading.value = false
  }
}

// PDF loading
const loadPDF = async (blob) => {
  try {
    const { getDocument } = await import('pdfjs-dist')
    
    const arrayBuffer = await blob.arrayBuffer()
    pdfDoc = await getDocument({ data: arrayBuffer }).promise
    pdfPageCount.value = pdfDoc.numPages
    currentPage.value = 1
    
    await nextTick()
    await renderPDFPage(1)
  } catch (err) {
    console.error('PDF loading error:', err)
    error.value = 'Failed to load PDF'
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
    const arrayBuffer = await blob.arrayBuffer()
    const workbook = XLSX.read(arrayBuffer, { type: 'array' })
    const worksheet = workbook.Sheets[workbook.SheetNames[0]]
    const data = XLSX.utils.sheet_to_json(worksheet, { header: 1 })

    if (data.length > 0) {
      excelHeaders.value = data[0] || []
      excelRows.value = data.slice(1) || []
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
    const workbook = XLSX.read(text, { type: 'string' })
    const worksheet = workbook.Sheets[workbook.SheetNames[0]]
    const data = XLSX.utils.sheet_to_json(worksheet, { header: 1 })

    if (data.length > 0) {
      excelHeaders.value = data[0] || []
      excelRows.value = data.slice(1) || []
    }
  } catch (err) {
    console.error('CSV loading error:', err)
    error.value = 'Failed to load CSV file'
  }
}

// DOCX loading
const loadDOCX = async (blob) => {
  try {
    const { renderAsync } = await import('docx-preview')
    
    if (docxContainer.value) {
      await renderAsync(blob, docxContainer.value)
    }
  } catch (err) {
    console.error('DOCX loading error:', err)
    error.value = 'Failed to load DOCX file'
  }
}

// Markdown loading
const loadMarkdown = async (blob) => {
  try {
    const text = await blob.text()
    markdownContent.value = marked(text)
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

const closeViewer = () => {
  emit('close')
  currentPage.value = 1
  pdfDoc = null
  pdfPageCount.value = 0
  error.value = null
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
