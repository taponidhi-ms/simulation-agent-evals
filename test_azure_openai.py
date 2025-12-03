#!/usr/bin/env python3
"""
Test script to validate Azure OpenAI integration.

This script tests that the Azure OpenAI client can be initialized correctly
with the proper configuration.
"""

import os
import sys
from conversation_generator.agents import LLMClient, AzureOpenAI


def test_azure_openai_import():
    """Test that AzureOpenAI can be imported."""
    print("Testing Azure OpenAI import...", end=" ")
    assert AzureOpenAI is not None, "AzureOpenAI failed to import"
    print("✓ PASS")


def test_llm_client_initialization():
    """Test that LLMClient can be initialized with Azure OpenAI configuration."""
    print("Testing LLMClient initialization...", end=" ")
    
    # Use dummy credentials for initialization test
    test_api_key = "test-api-key"
    test_endpoint = "https://test-resource.cognitiveservices.azure.com/"
    test_api_version = "2024-02-01"
    
    try:
        client = LLMClient(
            api_key=test_api_key,
            azure_endpoint=test_endpoint,
            api_version=test_api_version
        )
        assert client.client is not None, "Client was not initialized"
        assert isinstance(client.client, AzureOpenAI), "Client is not an AzureOpenAI instance"
        print("✓ PASS")
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False
    
    return True


def test_configuration_loading():
    """Test that configuration loads correctly."""
    print("Testing configuration loading...", end=" ")
    
    from conversation_generator import config
    
    # Test that all required config variables exist
    assert hasattr(config, 'AZURE_OPENAI_API_KEY'), "Missing AZURE_OPENAI_API_KEY"
    assert hasattr(config, 'AZURE_OPENAI_ENDPOINT'), "Missing AZURE_OPENAI_ENDPOINT"
    assert hasattr(config, 'AZURE_OPENAI_API_VERSION'), "Missing AZURE_OPENAI_API_VERSION"
    assert hasattr(config, 'CUSTOMER_DEPLOYMENT'), "Missing CUSTOMER_DEPLOYMENT"
    assert hasattr(config, 'CSR_DEPLOYMENT'), "Missing CSR_DEPLOYMENT"
    
    # Test default values
    assert config.AZURE_OPENAI_API_VERSION == "2024-02-01", "Incorrect default API version"
    assert config.CUSTOMER_DEPLOYMENT == "gpt-4o-mini", "Incorrect default customer deployment"
    assert config.CSR_DEPLOYMENT == "gpt-4o-mini", "Incorrect default CSR deployment"
    
    print("✓ PASS")
    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("Azure OpenAI Integration Tests")
    print("=" * 70)
    print()
    
    all_passed = True
    
    # Run tests
    test_azure_openai_import()
    all_passed = test_llm_client_initialization() and all_passed
    all_passed = test_configuration_loading() and all_passed
    
    print()
    print("=" * 70)
    if all_passed:
        print("All tests PASSED ✓")
        print("=" * 70)
        return 0
    else:
        print("Some tests FAILED ✗")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
