Here's an improved version of the code with a few enhancements:

```python
import re
from nltk.tokenize import sent_tokenize

def reduce_summaries(text):
    """
    Reduces a given text to its most concise summary.

    Args:
        text (str): The input text.

    Returns:
        str: The shortest sentence in the text.
    """

    # Tokenize the text into sentences
    sentences = sent_tokenize(text)

    # If there are no sentences, return an empty string
    if not sentences:
        return ""

    # Remove all the extraneous text except for the main sentence
    summary = min(sentences, key=len)

    return summary

text = "The quick brown fox jumps over the lazy dog. The cat is sleeping. The baby is crying."
print(reduce_summaries(text))
```

Here are the improvements made:

1. **Used `sent_tokenize` from NLTK library**: This function correctly splits the text into sentences, even if there's no dot (.) at the end of each sentence.

2. **Minimized instead of maximized**: In the original code, it took the maximum length sentence which could lead to a longer summary than necessary. Now, we take the minimum sentence which is the most concise possible summary.

3. **Added Docstring for function**: A docstring provides information about what the function does and how to use it. This makes the code more readable and understandable for other developers who might be using this function in their own code.

4. **Checked if sentences list is empty before accessing elements**: In case there are no sentences in the text, `sentences` will be an empty list. We can return an empty string immediately instead of trying to access its first element which would result in an 'IndexError: list index out of range'.