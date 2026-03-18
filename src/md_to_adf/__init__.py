"""md-to-adf: Convert Markdown to Atlassian Document Format (ADF)."""

__version__ = "1.1.0"

from md_to_adf.core import convert, validate

# Backward-compat aliases (deprecated, removed in v2)
import warnings


def markdown_to_adf(md_text):
    warnings.warn("markdown_to_adf() is deprecated, use convert()", DeprecationWarning, stacklevel=2)
    return convert(md_text)


def validate_adf(doc):
    warnings.warn("validate_adf() is deprecated, use validate()", DeprecationWarning, stacklevel=2)
    return validate(doc)
