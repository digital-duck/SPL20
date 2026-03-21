<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchTodos, createTodo, updateTodo, deleteTodo, importTodos } from './api.js'
import TodoInput     from './components/TodoInput.vue'
import TodoFilter    from './components/TodoFilter.vue'
import TodoList      from './components/TodoList.vue'
import EditModal     from './components/EditModal.vue'
import ImportExport  from './components/ImportExport.vue'

// ── State ──────────────────────────────────────────────────────────────────

const todos       = ref([])
const filter      = ref('all')
const errorMsg    = ref('')
const loading     = ref(false)
const editingTodo = ref(null)   // null = modal closed; object = modal open with this todo
const sortBy      = ref('time') // 'time' | 'name' | 'priority'
const sortDir     = ref('desc') // 'asc' | 'desc'  (time defaults to newest-first = desc)

const PRIORITY_ORDER = { high: 0, medium: 1, low: 2 }

// Toggle direction when clicking the active column; reset to default when switching columns
function handleSort(key) {
  if (sortBy.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = key
    sortDir.value = key === 'time' ? 'desc' : 'asc'
  }
}

// ── Derived ────────────────────────────────────────────────────────────────

const filteredTodos = computed(() => {
  let list = todos.value
  if (filter.value === 'active')    list = list.filter(t => !t.completed)
  if (filter.value === 'completed') list = list.filter(t =>  t.completed)

  const dir = sortDir.value === 'asc' ? 1 : -1
  return [...list].sort((a, b) => {
    if (sortBy.value === 'name')
      return dir * a.title.toLowerCase().localeCompare(b.title.toLowerCase())
    if (sortBy.value === 'priority')
      return dir * ((PRIORITY_ORDER[a.priority] ?? 1) - (PRIORITY_ORDER[b.priority] ?? 1))
    // 'time' — newest first by default (dir flips on toggle)
    return dir * (new Date(b.created_at) - new Date(a.created_at))
  })
})

const doneCount  = computed(() => todos.value.filter(t =>  t.completed).length)
const totalCount = computed(() => todos.value.length)

// ── Data loading ───────────────────────────────────────────────────────────

async function loadTodos() {
  loading.value = true
  try {
    todos.value = await fetchTodos()
    errorMsg.value = ''
  } catch (e) {
    errorMsg.value = 'Could not load todos: ' + e.message
  } finally {
    loading.value = false
  }
}

onMounted(loadTodos)

// ── Handlers ───────────────────────────────────────────────────────────────

async function handleAdd(title) {
  try {
    await createTodo(title)
    await loadTodos()
  } catch (e) {
    errorMsg.value = 'Could not create todo: ' + e.message
  }
}

async function handleToggle(todo) {
  try {
    await updateTodo(todo.id, { completed: !todo.completed })
    await loadTodos()
  } catch (e) {
    errorMsg.value = 'Could not update todo: ' + e.message
    await loadTodos()
  }
}

async function handleDelete(id) {
  try {
    await deleteTodo(id)
    await loadTodos()
  } catch (e) {
    errorMsg.value = 'Could not delete todo: ' + e.message
  }
}

// Open the modal by setting editingTodo — EditModal watches this prop
function handleEdit(todo) {
  editingTodo.value = todo
}

// Import: deduplicate by title (case-insensitive), then create via API
const importStatus = ref('')
async function handleImport(items) {
  // Build a set of existing titles for O(1) lookup
  const existingTitles = new Set(
    todos.value.map(t => t.title.trim().toLowerCase())
  )

  const newItems  = items.filter(i => !existingTitles.has(i.title.trim().toLowerCase()))
  const skipped   = items.length - newItems.length

  if (newItems.length === 0) {
    importStatus.value = skipped
      ? `All ${skipped} item${skipped !== 1 ? 's' : ''} already exist — nothing imported`
      : 'Nothing to import'
    setTimeout(() => { importStatus.value = '' }, 4000)
    return
  }

  importStatus.value = 'Importing…'
  try {
    const { ok, failed } = await importTodos(newItems)
    const parts = [`Imported ${ok} todo${ok !== 1 ? 's' : ''}`]
    if (skipped) parts.push(`${skipped} duplicate${skipped !== 1 ? 's' : ''} skipped`)
    if (failed)  parts.push(`${failed} failed`)
    importStatus.value = parts.join(' · ')
    await loadTodos()
    setTimeout(() => { importStatus.value = '' }, 4000)
  } catch (e) {
    errorMsg.value = 'Import error: ' + e.message
    importStatus.value = ''
  }
}

// Called by EditModal when user saves — patch title + priority, close modal
async function handleSave({ title, priority }) {
  try {
    await updateTodo(editingTodo.value.id, { title, priority })
    editingTodo.value = null
    await loadTodos()
  } catch (e) {
    errorMsg.value = 'Could not save todo: ' + e.message
  }
}
</script>

<template>
  <div class="page">
    <div class="card">

      <header class="card-header">
        <h1>📝 Todo App</h1>
        <a href="http://localhost:8000/docs" target="_blank" class="api-link">API docs ↗</a>
      </header>

      <div v-if="errorMsg" class="error-banner">
        ⚠ {{ errorMsg }}
        <button @click="errorMsg = ''">✕</button>
      </div>

      <TodoInput @add="handleAdd" />
      <div class="filter-bar">
        <TodoFilter :filter="filter" @change="filter = $event" />
        <ImportExport :todos="todos" @import="handleImport" />
      </div>
      <p v-if="importStatus" class="import-status">{{ importStatus }}</p>

      <p v-if="loading" class="loading">Loading…</p>
      <TodoList
        v-else
        :todos="filteredTodos"
        :sortBy="sortBy"
        :sortDir="sortDir"
        @toggle="handleToggle"
        @delete="handleDelete"
        @edit="handleEdit"
        @sort="handleSort"
      />

      <footer class="card-footer">
        <span>{{ totalCount }} item{{ totalCount !== 1 ? 's' : '' }}</span>
        <span v-if="doneCount">{{ doneCount }} completed</span>
      </footer>
    </div>
  </div>

  <!-- Modal sits outside the card — rendered under <body> via Teleport -->
  <EditModal
    :todo="editingTodo"
    @save="handleSave"
    @close="editingTodo = null"
  />
</template>

<style scoped>
.page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  padding: 40px 16px;
  background: #f0f2f5;
}
.card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,.08);
  width: 100%;
  max-width: 560px;
  height: fit-content;
  overflow: hidden;
}
.card-header {
  background: #4f46e5;
  color: #fff;
  padding: 24px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-header h1 { font-size: 1.5rem; font-weight: 700; }
.api-link { color: #c7d2fe; font-size: .85rem; text-decoration: none; }
.api-link:hover { text-decoration: underline; }
.error-banner {
  background: #fef2f2; color: #b91c1c;
  padding: 10px 28px; font-size: .9rem;
  display: flex; justify-content: space-between; align-items: center;
}
.error-banner button { background: none; border: none; cursor: pointer; color: #b91c1c; font-size: 1rem; }
.loading { text-align: center; padding: 32px; color: #9ca3af; }
.card-footer {
  padding: 12px 28px; font-size: .8rem; color: #9ca3af;
  border-top: 1px solid #f0f0f0;
  display: flex; justify-content: space-between;
}
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 28px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}
.import-status {
  padding: 8px 28px; font-size: .82rem;
  color: #4f46e5; background: #eef2ff;
}
</style>
