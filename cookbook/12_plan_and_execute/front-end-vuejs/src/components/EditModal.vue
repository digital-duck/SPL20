<script setup>
/**
 * EditModal.vue — popup form for editing a todo's title and priority.
 *
 * Props:
 *   todo (object|null) — the todo being edited; null means modal is closed
 *
 * Emits:
 *   save({ title, priority }) — user clicked Save
 *   close                     — user cancelled or clicked outside
 *
 * The modal uses Vue's <Teleport> to render outside the card div (directly
 * under <body>), so CSS z-index and fixed positioning work correctly regardless
 * of where EditModal is used in the component tree.
 */
import { ref, watch, nextTick } from 'vue'

const props = defineProps({ todo: Object })
const emit  = defineEmits(['save', 'close'])

const titleInput = ref(null)   // template ref — used to focus the input on open
const title    = ref('')
const priority = ref('medium')

// Watch the todo prop — when it changes to a real todo, populate the form fields
watch(() => props.todo, async (todo) => {
  if (!todo) return
  title.value    = todo.title
  priority.value = todo.priority ?? 'medium'
  await nextTick()
  titleInput.value?.focus()
  titleInput.value?.select()
})

function save() {
  const trimmed = title.value.trim()
  if (!trimmed) return
  emit('save', { title: trimmed, priority: priority.value })
}
</script>

<template>
  <!-- Teleport renders this HTML directly under <body> -->
  <Teleport to="body">
    <!--
      v-if unmounts the modal entirely when no todo is selected.
      The @click.self on the overlay closes the modal when clicking outside the white box.
    -->
    <div v-if="todo" class="overlay" @click.self="emit('close')">
      <div class="modal" @keydown.escape="emit('close')">
        <h2>Edit Task</h2>

        <!-- Title field -->
        <div class="field">
          <label for="modal-title">Title</label>
          <input
            id="modal-title"
            ref="titleInput"
            v-model="title"
            type="text"
            autocomplete="off"
            @keydown.enter="save"
          />
        </div>

        <!-- Priority radio group -->
        <div class="field">
          <label>Priority</label>
          <div class="priority-group">
            <!--
              v-model on radio inputs binds all three to the same `priority` ref.
              Selecting one automatically deselects the others.
            -->
            <label :class="['option', 'high',   { selected: priority === 'high'   }]">
              <input type="radio" v-model="priority" value="high"   /> 🔴 High
            </label>
            <label :class="['option', 'medium', { selected: priority === 'medium' }]">
              <input type="radio" v-model="priority" value="medium" /> 🟡 Medium
            </label>
            <label :class="['option', 'low',    { selected: priority === 'low'    }]">
              <input type="radio" v-model="priority" value="low"    /> 🟢 Low
            </label>
          </div>
        </div>

        <div class="actions">
          <button class="btn-cancel" @click="emit('close')">Cancel</button>
          <button class="btn-save"   @click="save">Save</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.4);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal {
  background: #fff;
  border-radius: 14px;
  padding: 28px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 20px 60px rgba(0,0,0,.2);
  animation: pop .15s ease;
}
@keyframes pop { from { transform: scale(.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }

h2 { font-size: 1.1rem; font-weight: 700; margin-bottom: 20px; color: #111; }

.field { margin-bottom: 16px; }
.field > label {
  display: block; font-size: .85rem; font-weight: 600;
  color: #374151; margin-bottom: 6px;
}
.field input[type="text"] {
  width: 100%; padding: 10px 12px;
  border: 1.5px solid #d1d5db; border-radius: 8px;
  font-size: .95rem; outline: none; transition: border-color .2s;
}
.field input[type="text"]:focus { border-color: #4f46e5; }

.priority-group { display: flex; gap: 8px; }
.option {
  flex: 1; text-align: center; padding: 8px 4px;
  border: 1.5px solid #e5e7eb; border-radius: 8px;
  cursor: pointer; font-size: .85rem; font-weight: 600;
  transition: all .15s; user-select: none;
}
.option input[type="radio"] { display: none; }
.option.high.selected   { border-color: #ef4444; background: #fef2f2; color: #ef4444; }
.option.medium.selected { border-color: #d97706; background: #fffbeb; color: #d97706; }
.option.low.selected    { border-color: #16a34a; background: #f0fdf4; color: #16a34a; }
.option:hover { background: #f9fafb; }

.actions { display: flex; gap: 8px; margin-top: 24px; justify-content: flex-end; }
.btn-cancel {
  padding: 9px 18px; background: #f3f4f6; border: none;
  border-radius: 8px; font-size: .9rem; cursor: pointer; color: #374151;
}
.btn-cancel:hover { background: #e5e7eb; }
.btn-save {
  padding: 9px 20px; background: #4f46e5; color: #fff; border: none;
  border-radius: 8px; font-size: .9rem; font-weight: 600; cursor: pointer;
}
.btn-save:hover { background: #4338ca; }
</style>
