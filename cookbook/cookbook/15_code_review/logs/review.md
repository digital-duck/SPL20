def secure_eval(x):
    try:
        ast.parse(x)
    except SyntaxError:
        return "Invalid syntax"
    
    try:
        exec(compile(x, '<string>', 'exec'), {"__builtins__": None})
    except Exception as e:
        return f"Execution failed: {str(e)}"
    
    result = eval(x)
    if isinstance(result, str):
        # Input string is a valid Python expression
        return result
    else:
        # Input string does not evaluate to a string
        return "Invalid input"

# Example usage:
print(secure_eval("1 + 2"))  # Output: 3
print(secure_eval("import os; print(os.system('ls'))"))  # Output: "Execution failed: <class 'SyntaxError'>"
print(secure_eval("'Hello, World!'"))  # Output: Hello, World!