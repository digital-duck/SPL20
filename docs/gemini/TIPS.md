# Gemini CLI Tips: Workspace Management

To add an additional directory (e.g., `SPL30`) to your current workspace so the agent can access it, use one of the following methods:

### 1. Command Line Flag
When starting the Gemini CLI, specify multiple workspace directories using the `--workspace` or `-w` flag:
```bash
gemini --workspace /home/papagame/projects/digital-duck/SPL20 --workspace /home/papagame/projects/digital-duck/SPL30
```

### 2. Runtime Command
If you are already in an interactive session, add a directory dynamically:
```bash
gemini workspace add /home/papagame/projects/digital-duck/SPL30
```

### 3. Configuration File
Permanently add the directory by editing your Gemini CLI configuration file (typically `~/.gemini/config.yaml`):
```yaml
workspaces:
  - /home/papagame/projects/digital-duck/SPL20
  - /home/papagame/projects/digital-duck/SPL30
```

*Note: After updating the configuration file, you may need to re-launch the Gemini CLI for changes to take effect.*
