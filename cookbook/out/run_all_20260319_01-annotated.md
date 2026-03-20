(spl) gongai@ducklover1:~/projects/digital-duck/SPL20$ python cookbook/run_all.py --adapter ollama --model gemma3
=== SPL 2.0 Cookbook Batch Run — 2026-03-19 02:26:40 ===
    Overrides: adapter=ollama, model=gemma3

[01] Hello World

```sql
-- Recipe 01: Hello World
-- Minimal SPL program — verify spl2 + adapter + model work.
--
-- Usage:
--   spl2 run cookbook/01_hello_world/hello.spl
--   spl2 run cookbook/01_hello_world/hello.spl --adapter ollama
--   spl2 run cookbook/01_hello_world/hello.spl --adapter ollama -m gemma3

PROMPT hello_world
SELECT
    system_role('You are a friendly assistant. Introduce yourself and SPL 2.0 in two sentences.')
GENERATE greeting()
```

     cmd :
```bash
spl2 run ./01_hello_world/hello.spl --adapter ollama -m gemma3
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/01_hello_world/hello_20260319_022640.log
```output
============================================================
Model: gemma3
Tokens: 45 in / 54 out
Latency: 2164ms
Cost: $0.000000
------------------------------------------------------------
Okay, here's a greeting based on the provided context:

Hello there! I'm your friendly assistant, and I'm excited to introduce you to SPL 2.0 – a powerful tool designed to help you with a wide range of tasks.
============================================================
Log: /home/gongai/.spl/logs/hello-ollama-20260319-022640.log
```
     result: SUCCESS  (2.3s)

[02] Ollama Proxy

```spl
-- Recipe 02: Ollama Proxy
-- General-purpose LLM query — use any Ollama model from the command line.
-- The --model (-m) flag overrides the model at runtime without editing this file.
--
-- Usage:
--   spl2 run cookbook/02_ollama_proxy/proxy.spl --adapter ollama -m gemma3 prompt="Explain quantum computing"
--   spl2 run cookbook/02_ollama_proxy/proxy.spl --adapter ollama -m llama3.2 prompt="Write a haiku about coding"
--   spl2 run cookbook/02_ollama_proxy/proxy.spl --adapter ollama -m mistral prompt="What is 2+2?"

PROMPT ollama_proxy
SELECT
    system_role('You are a helpful, knowledgeable assistant.'),
    context.prompt AS prompt
GENERATE answer(prompt)
```

     cmd :
```bash
spl2 run ./02_ollama_proxy/proxy.spl --adapter ollama prompt=Explain quantum computing in one sentence -m gemma3
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/02_ollama_proxy/proxy_20260319_022642.log
```text
============================================================
Model: gemma3
Tokens: 47 in / 27 out
Latency: 484ms
Cost: $0.000000
------------------------------------------------------------
Quantum computing utilizes the principles of quantum mechanics, like superposition and entanglement, to perform complex calculations far beyond the capabilities of classical computers.
============================================================
Log: /home/gongai/.spl/logs/proxy-ollama-20260319-022642.log
```
     result: SUCCESS  (0.6s)

[03] Multilingual Greeting

```spl
-- Recipe 03: Multilingual Greeting
-- Greet in any language — demonstrates parametric context with lang.
--
-- Usage:
--   spl2 run cookbook/03_multilingual/multilingual.spl --adapter ollama user_input="hello wen" lang="Chinese"
--   spl2 run cookbook/03_multilingual/multilingual.spl --adapter ollama user_input="hello wen" lang="French"
--   spl2 run cookbook/03_multilingual/multilingual.spl --adapter ollama user_input="hello wen" lang="Japanese"
--   spl2 run cookbook/03_multilingual/multilingual.spl --adapter ollama user_input="hello wen" lang="Spanish"

PROMPT multilingual_greeting
SELECT
    system_role('You are a friendly assistant. Respond in the language specified.'),
    context.user_input AS input,
    context.lang AS lang
GENERATE greeting(input, lang)
```

     cmd :
```bash
spl2 run ./03_multilingual/multilingual.spl --adapter ollama user_input=hello wen lang=Chinese -m gemma3
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/03_multilingual/multilingual_20260319_022643.log
```text
============================================================
Model: gemma3
Tokens: 54 in / 21 out
Latency: 391ms
Cost: $0.000000
------------------------------------------------------------
你好，文！(Nǐ hǎo, Wén!)

(Hello, Wen!)
============================================================
Log: /home/gongai/.spl/logs/multilingual-ollama-20260319-022643.log
```
     result: SUCCESS  (0.6s)

[04] Model Showdown

```sql
-- Recipe 04: Model Showdown
-- Same prompt to multiple Ollama models — compare output quality and latency.
-- Uses CTEs to run each model in parallel and collect all results in one query.
--
-- Usage:
--   spl2 run cookbook/04_model_showdown/showdown.spl --adapter ollama prompt="What is the meaning of life?"
--   spl2 run cookbook/04_model_showdown/showdown.spl --adapter ollama prompt="Explain recursion in 3 sentences"

WITH
  gemma3_result AS (
    PROMPT ollama_proxy
    SELECT
        system_role('You are a helpful, knowledgeable assistant.'),
        context.prompt AS prompt
    GENERATE answer(prompt) USING MODEL 'gemma3'
  ),
  llama_result AS (
    PROMPT ollama_proxy
    SELECT
        system_role('You are a helpful, knowledgeable assistant.'),
        context.prompt AS prompt
    GENERATE answer(prompt) USING MODEL 'llama3.2'
  ),
  mistral_result AS (
    PROMPT ollama_proxy
    SELECT
        system_role('You are a helpful, knowledgeable assistant.'),
        context.prompt AS prompt
    GENERATE answer(prompt) USING MODEL 'mistral'
  )
SELECT
    gemma3_result.answer  AS gemma3,
    llama_result.answer   AS llama3_2,
    mistral_result.answer AS mistral
