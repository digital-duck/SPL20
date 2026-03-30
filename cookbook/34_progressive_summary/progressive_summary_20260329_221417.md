
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
[INFO] Fidelity score: Based on your general summary, it appears that you are looking for a verification of the fidelity of a summary that captures the main points of Input 1.

To proceed, could you please specify what you would like to verify? For example:

* Are you looking to verify if the summary is accurate?
* Is there a specific aspect of the input or summary that you would like to focus on (e.g. AI's impact on industries, bias and accountability)?
* Do you want to compare the summary with Input 1, Input 2 (which does not exist), and Input 3?

Please let me know what your requirements are so I can assist you accordingly.
============================================================
Caller:  momagrid-hub
Adapter: momagrid
Status: complete
LLM Calls: 5
Tokens: 1327 in / 608 out
Latency: 32201ms
Timestamp: 2026-03-29 22:18:31
------------------------------------------------------------
```output
It seems like we're in a bit of a loop here!

To clarify, I think there's been a misunderstanding. You initially asked for a summary of Input 1 (which doesn't exist), and then provided some general information about artificial intelligence. Then, you mentioned that you'd like to proceed with Input 2, but since it doesn't exist either, we're not going anywhere.

However, I notice that you've provided input 5 ("executive") which doesn't seem related to the conversation at all. Could you please provide the actual Input 1, Input 2, and Input 3 so we can move forward with summarizing them?

If you'd like to provide a sample text for Input 1, I'd be happy to assist you in creating a summary package (Input 4). Please let me know how I can help!
```
------------------------------------------------------------
Variables:
  @text = Artificial intelligence has transformed industries from healthcare to finance, enabling automation of complex tasks that previously required human expertise. Machine learning models can now diagnose diseases from medical images, detect fraud in financial transactions, and generate human-like text. However, these advances raise important questions about bias, accountability, and the future of work.
  @audience = executive
  @layers = 3
  @sentence_summary = Unfortunately, there is no summary constraints provided (Input 2) for me to use in summarizing Input 1. If you provide the summary constraints, I can assist with a more focused and concise summary of Input 1.

If not, here's a general summary:

Artificial intelligence has revolutionized industries by automating complex tasks, enabling diagnosis from medical images, fraud detection, and human-like text generation. However, these advancements raise important questions about bias, accountability, and the future of work.
  @paragraph_summary = Based on Input 1 alone, I can provide a summary:

Artificial intelligence has transformed industries by automating complex tasks, enabling diagnosis from medical images, fraud detection, and human-like text generation. However, these advancements raise important questions about bias, accountability, and the future of work.

If you'd like to proceed with Input 2 and Input 3, I can help provide a more focused summary. Could you please provide the summary constraints for Input 2?
  @page_summary = Based on Input 1 alone, the summary constraints could be:

* Length: 50-75 words
* Tone: Informative and neutral
* Focus: Highlighting the transformation of industries through AI and its implications.
* Key points to include: Automation of complex tasks, diagnosis from medical images, fraud detection, human-like text generation, bias, accountability, and the future of work.

Please let me know if you'd like me to proceed with Input 2 and provide a more focused summary.
  @fidelity_score = Based on your general summary, it appears that you are looking for a verification of the fidelity of a summary that captures the main points of Input 1.

To proceed, could you please specify what you would like to verify? For example:

* Are you looking to verify if the summary is accurate?
* Is there a specific aspect of the input or summary that you would like to focus on (e.g. AI's impact on industries, bias and accountability)?
* Do you want to compare the summary with Input 1, Input 2 (which does not exist), and Input 3?

Please let me know what your requirements are so I can assist you accordingly.
============================================================
Log: /home/hpgong/.spl/logs/progressive_summary-momagrid-20260329-221759.md
