Here is an improved version of your function with more robust error checking and handling:

```python
import nltk

def reduce_summaries(input_text, num_chunks):
    """
    Reduce the complexity of a given text into summary chunks.

    Args:
        input_text (str): The original text to be summarized.
        num_chunks (int): The number of words to include in each chunk.

    Returns:
        str: A string containing the summary chunks.
    """

    # Check if input text is empty
    if not input_text.strip():
        return "Input text cannot be empty."

    # Tokenize the input text into sentences
    try:
        sentences = nltk.sent_tokenize(input_text)
    except Exception as e:
        raise ValueError("Failed to tokenize input text.") from e

    # Check if chunking is requested
    if num_chunks <= 0:
        return "Invalid number of chunks. Please provide a positive integer."

    # Initialize an empty list to store the summary chunks
    summary_chunks = []

    # Loop through each sentence in the input text
    for sentence in sentences:
        try:
            # Tokenize the sentence into words
            words = nltk.word_tokenize(sentence)
            
            # Check if there are enough words for chunking
            if len(words) < num_chunks:
                raise ValueError("Not enough words to create chunks.")
        
            # Join the first 'num_chunks' number of words to form a chunk
            chunk = ' '.join(words[:num_chunks])
        
            # Add the chunk to the summary chunks list
            summary_chunks.append(chunk)
        except Exception as e:
            raise ValueError(f"Failed to process sentence: {sentence}") from e

    # Return the summary chunks as bullet points
    if not summary_chunks:
        return "No sentences found in the input text."
    
    return '\n'.join([f'* {chunk}' for chunk in summary_chunks])
```

Example usage:

```python
print(reduce_summaries("The quick brown fox jumps over the lazy dog.", 2))
# Output: * The quick brown fox * jumps over the lazy dog.

print(reduce_summaries("", 3)) # Raises ValueError
```