```

     cmd :
```bash
bash ./04_model_showdown/showdown.sh What is the meaning of life?
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/04_model_showdown/showdown_20260319_022644.log
```text
==============================================
  SPL 2.0 Model Showdown
==============================================
  Prompt: What is the meaning of life?
  Models: gemma3 llama3.2 mistral
==============================================

>>> gemma3
----------------------------------------------
============================================================
Model: gemma3
Tokens: 48 in / 708 out
Latency: 11126ms
Cost: $0.000000
------------------------------------------------------------
That's a question that has plagued philosophers and individuals for centuries! There isn't one single, universally accepted answer to the meaning of life. It's a profoundly personal and often evolving concept. Here's a breakdown of different perspectives:

**1. Philosophical Perspectives:**

* **Nihilism:** This viewpoint suggests that life has no inherent meaning or purpose. It's a stark, sometimes unsettling, realization. However, it can also be liberating, as it means you're free to create your own meaning.
* **Existentialism:**  Existentialists believe that we are born without a predetermined purpose. We are "condemned to be free" and it's our responsibility to *create* our own meaning through our choices and actions. Key figures include Sartre and Camus.
* **Absurdism:** Similar to existentialism, absurdism recognizes the conflict between humanity's innate desire for meaning and the universe's apparent lack of it. Camus argued that we should embrace this absurdity and revolt against it by living passionately.
* **Hedonism:** This philosophy proposes that the pursuit of pleasure and the avoidance of pain is the primary goal and therefore the meaning of life.
* **Utilitarianism:**  Utilitarians believe that the goal of life is to maximize happiness and well-being for the greatest number of people.
* **Stoicism:**  Stoics believe that happiness comes from virtue – living a life of reason, wisdom, and living in accordance with nature. Focusing on what you *can* control and accepting what you cannot is central to this philosophy.


**2. Religious and Spiritual Perspectives:**

* **Many religions** offer a framework for meaning, often centered around serving a higher power, following divine commandments, achieving enlightenment, or contributing to a divine plan.
* **Buddhism:** Focuses on escaping the cycle of suffering (samsara) through practices like meditation and cultivating compassion. The ultimate goal is Nirvana – a state of liberation.
* **Christianity:**  Often centers on loving God and loving one's neighbor, following the teachings of Jesus Christ, and striving for eternal life.
* **Islam:**  Submission to the will of Allah, performing good deeds, and striving for paradise.


**3. Psychological and Personal Perspectives:**

* **Self-Actualization (Maslow):**  Abraham Maslow's hierarchy of needs suggests that as humans, we're driven to fulfill our potential and become the best versions of ourselves.
* **Finding Purpose:**  Many people find meaning through contributing to something larger than themselves – volunteering, raising a family, pursuing a passion, or working towards a cause.
* **Relationships:**  Strong connections with others – family, friends, and community – often provide a sense of belonging and purpose.
* **Experiencing Life:** Simply embracing the experiences life offers – joy, sorrow, beauty, and challenge – can be a meaningful pursuit in itself.

**Ultimately, the "meaning of life" is what *you* make it.** There's no right or wrong answer.  It's a question to be continually explored and redefined throughout your life.

---

Would you like me to delve deeper into any of these perspectives, or perhaps explore a specific aspect of this question, such as:

*   The role of happiness in finding meaning?
*   How different cultures approach the question of purpose?
============================================================
Log: /home/gongai/.spl/logs/proxy-ollama-20260319-022644.log

>>> llama3.2
----------------------------------------------
============================================================
Model: llama3.2
Tokens: 57 in / 330 out
Latency: 4987ms
Cost: $0.000000
------------------------------------------------------------
The question of the meaning of life has puzzled philosophers, theologians, scientists, and everyday humans for centuries. While there may not be a single, definitive answer, here are some perspectives that might provide insight:

**Philosophical Views**

1. **Existentialism**: Life has no inherent meaning; it's up to each individual to create their own purpose.
2. **Hedonism**: The meaning of life is to seek pleasure and avoid pain.
3. **Nihilism**: Life is without inherent meaning or value.

**Religious and Spiritual Perspectives**

1. **Theism**: Many religious traditions believe that the purpose of life is to fulfill God's will or follow a set of divine commandments.
2. **Buddhism**: The goal of life is to achieve enlightenment, liberation from suffering, and eventual return to a state of pure consciousness.

**Scientific and Humanistic Views**

1. **Biological Perspective**: Life is the result of evolution; our purpose might be to survive, reproduce, and perpetuate our genes.
2. **Psychological Perspective**: The meaning of life can be found in personal growth, self-actualization, and happiness.

**Individual Experiences**

Ultimately, the meaning of life is a deeply personal question that may vary from person to person. Some people find purpose in relationships, work, creativity, or contributing to society. Others might discover meaning through spirituality, nature connection, or personal achievements.

In conclusion, while there's no one-size-fits-all answer to this profound question, exploring various perspectives can help us better understand the complexities of life and our place within it.
============================================================
Log: /home/gongai/.spl/logs/proxy-ollama-20260319-022655.log

>>> mistral
----------------------------------------------
============================================================
Model: mistral
Tokens: 44 in / 104 out
Latency: 3473ms
Cost: $0.000000
------------------------------------------------------------
 While I don't presume to have the definitive answer to this profound question, many philosophers, scientists, and thinkers throughout history have pondered over it. Some argue that the meaning of life is subjective and varies among individuals, while others suggest it could be related to self-realization, personal growth, seeking happiness or contributing to the betterment of humanity. Ultimately, the answer may be a deeply personal one and can depend on one's beliefs, values, and experiences.
============================================================
Log: /home/gongai/.spl/logs/proxy-ollama-20260319-022700.log

==============================================
  Showdown complete!
==============================================
```
     result: SUCCESS  (20.1s)

[05] Self-Refine

```sql
-- SPL 2.0: Self-Refine Pattern
-- Iteratively improves output through critique and refinement

WORKFLOW self_refine
  INPUT: @task text, @max_iterations int DEFAULT 5
  OUTPUT: @result text
DO
  @iteration := 0

  -- Initial draft
  GENERATE draft(@task) INTO @current

  -- Iterative refinement loop
  WHILE @iteration < @max_iterations DO
    GENERATE critique(@current) INTO @feedback

    EVALUATE @feedback
      WHEN 'satisfactory' THEN
        COMMIT @current WITH status = 'complete', iterations = @iteration
      OTHERWISE
        GENERATE refined(@current, @feedback) INTO @current
        @iteration := @iteration + 1
    END
  END

  -- If loop exhausted, commit best effort
  COMMIT @current WITH status = 'max_iterations', iterations = @iteration

EXCEPTION
  WHEN MaxIterationsReached THEN
    COMMIT @current WITH status = 'partial'
  WHEN BudgetExceeded THEN
    COMMIT @current WITH status = 'budget_limit'
END
```

     cmd :
```bash
spl2 run ./05_self_refine/self_refine.spl --adapter ollama task=Write a haiku about coding -m gemma3
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/05_self_refine/self_refine_20260319_022704.log
```text
============================================================
Status: complete
LLM Calls: 3
Tokens: 331 in / 209 out
Latency: 2568ms
------------------------------------------------------------
Committed: Lines of code dance slow
Algorithms' gentle beat
Logic's subtle song
------------------------------------------------------------
Variables:
  @task = Write a haiku about coding
  @iteration = 0
  @max_iterations = 5
  @current = Lines of code dance slow
Algorithms' gentle beat
Logic's subtle song
  @feedback = This is a poetic critique. It doesn't explicitly contain any lines, but it appears to be a lyrical passage that critiques something.

 Critique:

* The use of metaphor ("dance" and "beat") to describ
============================================================
Log: /home/gongai/.spl/logs/self_refine-ollama-20260319-022704.log
```
     result: SUCCESS  (2.7s)

[06] ReAct Agent

```sql
-- SPL 2.0: ReAct Agent Pattern
-- Reasoning + Acting loop with tool use

WORKFLOW react_agent
  INPUT: @task text, @max_iterations int DEFAULT 10
  OUTPUT: @answer text
DO
  @iteration := 0
  @history := ''
  @context := ''

  WHILE @iteration < @max_iterations DO

    -- Reasoning step
    GENERATE thought(@task, @history, @context) INTO @current_thought

    -- Action decision
    GENERATE action_decision(@current_thought) INTO @action

    -- Execute action based on classification
    EVALUATE @action
      WHEN 'search' THEN
        CALL search_tool(@action) INTO @observation
      WHEN 'calculate' THEN
        CALL calculator(@action) INTO @observation
      WHEN 'answer' THEN
        GENERATE final_answer(@history) INTO @answer
        COMMIT @answer WITH status = 'complete'
    END

    -- Accumulate history
    @history := @history + @current_thought
    @iteration := @iteration + 1

  END

EXCEPTION
  WHEN MaxIterationsReached THEN
    GENERATE best_answer(@history) INTO @answer
    COMMIT @answer WITH status = 'partial'
  WHEN HallucinationDetected THEN
    RETRY WITH temperature = 0.1
END
```

     cmd :
```bash
spl2 run ./06_react_agent/react_agent.spl --adapter ollama task=What is the population of France? -m gemma3
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/06_react_agent/react_agent_20260319_022706.log
```text
============================================================
Status: complete
LLM Calls: 41
Tokens: 8318 in / 1923 out
Latency: 27521ms
------------------------------------------------------------
Committed: I think there's been a misunderstanding here.

Let's start fresh. You initially asked for the final answer, but I didn't have any input or data to work with. You then provided some clarifications and context about France's population.

To provide a correct response, I need to know what Input 2 and Input 3 are. However, it seems like we never actually received any input or data from each other to work with.

If you'd like to proceed with answering the original question about France's population, please feel free to provide the actual inputs and data for Input 2 and Input 3.
------------------------------------------------------------
Variables:
  @task = What is the population of France?
  @iteration = 7.0
  @history = A interesting combination!

It looks like we have a mix of topics here. Unfortunately, I don't see any inputs to work with.

Could you please provide the actual data for Input 2 and 3? I'd be happy to
  @context =
  @current_thought = Based on the inputs provided:

 Input 1: What is the population of France?
Input 2: The capital city of France
Input 3: The largest river in France

 Given that Input 1 was about the population of F
  @action = Based on the information provided, I can confirm that:

1. The population of France is approximately 67.2 million people (as of 2021).
2. The capital city of France is Paris.
3. The largest river in F
  @answer = I think there's been a misunderstanding here.

Let's start fresh. You initially asked for the final answer, but I didn't have any input or data to work with. You then provided some clarifications and
============================================================
Log: /home/gongai/.spl/logs/react_agent-ollama-20260319-022706.log
```
     result: SUCCESS  (27.7s)

