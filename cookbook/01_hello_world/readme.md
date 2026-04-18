# Recipe 01: Hello World

Minimal SPL program — verifies that `spl`, the chosen adapter, and the model are all wired up correctly. This recipe supports parameters and is optimized for both large and small (local) models.


✦ To use SPL 2.0 properly in your environment, you should use the spl2 Conda environment and perform an editable
  installation. This ensures that any changes you make to the SPL source code are immediately reflected when you run the
  spl command.

1. Activate the SPL 2.0 Environment
Since you already have a spl2 environment created:

```bash
conda activate spl2
```

2. Perform an Editable Installation
Navigate to your project root and install SPL with its development dependencies:

```bash
cd ~/projects/digital-duck/SPL20
pip install -e ".[dev]"
```

* -e (Editable): Links the spl command directly to your source code in ~/projects/digital-duck/SPL20/spl/.
* .[dev]: Installs the core dependencies (from pyproject.toml) plus testing tools like pytest.

3. Verify the Setup
Check that the spl command is now pointing to your local directory:

```bash
which spl
# Should output something like: /home/papagame/anaconda3/envs/spl2/bin/spl
spl version
# Should output: spl 2.0.0
```

Pro Tip: Running without installation
If you ever want to run the code strictly from the current directory without relying on the pip path, you can use:


```bash
PYTHONPATH=. python3 -m spl.cli run cookbook/01_hello_world/hello.spl --adapter ollama
```


## Usage

```bash
# Echo adapter (no LLM needed — mirrors prompt back)
spl run cookbook/01_hello_world/hello.spl

# Local Ollama (default model)
spl run cookbook/01_hello_world/hello.spl --adapter ollama

# With parameters (translated greeting)
spl run cookbook/01_hello_world/hello.spl --adapter ollama \
    --param user_input="hello wen" \
    --param lang="Chinese"

# Specific model
spl run cookbook/01_hello_world/hello.spl --adapter ollama -m llama3.2
```

```bash
export FILE_SPL="$HOME/projects/digital-duck/SPL20/cookbook/01_hello_world/hello.spl"

## different commands
# python
spl    run $FILE_SPL --adapter ollama -m gemma3 --param user_input="hello wen" --param lang="Chinese"

# TypeScript
spl-ts run $FILE_SPL --adapter ollama -m gemma3 --param user_input="hello wen" --param lang="Chinese"

# Go
spl-go run $FILE_SPL --adapter ollama -m gemma3 --param user_input="hello wen" --param lang="Chinese"
```


## What it does

1.  **Defines a Template**: Uses `CREATE FUNCTION greeting()` to provide a structured prompt template.
2.  **Handles Context**: `SELECT`s `user_input` and `lang` from the execution context (passed via `--param`).
3.  **Generates Response**: Instructs the model to introduce itself and SPL 2.0 in two sentences, respecting the requested language and user input.

Using an explicit `CREATE FUNCTION` ensures that smaller models (like `llama3.2` or `gemma2`) provide a direct response instead of attempting to "write code" for the function.
