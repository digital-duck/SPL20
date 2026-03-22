# Recipe 19: Memory-Augmented Conversation

A conversational agent that loads a persistent user profile and chat history from the SPL memory store, extracts new facts from each turn, and replies with full context.

## Setup

No setup required — the memory store is created automatically under `.spl/memory.db`.

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `user_input` | TEXT | *(required)* | The user's message for this turn |

## Usage

```bash
# Turn 1: introduce yourself
spl run cookbook/19_memory_conversation/memory_chat.spl --adapter ollama \
    user_input="My name is Alice and I'm a data scientist"

# Turn 2: test recall
spl run cookbook/19_memory_conversation/memory_chat.spl --adapter ollama \
    user_input="What's my name?"

# Turn 3: add more facts
spl run cookbook/19_memory_conversation/memory_chat.spl --adapter ollama \
    user_input="I prefer Python over R"

# Turn 4: review stored profile
spl run cookbook/19_memory_conversation/memory_chat.spl --adapter ollama \
    user_input="What do you know about me?"
```

## Memory management

```bash
# Inspect stored profile
spl memory get chat_user_profile

# Reset between sessions
spl memory delete chat_user_profile
spl memory delete chat_history
```

## Note

Workflow-level `memory.set` is not yet implemented — facts are extracted and merged in-memory within the workflow but not persisted back automatically. Use `spl memory set` to seed the store manually if needed.
