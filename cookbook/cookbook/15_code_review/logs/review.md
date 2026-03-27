Here's a Python function that uses the `asteval` library for safe evaluation of mathematical expressions:

```python
import asteval

def safe_eval_expression(expression):
    a = asteval.AstEvaluator()
    try:
        return a.eval(expression)
    except Exception as e:
        raise ValueError(f"Failed to evaluate expression: {e}")

# Usage example:
expression = "1 + 2 * 3"
result = safe_eval_expression(expression)
print(result)  # Output: 7
```

In this function, `asteval.AstEvaluator()` is used to create an instance of the evaluator. The `eval` method is then called on this instance, passing in the input expression as a string.

If everything goes smoothly and the evaluation is successful, the result is returned. If any errors occur during evaluation (e.g., invalid syntax or unsupported operations), a `ValueError` exception is raised with an error message indicating what went wrong.

This approach ensures that user-supplied expressions are evaluated in a controlled environment, minimizing the risk of code injection attacks and other security risks associated with using `eval()`.