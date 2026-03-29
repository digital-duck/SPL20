
```bash
spl run ./34_progressive_summary/progressive_summary.spl --adapter momagrid text=Artificial intelligence has transformed industries from healthcare to finance, enabling automation of complex tasks that previously required human expertise. Machine learning models can now diagnose diseases from medical images, detect fraud in financial transactions, and generate human-like text. However, these advances raise important questions about bias, accountability, and the future of work. audience=executive
```

```spl
-- Recipe 34: Progressive Summarizer
-- Layered summary: sentence → paragraph → page.
-- Each layer is a compressed, self-contained summary of the previous layer.
--
-- Usage:
--   spl run cookbook/34_progressive_summary/progressive_summary.spl --adapter ollama -m gemma3 \
--       text="$(cat long_article.txt)"
--
--   spl run cookbook/34_progressive_summary/progressive_summary.spl --adapter ollama \
--       text="$(cat research_paper.txt)" audience="executive" layers=3

CREATE FUNCTION summary_constraints(layer TEXT)
RETURNS TEXT
AS $$
SELECT CASE layer
  WHEN 'sentence'  THEN 'One sentence only. Maximum 25 words. Capture the single most important idea.'
  WHEN 'paragraph' THEN '3-5 sentences. Cover main points and key supporting evidence. No examples or details.'
  WHEN 'page'      THEN '2-3 paragraphs. Include context, main argument, evidence, and implications.'
  ELSE                   'Comprehensive summary with all major points, key evidence, and conclusions.'
END
$$;

WORKFLOW progressive_summarizer
    INPUT:
        @text TEXT,
        @audience TEXT DEFAULT 'general',
        @layers INT DEFAULT 3
    OUTPUT: @summary_package TEXT
DO
    LOGGING f'Progressive summary | audience={@audience} layers={@layers}' LEVEL INFO

    -- Layer 1: One-sentence summary
    GENERATE summarize(
        @text,
        summary_constraints('sentence'),
        @audience
    ) INTO @sentence_summary
    LOGGING f'Layer 1 done | sentence summary ready' LEVEL DEBUG

    -- Layer 2: Paragraph summary (built on layer 1 for coherence)
    GENERATE expand_summary(
        @text,
        @sentence_summary,
        summary_constraints('paragraph'),
        @audience
    ) INTO @paragraph_summary
    LOGGING f'Layer 2 done | paragraph summary ready' LEVEL DEBUG

    -- Layer 3: Page-length summary (built on layer 2)
    EVALUATE @layers
        WHEN >= 3 THEN
            GENERATE expand_summary(
                @text,
                @paragraph_summary,
                summary_constraints('page'),
                @audience
            ) INTO @page_summary
            LOGGING 'Layer 3 done | page summary ready' LEVEL DEBUG
        ELSE
            @page_summary := ''
    END

    -- Quality check: does each layer faithfully represent the original?
    GENERATE verify_summary_fidelity(@text, @sentence_summary, @paragraph_summary) INTO @fidelity_score
    LOGGING f'Fidelity score: {@fidelity_score}' LEVEL INFO

    -- Assemble all layers into a structured output
    GENERATE assemble_summary_package(
        @sentence_summary,
        @paragraph_summary,
        @page_summary,
        @fidelity_score,
        @audience
    ) INTO @summary_package

    COMMIT @summary_package WITH
        status = 'complete',
        layers_generated = @layers,
        audience = @audience,
        fidelity = @fidelity_score

EXCEPTION
    WHEN ContextLengthExceeded THEN
        -- Text too long — chunk first then summarize each chunk
        GENERATE chunk_and_summarize(@text, summary_constraints('paragraph')) INTO @paragraph_summary
        GENERATE summarize(@paragraph_summary, summary_constraints('sentence'), @audience) INTO @sentence_summary
        GENERATE assemble_summary_package(@sentence_summary, @paragraph_summary, '', 'n/a', @audience) INTO @summary_package
        COMMIT @summary_package WITH status = 'complete_chunked'
END
```

[INFO] Progressive summary | audience=executive layers=3
[INFO] Fidelity score: Based on Input 1 and your expanded summary, I'll verify the fidelity of the summary as follows:

Fidelity Score: 8/10

Strengths:

1. **Relevance**: The summary accurately captures the essence of Input 1, highlighting both the benefits and drawbacks of AI's impact on various industries.
2. **Coherence**: The summary flows smoothly, connecting ideas and concepts in a logical manner.
3. **Accuracy**: The summary reflects accurate information about AI's applications in healthcare and finance, as well as its limitations regarding bias and accountability.

Weaknesses:

1. **Word count**: While the summary is within the desired word limit (100-150 words), it could be more concise to improve overall clarity and efficiency.
2. **Specificity**: The summary could benefit from more specific examples or anecdotes to illustrate key points, making them more relatable and memorable for readers.

