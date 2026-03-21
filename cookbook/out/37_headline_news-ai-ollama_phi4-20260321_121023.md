
```bash
spl2 run cookbook/37_headline_news/headline_news.spl --adapter ollama -m phi4 topic=artificial intelligence
```

```spl2
-- Recipe 37: Headline News Aggregator
-- Generate, expand, and evaluate a daily news digest for a given topic area.
-- Uses claude_cli adapter with Opus model for broad knowledge synthesis.
--
-- Pattern:
--   generate_headlines(topic) → N headlines
--     → expand each headline into a brief summary
--     → evaluate coverage and balance
--     → refine if coverage gaps detected
--     → commit structured daily digest
--
-- Usage:
--   spl2 run cookbook/37_headline_news/headline_news.spl --adapter claude_cli -m claude-opus-4-6 \
--       topic="artificial intelligence"
--
--   spl2 run cookbook/37_headline_news/headline_news.spl --adapter claude_cli -m claude-opus-4-6 \
--       topic="renewable energy" format="executive brief" max_headlines=5
--
--   spl2 run cookbook/37_headline_news/headline_news.spl --adapter claude_cli -m claude-opus-4-6 \
--       topic="quantum computing" format="bullet points" perspective="global"

CREATE FUNCTION news_format_guide(format TEXT DEFAULT 'structured')
RETURNS TEXT AS $$
SELECT CASE format
  WHEN 'executive brief'  THEN 'Concise executive summary. Lead with the most significant development. 2-3 sentences per item. Close with a one-line strategic implication.'
  WHEN 'bullet points'    THEN 'Bulleted list. One headline per bullet. Sub-bullets for key facts. No more than 3 sub-bullets per headline.'
  WHEN 'narrative'        THEN 'Flowing prose connecting the headlines into a coherent story. Identify themes and through-lines. 3-4 paragraphs.'
  ELSE                         'Structured digest. Each headline followed by a 2-3 sentence summary. Group related items. End with a brief synthesis.'
END
$$;

CREATE FUNCTION perspective_guide(perspective TEXT DEFAULT 'balanced')
RETURNS TEXT AS $$
SELECT CASE perspective
  WHEN 'technical'   THEN 'Focus on technical developments, research breakthroughs, and engineering milestones. Prioritize substance over narrative.'
  WHEN 'business'    THEN 'Focus on market impact, company moves, investment, and economic implications. Prioritize commercial significance.'
  WHEN 'global'      THEN 'Cover developments across multiple regions and countries. Note geographic variation in trends. Avoid US-centric framing.'
  WHEN 'policy'      THEN 'Focus on regulatory developments, government actions, and policy implications. Note geopolitical dimensions.'
  ELSE                    'Balanced coverage across technical, business, policy, and societal dimensions. Represent multiple viewpoints.'
END
$$;

WORKFLOW headline_news
    INPUT:
        @topic            TEXT,
        @date             TEXT DEFAULT 'today',
        @max_headlines    INTEGER DEFAULT 7,
        @format           TEXT DEFAULT 'structured',
        @perspective      TEXT DEFAULT 'balanced'
    OUTPUT: @digest TEXT
DO
    -- Step 1: Generate top headlines for the topic
    GENERATE generate_headlines(
        @topic,
        @max_headlines,
        @date,
        perspective_guide(@perspective)
    ) INTO @headlines

    -- Step 2: Expand each headline into a brief summary with key facts
    GENERATE expand_headlines(
        @headlines,
        @topic,
        perspective_guide(@perspective)
    ) INTO @expanded

    -- Step 3: Evaluate coverage — are major angles represented?
    GENERATE evaluate_coverage(
        @expanded,
        @topic,
        perspective_guide(@perspective)
    ) INTO @coverage_score

    -- Step 4: Refine if coverage gaps detected
    EVALUATE @coverage_score
        WHEN > 0.75 THEN
            -- Coverage is solid — format and commit
            GENERATE format_digest(
                @expanded,
                @topic,
                @date,
                news_format_guide(@format)
            ) INTO @digest
            COMMIT @digest WITH status = 'complete', coverage = @coverage_score

        OTHERWISE
            -- Coverage gaps — add missing angles and reformat
            GENERATE fill_coverage_gaps(
                @expanded,
                @topic,
                @coverage_score,
                perspective_guide(@perspective)
            ) INTO @expanded

            GENERATE format_digest(
                @expanded,
                @topic,
                @date,
                news_format_guide(@format)
            ) INTO @digest
            COMMIT @digest WITH status = 'refined', coverage = @coverage_score
    END

EXCEPTION
    WHEN ContextLengthExceeded THEN
        -- Too many headlines — trim and commit best effort
        GENERATE format_digest(
            @headlines,
            @topic,
            @date,
            news_format_guide(@format)
        ) INTO @digest
        COMMIT @digest WITH status = 'partial'

    WHEN BudgetExceeded THEN
        COMMIT @expanded WITH status = 'budget_limit'
END
```

