#!/usr/bin/env python3
# coding: utf-8
"""API Helper Functions - Global instance and convenience wrappers"""

from typing import Dict, Optional

from interview_system.integrations.api_providers import API_PROVIDERS, APIProviderConfig
from interview_system.integrations.api_client import UnifiedAPIClient

_api_client: Optional[UnifiedAPIClient] = None


def get_api_client() -> UnifiedAPIClient:
    """Get global API client instance"""
    global _api_client
    if _api_client is None:
        _api_client = UnifiedAPIClient()
    return _api_client


def get_available_providers() -> Dict[str, APIProviderConfig]:
    """Get all available API providers"""
    return API_PROVIDERS


def initialize_api(
    provider_id: str,
    api_key: str,
    secret_key: str = None,
    model: str = None
) -> bool:
    """Initialize global API client"""
    return get_api_client().initialize(provider_id, api_key, secret_key, model)


def generate_followup(answer: str, topic: dict, conversation_log: list = None) -> Optional[str]:
    """Generate intelligent followup (convenience function)"""
    return get_api_client().generate_followup(answer, topic, conversation_log)


def is_api_available() -> bool:
    """Check if API is available"""
    return get_api_client().is_available


def get_current_provider_name() -> str:
    """Get current API provider name"""
    client = get_api_client()
    if client.current_provider:
        return client.current_provider.name
    return "未配置"