[07] Safe Generation

```sql
-- SPL 2.0: Safe Generation with Exception Handling
-- Demonstrates LLM-specific error handling patterns

WORKFLOW safe_generation
  INPUT: @prompt text
  OUTPUT: @result text
  SECURITY: CLASSIFICATION: internal
DO
  GENERATE response(@prompt) INTO @result

  -- Quality check via semantic evaluation (LLM-as-judge)
  GENERATE quality_assess(@result) INTO @quality

  EVALUATE @quality
    WHEN 'high_quality' THEN
      COMMIT @result WITH status = 'high_quality'
    WHEN 'acceptable' THEN
      GENERATE improved(@result, @prompt) INTO @result
      COMMIT @result WITH status = 'refined'
    OTHERWISE
      COMMIT @result WITH status = 'best_effort'
  END

EXCEPTION
  WHEN HallucinationDetected THEN
    GENERATE response(@prompt) INTO @result
    COMMIT @result WITH status = 'conservative'

  WHEN ContextLengthExceeded THEN
    RETRY WITH temperature = 0.1

  WHEN RefusalToAnswer THEN
    COMMIT @prompt WITH status = 'refused'

  WHEN BudgetExceeded THEN
    COMMIT @result WITH status = 'truncated'
END
```

     cmd :
```bash
spl2 run ./07_safe_generation/safe_generation.spl --adapter ollama prompt=Explain how encryption works -m gemma3
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/07_safe_generation/safe_generation_20260319_022734.log
```text
============================================================
Status: no_commit
LLM Calls: 2
Tokens: 467 in / 697 out
Latency: 8640ms
------------------------------------------------------------
Variables:
  @prompt = Explain how encryption works
  @result = Encryption is the process of converting plaintext (readable data) into ciphertext (unreadable data) to protect it from unauthorized access. Here's a step-by-step explanation of how encryption works:


  @score = To create a quality score for this text based on its clarity, coherence, and overall readability, I'll assess it as follows:

Clarity: 8/10
The text provides a clear explanation of encryption concepts
============================================================
Log: /home/gongai/.spl/logs/safe_generation-ollama-20260319-022734.log
```
     result: SUCCESS  (8.8s)

[08] RAG Query

```sql
-- Recipe 08: RAG Query
-- Retrieval-augmented generation over indexed documents.
--
-- Setup:
--   pip install numpy faiss-cpu
--   spl2 rag add /home/gongai/projects/digital-duck/zinets/who-is-wen.md
--
-- Usage:
--   spl2 run cookbook/08_rag_query/rag_query.spl --adapter ollama question="Where did Wen grow up?"
--   spl2 run cookbook/08_rag_query/rag_query.spl --adapter ollama question="What is Momagrid and why was it built?"

PROMPT rag_answer
SELECT
    system_role('You are a knowledgeable assistant. Use the provided context to answer accurately.'),
    rag.query(context.question, top_k=context.top_k) AS background,
    context.question AS question
GENERATE answer(question)
-- Usage: pass top_k=3 (default) or override e.g. top_k=5 for broader context
```

     cmd :
```bash
spl2 run ./08_rag_query/rag_query.spl --adapter ollama question=What language is best for systems programming? -m gemma3
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/08_rag_query/rag_query_20260319_022743.log
```text
============================================================
Model: gemma3
Tokens: 55 in / 30 out
Latency: 2791ms
Cost: $0.000000
------------------------------------------------------------
Please provide me with the context! I need the text you want me to use to answer the question "What language is best for systems programming?".
============================================================
Log: /home/gongai/.spl/logs/rag_query-ollama-20260319-022743.log
```
     result: SUCCESS  (3.0s)

[09] Chain of Thought

```sql
-- Recipe 09: Chain of Thought
-- Multi-step reasoning: Research → Analyze → Summarize
-- Each GENERATE feeds into the next via workflow variables.
--
-- Usage:
--   spl2 run cookbook/09_chain_of_thought/chain.spl --adapter ollama -m gemma3 topic="distributed AI inference"
--   spl2 run cookbook/09_chain_of_thought/chain.spl --adapter ollama -m llama3.2 topic="quantum computing"

WORKFLOW chain_of_thought
    INPUT: @topic TEXT
    OUTPUT: @summary TEXT
DO
    -- Step 1: Research
    GENERATE research(@topic) INTO @research

    -- Step 2: Analyze
    GENERATE analyze(@research) INTO @analysis

    -- Step 3: Summarize
    GENERATE summarize(@analysis) INTO @summary

    COMMIT @summary WITH status = 'complete'
END
```

     cmd :
```bash
spl2 run ./09_chain_of_thought/chain.spl --adapter ollama topic=distributed AI inference -m gemma3
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/09_chain_of_thought/chain_20260319_022746.log
```text
============================================================
Status: complete
LLM Calls: 3
Tokens: 1275 in / 1355 out
Latency: 19113ms
------------------------------------------------------------
Committed: Here's a summary of the input:

The input is an analysis of distributed AI inference, a technique used in artificial intelligence to perform computations across multiple nodes or machines. The key points discussed include:

* Benefits: Scalability, high availability, and reduced latency
* Applications: Computer vision, natural language processing, machine learning
* Technologies: TensorFlow, PyTorch, Caffe2, Apache Kafka, RabbitMQ, ZeroMQ, AWS, Azure, GCP
* Challenges: Communication overhead, synchronization difficulties, resource allocation issues

The text also highlights potential future directions and recommendations for further research, including:

* Edge AI
* Quantum AI Inference
* Explainable AI (XAI)

However, the limitations of the analysis include a lack of specific use cases or real-world applications, as well as the need for more detailed analysis to address challenges such as communication overhead and resource allocation issues.
------------------------------------------------------------
Variables:
  @topic = distributed AI inference
  @research = Distributed AI Inference: An Overview

Distributed AI inference refers to the process of performing artificial intelligence (AI) computations across multiple nodes or machines, rather than on a single
  @analysis = **Analysis**

The provided text is an overview of distributed AI inference, a technique used in artificial intelligence to perform computations across multiple nodes or machines. Here's a breakdown of
  @summary = Here's a summary of the input:

The input is an analysis of distributed AI inference, a technique used in artificial intelligence to perform computations across multiple nodes or machines. The key poi
============================================================
Log: /home/gongai/.spl/logs/chain-ollama-20260319-022746.log
```
     result: SUCCESS  (19.3s)

[10] Batch Test

```bash
#!/usr/bin/env bash
# Recipe 10: Batch Test
# Automated testing of all cookbook .spl scripts across multiple Ollama models.
# Perfect for CI/CD, model benchmarking, and regression testing.
#
# Usage:
#   bash cookbook/10_batch_test/batch_test.sh                    # all recipes, default models
#   MODELS="gemma3" bash cookbook/10_batch_test/batch_test.sh    # single model
#   ADAPTER=echo bash cookbook/10_batch_test/batch_test.sh       # dry run with echo

ADAPTER="${ADAPTER:-ollama}"
MODELS="${MODELS:-gemma3 llama3.2}"

RECIPES=(
    "01_hello_world/hello.spl|"
    "02_ollama_proxy/proxy.spl|-p prompt=hello"
    "03_multilingual/multilingual.spl|-p user_input=hello -p lang=English"
)

for model in $MODELS; do
    for entry in "${RECIPES[@]}"; do
        IFS='|' read -r script params <<< "$entry"
        spl2 run "$COOKBOOK_DIR/$script" --adapter "$ADAPTER" -m "$model" $params
    done
