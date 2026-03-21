<script setup>
/**
 * TodoList.vue — renders the list of todos with sortable column headers.
 *
 * Props:
 *   todos  (array)  — the filtered list from App.vue
 *   sortBy (string) — current sort key: 'priority' | 'name' | 'time'
 *
 * Emits:
 *   toggle(todo)  — user clicked the checkbox
 *   delete(id)    — user clicked the delete button
 *   edit(todo)    — user clicked the edit button
 *   sort(key)     — user clicked a column header to change sort
 */
import TodoItem from './TodoItem.vue'

defineProps({ todos: Array, sortBy: String, sortDir: String })
defineEmits(['toggle', 'delete', 'edit', 'sort'])
</script>

<template>
  <div class="todo-list">
    <!-- Column header row — mirrors the flex layout of TodoItem -->
    <div class="list-header">
      <!-- Spacer for the checkbox -->
      <span class="col-check" />

      <!-- Name sort header — span takes flex:1, button stays content-width -->
      <span class="col-name">
        <button
          :class="['sort-btn', { active: sortBy === 'name' }]"
          @click="$emit('sort', 'name')"
          title="Sort by name"
        >
          Name
          <span v-if="sortBy === 'name'" class="sort-arrow">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
        </button>
      </span>

      <!-- Priority sort header -->
      <button
        :class="['col-priority', 'sort-btn', { active: sortBy === 'priority' }]"
        @click="$emit('sort', 'priority')"
        title="Sort by priority"
      >
        Priority
        <span v-if="sortBy === 'priority'" class="sort-arrow">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
      </button>

      <!-- Time sort header -->
      <button
        :class="['col-time', 'sort-btn', { active: sortBy === 'time' }]"
        @click="$emit('sort', 'time')"
        title="Sort by time added"
      >
        Time
        <span v-if="sortBy === 'time'" class="sort-arrow">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
      </button>

      <!-- Spacer for edit + delete buttons -->
      <span class="col-actions" />
    </div>

    <p v-if="todos.length === 0" class="empty">
      No todos here — add one above!
    </p>

    <TodoItem
      v-else
      v-for="todo in todos"
      :key="todo.id"
      :todo="todo"
      @toggle="$emit('toggle', todo)"
      @delete="$emit('delete', todo.id)"
      @edit="$emit('edit', todo)"
    />
  </div>
</template>

<style scoped>
.todo-list { padding: 0; min-height: 60px; }

/* Header row — same padding + gap as TodoItem so columns line up */
.list-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 28px;
  border-bottom: 2px solid #e5e7eb;
  background: #f9fafb;
}

/* Column widths — must mirror TodoItem.vue layout exactly */
.col-check    { width: 18px; flex-shrink: 0; }
.col-name     { flex: 1; text-align: left; }        /* flex: 1 like .todo-title */
.col-priority { flex-shrink: 0; min-width: 80px; margin-right: 16px; } /* gap before TIME */
.col-time     { white-space: nowrap; }       /* like .todo-meta */
.col-actions { width: 72px; flex-shrink: 0; } /* ~edit + delete button width */

.sort-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: .75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .04em;
  color: #9ca3af;
  padding: 2px 4px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  transition: color .15s, background .15s;
}
.sort-btn:hover { color: #4f46e5; background: #eef2ff; }
.sort-btn.active { color: #4f46e5; }
.sort-arrow { font-size: .65rem; }

.empty {
  text-align: center;
  padding: 32px;
  color: #9ca3af;
  font-size: .9rem;
}
</style>
