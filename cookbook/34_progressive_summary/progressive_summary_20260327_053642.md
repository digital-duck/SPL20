
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
[INFO] Fidelity score: To verify summary fidelity for Input 1, Input 2, and Input 3, I'll assess each input's accuracy, completeness, and relevance to the original text.

Input 1:
Accuracy: 9/10 (The summary accurately captures the main ideas of the original text but lacks some details.)
Completeness: 8.5/10 (Some nuances and implications are missing from the summary.)
Relevance: 10/10 (The summary directly addresses the topic of artificial intelligence and its impact on industries.)

Input 2:
Accuracy: N/A (No input provided for verification.)
Completeness: N/A (No input provided for verification.)
Relevance: N/A (No input provided for verification.)

Input 3:
Accuracy: 9.5/10 (The summary accurately captures the main ideas of the original text and provides additional context and depth.)
Completeness: 9/10 (Most nuances and implications are included in the summary, but some minor details may be missing.)
Relevance: 10/10 (The summary directly addresses the topic of artificial intelligence and its impact on industries.)

Overall, Input 3 provides a more comprehensive and accurate summary than Input 1. Both inputs demonstrate good understanding of the original text, but Input 3 exceeds in terms of completeness and depth.

To address the missing information about summary_constraints and executive:

- summary_constraints: Since no specific constraints were mentioned in the input text, it's challenging to provide a summary that adheres to these constraints.
- executive: The input text doesn't mention an "executive" or any relevant context. If you could provide more information about this component, I would be happy to help create a revised summary that meets its requirements.
============================================================
Status: complete
LLM Calls: 5
Tokens: 2577 in / 1830 out
Latency: 25949ms
------------------------------------------------------------
```output
Summary Package Assembled:

**Executive Summary**

Artificial intelligence (AI) has transformed various industries by automating complex tasks that previously required human expertise. AI-powered machine learning models can diagnose diseases from medical images, detect fraud in financial transactions, and generate text that is increasingly indistinguishable from human writing. However, these advancements also raise concerns about bias, accountability, and the future of work.

The impact of AI on industries is multifaceted, with far-reaching implications for human well-being, dignity, and values. To mitigate these challenges, it is essential to develop and implement robust AI governance frameworks that prioritize transparency, accountability, and fairness. By harnessing the potential of AI responsibly, we can drive positive change and improve lives worldwide.

**Summary Package**

1. **Introduction**
Artificial intelligence (AI) has revolutionized various sectors with its ability to automate complex tasks that previously required human expertise.
2. **Advancements in AI-Powered Applications**
AI-powered machine learning models can accurately diagnose diseases from medical images, detect fraud in financial transactions, and generate text that is increasingly indistinguishable from human writing.
3. **Concerns and Challenges**
However, these advancements also raise important concerns about bias, accountability, and the future of work. As AI systems become more pervasive, there is a growing need to address issues related to fairness, transparency, and ethics in AI decision-making.
4. **Mitigating Challenges through Robust Governance Frameworks**
To mitigate these challenges, it is crucial to develop and implement robust AI governance frameworks that emphasize transparency, accountability, and fairness. This includes establishing clear regulations, standards, and guidelines for AI development and deployment, as well as investing in research and education programs that prepare workers for an increasingly automated workforce.
5. **Conclusion**
Ultimately, the impact of artificial intelligence on industries is multifaceted, and its effects will be shaped by how we choose to design, deploy, and govern these systems. By prioritizing human values, fairness, and accountability, we can harness the potential of AI to drive positive change and improve lives worldwide.

**Assessment**

Accuracy: 9.5/10 (The summary accurately captures the main ideas of the original text and provides additional context and depth.)
Completeness: 9/10 (Most nuances and implications are included in the summary, but some minor details may be missing.)
Relevance: 10/10 (The summary directly addresses the topic of artificial intelligence and its impact on industries.)

**Summary Constraints**

Since no specific constraints were mentioned in the input text, it's challenging to provide a summary that adheres to these constraints.

If you could provide more information about the specific constraints or requirements for Input 4, I would be happy to help create a revised summary.
```
------------------------------------------------------------
Variables:
  @text = Artificial intelligence has transformed industries from healthcare to finance, enabling automation of complex tasks that previously required human expertise. Machine learning models can now diagnose diseases from medical images, detect fraud in financial transactions, and generate human-like text. However, these advances raise important questions about bias, accountability, and the future of work.
  @audience = executive
  @layers = 3
  @sentence_summary = It appears that you want me to summarize the input text related to artificial intelligence and its impact on industries. Here is a summary:

Artificial intelligence (AI) has significantly transformed various industries, including healthcare and finance, by automating complex tasks that previously required human expertise. AI-powered machine learning models can diagnose diseases from medical images, detect fraud in financial transactions, and generate human-like text. However, these advancements also raise concerns about bias, accountability, and the future of work.

