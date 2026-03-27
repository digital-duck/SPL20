
```bash
spl run ./34_progressive_summary/progressive_summary.spl --adapter ollama text=Artificial intelligence has transformed industries from healthcare to finance, enabling automation of complex tasks that previously required human expertise. Machine learning models can now diagnose diseases from medical images, detect fraud in financial transactions, and generate human-like text. However, these advances raise important questions about bias, accountability, and the future of work. audience=executive
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
[INFO] Fidelity score: Your expanded version of the statement accurately captures the impact of artificial intelligence on various industries and raises important questions about its implications. The additional points you mentioned, such as fairness, accountability, and job displacement, provide a more comprehensive understanding of the topic.

To further verify the summary's fidelity, I would like to suggest a few improvements:

1. Consider adding more specific examples or case studies to illustrate the applications of AI in healthcare and finance.
2. Provide more context on the potential risks associated with bias and accountability, such as data poisoning or algorithmic bias.
3. Expand on the discussion around job displacement by mentioning potential solutions, such as reskilling programs or social safety nets.

Here's an updated version incorporating these suggestions:

Artificial intelligence has revolutionized numerous industries, including healthcare, finance, and others, by automating complex tasks that previously required human expertise. This technological advancement has enabled the development of sophisticated machine learning models that can analyze medical images to diagnose diseases more accurately and detect fraudulent activities in financial transactions.

Moreover, AI-powered tools have made significant strides in generating high-quality, human-like text, opening up new possibilities for content creation and communication. The integration of AI in various sectors has not only improved efficiency but also created new opportunities for innovation and growth.

However, as AI continues to transform industries at an unprecedented rate, it also raises important questions about bias, accountability, and the future of work. For instance, how can we ensure that AI systems are fair and unbiased, particularly when dealing with sensitive data, such as medical records or financial information? Furthermore, what measures can be taken to mitigate the risks associated with job displacement in the age of automation?

For example, governments and organizations can invest in reskilling programs to help workers develop new skills, while also implementing policies to protect vulnerable populations. By engaging in open discussions about the ethics and governance of AI, we can work towards creating a future where these technologies complement human capabilities rather than replacing them.

Ultimately, understanding the implications of AI on society is crucial for harnessing its full potential while addressing the challenges it poses. As we move forward, it's essential to prioritize responsible AI development and deployment that prioritizes fairness, transparency, and accountability.
============================================================
Caller:  localhost
Adapter: ollama
Status: complete
LLM Calls: 5
Tokens: 2491 in / 1677 out
Latency: 24219ms
Timestamp: 2026-03-27 08:15:21
------------------------------------------------------------
```output
Based on Input 4, I will provide a revised summary package with additional context, examples, and suggestions for improvement.

Summary Package:

**Artificial Intelligence: Revolutionizing Industries and Shaping the Future**

Artificial intelligence has revolutionized numerous industries, including healthcare, finance, and others, by automating complex tasks that previously required human expertise. This technological advancement has enabled the development of sophisticated machine learning models that can analyze medical images to diagnose diseases more accurately and detect fraudulent activities in financial transactions.

Moreover, AI-powered tools have made significant strides in generating high-quality, human-like text, opening up new possibilities for content creation and communication. The integration of AI in various sectors has not only improved efficiency but also created new opportunities for innovation and growth.

However, as AI continues to transform industries at an unprecedented rate, it also raises important questions about bias, accountability, and the future of work. For instance, how can we ensure that AI systems are fair and unbiased, particularly when dealing with sensitive data, such as medical records or financial information? Furthermore, what measures can be taken to mitigate the risks associated with job displacement in the age of automation?

For example, governments and organizations can invest in reskilling programs to help workers develop new skills, while also implementing policies to protect vulnerable populations. By engaging in open discussions about the ethics and governance of AI, we can work towards creating a future where these technologies complement human capabilities rather than replacing them.

Ultimately, understanding the implications of AI on society is crucial for harnessing its full potential while addressing the challenges it poses. As we move forward, it's essential to prioritize responsible AI development and deployment that prioritizes fairness, transparency, and accountability.

Additional Context:

* The European Union has established a comprehensive set of regulations governing AI development and deployment, including the General Data Protection Regulation (GDPR) and the Artificial Intelligence Act.
* Companies like Google and Amazon have implemented AI-powered tools for content moderation and sentiment analysis, highlighting the potential benefits and challenges of these technologies in specific industries.

Potential Risks and Mitigation Strategies:

* Bias: Ensuring data quality, diversity, and representation can help mitigate bias in AI systems. Regular audits and testing can also identify and address biases early on.
* Accountability: Establishing clear lines of authority, responsibility, and liability can help ensure accountability for AI-related decisions and outcomes.
* Job Displacement: Implementing reskilling programs, social safety nets, and education initiatives can help workers adapt to changing job market conditions.