============================================================
Status: complete
LLM Calls: 5
Tokens: 2104 in / 1853 out
Latency: 24464ms
------------------------------------------------------------
```output
def format_digest(input1, input2, input3, output_function):
    # Check if each input is valid
    if not isinstance(input1, str) or not input1.strip():
        raise ValueError("Invalid input1. Input must be a non-empty string.")
    
    if not isinstance(input2, str) or len(input2) < 5:
        raise ValueError("Invalid input2. Input must be at least 5 characters long.")

    if not isinstance(input3, int):
        raise ValueError("Invalid input3. Input must be an integer.")

    # If output_function is a string, convert it to a function
    if callable(output_function) and isinstance(output_function, str):
        output_function = globals()[output_function]

    # Generate headline and perspective guide based on input parameters
    try:
        # Simplified get_perspective_guide function that directly returns the result
        perspective_guide = output_function(input1, input2)
        
        # If no return value is provided by output_function, use default values
        if perspective_guide is None:
            # For example, using a default value for today's date
            perspective_guide = "Today"

    except Exception as e:
        raise ValueError("Failed to generate headline and perspective guide.") from e

    # Return both the generated headline and the perspective guide
    return f"{input1} {perspective_guide}", perspective_guide

# Example usage:

def get_perspective_guide(input1, input2):
    """Simplified function that returns a string based on input parameters."""
    if len(input2) >= 5:
        # Hardcoded value for long inputs
        return "Long Input"
    else:
        # Default value for short inputs
        return "Short Input"

# Test the function with sample data
sample_input1 = "AI"
sample_input2 = "test"
sample_output_function = get_perspective_guide

result_headline, result_perspective_guide = format_digest(sample_input1, sample_input2, 0, sample_output_function)

print(result_headline)
print(result_perspective_guide)
```
------------------------------------------------------------
Variables:
  @topic = artificial intelligence
  @date = today
  @max_headlines = 7
  @format = structured
  @perspective = balanced
  @headlines = def generate_headlines(input1, input2, input3, input4):
    # Extract the inputs
    ai = input1
    num = input2
    date = input3
    
    # Assuming a format for the perspective guide
    perspective_guide = input4
    
    # Generate headlines based on the input parameters
    headline1 = f"AI Revolution: {ai} Advances by 7% This {date}"
    headline2 = f"{date}: The Future of {ai} is Brighter Than Ever"
    headline3 = f"New Breakthrough in {ai}: A Step Closer to {perspective_guide}"
    
    # Return the generated headlines
    return [headline1, headline2, headline3]
  @expanded = The revised version of the code is more efficient and straightforward. It correctly addresses the issues mentioned in Input 2 and provides a better user experience by returning both the generated headline and the perspective guide.

Here's a summary of the changes:

1.  **Input validation**: The code now checks if each input is valid before generating the headline. This ensures that the output will always be correct and prevents potential errors.
2.  **Simplified `get_perspective_guide` function**: Instead of returning a hardcoded string, the function now directly returns a string based on the input parameters.
3.  **Removed unnecessary variable assignment**: The code no longer assigns the value of `input1` to a new variable (`ai`) and then uses it as an input for another function. This simplifies the code and reduces redundancy.
4.  **Improved return values**: The function now returns both the generated headline and the perspective guide, providing more flexibility and usability.

Overall, the revised version is more efficient, user-friendly, and robust than the original code. It effectively addresses the issues mentioned in Input 2 and provides a better experience for users who interact with this function.
  @coverage_score = The function `generate_headlines` appears to be generating headlines related to AI advances. 

However, there are several issues with this code:

1. The variable `num` is an integer representing a percentage of AI advance, but it's not used in the generation of the headlines.

2. The variable `date` is a string representing the date format, but it's not used in the generation of the headlines either.

3. The function `get_perspective_guide` returns a hardcoded string instead of using the actual value of `ai`. This means that all three headlines will have the same content.

4. The variable `input1` is assigned to `ai`, which is then used as an input for another function (`generate_headlines`). However, this seems unnecessary and could be simplified.

5. There's no validation on the inputs. If any of them are invalid, it could lead to unexpected behavior or errors.

Here's a revised version of the code that addresses these issues:

```python
def generate_headline(input1, input2, input3, input4):
    """
    Generates a headline based on AI advances.

    Args:
        input1 (str): The perspective guide.
        input2 (int): The percentage of AI advance.
        input3 (str): The date format.
        input4 (str): A function to generate the perspective guide.

    Returns:
        str: A generated headline.
    """

    # Validate inputs
    if not isinstance(input1, str):
        raise ValueError("input1 must be a string")
    if not isinstance(input2, int) or input2 < 0 or input2 > 100:
        raise ValueError("input2 must be an integer between 0 and 100")
    if not isinstance(input3, str):
        raise ValueError("input3 must be a string")
    if not callable(input4):
        raise ValueError("input4 must be a function")

    # Generate headline based on input parameters
    headline = f"AI Revolution: A {input2}% Increase Will Change Everything by {input3}"
    
    # Return the generated headline and the perspective guide
    return headline, input1 + " will revolutionize " + input4()

# Example usage:
perspective_guide_function = generate_headline("artificial intelligence", 7, "%Y", lambda: "machine learning")
headline, perspective_guide = generate_headline("artificial intelligence", 7, "%Y", perspective_guide_function)
print(f"Headline: {headline}")
print(f"Perspective Guide: {perspective_guide}")
```

In this revised version:

*   The variable `num` has been removed because it was not being used in the generation of the headlines.
*   The variable `date` has also been removed for the same reason.
*   The function `get_perspective_guide` has been simplified to directly return a string based on the input parameters.
*   Input validation has been added to ensure that all inputs are valid before generating the headline.
*   The code now returns both the generated headline and the perspective guide, allowing it to be used as needed.
============================================================
Log: /home/gongai/.spl/logs/headline_news-ollama-20260321-121023.log
