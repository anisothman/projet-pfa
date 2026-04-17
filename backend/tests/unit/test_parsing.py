import pytest

from localis.core.errors import ParsingError
from localis.domain.schemas import Diagnostic
from localis.services.parsing import (
    clean_text,
    extract_json_block,
    parse_json,
    parse_model,
    strip_emojis,
)


class TestCleanText:
    def test_strip_emojis(self):
        assert strip_emojis("Hello 👋 World 🌍") == "Hello  World "

    def test_clean_whitespace(self):
        assert clean_text("  foo   bar\n\n\n\nbaz  ") == "foo bar\n\nbaz"

    def test_empty_input(self):
        assert clean_text("") == ""


class TestExtractJsonBlock:
    def test_fenced_block(self):
        text = 'Some text\n```json\n{"a": 1}\n```\n'
        assert extract_json_block(text) == '{"a": 1}'

    def test_fenced_without_lang(self):
        assert extract_json_block('```\n{"x": 2}\n```') == '{"x": 2}'

    def test_bare_object(self):
        assert extract_json_block('garbage before {"a": 1} trailing') == '{"a": 1}'

    def test_multiline_object(self):
        text = '{\n  "a": 1,\n  "b": [1, 2]\n}'
        assert extract_json_block(text) == text

    def test_empty_raises(self):
        with pytest.raises(ParsingError):
            extract_json_block("")

    def test_no_json_raises(self):
        with pytest.raises(ParsingError):
            extract_json_block("just some prose no braces")


class TestParseJson:
    def test_valid(self):
        assert parse_json('{"a": 1}') == {"a": 1}

    def test_invalid_raises(self):
        with pytest.raises(ParsingError):
            parse_json('{"a": oops}')

    def test_array_raises(self):
        with pytest.raises(ParsingError):
            parse_json("[1, 2, 3]")


class TestParseModel:
    def test_parse_diagnostic(self):
        payload = """```json
        {
          "points_forts": [{"titre": "A", "description": "B", "impact": "majeur"}],
          "points_faibles": [],
          "opportunites": [],
          "menaces": []
        }
        ```"""
        diag = parse_model(payload, Diagnostic)
        assert len(diag.points_forts) == 1
        assert diag.points_forts[0].titre == "A"

    def test_validation_error_raises_parsing_error(self):
        # Missing required fields won't fail since Diagnostic has defaults, but wrong types will.
        payload = '{"points_forts": "not-a-list"}'
        with pytest.raises(ParsingError):
            parse_model(payload, Diagnostic)
