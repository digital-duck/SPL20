# Recipe 03: Multilingual Greeting

Greet in any language — demonstrates parametric context passing via `user_input` and `lang`.

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `user_input` | TEXT | *(required)* | The greeting or message to translate |
| `lang` | TEXT | *(required)* | Target language (e.g. Chinese, French, Japanese, Spanish) |

## Usage

```bash
spl2 run cookbook/03_multilingual/multilingual.spl --adapter ollama \
    user_input="Hello Wen-Guang" lang="Chinese"

spl2 run cookbook/03_multilingual/multilingual.spl --adapter ollama \
    user_input="Good morning" lang="French"

spl2 run cookbook/03_multilingual/multilingual.spl --adapter ollama \
    user_input="How are you?" lang="Japanese"

spl2 run cookbook/03_multilingual/multilingual.spl --adapter ollama \
    user_input="See you later" lang="Spanish"
```
