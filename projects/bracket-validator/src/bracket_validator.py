"""Bracket validation utility."""


def validate_brackets(expression: str) -> bool:
    """Validate if brackets in expression are balanced.
    
    Args:
        expression: String containing brackets and optional other characters
        
    Returns:
        True if all brackets are balanced, False otherwise
    """
    bracket_map = {
        ')': '(',
        '}': '{',
        ']': '['
    }
    opening_brackets = set(bracket_map.values())
    closing_brackets = set(bracket_map.keys())
    stack = []
    
    for char in expression:
        if char in opening_brackets:
            stack.append(char)
        elif char in closing_brackets:
            # Fail fast: closing bracket with no matching opening
            if not stack:
                return False
            # Check if the popped bracket matches the closing type
            if stack.pop() != bracket_map[char]:
                return False
    
    # Valid only if all opening brackets have been closed
    return len(stack) == 0