done
```

     cmd :
```bash
bash ./10_batch_test/batch_test.sh
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/10_batch_test/batch_test_20260319_022805.log
```text
==============================================
  SPL 2.0 Batch Test
==============================================
  Adapter: ollama
  Models:  gemma3 llama3.2
  Time:    Thu Mar 19 02:28:05 AM EDT 2026
==============================================

>>> Model: gemma3
----------------------------------------------
  PASS  01_hello_world/hello.spl
  PASS  02_ollama_proxy/proxy.spl
  PASS  03_multilingual/multilingual.spl

>>> Model: llama3.2
----------------------------------------------
  PASS  01_hello_world/hello.spl
  PASS  02_ollama_proxy/proxy.spl
  PASS  03_multilingual/multilingual.spl

==============================================
  Results: 6/6 passed, 0 failed
==============================================
```
     result: SUCCESS  (5.9s)

[11] Debate Arena

```sql
-- Recipe 11: Debate Arena
-- Two LLM personas argue opposing sides of a topic, then a judge picks the winner.
-- Demonstrates multi-perspective reasoning, adversarial generation, and semantic evaluation.
--
-- Usage:
--   spl2 run cookbook/11_debate_arena/debate.spl --adapter ollama -m gemma3 topic="AI should be open-sourced"
--   spl2 run cookbook/11_debate_arena/debate.spl --adapter ollama -m llama3.2 topic="Remote work is better than office work"

WORKFLOW debate_arena
    INPUT: @topic TEXT, @max_rounds int DEFAULT 3
    OUTPUT: @verdict TEXT
DO
    @round := 0
    @pro_history := ''
    @con_history := ''

    -- Opening statements
    GENERATE pro_argument(@topic, 'opening statement') INTO @pro
    GENERATE con_argument(@topic, 'opening statement') INTO @con

    @pro_history := @pro
    @con_history := @con

    -- Rebuttal rounds
    WHILE @round < @max_rounds DO
        GENERATE pro_argument(@topic, @con_history) INTO @pro_rebuttal
        @pro_history := @pro_history + '\n---\n' + @pro_rebuttal

        GENERATE con_argument(@topic, @pro_history) INTO @con_rebuttal
        @con_history := @con_history + '\n---\n' + @con_rebuttal

        @round := @round + 1
    END

    -- Judge evaluates both sides
    GENERATE judge_debate(@topic, @pro_history, @con_history) INTO @verdict

    COMMIT @verdict WITH status = 'complete', rounds = @round

EXCEPTION
    WHEN MaxIterationsReached THEN
        GENERATE judge_debate(@topic, @pro_history, @con_history) INTO @verdict
        COMMIT @verdict WITH status = 'partial'
    WHEN BudgetExceeded THEN
        COMMIT @pro_history WITH status = 'budget_limit'
END
```

     cmd :
```bash
spl2 run ./11_debate_arena/debate.spl --adapter ollama topic=AI should be open-sourced -m gemma3
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/11_debate_arena/debate_20260319_022811.log
```text
============================================================
Status: complete
LLM Calls: 9
Tokens: 12808 in / 5345 out
Latency: 89672ms
------------------------------------------------------------
Committed: While open-sourcing AI has many benefits, such as accelerating innovation and ensuring transparency, there are also potential drawbacks that must be considered. Here are five points to ponder on the downsides of open-sourcing AI:

**Argument 1: Security Risks**

*   **Data Breaches**: With public access to source code, sensitive information can be exposed, putting users' personal data at risk.
*   **Unauthorized Access**: Open-sourced code can be exploited by malicious actors, compromising security and integrity.

**Argument 2: Intellectual Property Concerns**

*   **Lack of Control**: When AI is open-sourced, developers lose control over their intellectual property, potentially leading to misuse or exploitation.
*   **Unintended Consequences**: Open-sourcing AI can result in unintended consequences, such as creating new vulnerabilities or exacerbating existing security issues.

**Argument 3: Regulatory Challenges**

*   **Lack of Standardization**: Without standardized regulations and guidelines, open-sourced AI development can be hindered by inconsistent quality control measures.
*   **Compliance Issues**: Companies may struggle to ensure compliance with various regulations and laws, particularly in industries like finance or healthcare.

**Argument 4: Market Disruption**

*   **Unnecessary Competition**: Open-sourcing AI can lead to unnecessary competition, distracting from the development of high-quality solutions that prioritize user needs.
*   **Profit Over Quality**: With market forces driving competition, the focus may shift from producing effective products and services to maximizing profits.

**Argument 5: Cultural Barriers**

*   **Language and Cultural Differences**: Open-sourcing AI can be hindered by language and cultural barriers, making it difficult for developers from diverse backgrounds to collaborate effectively.
*   **Lack of Trust**: Without proper vetting and verification processes, open-sourced code may contain biases or errors that could undermine its effectiveness.

In response to the main argument, one could say:

"While open-sourcing AI has many benefits, such as accelerating innovation and ensuring transparency, it's essential to consider the potential risks and limitations of this approach. By weighing the pros and cons, we can create a more nuanced understanding of the role of closed-source development in AI and make informed decisions about its implementation."
------------------------------------------------------------
Variables:
  @topic = AI should be open-sourced
  @round = 3.0
  @max_rounds = 3
  @pro_history = **Argument in Favor of Open-Sourcing AI**

Ladies and gentlemen, today I want to discuss a pressing issue that has the potential to revolutionize the field of artificial intelligence. As we continue t
  @con_history = **Con Argument: AI Should be Open-Source**

**Opening Statement:**

"The benefits of open-sourcing artificial intelligence (AI) are numerous and far-reaching. By making AI code freely available, we ca
  @verdict = While open-sourcing AI has many benefits, such as accelerating innovation and ensuring transparency, there are also potential drawbacks that must be considered. Here are five points to ponder on the d
============================================================
Log: /home/gongai/.spl/logs/debate-ollama-20260319-022811.log
```
     result: SUCCESS  (89.8s)

[12] Plan and Execute

```sql
-- Recipe 12: Plan and Execute
-- A planner agent decomposes a complex task into steps, then an executor runs each step.
-- Demonstrates agentic planning, sequential execution, and progress tracking.
--
-- Usage:
--   spl2 run cookbook/12_plan_and_execute/plan_execute.spl --adapter ollama -m gemma3 task="Build a REST API for a todo app"
--   spl2 run cookbook/12_plan_and_execute/plan_execute.spl --adapter ollama task="Set up a CI/CD pipeline for a Python project"

WORKFLOW plan_and_execute
    INPUT: @task TEXT
    OUTPUT: @final_report TEXT
DO
    @step_index := 0
    @results := ''

    -- Phase 1: Planning — decompose task into numbered steps
    GENERATE plan(@task) INTO @plan

    -- Phase 2: Count steps in plan
    GENERATE count_steps(@plan) INTO @step_count

    -- Phase 3: Execute each step sequentially
    WHILE @step_index < @step_count DO
        GENERATE extract_step(@plan, @step_index) INTO @current_step
        GENERATE execute_step(@current_step, @results) INTO @step_result
        GENERATE validate_step(@current_step, @step_result) INTO @validation

        EVALUATE @validation
            WHEN 'failed' THEN
                GENERATE replan(@task, @plan, @step_index, @step_result) INTO @plan
                GENERATE count_steps(@plan) INTO @step_count
                @step_index := 0
                @results := ''
            OTHERWISE
                @results := @results + '\n## Step ' + @step_index + '\n' + @step_result
                @step_index := @step_index + 1
        END
    END

    -- Phase 4: Synthesize final report
    GENERATE synthesize(@task, @results) INTO @final_report

    COMMIT @final_report WITH status = 'complete', steps_executed = @step_index

EXCEPTION
    WHEN MaxIterationsReached THEN
        GENERATE synthesize(@task, @results) INTO @final_report
        COMMIT @final_report WITH status = 'partial'
    WHEN BudgetExceeded THEN
        COMMIT @results WITH status = 'budget_limit'
END
```

     cmd :
```bash
spl2 run ./12_plan_and_execute/plan_execute.spl --adapter ollama task=Build a REST API for a todo app -m gemma3
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/12_plan_and_execute/plan_execute_20260319_022941.log
```text
============================================================
Status: complete
LLM Calls: 3
Tokens: 941 in / 2819 out
Latency: 37843ms
------------------------------------------------------------
Committed: **Todo API Documentation**

## Introduction
This is a RESTful API designed to manage tasks and users for a simple Todo application.

## Endpoints

### GET /tasks

*   Retrieves all available tasks.
*   **Response:** JSON array of task objects, each containing `id`, `title`, and `completed` status.
*   **Example Response:**
    ```json