By acknowledging these challenges and working towards responsible AI development and deployment, we can harness the full potential of artificial intelligence while minimizing its negative impacts on society.
```
------------------------------------------------------------
Variables:
  @text = Artificial intelligence has transformed industries from healthcare to finance, enabling automation of complex tasks that previously required human expertise. Machine learning models can now diagnose diseases from medical images, detect fraud in financial transactions, and generate human-like text. However, these advances raise important questions about bias, accountability, and the future of work.
  @audience = executive
  @layers = 3
  @sentence_summary = It seems like you provided three inputs:

1. A statement about the impact of artificial intelligence on industries.
2. An empty summary constraints function (which I won't be able to use as it's not defined).
3. The word "executive".

Without more context or information, I can only provide a general response.

From Input 1, we can infer that AI is having a significant impact on various industries and raising important questions about its future implications.

If you could provide more context or clarify what you'd like me to summarize (using Input 2), I'll be happy to help further.
  @paragraph_summary = Based on your inputs, it seems that the task is to expand upon a summary related to artificial intelligence. However, since there is no defined function for "summary_constraints" and only one relevant input (Input 1), I will use Input 1 as the basis for expansion.

Here's an expanded version of the statement:

Artificial intelligence has revolutionized numerous industries, including healthcare, finance, and others, by automating complex tasks that previously required human expertise. This technological advancement has enabled the development of sophisticated machine learning models that can analyze medical images to diagnose diseases more accurately and detect fraudulent activities in financial transactions.

Moreover, AI-powered tools have made significant strides in generating high-quality, human-like text, opening up new possibilities for content creation and communication. The integration of AI in various sectors has not only improved efficiency but also created new opportunities for innovation and growth.

However, as AI continues to transform industries at an unprecedented rate, it also raises important questions about bias, accountability, and the future of work. For instance, how can we ensure that AI systems are fair and unbiased, particularly when dealing with sensitive data? Furthermore, what measures can be taken to mitigate the risks associated with job displacement in the age of automation?

Ultimately, understanding the implications of AI on society is crucial for harnessing its full potential while addressing the challenges it poses. By engaging in open discussions about the ethics and governance of AI, we can work towards creating a future where these technologies complement human capabilities rather than replacing them.
  @page_summary = Based on Input 1, here's an expanded summary:

Artificial intelligence has revolutionized numerous industries, including healthcare, finance, and others, by automating complex tasks that previously required human expertise. This technological advancement has enabled the development of sophisticated machine learning models that can analyze medical images to diagnose diseases more accurately and detect fraudulent activities in financial transactions.

Moreover, AI-powered tools have made significant strides in generating high-quality, human-like text, opening up new possibilities for content creation and communication. The integration of AI in various sectors has not only improved efficiency but also created new opportunities for innovation and growth.

However, as AI continues to transform industries at an unprecedented rate, it also raises important questions about bias, accountability, and the future of work. For instance, how can we ensure that AI systems are fair and unbiased, particularly when dealing with sensitive data? Furthermore, what measures can be taken to mitigate the risks associated with job displacement in the age of automation?

Ultimately, understanding the implications of AI on society is crucial for harnessing its full potential while addressing the challenges it poses. By engaging in open discussions about the ethics and governance of AI, we can work towards creating a future where these technologies complement human capabilities rather than replacing them.

The expansion considers Input 1 as the basis for the summary and adds more details and ideas to provide a comprehensive overview of artificial intelligence's impact on various industries.
  @fidelity_score = Your expanded version of the statement accurately captures the impact of artificial intelligence on various industries and raises important questions about its implications. The additional points you mentioned, such as fairness, accountability, and job displacement, provide a more comprehensive understanding of the topic.

To further verify the summary's fidelity, I would like to suggest a few improvements:

1. Consider adding more specific examples or case studies to illustrate the applications of AI in healthcare and finance.
2. Provide more context on the potential risks associated with bias and accountability, such as data poisoning or algorithmic bias.
3. Expand on the discussion around job displacement by mentioning potential solutions, such as reskilling programs or social safety nets.

Here's an updated version incorporating these suggestions:

Artificial intelligence has revolutionized numerous industries, including healthcare, finance, and others, by automating complex tasks that previously required human expertise. This technological advancement has enabled the development of sophisticated machine learning models that can analyze medical images to diagnose diseases more accurately and detect fraudulent activities in financial transactions.

Moreover, AI-powered tools have made significant strides in generating high-quality, human-like text, opening up new possibilities for content creation and communication. The integration of AI in various sectors has not only improved efficiency but also created new opportunities for innovation and growth.

However, as AI continues to transform industries at an unprecedented rate, it also raises important questions about bias, accountability, and the future of work. For instance, how can we ensure that AI systems are fair and unbiased, particularly when dealing with sensitive data, such as medical records or financial information? Furthermore, what measures can be taken to mitigate the risks associated with job displacement in the age of automation?

For example, governments and organizations can invest in reskilling programs to help workers develop new skills, while also implementing policies to protect vulnerable populations. By engaging in open discussions about the ethics and governance of AI, we can work towards creating a future where these technologies complement human capabilities rather than replacing them.

Ultimately, understanding the implications of AI on society is crucial for harnessing its full potential while addressing the challenges it poses. As we move forward, it's essential to prioritize responsible AI development and deployment that prioritizes fairness, transparency, and accountability.
============================================================
Log: /home/papagame/.spl/logs/progressive_summary-ollama-20260327-081457.md
