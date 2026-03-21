# Todo App — Simple Frontend

A single-file vanilla HTML/CSS/JS frontend for the Todo REST API.
No build step, no dependencies — open directly in a browser.

## How to run

Make sure the FastAPI backend is running first:
```bash
cd ../output-claude-sonnet4-6
uvicorn main:app --reload
```

Then open the frontend — either:
```bash
# Option A: open directly (works in most browsers)
open front-end-simple/index.html

# Option B: serve with Python (avoids any file:// quirks)
python3 -m http.server 3000 --directory front-end-simple
# then open http://localhost:3000
```

## What it demonstrates

| Concept | Where |
|---------|-------|
| `fetch()` API | `apiFetch()` helper |
| Async/await | every handler function |
| DOM manipulation | `render()` function |
| Event listeners | form submit, filter buttons |
| Error handling | try/catch + toast notification |
| HTML escaping | `escHtml()` — prevents XSS |

## File layout

```
front-end-simple/
└── index.html    # everything: HTML structure, CSS styles, JS logic
```

The simplicity is intentional — all logic in one file makes it easy to
read top-to-bottom and understand how each piece connects.
