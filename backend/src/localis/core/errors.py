"""Typed exceptions used across services. Caught by the API layer to produce HTTP responses."""


class LocalisError(Exception):
    """Base for all domain errors."""


class SerpAPIError(LocalisError):
    """SerpAPI failed (network, bad key, malformed payload)."""


class CompanyNotFoundError(LocalisError):
    """SerpAPI succeeded but didn't return enough signal to trust the analysis.

    Prevents the LLM from hallucinating a report when the search turned up nothing
    recognizable — e.g. the user typed a first name or a typo.
    """


class LLMError(LocalisError):
    """LLM call failed (non-quota reason)."""


class LLMQuotaError(LLMError):
    """LLM provider rejected the request due to quota / rate limit.

    The router catches this specifically to trigger provider fallback.
    """


class ParsingError(LocalisError):
    """LLM output could not be parsed into the expected schema."""


class ReportNotFoundError(LocalisError):
    """Report id does not exist in the reports directory."""