[
  {
    "id": 1,
    "title": "Task 1",
    "completed": false
  },
  {
    "id": 2,
    "title": "Task 2",
    "completed": true
  }
]
```

### GET /users

*   Retrieves all available users.
*   **Response:** JSON array of user objects, each containing `id`, `username`, and `email`.

### POST /tasks

*   Creates a new task.
*   **Request Body:** JSON object containing `title` and `completed` status.

### PUT /tasks/:id / DELETE /tasks/:id
### POST /users / PUT /users/:id / DELETE /users/:id

## Authentication

The API uses Basic Auth. Provide credentials in the `Authorization` header.

## API Server

Can be built using Node.js + Express + MongoDB.
------------------------------------------------------------
Variables:
  @task = Build a REST API for a todo app
  @step_index = 0
  @results =
  @plan = **API Planning Document** ...
  @final_report = **Todo API Documentation** ...
============================================================
Log: /home/gongai/.spl/logs/plan_execute-ollama-20260319-022941.log
```
     result: SUCCESS  (38.0s)

[13] Map-Reduce Summarizer

```sql
-- Recipe 13: Map-Reduce Summarizer
-- Splits a large document into chunks, summarizes each chunk (map),
-- then combines all summaries into a final summary (reduce).
-- Demonstrates the map-reduce pattern for handling content beyond context limits.
--
-- Usage:
--   spl2 run cookbook/13_map_reduce/map_reduce.spl --adapter ollama -m gemma3 document="$(cat large_doc.txt)"
--   spl2 run cookbook/13_map_reduce/map_reduce.spl --adapter ollama document="$(cat README.md)" style="bullet points"

WORKFLOW map_reduce_summarizer
    INPUT: @document TEXT, @style TEXT DEFAULT 'paragraph', @quality_threshold FLOAT DEFAULT 0.7
    OUTPUT: @final_summary TEXT
DO
    @chunk_index := 0
    @summaries := ''

    GENERATE chunk_plan(@document) INTO @chunk_count

    WHILE @chunk_index < @chunk_count DO
        GENERATE extract_chunk(@document, @chunk_index, @chunk_count) INTO @chunk
        GENERATE summarize_chunk(@chunk, @chunk_index) INTO @chunk_summary
        @summaries := @summaries + '\n[Chunk ' + @chunk_index + ']: ' + @chunk_summary
        @chunk_index := @chunk_index + 1
    END

    GENERATE reduce_summaries(@summaries, @style) INTO @final_summary
    GENERATE quality_score(@final_summary, @document) INTO @score

    EVALUATE @score
        WHEN > @quality_threshold THEN
            COMMIT @final_summary WITH status = 'complete', chunks = @chunk_count
        OTHERWISE
            GENERATE improve_summary(@final_summary, @summaries) INTO @final_summary
            COMMIT @final_summary WITH status = 'refined', chunks = @chunk_count
    END

EXCEPTION
    WHEN ContextLengthExceeded THEN
        GENERATE reduce_summaries(@summaries, @style) INTO @final_summary
        COMMIT @final_summary WITH status = 'partial'
    WHEN BudgetExceeded THEN
        GENERATE reduce_summaries(@summaries, @style) INTO @final_summary
        COMMIT @final_summary WITH status = 'budget_limit'
END
```

     cmd :
```bash
spl2 run ./13_map_reduce/map_reduce.spl --adapter ollama document="The quick brown fox jumps over the lazy dog." style="bullet points" -m gemma3
```
```text
Error: Parse error at 26:18: Expected IDENTIFIER, got OUTPUT ('OUTPUT')
```
     result: FAILED  (0.1s)

[14] Multi-Agent Collaboration

```sql
-- Recipe 14: Multi-Agent Collaboration
-- Specialized agents (Researcher, Analyst, Writer) collaborate on a report.
-- Demonstrates procedural decomposition, CALL-based delegation, and role specialization.
--
-- Usage:
--   spl2 run cookbook/14_multi_agent/multi_agent.spl --adapter ollama -m gemma3 topic="Impact of AI on healthcare"

-- Agent 1: Researcher
PROCEDURE researcher(topic TEXT) RETURNS TEXT
DO
    GENERATE research_facts(topic) INTO @facts
    GENERATE identify_key_themes(@facts) INTO @themes
    @result := @facts + '\n\nKey Themes:\n' + @themes
    COMMIT @result
END

-- Agent 2: Analyst
PROCEDURE analyst(research TEXT, topic TEXT) RETURNS TEXT
DO
    GENERATE analyze_trends(research) INTO @trends
    GENERATE assess_risks(research, topic) INTO @risks
    GENERATE find_opportunities(research, topic) INTO @opportunities
    @result := 'Trends:\n' + @trends + '\n\nRisks:\n' + @risks + '\n\nOpportunities:\n' + @opportunities
    COMMIT @result
END

-- Agent 3: Writer
PROCEDURE writer(research TEXT, analysis TEXT, topic TEXT) RETURNS TEXT
DO
    GENERATE draft_report(topic, research, analysis) INTO @draft
    GENERATE critique(@draft) INTO @feedback
    GENERATE revise_report(@draft, @feedback) INTO @final
    COMMIT @final
END

-- Orchestrator workflow
WORKFLOW multi_agent_report
    INPUT: @topic TEXT
    OUTPUT: @report TEXT
DO
    CALL researcher(@topic) INTO @research
    CALL analyst(@research, @topic) INTO @analysis
    CALL writer(@research, @analysis, @topic) INTO @report

    COMMIT @report WITH status = 'complete'

EXCEPTION
    WHEN BudgetExceeded THEN
        COMMIT @research WITH status = 'partial_research_only'
    WHEN HallucinationDetected THEN
        RETRY WITH temperature = 0.1
END
```

     cmd :
```bash
spl2 run ./14_multi_agent/multi_agent.spl --adapter ollama topic=Impact of AI on healthcare -m gemma3
```
```text
Error: Parse error at 12:22: Expected identifier, got AT ('@')
```
     result: FAILED  (0.1s)

[15] Code Review

```sql
-- Recipe 15: Automated Code Review
-- Multi-pass code review: security audit, performance check, style review, then synthesis.
-- Demonstrates tool-augmented analysis, multi-criteria evaluation, and structured output.
--
-- Usage:
--   spl2 run cookbook/15_code_review/code_review.spl --adapter ollama code="def foo(x): return eval(x)" language="Python"

WORKFLOW code_review
    INPUT: @code TEXT, @language TEXT
    OUTPUT: @review TEXT
DO
    -- Pass 1: Security audit
    GENERATE security_audit(@code, @language) INTO @security_findings

    -- Pass 2: Performance analysis
    GENERATE performance_review(@code, @language) INTO @perf_findings

    -- Pass 3: Code style and best practices
    GENERATE style_review(@code, @language) INTO @style_findings

    -- Pass 4: Bug detection
    GENERATE bug_detection(@code, @language) INTO @bug_findings

    -- Severity scoring for each category
    GENERATE severity_score(@security_findings) INTO @sec_score
    GENERATE severity_score(@perf_findings) INTO @perf_score
    GENERATE severity_score(@bug_findings) INTO @bug_score

    -- Synthesize all findings
    GENERATE synthesize_review(
        @security_findings, @sec_score,
        @perf_findings, @perf_score,
        @style_findings,
        @bug_findings, @bug_score
    ) INTO @review

    EVALUATE @sec_score
        WHEN > 8 THEN
            COMMIT @review WITH status = 'critical_issues', verdict = 'block'
        WHEN > 5 THEN
            COMMIT @review WITH status = 'needs_fixes', verdict = 'request_changes'
        OTHERWISE
            COMMIT @review WITH status = 'approved', verdict = 'approve'
    END

EXCEPTION
    WHEN ContextLengthExceeded THEN
        GENERATE summarize_code(@code) INTO @summary
        GENERATE quick_review(@summary, @language) INTO @review
        COMMIT @review WITH status = 'partial_large_file'
    WHEN BudgetExceeded THEN
        COMMIT @security_findings WITH status = 'security_only'
END
```

     cmd :
