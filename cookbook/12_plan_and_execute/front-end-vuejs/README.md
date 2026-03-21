# Todo App — Vue 3 Frontend

A component-based frontend built with Vue 3 + Vite.
Demonstrates how to structure a real Vue app with components, props, and events.

## How to run

Make sure the FastAPI backend is running first:
```bash
cd ../output-claude-sonnet4-6
uvicorn main:app --reload
```

Then start the Vue dev server:
```bash
cd front-end-vuejs
npm install
npm run dev
# open http://localhost:5173
```

The Vite dev server proxies `/api/*` → `http://localhost:8000/*` automatically,
so no CORS configuration is needed.

## Project layout

```
front-end-vuejs/
├── index.html           # HTML entry point — mounts <div id="app">
├── vite.config.js       # Vite config: Vue plugin + API proxy
├── package.json         # Dependencies (vue, vite, @vitejs/plugin-vue)
└── src/
    ├── main.js          # Creates and mounts the Vue app
    ├── api.js           # All fetch() calls to the REST API
    ├── App.vue          # Root component — owns all state
    └── components/
        ├── TodoInput.vue   # "Add a todo" form
        ├── TodoFilter.vue  # All / Active / Completed tabs
        ├── TodoList.vue    # Renders the list of TodoItems
        └── TodoItem.vue    # A single todo row
```

## Key Vue 3 concepts used

| Concept | Where | What it does |
|---------|-------|-------------|
| `ref()` | `App.vue` | Reactive primitive — UI re-renders when value changes |
| `computed()` | `App.vue` | Derived value (filtered list, counts) — auto-updates |
| `onMounted()` | `App.vue` | Lifecycle hook — fetch todos when app first loads |
| `defineProps` | all components | Declare data the parent passes in |
| `defineEmits` | all components | Declare events this component sends to its parent |
| `v-model` | `TodoInput.vue` | Two-way binding between input and reactive variable |
| `v-for` | `TodoList.vue`, `TodoFilter.vue` | Render a list of elements |
| `v-if / v-else` | `TodoList.vue` | Conditional rendering |
| `:class` | `TodoItem.vue` | Conditionally apply a CSS class |
| `@click / @change` | throughout | Listen for DOM events |
| `$emit` | child components | Send event up to parent |

## Data flow

```
App.vue  (owns state: todos[], filter, errorMsg)
  │
  ├─ props down ──► TodoInput   (title) ──► @add ──────────┐
  ├─ props down ──► TodoFilter  (filter) ──► @change ──────┤ events up
  └─ props down ──► TodoList    (todos[])                   │
                        └─► TodoItem ──► @toggle / @delete ─┘
                                                            │
                                                      App.vue calls API
                                                      then reloads todos
```

This one-directional flow ("props down, events up") is the core Vue pattern.
State lives in one place (App.vue); children are just display + input.
