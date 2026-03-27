
```bash
spl run ./23_structured_output/structured_output.spl --adapter ollama text=John Smith, 42, joined Acme Corp in March 2021 earning $95,000/year
```

```spl
-- Recipe 23: Structured Output
-- Extract typed, structured data from free-form text using CREATE FUNCTION with JSON schema.
-- Demonstrates schema-constrained generation — the LLM must return valid JSON matching the spec.
--
-- Usage:
--   spl run cookbook/23_structured_output/structured_output.spl --adapter ollama -m gemma3 \
--       text="John Smith, 42, joined Acme Corp in March 2021 earning $95,000/year"
--
--   spl run cookbook/23_structured_output/structured_output.spl --adapter ollama \
--       text="Invoice #INV-2045 from TechSupplies Ltd dated 15 Jan 2024 for $3,420.50 due in 30 days"

-- Define the extraction schema
CREATE FUNCTION extract_entity_schema()
RETURNS JSON
AS $$
{
  "type": "object",
  "properties": {
    "people": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name":       { "type": "string" },
          "age":        { "type": "integer" },
          "role":       { "type": "string" },
          "salary":     { "type": "number" },
          "start_date": { "type": "string", "format": "date" }
        },
        "required": ["name"]
      }
    },
    "organizations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name":     { "type": "string" },
          "type":     { "type": "string" },
          "industry": { "type": "string" }
        },
        "required": ["name"]
      }
    },
    "amounts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "value":    { "type": "number" },
          "currency": { "type": "string", "default": "USD" },
          "label":    { "type": "string" }
        },
        "required": ["value"]
      }
    },
    "dates": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "value": { "type": "string" },
          "label": { "type": "string" }
        },
        "required": ["value"]
      }
    }
  }
}
$$;

PROMPT extract_entities
SELECT
    system_role('You are a precise data extraction engine. Extract all entities from the text and return valid JSON matching the provided schema. Return only the JSON object, no explanation.'),
    context.text AS text,
    extract_entity_schema() AS schema
GENERATE structured_extraction(text, schema)
```

Traceback (most recent call last):
  File "/home/papagame/anaconda3/envs/spl2/bin/spl", line 6, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/papagame/projects/digital-duck/SPL20/spl/cli.py", line 1399, in main
    cli()
  File "/home/papagame/anaconda3/envs/spl2/lib/python3.11/site-packages/click/core.py", line 1485, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl2/lib/python3.11/site-packages/click/core.py", line 1406, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl2/lib/python3.11/site-packages/click/core.py", line 1873, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl2/lib/python3.11/site-packages/click/core.py", line 1269, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl2/lib/python3.11/site-packages/click/core.py", line 824, in invoke
    return callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL20/spl/cli.py", line 360, in cmd_execute
    log_path = _setup_logging(run_name="run", adapter=adapter, spl_file=file)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL20/spl/cli.py", line 138, in _setup_logging
    log_path = setup_logging(
               ^^^^^^^^^^^^^^
TypeError: setup_logging() got an unexpected keyword argument 'log_ext'
