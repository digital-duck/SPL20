
```bash
spl run ./34_progressive_summary/progressive_summary.spl --adapter ollama -m gemma3 text=Artificial intelligence has transformed industries from healthcare to finance, enabling automation of complex tasks that previously required human expertise. Machine learning models can now diagnose diseases from medical images, detect fraud in financial transactions, and generate human-like text. However, these advances raise important questions about bias, accountability, and the future of work. audience=executive
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
RETURNS TEXT AS $$
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
[INFO] Fidelity score: Thank you for the detailed explanation of the task. Based on your analysis, it seems that:

* Input 1 provides an overview of the impact of artificial intelligence on industries and raises important questions about bias, accountability, and the future of work.
* Input 2 is missing and lacks sufficient information to provide a summary based on Input 1 alone.
* The mention of "summary_constraints" refers to guidelines for summarization, but specific constraints are not provided.
* Input 3 appears to be an indication that no additional information is available to expand upon the first statement.

To proceed with verifying the fidelity of the summary, I would like to request clarification on Input 2. Could you please provide more context or information about what Input 2 entails? This will help me understand the content and constraints for providing a summary.

Additionally, if there are specific "summary_constraints" that need to be met, it would be helpful to know what those constraints are (e.g., word limit, tone, specific keywords, etc.).
============================================================
Status: complete
LLM Calls: 5
Tokens: 1870 in / 932 out
Latency: 12660ms
------------------------------------------------------------
```output
It seems like you're trying to provide a response to an incomplete or unclear task. I'll do my best to help.

Based on the inputs provided, it appears that there is no clear request for a summary package, and some of the inputs seem to be missing context or information.

Input 1 mentions that there's not enough information to summarize based on Input 1 alone, but it doesn't provide any specific details about what needs summarizing.

Input 2 seems to be missing, and Input 3 appears to be a reference to a function or module named "summary_constraints" without providing any further details.

Input 4 mentions the word "executive," but it does not provide clear context for its relevance to the existing input.

Given this information, I'd like to request clarification on what the task is and what specific information is needed to proceed with summarizing text. Could you please provide more context or detail about what you're trying to accomplish?
```
------------------------------------------------------------
Variables:
  @text = Artificial intelligence has transformed industries from healthcare to finance, enabling automation of complex tasks that previously required human expertise. Machine learning models can now diagnose diseases from medical images, detect fraud in financial transactions, and generate human-like text. However, these advances raise important questions about bias, accountability, and the future of work.
  @audience = executive
  @layers = 3
  @sentence_summary = There is not enough information to summarize based on Input 1 alone. 

Input 2 is missing.

However, since you've mentioned the term "summary_constraints", I assume it refers to a set of constraints that must be met when summarizing text.

If we consider summary_constraints as a general guideline for summarization, here are some possible constraints:

- Be concise: The summary should not exceed a certain number of words.
- Focus on key points: The summary should highlight the most important information in the original text.
- Use clear language: The summary should use simple and easy-to-understand language to convey the main ideas.

If you provide more specific constraints or clarify Input 2, I'd be happy to help further.
  @paragraph_summary = Based on the input provided, it seems that there is no additional information to expand upon. The first statement discusses the impact of artificial intelligence on various industries and raises important questions about bias, accountability, and the future of work.

The second statement indicates that there is not enough information to provide a summary, which suggests that Input 2 is missing or incomplete.

Input 3 seems to be referring to a function or module named "summary_constraints" without providing any further details. Without more context or information about what this constraint entails, it's challenging to proceed with summarizing the text.

Input 4 mentions the word "executive," but it does not provide clear context for its relevance to the existing input.

Given the current information, I would like to request clarification on Input 2 to better understand the content and constraints for providing a summary.
  @page_summary = To provide a meaningful expansion of the original text, we need more context or information. Based on your inputs:

1. The initial statement discusses AI's impact on various industries and raises questions about bias, accountability, and work.
2. You're unsure if there's enough information to expand upon this text.
3. There's a mention of "summary_constraints" without further details.
4. The word "executive" is mentioned without context.

To proceed with providing a summary, could you please clarify or provide more specific details about:

- Input 2: What specific aspects of the original statement would you like to expand upon? Are there particular concerns about bias, accountability, or work that require further clarification?
- Input 3: Could you please describe what "summary_constraints" entails and how it relates to expanding the summary of the AI impact on industries?
- Input 4: How does the mention of an "executive" relate to your request for a summary or the original text?

With clearer guidance, I can better assist in creating a comprehensive expansion of the original statement.
  @fidelity_score = Thank you for the detailed explanation of the task. Based on your analysis, it seems that:

* Input 1 provides an overview of the impact of artificial intelligence on industries and raises important questions about bias, accountability, and the future of work.
* Input 2 is missing and lacks sufficient information to provide a summary based on Input 1 alone.
* The mention of "summary_constraints" refers to guidelines for summarization, but specific constraints are not provided.
* Input 3 appears to be an indication that no additional information is available to expand upon the first statement.

To proceed with verifying the fidelity of the summary, I would like to request clarification on Input 2. Could you please provide more context or information about what Input 2 entails? This will help me understand the content and constraints for providing a summary.

Additionally, if there are specific "summary_constraints" that need to be met, it would be helpful to know what those constraints are (e.g., word limit, tone, specific keywords, etc.).
============================================================
Log: /home/gongai/.spl/logs/progressive_summary-ollama-20260325-162344.md
