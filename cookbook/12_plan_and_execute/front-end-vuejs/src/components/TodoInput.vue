<script setup>
/**
 * TodoInput.vue — the "add a new todo" form.
 *
 * Emits:
 *   add(title: string) — when the user submits a non-empty title
 *
 * defineEmits declares what events this component can send to its parent.
 * The parent listens with @add="handleAdd".
 */
import { ref } from 'vue'

const emit = defineEmits(['add'])

const title = ref('')   // two-way bound to the <input> via v-model

function submit() {
  const trimmed = title.value.trim()
  if (!trimmed) return
  emit('add', trimmed)   // tell the parent
  title.value = ''       // clear the input
}
</script>

<template>
  <form class="add-form" @submit.prevent="submit">
    <!--
      v-model binds the input value to the reactive `title` ref.
      Typing updates title.value; changing title.value updates the input.
    -->
    <input
      v-model="title"
      type="text"
      placeholder="What needs to be done?"
      autocomplete="off"
    />
    <button type="submit">Add</button>
  </form>
</template>

<style scoped>
.add-form {
  display: flex;
  gap: 8px;
  padding: 20px 28px;
  border-bottom: 1px solid #f0f0f0;
}
.add-form input {
  flex: 1;
  padding: 10px 14px;
  border: 1.5px solid #d1d5db;
  border-radius: 8px;
  font-size: .95rem;
  outline: none;
  transition: border-color .2s;
}
.add-form input:focus { border-color: #4f46e5; }
.add-form button {
  padding: 10px 18px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: .95rem;
  font-weight: 600;
  cursor: pointer;
  transition: background .2s;
}
.add-form button:hover { background: #4338ca; }
</style>
