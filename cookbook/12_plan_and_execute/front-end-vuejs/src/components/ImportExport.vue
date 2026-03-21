<script setup>
/**
 * ImportExport.vue — toolbar: sort controls + Export/Import buttons.
 *
 * Props:
 *   todos   (array)  — full unfiltered list, used for export
 *
 * Emits:
 *   import(items) — parsed array of todo objects from the JSON file
 *
 * Export flow:
 *   1. Map todos to { title, completed, priority }
 *   2. Create a JSON Blob and trigger a browser download
 *
 * Import flow:
 *   1. Hidden <input type="file"> is triggered programmatically on button click
 *   2. FileReader reads the selected file as text
 *   3. JSON is parsed and validated (must be an array with title strings)
 *   4. Emit 'import' with the parsed items — parent handles API calls
 */
import { ref } from 'vue'

const props  = defineProps({ todos: Array })
const emit   = defineEmits(['import'])

const fileInput = ref(null)   // template ref to the hidden file input
const error     = ref('')

// ── Export ────────────────────────────────────────────────

function exportTodos() {
  // Keep only the fields that matter for portability — drop id and created_at
  const data = props.todos.map(({ title, completed, priority }) => ({
    title,
    completed,
    priority,
  }))

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url  = URL.createObjectURL(blob)

  // Create a temporary <a> tag, click it to trigger the download, then clean up
  const a = document.createElement('a')
  a.href     = url
  a.download = `todos-${new Date().toISOString().slice(0, 10)}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// ── Import ────────────────────────────────────────────────

function triggerImport() {
  error.value = ''
  fileInput.value.value = ''   // reset so the same file can be re-selected
  fileInput.value.click()
}

function onFileSelected(e) {
  const file = e.target.files[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (ev) => {
    try {
      const parsed = JSON.parse(ev.target.result)

      // Validate: must be an array of objects with at least a title field
      if (!Array.isArray(parsed)) throw new Error('JSON must be an array')
      const invalid = parsed.filter(item => typeof item.title !== 'string' || !item.title.trim())
      if (invalid.length) throw new Error(`${invalid.length} item(s) missing a title`)

      emit('import', parsed)
    } catch (err) {
      error.value = 'Import failed: ' + err.message
    }
  }
  reader.readAsText(file)
}
</script>

<template>
  <div class="toolbar">
    <div class="actions">
      <!-- Export button -->
      <button class="btn" :disabled="todos.length === 0" @click="exportTodos" title="Export all todos as JSON">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        Export
      </button>

      <!-- Import button — triggers the hidden file input -->
      <button class="btn btn-primary" @click="triggerImport" title="Import todos from a JSON file">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        Import
      </button>

      <!-- Hidden file picker — only accepts .json files -->
      <input
        ref="fileInput"
        type="file"
        accept=".json,application/json"
        style="display:none"
        @change="onFileSelected"
      />
    </div>
  </div>

  <!-- Validation error -->
  <p v-if="error" class="error">{{ error }}</p>
</template>

<style scoped>
.toolbar {
  display: contents; /* let the parent row control layout */
}

.actions { display: flex; gap: 8px; justify-content: flex-end; }

.btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1.5px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  color: #374151;
  font-size: .82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all .15s;
}
.btn:hover:not(:disabled) { border-color: #9ca3af; background: #f3f4f6; }
.btn:disabled { opacity: .4; cursor: not-allowed; }

.btn-primary {
  background: #4f46e5;
  border-color: #4f46e5;
  color: #fff;
}
.btn-primary:hover:not(:disabled) { background: #4338ca; border-color: #4338ca; }

.error {
  padding: 8px 28px;
  font-size: .82rem;
  color: #b91c1c;
  background: #fef2f2;
}
</style>
