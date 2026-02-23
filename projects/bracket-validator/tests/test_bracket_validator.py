import pytest
from bracket_validator import validate_brackets


class TestBracketValidator:
    """Test cases for validate_brackets function."""
    
    # Nested valid cases
    def test_nested_balanced_parentheses(self):
        assert validate_brackets("({[]})") is True
    
    def test_nested_balanced_mixed(self):
        assert validate_brackets("[(){}]") is True
    
    def test_deeply_nested(self):
        assert validate_brackets("{{{{}}}}") is True
    
    def test_nested_with_text(self):
        assert validate_brackets("func({x}) + arr[0]") is True
    
    # Interleaved invalid cases
    def test_interleaved_invalid(self):
        assert validate_brackets("({)}") is False
    
    def test_interleaved_invalid2(self):
        assert validate_brackets("[({]})") is False
    
    # Empty input
    def test_empty_input(self):
        assert validate_brackets("") is True
    
    # Alphanumeric only (no brackets)
    def test_alphanumeric_only(self):
        assert validate_brackets("abc123def") is True
    
    # Fail fast - closing before opening
    def test_premature_close_single(self):
        assert validate_brackets(")") is False
    
    def test_premature_close_multiple(self):
        assert validate_brackets("]}{") is False
    
    # Mismatched bracket types
    def test_mismatched_brackets(self):
        assert validate_brackets("(]") is False
    
    def test_mismatched_brackets2(self):
        assert validate_brackets("{)") is False
    
    # Unclosed opening brackets
    def test_unclosed_opening(self):
        assert validate_brackets("(") is False
    
    def test_unclosed_opening2(self):
        assert validate_brackets("({[") is False
    
    def test_unclosed_mixed(self):
        assert validate_brackets("({)}") is False
    
    # Valid with other characters mixed in
    def test_valid_with_text(self):
        assert validate_brackets("a(b)c") is True
    
    def test_valid_with_special_chars(self):
        assert validate_brackets("if (x > 0) { return x; }") is True
    
    # Valid edge cases
    def test_only_opening_brackets(self):
        assert validate_brackets("({[") is False
    
    def test_only_closing_brackets(self):
        assert validate_brackets(")}]") is False
    
    def test_balanced_complex(self):
        assert validate_brackets("((({})))") is True