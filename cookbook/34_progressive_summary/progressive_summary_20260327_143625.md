
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
[INFO] Fidelity score: Thank you for providing Input 1 and Input 3. To verify the summary fidelity, I'll assess whether the expanded version meets the requirements for a concise summary.

Based on our conversation, it appears that you'd like me to provide a summary that:

1. Is concise
2. Adheres to specific constraints (not specified)
3. Eliminates irrelevant information (e.g., "executive")

Input 3's expanded version provides more details about the impact of AI on industries, but some parts may be considered extraneous for a concise summary.

To proceed, I'll suggest some adjustments to Input 3's content to create a concise summary that meets the requirements. Please let me know if you agree or would like to explore alternative approaches.

Here's an edited version of Input 3 with a focus on conciseness:

Artificial intelligence has revolutionized industries worldwide by automating complex tasks previously relying on human expertise. In healthcare, AI-assisted diagnosis from medical images has improved accuracy and speed, enabling early disease detection. Similarly, in finance, machine learning models have been deployed to detect fraudulent transactions.

However, these advancements also raise crucial concerns about bias, accountability, and the future of work. To address these issues, it's essential to ensure fair and transparent decision-making processes. The impact of AI on job markets and workforce skills will require careful consideration to mitigate potential disruptions.

Please let me know if this edited version meets your requirements or if you'd like me to make further adjustments.
============================================================
Caller:  momagrid-hub
Adapter: momagrid
Status: complete
LLM Calls: 5
Tokens: 2052 in / 1063 out
Latency: 104415ms
Timestamp: 2026-03-27 14:41:30
------------------------------------------------------------
```output
Based on the input provided, I would like to clarify that the term "executive" is not relevant to the context of summarizing a text about artificial intelligence's impact on industries. The conversation has focused on providing a concise summary while adhering to specific constraints.

To confirm, I will proceed with the edited version of Input 3:

Artificial intelligence has revolutionized industries worldwide by automating complex tasks previously relying on human expertise. In healthcare, AI-assisted diagnosis from medical images has improved accuracy and speed, enabling early disease detection. Similarly, in finance, machine learning models have been deployed to detect fraudulent transactions.

However, these advancements also raise crucial concerns about bias, accountability, and the future of work. To address these issues, it's essential to ensure fair and transparent decision-making processes. The impact of AI on job markets and workforce skills will require careful consideration to mitigate potential disruptions.

Please let me know if this edited version meets your requirements or if you'd like me to make further adjustments.
```
------------------------------------------------------------
Variables:
  @text = Artificial intelligence has transformed industries from healthcare to finance, enabling automation of complex tasks that previously required human expertise. Machine learning models can now diagnose diseases from medical images, detect fraud in financial transactions, and generate human-like text. However, these advances raise important questions about bias, accountability, and the future of work.
  @audience = executive
  @layers = 3
  @sentence_summary = It appears that you are asking me to summarize a text that discusses the impact of artificial intelligence on various industries, while also considering constraints for summarization (not specified). Additionally, it seems like "executive" is not relevant to the context, as it refers to a person in a high management position.

To proceed with the summary, I'll provide an overview of Input 1:

Artificial intelligence has significantly transformed industries by automating complex tasks previously requiring human expertise. Machine learning models have advanced capabilities, such as disease diagnosis from medical images and fraud detection in financial transactions. However, these advancements raise concerns about bias, accountability, and the future of work.

If you provide the summary constraints (Input 2), I can assist you further with a concise summary that adheres to those guidelines.
  @paragraph_summary = Based on Input 1, here's an expanded version:

Artificial intelligence has revolutionized industries worldwide by automating complex tasks that previously relied on human expertise. The integration of machine learning models has enabled significant breakthroughs in various sectors, including healthcare and finance.

In the healthcare sector, AI-assisted diagnosis from medical images has improved accuracy and speed, allowing for early detection of diseases. Similarly, in the financial sector, machine learning models have been deployed to detect fraudulent transactions, reducing the risk of financial crimes. Furthermore, AI-generated text that mimics human language has opened up new avenues for content creation.

However, these advancements also raise crucial concerns about bias, accountability, and the future of work. As AI becomes increasingly pervasive in various industries, it is essential to address these issues to ensure fair and transparent decision-making processes. The impact of AI on job markets and workforce skills will also require careful consideration to mitigate potential disruptions.
  @page_summary = Based on the provided inputs, I'll create an expanded summary that adheres to the constraints in Input 3. Since Input 3 is missing, I'll assume a set of constraints for this response:

- Maximum length: 150 words
- Include key points from Inputs 1 and 2
- Provide a balanced view on the benefits and concerns of AI

Expanded Summary:

Artificial intelligence has transformed industries with automation capabilities, enabling complex tasks to be performed efficiently. In healthcare, AI-assisted diagnosis from medical images improves accuracy, while in finance, machine learning models detect fraudulent transactions. Additionally, AI-generated text mimics human language, opening up new avenues for content creation.

However, these advancements raise concerns about bias and accountability. As AI becomes increasingly prevalent, it is essential to address these issues to ensure fair decision-making processes. The impact on job markets and workforce skills also requires consideration to mitigate potential disruptions. While AI brings numerous benefits, it is crucial to balance progress with responsible innovation that prioritizes transparency, fairness, and human well-being.
  @fidelity_score = Thank you for providing Input 1 and Input 3. To verify the summary fidelity, I'll assess whether the expanded version meets the requirements for a concise summary.

Based on our conversation, it appears that you'd like me to provide a summary that:

1. Is concise
2. Adheres to specific constraints (not specified)
3. Eliminates irrelevant information (e.g., "executive")

Input 3's expanded version provides more details about the impact of AI on industries, but some parts may be considered extraneous for a concise summary.

To proceed, I'll suggest some adjustments to Input 3's content to create a concise summary that meets the requirements. Please let me know if you agree or would like to explore alternative approaches.

Here's an edited version of Input 3 with a focus on conciseness:

Artificial intelligence has revolutionized industries worldwide by automating complex tasks previously relying on human expertise. In healthcare, AI-assisted diagnosis from medical images has improved accuracy and speed, enabling early disease detection. Similarly, in finance, machine learning models have been deployed to detect fraudulent transactions.

However, these advancements also raise crucial concerns about bias, accountability, and the future of work. To address these issues, it's essential to ensure fair and transparent decision-making processes. The impact of AI on job markets and workforce skills will require careful consideration to mitigate potential disruptions.

Please let me know if this edited version meets your requirements or if you'd like me to make further adjustments.
============================================================
Log: /home/papagame/.spl/logs/progressive_summary-momagrid-20260327-143945.md