As for Input 2 and Input 3, I don't see any information provided about summary_constraints or executive. Could you please provide more context or clarify what specific constraints or information is being referred to?
  @paragraph_summary = Based on the input text related to artificial intelligence and its impact on industries, here's an expanded version of the summary:

Artificial intelligence (AI) has revolutionized various sectors, including healthcare and finance, by automating complex tasks that previously required human expertise. AI-powered machine learning models can accurately diagnose diseases from medical images, detect fraud in financial transactions, and generate text that is increasingly indistinguishable from human writing. These advancements have far-reaching implications for industries worldwide.

However, these significant breakthroughs also raise important concerns about bias, accountability, and the future of work. As AI systems become more pervasive, there is a growing need to address issues related to fairness, transparency, and ethics in AI decision-making. Moreover, the increasing automation of tasks may lead to job displacement and require fundamental changes in education and training programs.

Furthermore, the emergence of AI has sparked debates about the role of humans in society and the potential consequences of relying heavily on machines for critical tasks. While AI has the potential to improve efficiency, productivity, and decision-making, it is essential to ensure that its development and deployment prioritize human well-being, dignity, and values.

Overall, the impact of artificial intelligence on industries is multifaceted, and its effects will be shaped by how we choose to design, deploy, and govern these systems.
  @page_summary = Based on the provided input text, I'll expand the summary as requested. Here's an expanded version of the previous response:

Artificial intelligence (AI) has revolutionized various sectors, including healthcare and finance, by automating complex tasks that previously required human expertise. AI-powered machine learning models can accurately diagnose diseases from medical images, detect fraud in financial transactions, and generate text that is increasingly indistinguishable from human writing.

These advancements have far-reaching implications for industries worldwide, with the potential to improve efficiency, productivity, and decision-making. For instance, AI can help healthcare professionals analyze vast amounts of patient data more quickly and accurately, leading to better treatment outcomes. Similarly, AI-powered chatbots can assist financial institutions in detecting suspicious transactions and preventing cybercrime.

However, these significant breakthroughs also raise important concerns about bias, accountability, and the future of work. As AI systems become more pervasive, there is a growing need to address issues related to fairness, transparency, and ethics in AI decision-making. Moreover, the increasing automation of tasks may lead to job displacement and require fundamental changes in education and training programs.

Furthermore, the emergence of AI has sparked debates about the role of humans in society and the potential consequences of relying heavily on machines for critical tasks. While AI has the potential to improve efficiency, productivity, and decision-making, it is essential to ensure that its development and deployment prioritize human well-being, dignity, and values.

To mitigate these challenges, it is crucial to develop and implement robust AI governance frameworks that emphasize transparency, accountability, and fairness. This includes establishing clear regulations, standards, and guidelines for AI development and deployment, as well as investing in research and education programs that prepare workers for an increasingly automated workforce.

Ultimately, the impact of artificial intelligence on industries is multifaceted, and its effects will be shaped by how we choose to design, deploy, and govern these systems. By prioritizing human values, fairness, and accountability, we can harness the potential of AI to drive positive change and improve lives worldwide.

Here's a summary of the expanded response:

Artificial intelligence (AI) has revolutionized various sectors with its ability to automate complex tasks that previously required human expertise. However, this shift raises important concerns about bias, accountability, and the future of work. To mitigate these challenges, it is essential to develop and implement robust AI governance frameworks that prioritize transparency, accountability, and fairness. By doing so, we can harness the potential of AI to drive positive change and improve lives worldwide while ensuring that human well-being, dignity, and values are at the forefront of its development and deployment.
  @fidelity_score = To verify summary fidelity for Input 1, Input 2, and Input 3, I'll assess each input's accuracy, completeness, and relevance to the original text.

Input 1:
Accuracy: 9/10 (The summary accurately captures the main ideas of the original text but lacks some details.)
Completeness: 8.5/10 (Some nuances and implications are missing from the summary.)
Relevance: 10/10 (The summary directly addresses the topic of artificial intelligence and its impact on industries.)

Input 2:
Accuracy: N/A (No input provided for verification.)
Completeness: N/A (No input provided for verification.)
Relevance: N/A (No input provided for verification.)

Input 3:
Accuracy: 9.5/10 (The summary accurately captures the main ideas of the original text and provides additional context and depth.)
Completeness: 9/10 (Most nuances and implications are included in the summary, but some minor details may be missing.)
Relevance: 10/10 (The summary directly addresses the topic of artificial intelligence and its impact on industries.)

Overall, Input 3 provides a more comprehensive and accurate summary than Input 1. Both inputs demonstrate good understanding of the original text, but Input 3 exceeds in terms of completeness and depth.

To address the missing information about summary_constraints and executive:

- summary_constraints: Since no specific constraints were mentioned in the input text, it's challenging to provide a summary that adheres to these constraints.
- executive: The input text doesn't mention an "executive" or any relevant context. If you could provide more information about this component, I would be happy to help create a revised summary that meets its requirements.
============================================================
Log: /home/papagame/.spl/logs/progressive_summary-ollama-20260327-053642.md
