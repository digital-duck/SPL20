# NDD Closure Is Working

*Recorded: 2026-04-12 — First real-world NDD closure run on the SPL20 codebase*

---

## What We Did

Applied the NDD closure principle to SPL 2.0 itself:

```
S  = SPL-design-v1.1.md           (original design spec)
G  = spl/ codebase                 (the implementation)
E  = SPL20-user-guide.md          (spec extracted from code, user perspective)
J  = SPL20-ndd-closure-report.md  (closure judge: structured diff of S vs E)
```

The user guide was written from the codebase — what you can actually do,
not what was planned. The closure report is the structured diff between
the two. Verdict: **[DIVERGED]**, with four real gaps found.

---

## The Four Gaps NDD Found

These are not documentation oversights. They are functional gaps that a user
would hit in production:

| Gap | What the spec promised | What the code delivers |
|-----|----------------------|----------------------|
| `WHILE @item IN @items` | Collection-based iteration with item variable | `__in_list__` node in parser, but `@item` is never bound in executor — body runs but without the loop variable |
| `ToolFailed` exception | Catchable exception when a CALL tool throws | Not in `EXCEPTION_CLASSES`; Python exceptions from CALL tools bypass the SPL exception system entirely |
| `HallucinationDetected` auto-detection | Runtime confidence threshold triggers the exception | Only raised via explicit `RAISE HallucinationDetected`; no automatic detection |
| `COMMIT` vs `RETURN` | `COMMIT` is the finalisation keyword | `COMMIT` is a deprecated alias; `RETURN` is primary — spec teaches the wrong keyword |

Finding these four gaps through NDD closure — rather than through user bug
reports or manual spec review — is the method working exactly as intended.

---

## Why NDD Closure Works Here

The traditional model:

```
Spec → Code → Spec diverges silently → Users find gaps at runtime
```

The NDD closure model:

```
Spec → Code → E(Code) → J(Spec, E(Code)) → gaps are explicit and traceable
```

The judge (`J`) is the diff between what was promised and what was built.
It is falsifiable, repeatable, and model-agnostic.

The key insight from this run: the user guide is a **better spec** than the
original design doc for most purposes, because it was derived from the code,
not from intent. When the codebase is your source of truth, the extracted
user guide supersedes the original spec — the design doc becomes a statement
of *original intent*, and the divergences are the distance between intent
and reality.

---

## The Right Methodology: Top-Down, User Perspective First

One lesson from this run shapes how NDD closure should be applied going forward.

**The mistake to avoid:** starting the extraction from file-level code details
(class names, function signatures, AST nodes). That produces a technical spec —
accurate, but not what users care about.

**The right approach:**

```
Step 1: Write the user guide
        What can a user do? What syntax works? What are the gotchas?
        This is E(G(S)) — the extracted spec.

Step 2: Compare user guide against original spec
        What did the spec promise that the user guide cannot deliver?
        What does the user guide describe that the spec never mentioned?
        This is J(S, E(G(S))).

Step 3: Drill down technically only where gaps appear
        A gap in the user guide ("@item not bound") is a pointer to
        a specific code location (executor._exec_while). The technical
        investigation is targeted, not exhaustive.
```

This ordering matters because specs are always written from the user's
perspective. A spec never says "the `__in_list__` FunctionCall node will
be parsed into an AST and dispatched to `_exec_while`." It says "you can
iterate over a list with `WHILE @item IN @items`." The closure check must
operate at the same level of abstraction as the promise.

**Analogy:** A product manager writes a spec. An engineer implements it.
QA tests the spec. NDD closure is QA — but automatic, structured, and
driven by the extracted user guide, not by a human reading both documents
and hoping to spot the diff.

---

## Source of Truth

Wen clarified an important principle on 2026-04-12:

> "Some missing features in spec is because I have not done a good job
> updating it while I work with you to develop SPL v2.0. Now the codebase
> is our source of truth."

This is the correct stance for a living software project. The design doc
captures *original intent* and *rationale* — why certain decisions were made,
what problems were being solved. The codebase captures *current reality*.
The user guide bridges them: it is the spec that users actually need.

NDD closure tells you the distance between the three:
- Original intent → current reality (what changed during development)
- Current reality → user guide (what is real but undocumented)
- User guide → original intent (what was promised but not yet delivered)

Each distance is a different kind of work to resolve.

---

## What's Next

The four gaps found are now actionable:

1. **`WHILE @item IN @items`** — fix `_exec_while` to bind the item variable
2. **`ToolFailed`** — register the exception, wrap CALL tool errors
3. **`HallucinationDetected`** — document the manual-raise pattern explicitly;
   decide whether auto-detection belongs in v2.1
4. **`COMMIT` → `RETURN`** — update `SPL-design-v1.1.md` to reflect `RETURN`
   as primary, `COMMIT` as deprecated alias

When these are fixed, running NDD closure again should return `[CLOSED]`.
That is the definition of done: the extracted user guide and the original
spec converge. Fixed point reached.

---

## Files in This Folder

| File | What it is |
|------|-----------|
| `SPL20-user-guide.md` | `E(G(S))` — spec extracted from codebase, user perspective |
| `SPL20-ndd-closure-report.md` | `J(S, E(G(S)))` — structured diff, verdict [DIVERGED] |
| `ndd-is-working.md` | This file — methodology notes and findings |
