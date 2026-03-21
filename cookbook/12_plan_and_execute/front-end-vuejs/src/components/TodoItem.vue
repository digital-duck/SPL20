<script setup>
/**
 * TodoItem.vue — a single row in the todo list.
 *
 * Props:
 *   todo (object) — { id, title, completed, priority, created_at }
 *
 * Emits:
 *   toggle  — user clicked the checkbox
 *   delete  — user clicked the delete button
 *   edit    — user clicked the edit button (App.vue opens the modal)
 */
defineProps({ todo: Object })
defineEmits(['toggle', 'delete', 'edit'])

function formatDate(iso) {
  const d = new Date(iso + 'Z')
  return d.toLocaleDateString(undefined, {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

const BADGE = {
  high:   { label: 'High',   cls: 'high'   },
  medium: { label: 'Medium', cls: 'medium' },
  low:    { label: 'Low',    cls: 'low'    },
}
</script>

<template>
  <div class="todo-item">
    <input type="checkbox" :checked="todo.completed" @change="$emit('toggle')" />

    <span class="todo-title" :class="{ done: todo.completed }">
      {{ todo.title }}
    </span>

    <!-- Priority badge -->
    <span class="badge" :class="BADGE[todo.priority]?.cls ?? 'medium'">
      {{ BADGE[todo.priority]?.label ?? 'Medium' }}
    </span>

    <span class="todo-meta">{{ formatDate(todo.created_at) }}</span>

    <!-- Edit button — opens modal in App.vue -->
    <button class="btn-edit" title="Edit" @click="$emit('edit')">
      <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
           fill="none" stroke="currentColor" stroke-width="2"
           stroke-linecap="round" stroke-linejoin="round">
        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
      </svg>
    </button>

    <button class="btn-delete" title="Delete" @click="$emit('delete')">✕</button>
  </div>
</template>

<style scoped>
.todo-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 28px;
  border-bottom: 1px solid #f9f9f9;
  transition: background .15s;
}
.todo-item:hover { background: #fafafa; }
.todo-item:last-child { border-bottom: none; }

input[type="checkbox"] {
  width: 18px; height: 18px;
  accent-color: #4f46e5;
  cursor: pointer;
  flex-shrink: 0;
}

.badge {
  font-size: .7rem; font-weight: 600;
  padding: 2px 7px; border-radius: 10px;
  text-transform: uppercase; letter-spacing: .03em;
  flex-shrink: 0;
  min-width: 80px; text-align: center;
  margin-right: 16px;
}
.badge.high   { background: #fef2f2; color: #ef4444; }
.badge.medium { background: #fffbeb; color: #d97706; }
.badge.low    { background: #f0fdf4; color: #16a34a; }

.todo-title { flex: 1; font-size: .95rem; line-height: 1.4; }
.todo-title.done { text-decoration: line-through; color: #9ca3af; }

.todo-meta { font-size: .75rem; color: #b0b7c3; white-space: nowrap; }

.btn-edit {
  background: none; border: none; cursor: pointer; color: #6366f1;
  padding: 4px 6px; border-radius: 6px;
  transition: color .15s, background .15s;
  display: flex; align-items: center;
}
.btn-edit:hover { color: #4338ca; background: #eef2ff; }

.btn-delete {
  background: none; border: none; cursor: pointer; color: #d1d5db;
  font-size: 1.1rem; padding: 2px 6px; border-radius: 6px;
  transition: color .15s, background .15s; line-height: 1;
}
.btn-delete:hover { color: #ef4444; background: #fef2f2; }
</style>
