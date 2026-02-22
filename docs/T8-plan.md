# T8: Bracket Validator - Architecture Plan

## Overview
Create a parser utility that validates whether brackets are balanced in incoming expression strings using a stack-based approach.

## Design

### Core Algorithm
- Use a stack to track opening brackets
- When encountering an opening bracket (`(`, `{`, `[`), push to stack
- When encountering a closing bracket (`)`, `}`, `]`), pop from stack and validate matching type
- Ignore all non-bracket characters
- Fail fast: if closing bracket appears with no matching opening bracket on stack, return invalid immediately

### Data Structure
- Stack: simple Python list (LIFO)
- Bracket mapping: dict mapping closing->opening for validation

### Function Signature
```python
def validate_brackets(expression: str) -> bool:
    """Validate if brackets in expression are balanced.
    
    Args:
        expression: String containing brackets and optional other characters
        
    Returns:
        True if all brackets are balanced, False otherwise
    """
```

### Edge Cases
1. Empty input → valid (no brackets to validate)
2. Only non-bracket characters → valid
3. Nested valid brackets → valid (e.g., `({[]})`)
4. Interleaved invalid → invalid (e.g., `({)}`)
5. Closing before opening → invalid (fail fast)
6. Mismatched bracket types → invalid
7. Unclosed opening brackets → invalid

## Test Plan
- Nested valid: `({[]})`, `[(){}]`
- Interleaved invalid: `({)}`, `[({]})`
- Empty input: `""`
- Alphanumeric: `abc123def`
- Mixed text: `func({x}) + arr[0]`
- Premature close: `)`, `]}` 

## File Structure
```
factory-testing/
├── docs/
│   └── T8-plan.md (this file)
├── src/
│   └── bracket_validator.py
└── tests/
    └── test_bracket_validator.py
```

## Implementation Notes
- Pure function, no side effects
- O(n) time complexity where n = len(expression)
- O(d) space complexity where d = max nesting depth
