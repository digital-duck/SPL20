=== SPL 2.0 Cookbook Batch Run — 2026-04-16 22:26:56 ===
    Overrides : adapter=ollama, model=gemma3

[01] Hello World
     cmd : python3 -m gemma3 execute ./cookbook/01_hello_world/hello.spl --adapter ollama
     log : /home/papagame/projects/digital-duck/SPL20/cookbook/01_hello_world/logs/hello_20260416_222656.md
     | /home/papagame/anaconda3/bin/python3: No module named gemma3
     result: FAILED  (0.0s)

[02] Ollama Proxy
     cmd : python3 -m gemma3 execute ./cookbook/02_ollama_proxy/proxy.spl --adapter ollama prompt=Explain quantum computing in one sentence
     log : /home/papagame/projects/digital-duck/SPL20/cookbook/02_ollama_proxy/logs/proxy_20260416_222656.md
     | /home/papagame/anaconda3/bin/python3: No module named gemma3
     result: FAILED  (0.0s)

[03] Multilingual Greeting
     cmd : python3 -m gemma3 execute ./cookbook/03_multilingual/multilingual.spl --adapter ollama user_input=Hello Wen-Guang lang=Chinese
     log : /home/papagame/projects/digital-duck/SPL20/cookbook/03_multilingual/logs/multilingual_20260416_222656.md
     | /home/papagame/anaconda3/bin/python3: No module named gemma3
     result: FAILED  (0.0s)


=== Summary: 0/3 Success  (total 0.1s) ===

ID    Recipe                        Status     Elapsed
--------------------------------------------------------
01    Hello World                   FAILED        0.0s
02    Ollama Proxy                  FAILED        0.0s
03    Multilingual Greeting         FAILED        0.0s

