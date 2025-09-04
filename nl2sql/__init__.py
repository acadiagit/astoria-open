# Path: nl2sql/__init__.py
# Filename: __init__.py
# Purpose: NL2SQL Package initialization - hybrid natural language to SQL conversion system

"""
NL2SQL Package for Maritime Database Queries

A hybrid natural language to SQL conversion system that combines
rule-based parsing with LLM fallback for optimal performance.
"""

__version__ = "1.0.0"
__author__ = "Maritime NL2SQL Team"

from .nl2sql_service import NL2SQLService

__all__ = ['NL2SQLService']

#end-of-file