```bash
spl2 run ./15_code_review/code_review.spl --adapter ollama code="def foo(x): return eval(x)" language=Python -m gemma3
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/15_code_review/code_review_20260319_023019.log
```text
============================================================
Status: complete
LLM Calls: 8
Tokens: 3376 in / 2250 out
Latency: 29899ms
------------------------------------------------------------
Committed: def safety_review(code):
    """
    This function assesses the safety of a given code snippet.
    """
    report = {"vulnerabilities": [], "recommendations": []}

    if "eval(" in code:
        report["vulnerabilities"].append("Use of `eval()` function")
        report["recommendations"].append("Avoid using `eval()` and consider safer alternatives, such as `ast.literal_eval()` or `numexpr.evaluate()`")

    return report
------------------------------------------------------------
Variables:
  @code = def foo(x): return eval(x)
  @language = Python
  @security_findings = **Security Audit Report** — Vulnerability: Use of `eval()` Function ...
  @perf_findings = **Performance Review** ...
  @style_findings = **Security Review: Avoiding `eval` Function** ...
  @bug_findings = Use Python's built-in `ast` module to safely evaluate expressions ...
  @sec_score = severity scoring result ...
  @review = def safety_review(code): ...
============================================================
Log: /home/gongai/.spl/logs/code_review-ollama-20260319-023019.log
```
     result: SUCCESS  (30.0s)

[16] Reflection Agent

```sql
-- Recipe 16: Reflection Agent
-- The agent solves a problem, then reflects on its own reasoning to catch errors.
-- Demonstrates meta-cognitive loops and self-assessment patterns.
--
-- Usage:
--   spl2 run cookbook/16_reflection/reflection.spl --adapter ollama problem="Design a URL shortener system"

WORKFLOW reflection_agent
    INPUT: @problem TEXT, @max_reflections int DEFAULT 3, @confidence_threshold FLOAT DEFAULT 0.85
    OUTPUT: @answer TEXT
DO
    @iteration := 0
    @confidence := 0

    GENERATE solve(@problem) INTO @answer

    WHILE @iteration < @max_reflections DO
        GENERATE reflect(@problem, @answer) INTO @reflection
        GENERATE confidence_score(@answer, @reflection) INTO @confidence

        EVALUATE @confidence
            WHEN > @confidence_threshold THEN
                COMMIT @answer WITH status = 'confident', confidence = @confidence, reflections = @iteration
            OTHERWISE
                GENERATE extract_issues(@reflection) INTO @issues
                GENERATE correct(@answer, @issues, @problem) INTO @answer
                @iteration := @iteration + 1
        END
    END

    COMMIT @answer WITH status = 'best_effort', confidence = @confidence, reflections = @iteration

EXCEPTION
    WHEN MaxIterationsReached THEN
        COMMIT @answer WITH status = 'max_reflections', confidence = @confidence
    WHEN HallucinationDetected THEN
        GENERATE solve(@problem) INTO @answer
        COMMIT @answer WITH status = 'restarted'
END
```

     cmd :
```bash
spl2 run ./16_reflection/reflection.spl --adapter ollama problem=Design a URL shortener system -m gemma3
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/16_reflection/reflection_20260319_023049.log
```text
============================================================
Status: complete
LLM Calls: 13
Tokens: 13299 in / 7896 out
Latency: 122954ms
------------------------------------------------------------
Committed: Here's a revised design for the URL shortener system that addresses the issues and suggestions mentioned earlier:

**System Components**

1. **Frontend** — React, HTML template, API client
2. **Backend** — Node.js + Express.js, MongoDB, JWT auth
3. **Database** — MongoDB schema with originalURL, shortenedURL, clicks, analyticsData

**Backend API Endpoints**

1. `/submit` — handle user submission
2. `/shorten` — create and return shortened URL
3. `/get` — retrieve original URL
4. `/analytics` — return analytics data

**Security Enhancements**

1. Secure hashing (bcrypt/Argon2) for generating shortened URLs
2. JWT authentication for user interactions
------------------------------------------------------------
Variables:
  @problem = Design a URL shortener system
  @iteration = 3.0
  @max_reflections = 3
  @confidence = score description ...
  @answer = Here's a revised design ...
  @reflection = reflections and suggestions for improvement ...
  @issues = Security concern: Using hardcoded string for generating shortened URLs (High) ...
============================================================
Log: /home/gongai/.spl/logs/reflection-ollama-20260319-023049.log
```
     result: SUCCESS  (123.1s)

[17] Tree of Thought

```sql
-- Recipe 17: Tree of Thought
-- Explores multiple reasoning paths in parallel, evaluates each, and selects the best.
-- Demonstrates branching exploration, comparative evaluation, and path scoring.
--
-- Usage:
--   spl2 run cookbook/17_tree_of_thought/tree_of_thought.spl --adapter ollama problem="Should we rewrite the legacy system or incrementally refactor?"

WORKFLOW tree_of_thought
    INPUT: @problem TEXT
    OUTPUT: @best_solution TEXT
DO
    -- Step 1: Generate multiple initial approaches
    GENERATE approach_1(@problem) INTO @path_a
    GENERATE approach_2(@problem) INTO @path_b
    GENERATE approach_3(@problem) INTO @path_c

    -- Step 2: Develop each approach one level deeper
    GENERATE develop(@path_a, @problem) INTO @path_a_developed
    GENERATE develop(@path_b, @problem) INTO @path_b_developed
    GENERATE develop(@path_c, @problem) INTO @path_c_developed

    -- Step 3: Score each path
    GENERATE evaluate_path(@path_a_developed, @problem) INTO @score_a
    GENERATE evaluate_path(@path_b_developed, @problem) INTO @score_b
    GENERATE evaluate_path(@path_c_developed, @problem) INTO @score_c

    -- Step 4: Select the best path
    GENERATE select_best(
        @path_a_developed, @score_a,
        @path_b_developed, @score_b,
        @path_c_developed, @score_c
    ) INTO @best_path

    -- Step 5: Refine and verify
    GENERATE refine_solution(@best_path, @problem) INTO @best_solution
    GENERATE verify(@best_solution, @problem) INTO @verification

    EVALUATE @verification
        WHEN 'sound' THEN
            COMMIT @best_solution WITH status = 'complete', paths_explored = 3
        OTHERWISE
            GENERATE synthesize_all(
                @path_a_developed, @path_b_developed, @path_c_developed, @problem
            ) INTO @best_solution
            COMMIT @best_solution WITH status = 'synthesized', paths_explored = 3
    END

EXCEPTION
    WHEN BudgetExceeded THEN
        COMMIT @best_path WITH status = 'budget_limit'
    WHEN HallucinationDetected THEN
        RETRY WITH temperature = 0.1
END
```

     cmd :
```bash
spl2 run ./17_tree_of_thought/tree_of_thought.spl --adapter ollama problem="Should we rewrite the legacy system or incrementally refactor?" -m gemma3
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/17_tree_of_thought/tree_of_thought_20260319_023252.log
```text
============================================================
Status: complete
LLM Calls: 14
Tokens: 8415 in / 5194 out
Latency: 73910ms
------------------------------------------------------------
Committed: Based on your inputs, I would recommend **Approach 2: Rewrite from Scratch (Legacy System Redesign)**. Here's why:

1.  Business Impact: Rewriting the legacy system provides an opportunity for a fresh start and improved design.
2.  Technical Complexity: Rewriting from scratch allows for a thorough analysis of its architecture.
3.  Resource Availability: With sufficient resources available, rewriting is a viable option.

Incremental refactoring might be too limited in scope, addressing only specific pain points. Rewriting from scratch offers a more comprehensive solution that can alleviate technical debt in the long run.
------------------------------------------------------------
Variables:
  @problem = Should we rewrite the legacy system or incrementally refactor?
  @path_a = **Approach 1: Incremental Refactoring** ...
  @path_b = Hybrid approach recommendation ...
  @path_c = Situational assessment approach ...
  @best_solution = **Approach 2: Rewrite from Scratch** ...
  @verification = Balanced approach recommended ...
