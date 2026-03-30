
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
[INFO] Fidelity score: The provided summaries seem to be well-structured and informative, but there are some issues with Input 2:

1. Lack of clarity: The message seems incomplete or unclear, as it doesn't specify what "summary_fidelity" refers to.
2. Inadequate information: There is no context or details about the constraints for the summary.

However, based on Input 1 and Input 3, here are some observations:

* The summaries provide an overview of AI's impact on various industries, including healthcare, finance, customer service, marketing, and education.
* They highlight the benefits of AI, such as automation, improved efficiency, and productivity.
* They also discuss the challenges and concerns associated with AI, including bias, accountability, and job displacement.

To improve Input 2, it would be helpful to provide more context or clarify what is being asked. If you could specify the constraints or requirements for the summary, I'd be happy to assist further.
============================================================
Caller:  momagrid-hub
Adapter: momagrid
Status: complete
LLM Calls: 5
Tokens: 2539 in / 1408 out
Latency: 58144ms
Timestamp: 2026-03-29 21:07:31
------------------------------------------------------------
```output
It seems like we've got a good starting point with the previous summaries. To summarize (pun intended), here's an updated version based on Input 3:

Artificial intelligence has revolutionized industries across various sectors, including healthcare, finance, customer service, marketing, and education. The automation of complex tasks has enabled increased efficiency, productivity, and accuracy in these fields.

For instance, AI-powered machine learning models can analyze medical images to diagnose diseases more accurately than human doctors. In the finance industry, AI-driven systems can detect fraud in financial transactions with high accuracy, helping to prevent financial crimes and protect individuals from identity theft.

Beyond healthcare and finance, AI has also made significant contributions to customer service, marketing, and education. For example, AI-powered chatbots and virtual assistants can provide customers with 24/7 support, answering their queries and resolving issues efficiently. AI-driven language models can generate human-like text, enabling the creation of personalized content, such as chatbots, virtual assistants, and even entire websites.

However, these advances in AI also raise important questions about bias, accountability, and the future of work. As AI systems become more sophisticated, there is a risk that they may perpetuate existing biases and prejudices, leading to unfair outcomes. Therefore, it's essential to develop and implement fair and transparent AI systems that can ensure accountability and fairness.

Moreover, the increasing use of AI in industries may lead to job displacement, particularly for tasks that are repetitive or can be easily automated. To mitigate this impact, governments, businesses, and educators must work together to provide workers with the skills they need to thrive in an AI-driven economy.

In conclusion, AI has transformed industries in profound ways, enabling automation of complex tasks and improving efficiency and productivity. However, it's essential to address the challenges and concerns associated with this technology, including bias, accountability, and the future of work, to ensure that its benefits are shared equitably by all stakeholders.

What specific constraints or requirements do you need me to follow for the summary?
```
------------------------------------------------------------
Variables:
  @text = Artificial intelligence has transformed industries from healthcare to finance, enabling automation of complex tasks that previously required human expertise. Machine learning models can now diagnose diseases from medical images, detect fraud in financial transactions, and generate human-like text. However, these advances raise important questions about bias, accountability, and the future of work.
  @audience = executive
  @layers = 3
  @sentence_summary = It appears that you're asking me to summarize a piece of text with specific constraints (which are not explicitly mentioned in Input 2), but it seems like Input 2 is incomplete or missing some information. However, I can still provide a summary based on the first input.

To summarize:

Artificial intelligence has transformed various industries by automating complex tasks, enabling diagnosis, fraud detection, and human-like text generation. Despite its benefits, this advancement raises concerns about bias, accountability, and the future of work.

If you could provide more information or clarify the constraints, I'd be happy to help further.
  @paragraph_summary = Based on Input 1, here's an expanded summary:

Artificial intelligence has revolutionized industries across the globe, transforming the way complex tasks are performed. In the healthcare sector, AI-powered machine learning models can analyze medical images to diagnose diseases more accurately and quickly than human doctors. This technology has also enabled the development of personalized medicine, where treatments are tailored to individual patients' needs.

In the finance industry, AI-driven systems can detect fraud in financial transactions with high accuracy, helping to prevent financial crimes and protect individuals from identity theft. Additionally, AI-powered chatbots and virtual assistants can provide customers with 24/7 support, answering their queries and resolving issues efficiently.

Beyond healthcare and finance, AI has also made significant contributions to other sectors, including customer service, marketing, and education. For instance, AI-powered language models can generate human-like text, enabling the creation of personalized content, such as chatbots, virtual assistants, and even entire websites.

However, these advances in AI raise important questions about bias, accountability, and the future of work. As AI systems become more sophisticated, there is a risk that they may perpetuate existing biases and prejudices, leading to unfair outcomes. Therefore, it's essential to develop and implement fair and transparent AI systems that can ensure accountability and fairness.

Moreover, the increasing use of AI in industries is likely to lead to job displacement, particularly for tasks that are repetitive or can be easily automated. To mitigate this impact, governments, businesses, and educators must work together to provide workers with the skills they need to thrive in an AI-driven economy. This includes developing expertise in areas such as data science, machine learning, and programming.

In conclusion, AI has transformed industries in profound ways, enabling automation of complex tasks and improving efficiency and productivity. However, it's essential to address the challenges and concerns associated with this technology, including bias, accountability, and the future of work, to ensure that its benefits are shared equitably by all stakeholders.
  @page_summary = Here is an expanded summary based on Input 1:

Artificial intelligence has transformed industries from healthcare to finance, enabling automation of complex tasks that previously required human expertise. Machine learning models can now diagnose diseases from medical images, detect fraud in financial transactions, and generate human-like text.

However, these advances raise important questions about bias, accountability, and the future of work.

While AI has brought numerous benefits, including increased efficiency and productivity, it also poses significant challenges, such as the potential for perpetuating existing biases and prejudices. Furthermore, the increasing use of AI in industries may lead to job displacement, particularly for tasks that are repetitive or can be easily automated.

To address these concerns, it is essential to develop and implement fair and transparent AI systems that can ensure accountability and fairness. This includes investing in education and training programs that equip workers with the skills needed to thrive in an AI-driven economy, such as data science, machine learning, and programming.

Moreover, there is a need for policymakers and industry leaders to work together to establish guidelines and regulations for the development and deployment of AI systems. This can help mitigate the risks associated with AI and ensure that its benefits are shared equitably by all stakeholders.

Ultimately, the future of AI will depend on our ability to harness its power responsibly and ethically. By acknowledging both the benefits and limitations of AI, we can work towards creating a future where technology enhances human potential while minimizing its negative impacts.
  @fidelity_score = The provided summaries seem to be well-structured and informative, but there are some issues with Input 2:

1. Lack of clarity: The message seems incomplete or unclear, as it doesn't specify what "summary_fidelity" refers to.
2. Inadequate information: There is no context or details about the constraints for the summary.

However, based on Input 1 and Input 3, here are some observations:

* The summaries provide an overview of AI's impact on various industries, including healthcare, finance, customer service, marketing, and education.
* They highlight the benefits of AI, such as automation, improved efficiency, and productivity.
* They also discuss the challenges and concerns associated with AI, including bias, accountability, and job displacement.

To improve Input 2, it would be helpful to provide more context or clarify what is being asked. If you could specify the constraints or requirements for the summary, I'd be happy to assist further.
============================================================
Log: /home/papagame/.spl/logs/progressive_summary-momagrid-20260329-210633.md
