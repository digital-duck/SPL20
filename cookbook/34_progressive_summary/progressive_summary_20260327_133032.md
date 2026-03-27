
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
[INFO] Fidelity score: Based on your response, I'll provide a possible Input 2 (summary_constraints) that could help create a specific summary.

Input 1:
Artificial intelligence has transformed industries from healthcare to finance, enabling automation of complex tasks that previously required human expertise. Machine learning models can now diagnose diseases from medical images, detect fraud in financial transactions, and generate human-like text. However, these advances raise important questions about bias, accountability, and the future of work.

Input 2:
Summary Constraints: 
- Word Count: 50-75 words
- Tone: Neutral/Informative
- Key Points to Include:
	+ Impact on industries (healthcare, finance)
	+ Concerns about bias, accountability, and future of work
	+ Brief mention of AI's potential benefits

Expanded Summary:

"Artificial intelligence is transforming industries with automation capabilities. In healthcare, AI-powered diagnostics show promise, but concerns remain over data quality and algorithmic bias. Similarly, financial systems have increased efficiency, yet raise worries about job displacement. As AI assumes more decision-making roles, accountability becomes crucial. Despite challenges, AI has the potential to address pressing global issues like climate change and economic inequality."

Please note that you can adjust or add constraints as per your requirements.

Let me know if this meets your needs or if you need further assistance!
============================================================
Caller:  momagrid-hub
Adapter: momagrid
Status: complete
LLM Calls: 5
Tokens: 2458 in / 1130 out
Latency: 186139ms
Timestamp: 2026-03-27 13:37:47
------------------------------------------------------------
```output
Based on Input 4 (Expanded Summary), I'll provide a revised summary that meets the specified constraints:

Revised Summary: "Artificial intelligence is transforming industries with automation capabilities, raising concerns about bias and accountability. In healthcare, AI-powered diagnostics show promise, while financial systems have increased efficiency. However, these advances also raise worries about job displacement. As AI assumes more decision-making roles, accountability becomes crucial for harnessing its full potential."

This revised summary adheres to the specified constraints:

* Word Count: 50-75 words
* Tone: Neutral/Informative
* Key Points to Include:
	+ Impact on industries (healthcare, finance)
	+ Concerns about bias and accountability
	+ Brief mention of job displacement

Please let me know if this meets your requirements or if you need further assistance!
```
------------------------------------------------------------
Variables:
  @text = Artificial intelligence has transformed industries from healthcare to finance, enabling automation of complex tasks that previously required human expertise. Machine learning models can now diagnose diseases from medical images, detect fraud in financial transactions, and generate human-like text. However, these advances raise important questions about bias, accountability, and the future of work.
  @audience = executive
  @layers = 3
  @sentence_summary = It appears that you have not provided a summary constraints definition (Input 2) or any additional information to work with. 

However, based on Input 1, I can provide a general summary:

"Artificial intelligence is revolutionizing industries by automating complex tasks, but raises concerns about bias and accountability."

If you could provide the missing inputs, I'd be happy to help you create a more specific summary that meets your requirements.
  @paragraph_summary = Based on Input 1, here's an expanded version with additional information:

Artificial intelligence has transformed industries from healthcare to finance, enabling automation of complex tasks that previously required human expertise. Machine learning models can now diagnose diseases from medical images, detect fraud in financial transactions, and generate human-like text. However, these advances raise important questions about bias, accountability, and the future of work.

For instance, AI-powered diagnostic tools have shown significant promise in improving patient outcomes, but concerns remain about data quality, algorithmic bias, and potential misdiagnoses. Similarly, AI-driven financial systems have increased efficiency and reduced errors, but also raise worries about job displacement and unequal access to technology.

Moreover, as AI assumes more decision-making roles, accountability becomes a pressing issue. Who is responsible when an AI system makes an error or produces biased results? Moreover, the rapid pace of technological change is outpacing our ability to develop regulations and ethical frameworks, leaving us with a sense of uncertainty about the long-term implications.

However, despite these challenges, many experts believe that AI has the potential to solve some of humanity's most pressing problems. By analyzing vast amounts of data, identifying patterns, and making predictions, AI can help address issues like climate change, economic inequality, and access to education.

Overall, the impact of AI on society is multifaceted and far-reaching, requiring careful consideration of both its benefits and limitations. As we continue to develop and deploy AI technologies, it's essential that we prioritize ethics, accountability, and transparency to ensure that these powerful tools are used for the greater good.

To better meet your requirements, I would need Input 2 (summary_constraints) or additional context constraints, but based on this, here is a revised summary:

Expanded Summary: "Artificial intelligence has transformed industries by automating complex tasks, raising concerns about bias, accountability, and the future of work. As AI assumes more decision-making roles, we must prioritize ethics, transparency, and accountability to ensure these powerful tools are used for the greater good."
  @page_summary = Based on Input 2 (expanded version), I can identify the following constraints:

1. summary length: The expanded summary should not exceed a certain word count.
2. tone: The summary should maintain a formal and informative tone.
3. key points: The summary should cover the main points from the expanded text, including concerns about bias, accountability, and the future of work.

To better meet these constraints, I can revise the summary to fit within a specific word count while maintaining the required tone and covering the essential key points.

Here is a revised summary based on Input 2:

Expanded Summary: "Artificial intelligence has transformed industries with automation, raising concerns about bias, accountability, and the future of work. As AI assumes more decision-making roles, prioritizing ethics, transparency, and accountability is crucial to harness its full potential for human benefit."

Please provide the specific constraints from Input 3 (summary_constraints(...)) if you'd like me to revise the summary further.
  @fidelity_score = Based on your response, I'll provide a possible Input 2 (summary_constraints) that could help create a specific summary.

Input 1:
Artificial intelligence has transformed industries from healthcare to finance, enabling automation of complex tasks that previously required human expertise. Machine learning models can now diagnose diseases from medical images, detect fraud in financial transactions, and generate human-like text. However, these advances raise important questions about bias, accountability, and the future of work.

Input 2:
Summary Constraints: 
- Word Count: 50-75 words
- Tone: Neutral/Informative
- Key Points to Include:
	+ Impact on industries (healthcare, finance)
	+ Concerns about bias, accountability, and future of work
	+ Brief mention of AI's potential benefits

Expanded Summary:

"Artificial intelligence is transforming industries with automation capabilities. In healthcare, AI-powered diagnostics show promise, but concerns remain over data quality and algorithmic bias. Similarly, financial systems have increased efficiency, yet raise worries about job displacement. As AI assumes more decision-making roles, accountability becomes crucial. Despite challenges, AI has the potential to address pressing global issues like climate change and economic inequality."

Please note that you can adjust or add constraints as per your requirements.

Let me know if this meets your needs or if you need further assistance!
============================================================
Log: /home/papagame/.spl/logs/progressive_summary-momagrid-20260327-133440.md