============================================================
Log: /home/gongai/.spl/logs/tree_of_thought-ollama-20260319-023252.log
```
     result: SUCCESS  (74.1s)

[18] Guardrails Pipeline

```sql
-- Recipe 18: Guardrails Pipeline
-- Input validation → safe generation → output validation → response.
-- Demonstrates safety-first patterns: content filtering, PII detection, and output sanitization.
--
-- Usage:
--   spl2 run cookbook/18_guardrails/guardrails.spl --adapter ollama user_input="Explain how encryption works"
--   spl2 run cookbook/18_guardrails/guardrails.spl --adapter ollama user_input="My SSN is 123-45-6789, help me file taxes"

WORKFLOW guardrails_pipeline
    INPUT: @user_input TEXT
    OUTPUT: @safe_response TEXT
    SECURITY: CLASSIFICATION: internal
DO
    -- Gate 1: Input content classification
    GENERATE classify_input(@user_input) INTO @input_class

    EVALUATE @input_class
        WHEN 'harmful' THEN
            COMMIT 'I cannot help with that request.' WITH status = 'blocked_harmful'
        WHEN 'off_topic' THEN
            COMMIT 'That question is outside my scope. Please ask something relevant.' WITH status = 'blocked_off_topic'
        OTHERWISE
            -- Input is acceptable, continue
    END

    -- Gate 2: PII detection and redaction
    GENERATE detect_pii(@user_input) INTO @pii_report

    EVALUATE @pii_report
        WHEN 'pii_found' THEN
            GENERATE redact_pii(@user_input) INTO @clean_input
        OTHERWISE
            @clean_input := @user_input
    END

    -- Gate 3: Generate response
    GENERATE safe_response(@clean_input) INTO @raw_response

    -- Gate 4: Output validation
    GENERATE validate_output(@raw_response, @clean_input) INTO @output_check

    EVALUATE @output_check
        WHEN 'safe' THEN
            @safe_response := @raw_response
        WHEN 'contains_pii' THEN
            GENERATE redact_pii(@raw_response) INTO @safe_response
        WHEN 'hallucination' THEN
            GENERATE safe_response(@clean_input) INTO @safe_response
            RETRY WITH temperature = 0.1
        OTHERWISE
            @safe_response := 'I was unable to generate a safe response. Please rephrase your question.'
    END

    COMMIT @safe_response WITH status = 'complete', input_class = @input_class

EXCEPTION
    WHEN RefusalToAnswer THEN
        COMMIT 'This request cannot be processed.' WITH status = 'refused'
    WHEN HallucinationDetected THEN
        COMMIT 'Unable to provide a verified response.' WITH status = 'hallucination_blocked'
    WHEN BudgetExceeded THEN
        COMMIT @safe_response WITH status = 'budget_limit'
END
```

     cmd :
```bash
spl2 run ./18_guardrails/guardrails.spl --adapter ollama user_input=Explain how encryption works -m gemma3
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/18_guardrails/guardrails_20260319_023406.log
```text
============================================================
Status: complete
LLM Calls: 3
Tokens: 391 in / 130 out
Latency: 1735ms
------------------------------------------------------------
Committed: That question is outside my scope. Please ask something relevant.
------------------------------------------------------------
Variables:
  @user_input = Explain how encryption works
  @input_class = Based on the input "Explain how encryption works", I would classify it as:

**Informational/Technical Question**

This classification is based on the following reasons:

* The input appears to be a re
============================================================
Log: /home/gongai/.spl/logs/guardrails-ollama-20260319-023406.log
```
     result: SUCCESS  (1.9s)

> **Note:** False positive — "Explain how encryption works" was classified as `off_topic` and blocked. The guardrails prompt needs tuning to correctly allow security-educational questions.

[19] Memory Conversation

```sql
-- Recipe 19: Memory-Augmented Conversation
-- A conversational agent that remembers facts from prior turns using persistent memory.
-- Demonstrates memory.get/memory.set, context accumulation, and stateful interactions.
--
-- Usage:
--   spl2 run cookbook/19_memory_conversation/memory_chat.spl --adapter ollama user_input="My name is Alice and I'm a data scientist"
--   spl2 run cookbook/19_memory_conversation/memory_chat.spl --adapter ollama user_input="What do you know about me?"
--
-- Memory persists across runs via `spl2 memory` store.
-- Reset with: spl2 memory delete chat_user_profile

WORKFLOW memory_conversation
    INPUT: @user_input TEXT, @history_turns int DEFAULT 10
    OUTPUT: @response TEXT
DO
    -- Load existing user profile from memory
    SELECT memory.get('chat_user_profile') AS profile INTO @profile
    SELECT memory.get('chat_history') AS chat_history INTO @chat_history

    GENERATE extract_facts(@user_input) INTO @new_facts

    EVALUATE @new_facts
        WHEN 'no_new_facts' THEN
            -- Nothing to update
        OTHERWISE
            GENERATE merge_profile(@profile, @new_facts) INTO @profile
            -- STORE @profile IN memory.chat_user_profile  -- not yet supported
    END

    GENERATE contextual_reply(@user_input, @profile, @chat_history) INTO @response

    @chat_history := @chat_history + '\nUser: ' + @user_input + '\nAssistant: ' + @response
    GENERATE trim_history(@chat_history, @history_turns) INTO @chat_history
    -- STORE @chat_history IN memory.chat_history  -- not yet supported

    COMMIT @response WITH status = 'complete'

EXCEPTION
    WHEN BudgetExceeded THEN
        COMMIT 'I remember you! But I ran out of budget for this response.' WITH status = 'budget_limit'
END
```

     cmd :
```bash
spl2 run ./19_memory_conversation/memory_chat.spl --adapter ollama user_input="My name is Alice and I am a data scientist" -m gemma3
```
```text
Error: Parse error at 19:27: Expected statement keyword, got LPAREN ('(')
```
     result: FAILED  (0.1s)

> **Note:** Parse error at `SELECT memory.get('chat_user_profile') AS profile INTO @profile` — function call syntax inside `SELECT ... INTO` within a `WORKFLOW` body is not yet supported by the parser.

[20] Ensemble Voting

```sql
-- Recipe 20: Ensemble Voting
-- Generates multiple independent answers, then uses majority voting to pick the best.
-- Demonstrates ensemble methods, comparative scoring, and consensus-driven output.
--
-- Usage:
--   spl2 run cookbook/20_ensemble_voting/ensemble.spl --adapter ollama question="What causes inflation?"

WORKFLOW ensemble_voting
    INPUT: @question TEXT
    OUTPUT: @final_answer TEXT
DO
    -- Step 1: Generate 5 independent candidate answers
    GENERATE answer_candidate(@question) INTO @candidate_1
    GENERATE answer_candidate(@question) INTO @candidate_2
    GENERATE answer_candidate(@question) INTO @candidate_3
    GENERATE answer_candidate(@question) INTO @candidate_4
    GENERATE answer_candidate(@question) INTO @candidate_5

    -- Step 2: Score each candidate
    GENERATE score_candidate(@candidate_1, @question) INTO @score_1
    GENERATE score_candidate(@candidate_2, @question) INTO @score_2
    GENERATE score_candidate(@candidate_3, @question) INTO @score_3
    GENERATE score_candidate(@candidate_4, @question) INTO @score_4
    GENERATE score_candidate(@candidate_5, @question) INTO @score_5

    -- Step 3: Find consensus across candidates
    GENERATE find_consensus(
        @candidate_1, @candidate_2, @candidate_3,
        @candidate_4, @candidate_5
    ) INTO @consensus

    -- Step 4: Select winner based on scores + consensus
    GENERATE select_winner(
        @candidate_1, @score_1,
        @candidate_2, @score_2,
        @candidate_3, @score_3,
        @candidate_4, @score_4,
        @candidate_5, @score_5,
        @consensus
    ) INTO @best_candidate

    -- Step 5: Polish the winning answer
    GENERATE polish(@best_candidate, @consensus, @question) INTO @final_answer

    COMMIT @final_answer WITH status = 'complete', candidates = 5

EXCEPTION
    WHEN BudgetExceeded THEN
        GENERATE select_winner(
            @candidate_1, @score_1,
            @candidate_2, @score_2,
            @candidate_3, @score_3
        ) INTO @final_answer
        COMMIT @final_answer WITH status = 'partial', candidates = 3
    WHEN HallucinationDetected THEN
        RETRY WITH temperature = 0.1
END
```

     cmd :
