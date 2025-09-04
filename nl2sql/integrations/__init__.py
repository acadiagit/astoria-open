# Path: nl2sql/integrations/__init__.py
# Filename: __init__.py
# Purpose: Integration components package initialization for external system bridges

"""
Integration Components

Provides bridges and adapters for integrating with external systems
like LangChain agents and other NL2SQL frameworks.
"""

from .langchain_bridge import LangChainBridge, BridgeResult

__all__ = [
    'LangChainBridge',
    'BridgeResult'
]

#end-of-script