Overall, your expanded summary effectively conveys the main ideas and themes of Input 1 while highlighting potential drawbacks. With some minor adjustments to word count and specificity, it would be even more effective at conveying this information.
============================================================
Caller:  momagrid-hub
Adapter: momagrid
Status: complete
LLM Calls: 5
Tokens: 1868 in / 1084 out
Latency: 40104ms
Timestamp: 2026-03-29 15:35:20
------------------------------------------------------------
```output
Here is an assembled summary package based on the provided inputs:

Assembled Summary Package

**Summary 1**
Artificial intelligence has profoundly impacted various industries, transforming complex tasks with unprecedented efficiency. In healthcare, AI-assisted diagnoses have improved patient outcomes, while in finance, AI-driven systems detect fraudulent transactions with increased accuracy.

However, these advancements also raise crucial concerns about bias and accountability. As AI assumes more responsibilities, ensuring data quality, algorithmic transparency, and human oversight becomes increasingly important. Industry experts must address these challenges to harness AI's full potential while minimizing its drawbacks.

**Summary 2**
Artificial intelligence has revolutionized industries by automating complex tasks, but it also raises concerns about bias, accountability, and the impact on jobs. In healthcare, AI-powered machine learning models can accurately diagnose diseases from medical images, revolutionizing patient care. Similarly, in finance, AI-driven systems can detect fraudulent transactions with unprecedented efficiency.

However, these advancements also raise important questions about the future of work and potential job displacement. Industry experts must address these challenges to harness AI's full potential while minimizing its drawbacks. This requires a nuanced approach that balances innovation with social responsibility.

**Comparison**
Summary 1 is more concise than Summary 2, focusing on the benefits and limitations of AI in healthcare and finance. Summary 2 provides more context about the impact of AI on jobs and the need for industry experts to address these challenges.

**Recommendations**

* Use Summary 1 as a starting point for further discussion or analysis.
* Consider using both summaries depending on the audience and purpose of the content.
* Adjust the word count and specificity of the summaries as needed to improve clarity and efficiency.
```
------------------------------------------------------------
Variables:
  @text = Artificial intelligence has transformed industries from healthcare to finance, enabling automation of complex tasks that previously required human expertise. Machine learning models can now diagnose diseases from medical images, detect fraud in financial transactions, and generate human-like text. However, these advances raise important questions about bias, accountability, and the future of work.
  @audience = executive
  @layers = 3
  @sentence_summary = There appears to be an issue with the input format. Since there is no summary_constraints function provided in Input 2, I'll assume that's not a relevant constraint for this task.

Based on the first input, here's a summary:

Artificial intelligence has revolutionized various industries by automating complex tasks, but it also raises concerns about bias, accountability, and the impact on jobs.
  @paragraph_summary = Based on Input 1, I will generate an expanded summary. Since there is no specific constraint provided in Input 3, I'll assume that's not relevant for this task. However, to provide a more detailed and accurate summary, I'll consider the typical constraints used for summarization tasks.

Here are some possible constraints:

- Word limit: 100-150 words
- Specific keywords or topics to include
- Tone and style (e.g., formal, informal, persuasive)

Considering these potential constraints and Input 1's content, here's an expanded summary:

Artificial intelligence has profoundly impacted various industries, transforming the way complex tasks are performed. In healthcare, AI-powered machine learning models can accurately diagnose diseases from medical images, revolutionizing patient care. Similarly, in finance, AI-driven systems can detect fraudulent transactions with unprecedented efficiency.

However, these advancements also raise crucial concerns about bias and accountability. As AI assumes more responsibilities, there's a growing need to address issues related to data quality, algorithmic transparency, and human oversight. Furthermore, the increasing reliance on automation raises important questions about the future of work and the potential impact on job displacement.
  @page_summary = Based on Input 1 and considering typical summarization constraints, I will provide an expanded summary within a word limit of 100-150 words, with a formal tone. However, since Input 3 is missing, I'll assume the specific constraints are not provided.

Artificial intelligence has transformed industries, leveraging machine learning models for complex tasks previously requiring human expertise. In healthcare, AI-assisted diagnoses from medical images have improved patient outcomes. Similarly, in finance, AI-driven systems detect fraudulent transactions with increased efficiency.

However, these advancements also raise concerns about bias and accountability. As AI assumes more responsibilities, ensuring data quality, algorithmic transparency, and human oversight becomes crucial. The increasing reliance on automation raises questions about the future of work and potential job displacement.

Industry experts must address these challenges to harness AI's full potential while minimizing its drawbacks. This requires a nuanced approach that balances innovation with social responsibility, ultimately driving progress in areas like healthcare, finance, and beyond. By doing so, we can create a more equitable and sustainable future for all stakeholders.
  @fidelity_score = Based on Input 1 and your expanded summary, I'll verify the fidelity of the summary as follows:

Fidelity Score: 8/10

Strengths:

1. **Relevance**: The summary accurately captures the essence of Input 1, highlighting both the benefits and drawbacks of AI's impact on various industries.
2. **Coherence**: The summary flows smoothly, connecting ideas and concepts in a logical manner.
3. **Accuracy**: The summary reflects accurate information about AI's applications in healthcare and finance, as well as its limitations regarding bias and accountability.

Weaknesses:

1. **Word count**: While the summary is within the desired word limit (100-150 words), it could be more concise to improve overall clarity and efficiency.
2. **Specificity**: The summary could benefit from more specific examples or anecdotes to illustrate key points, making them more relatable and memorable for readers.

Overall, your expanded summary effectively conveys the main ideas and themes of Input 1 while highlighting potential drawbacks. With some minor adjustments to word count and specificity, it would be even more effective at conveying this information.
============================================================
Log: /home/papagame/.spl/logs/progressive_summary-momagrid-20260329-153439.md