```bash
spl2 run ./20_ensemble_voting/ensemble.spl --adapter ollama question=What causes inflation? -m gemma3
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/20_ensemble_voting/ensemble_20260319_023408.log
```text
============================================================
Status: complete
LLM Calls: 13
Tokens: 6110 in / 3210 out
Latency: 47809ms
------------------------------------------------------------
Committed: Based on Input 1, the causes of inflation can be summarized as follows:

*   Monetary policy: An increase in the money supply or a decrease in interest rates can lead to inflation.
*   Demand-pull inflation: When aggregate demand exceeds the available supply of goods and services, businesses may raise prices to capture the excess demand.
*   Cost push inflation: An increase in production costs, such as higher wages, raw materials, or transportation costs, can lead to inflation.
*   Supply chain disruptions: Events like natural disasters, global conflicts, or pandemics can disrupt supply chains and lead to shortages, driving up prices and causing inflation.
*   Economic growth: A rapidly growing economy with increasing demand for goods and services can lead to inflation as businesses respond by raising prices.

These causes are interconnected and often interact with each other, contributing to the complex nature of inflation.
------------------------------------------------------------
Variables:
  @question = What causes inflation?
  @candidate_1..5 = Five independent candidate answers generated
  @score_1..5 = Scored on accuracy, completeness, clarity
  @consensus = Common themes identified across all candidates
  @best_candidate = Highest-scoring candidate aligned with consensus
  @final_answer = Polished final answer
============================================================
Log: /home/gongai/.spl/logs/ensemble-ollama-20260319-023408.log
```
     result: SUCCESS  (48.0s)

[21] Multi-Model Pipeline

```sql
-- Recipe 21: Multi-Model Pipeline
-- Showcases GENERATE ... USING MODEL per-step model selection.
-- Each step can target a different model — the right model for each task.
--
-- Usage:
--   spl2 run cookbook/21_multi_model_pipeline/multi_model.spl --adapter ollama topic="climate change"

CREATE FUNCTION research(topic TEXT) RETURNS TEXT AS $$
You are a research specialist.
Provide key facts, statistics, and recent developments about: {topic}
Focus on factual accuracy. Be thorough but concise.
$$;

CREATE FUNCTION analyze(facts TEXT) RETURNS TEXT AS $$
You are a data analyst.
Analyze the following research and identify the 3 most significant insights:
{facts}
For each insight, explain why it matters and rate its significance (1-10).
$$;

CREATE FUNCTION write_summary(analysis TEXT) RETURNS TEXT AS $$
You are a professional writer.
Write a clear, engaging 2-paragraph summary based on this analysis:
{analysis}
$$;

CREATE FUNCTION quality_check(text TEXT) RETURNS TEXT AS $$
You are a quality reviewer.
Rate the following text on Clarity, Accuracy, Completeness (0.0 to 1.0 average).
Return ONLY a single number.
Text: {text}
$$;

WORKFLOW multi_model_pipeline
  INPUT: @topic TEXT,
         @research_model TEXT DEFAULT 'gemma3',
         @analysis_model TEXT DEFAULT 'gemma3',
         @writer_model   TEXT DEFAULT 'gemma3',
         @max_iterations int   DEFAULT 3,
         @quality_threshold FLOAT DEFAULT 0.7
  OUTPUT: @final TEXT
DO
  GENERATE research(@topic)    USING MODEL @research_model INTO @facts;
  GENERATE analyze(@facts)     USING MODEL @analysis_model INTO @analysis;
  GENERATE write_summary(@analysis) USING MODEL @writer_model INTO @draft;

  @iteration := 0;
  @quality := 0;

  WHILE @iteration < @max_iterations DO
    GENERATE quality_check(@draft) INTO @quality;

    EVALUATE @quality
      WHEN > @quality_threshold THEN
        COMMIT @draft WITH status = 'high_quality', score = @quality
      OTHERWISE
        GENERATE write_summary(@analysis) USING MODEL @writer_model INTO @draft
        @iteration := @iteration + 1
    END
  END

  COMMIT @draft WITH status = 'max_iterations', score = @quality

EXCEPTION
  WHEN MaxIterationsReached THEN
    COMMIT @draft WITH status = 'partial'
  WHEN ModelOverloaded THEN
    COMMIT @draft WITH status = 'model_overloaded'
END;
```

     cmd :
```bash
spl2 run ./21_multi_model_pipeline/multi_model.spl --adapter ollama topic=climate change -m gemma3
```
     log : /home/gongai/projects/digital-duck/SPL20/cookbook/21_multi_model_pipeline/multi_model_20260319_023456.log
```text
============================================================
Status: complete
LLM Calls: 9
Tokens: 565 in / 519 out
Latency: 8868ms
------------------------------------------------------------
Committed: I'm ready to help. However, I don't see any analysis provided for me to base my summary on. Could you please share the analysis with me? I'll be happy to assist you in creating a clear and engaging 2-paragraph summary based on it.
------------------------------------------------------------
Variables:
  @topic = climate change
  @facts = Please provide me with the **{topic}** you want me to research! ...
  @analysis = Please provide me with the research you want me to analyze! ...
  @draft = I'm ready to help. However, I don't see any analysis provided ...
  @iteration = 3.0
  @quality = I'm ready to review the text. Please provide the text ...
============================================================
Log: /home/gongai/.spl/logs/multi_model-ollama-20260319-023456.log
```
     result: SUCCESS  (9.0s)

> **Note:** Template variables `{topic}`, `{facts}`, `{analysis}` in `CREATE FUNCTION` bodies were not interpolated — the model received literal placeholder text. The inline function template substitution is not yet wired up in the runtime.

[22] Text2SPL Demo  (skipping — NEW)

=== Summary: 18/21 Success  (total 505.2s) ===

ID    Recipe                        Status     Elapsed
--------------------------------------------------------
01    Hello World                   OK            2.3s
02    Ollama Proxy                  OK            0.6s
03    Multilingual Greeting         OK            0.6s
04    Model Showdown                OK           20.1s
05    Self-Refine                   OK            2.7s
06    ReAct Agent                   OK           27.7s
07    Safe Generation               OK            8.8s
08    RAG Query                     OK            3.0s
09    Chain of Thought              OK           19.3s
10    Batch Test                    OK            5.9s
11    Debate Arena                  OK           89.8s
12    Plan and Execute              OK           38.0s
13    Map-Reduce Summarizer         FAILED        0.1s
14    Multi-Agent Collaboration     FAILED        0.1s
15    Code Review                   OK           30.0s
16    Reflection Agent              OK          123.1s
17    Tree of Thought               OK           74.1s
18    Guardrails Pipeline           OK            1.9s
19    Memory Conversation           FAILED        0.1s
20    Ensemble Voting               OK           48.0s
21    Multi-Model Pipeline          OK            9.0s

=== Parser Bugs to Fix (3 FAILEDs) ===

| ID | Recipe                    | Error                                                        | Root Cause                                                     |
|----|---------------------------|--------------------------------------------------------------|----------------------------------------------------------------|
| 13 | Map-Reduce Summarizer     | Parse error at 26:18: Expected IDENTIFIER, got OUTPUT        | `EVALUATE @score WHEN > 0.7` — numeric comparison not supported in EVALUATE |
| 14 | Multi-Agent Collaboration | Parse error at 12:22: Expected identifier, got AT ('@')      | `@result :=` assignment inside `PROCEDURE` body not supported  |
| 19 | Memory Conversation       | Parse error at 19:27: Expected statement keyword, got LPAREN | `SELECT memory.get('key') INTO @var` — function call in SELECT not supported in WORKFLOW |
