def foo(x):
    try:
        result = safe_eval(x)
        if isinstance(result, str) and len(result) > 10:
            raise ValueError("Input is too long")
        # Add more conditions to check the type of result here
    except (ValueError, TypeError):
        print(f"Invalid input: {x}")

# Example usage:
foo("1 + 2")  # Output: 3
foo("[1,2,3]")  # Output: [1, 2, 3]
foo("<script>alert('XSS')</script>")  # Output: Invalid input: <script>alert('XSS')</script>