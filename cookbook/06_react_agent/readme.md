```bash
spl run cookbook/06_react_agent/react_agent.spl --adapter claude_cli -m claude-sonnet-4-6 --allowed-tools WebSearch country="France"    



spl run cookbook/06_react_agent/react_agent.spl --adapter claude_cli -m claude-sonnet-4-6 --allowed-tools WebSearch --tools cookbook/06_react_agent/tools.py country="China" \
    2>&1 | tee cookbook/out/06_react_agent-$(date +%Y%m%d_%H%M%S).md 

```