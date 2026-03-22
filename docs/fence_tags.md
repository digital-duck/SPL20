❯ what are tags used to annotate a markdown text block (either lang-specific code or text), e.g. sql, bash              

● Common ones relevant to SPL documentation:

  Code languages:
  sql        bash / sh      python       json
  yaml       toml           javascript   typescript
  go         rust           java         c / cpp

  Markup / data:
  xml        html           csv          ini

  Text / prose:
  text       plaintext      (no tag)     console / terminal

  Output / logs:
  console    output         log

  Special:
  diff       markdown       dockerfile   makefile

  For SPL specifically, there's no spl or spl tag registered in any highlighter, so the choices are:

  ┌─────────────────┬───────────────────────────────────────────────────────────┐
  │  Block content  │                         Best tag                          │
  ├─────────────────┼───────────────────────────────────────────────────────────┤
  │ SPL source code │ sql — closest syntax family, keywords highlight correctly │
  ├─────────────────┼───────────────────────────────────────────────────────────┤
  │ CLI invocations │ bash                                                      │
  ├─────────────────┼───────────────────────────────────────────────────────────┤
  │ Config YAML     │ yaml                                                      │
  ├─────────────────┼───────────────────────────────────────────────────────────┤
  │ JSONL / JSON    │ json                                                      │
  ├─────────────────┼───────────────────────────────────────────────────────────┤
  │ Sample output   │ text or console                                           │
  └─────────────────┴───────────────────────────────────────────────────────────┘

  That's already what we're using in the USER-GUIDE and the spl run markdown output — sql for .spl source and bash for
  the invocation block.
