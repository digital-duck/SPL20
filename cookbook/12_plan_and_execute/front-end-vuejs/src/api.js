/**
 * api.js — thin wrapper around the Todo REST API.
 *
 * All requests go through the Vite dev proxy (/api → http://localhost:8000)
 * so no CORS configuration is needed during development.
 */

const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (res.status === 204) return null   // DELETE returns no body
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `${res.status} ${res.statusText}`)
  }
  return res.json()
}

/** Fetch all todos. Pass completed=true/false to filter. */
export function fetchTodos(completed = null) {
  const qs = completed !== null ? `?completed=${completed}` : ''
  return request(`/todos${qs}`)
}

/** Create a new todo with the given title. */
export function createTodo(title) {
  return request('/todos', {
    method: 'POST',
    body: JSON.stringify({ title }),
  })
}

/** Partially update a todo (title and/or completed). */
export function updateTodo(id, patch) {
  return request(`/todos/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(patch),
  })
}

/** Delete a todo by id. */
export function deleteTodo(id) {
  return request(`/todos/${id}`, { method: 'DELETE' })
}

/** Import a list of todos — creates each one via POST. Returns { ok, failed } counts. */
export async function importTodos(items) {
  let ok = 0, failed = 0
  for (const item of items) {
    try {
      await request('/todos', {
        method: 'POST',
        body: JSON.stringify({
          title:     item.title     ?? '(untitled)',
          completed: item.completed ?? false,
          priority:  item.priority  ?? 'medium',
        }),
      })
      ok++
    } catch {
      failed++
    }
  }
  return { ok, failed }
}
