<script setup>
/**
 * TodoFilter.vue — All / Active / Completed filter tabs.
 *
 * Props:
 *   filter (string) — the currently active filter, passed down from App.vue
 *
 * Emits:
 *   change(newFilter: string) — when user clicks a tab
 *
 * defineProps declares what data the parent passes in.
 * Here the parent uses :filter="filter" to keep them in sync.
 */
defineProps({ filter: String })
const emit = defineEmits(['change'])

const tabs = [
  { label: 'Active',    value: 'active'    },
  { label: 'Completed', value: 'completed' },
  { label: 'All',       value: 'all'       },
]
</script>

<template>
  <div class="filters">
    <!--
      v-for renders one button per tab.
      :class applies 'active' only when this tab matches the current filter.
      @click emits the change event with the tab's value.
    -->
    <button
      v-for="tab in tabs"
      :key="tab.value"
      :class="{ active: filter === tab.value }"
      @click="emit('change', tab.value)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>

<style scoped>
.filters {
  display: flex;
  gap: 4px;
}
.filters button {
  padding: 5px 14px;
  border: 1.5px solid transparent;
  border-radius: 20px;
  font-size: .85rem;
  cursor: pointer;
  background: none;
  color: #6b7280;
  transition: all .15s;
}
.filters button.active {
  border-color: #4f46e5;
  color: #4f46e5;
  font-weight: 600;
}
.filters button:hover:not(.active) { background: #f3f4f6; }
</style>
