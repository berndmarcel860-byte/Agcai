#!/usr/bin/env python3
"""
Test script to verify OpenAI client proxy compatibility

This test simulates scenarios where the OpenAI Client may or may not
support the 'proxies' parameter, ensuring the safe_openai_client_factory
handles both cases gracefully.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from typing import Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from ai.conversation import safe_openai_client_factory
except ImportError:
    print("Error: Could not import safe_openai_client_factory")
    print("Make sure the src/ai/conversation.py file exists and is properly configured")
    sys.exit(1)


class MockOpenAIClient:
    """Mock OpenAI client that accepts api_key only"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.chat = MagicMock()


class MockOpenAIClientWithProxies:
    """Mock OpenAI client that accepts api_key and proxies"""
    def __init__(self, api_key: str, proxies: Optional[dict] = None):
        self.api_key = api_key
        self.proxies = proxies
        self.chat = MagicMock()


class TestClientProxyCompat(unittest.TestCase):
    """Test cases for OpenAI client proxy compatibility"""
    
    def setUp(self):
        """Set up test environment"""
        # Clear any existing proxy environment variables
        self.original_env = {}
        for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
            self.original_env[var] = os.environ.pop(var, None)
    
    def tearDown(self):
        """Clean up test environment"""
        # Restore original environment variables
        for var, value in self.original_env.items():
            if value is not None:
                os.environ[var] = value
            else:
                os.environ.pop(var, None)
    
    @patch('ai.conversation.OpenAI', MockOpenAIClient)
    def test_client_without_proxies(self):
        """Test creating client when no proxies are configured"""
        client = safe_openai_client_factory(api_key="test-key")
        
        self.assertIsNotNone(client)
        self.assertEqual(client.api_key, "test-key")
        
        # Verify no proxy environment variables were set
        self.assertNotIn('HTTP_PROXY', os.environ)
        self.assertNotIn('HTTPS_PROXY', os.environ)
    
    @patch('ai.conversation.OpenAI', MockOpenAIClientWithProxies)
    def test_client_with_proxies_supported(self):
        """Test creating client when proxies parameter is supported"""
        http_proxy = "http://proxy.example.com:8080"
        https_proxy = "http://proxy.example.com:8443"
        
        client = safe_openai_client_factory(
            api_key="test-key",
            http_proxy=http_proxy,
            https_proxy=https_proxy
        )
        
        self.assertIsNotNone(client)
        self.assertEqual(client.api_key, "test-key")
        
        # When proxies are supported, they should be passed to the client
        if hasattr(client, 'proxies') and client.proxies:
            self.assertEqual(client.proxies.get('http'), http_proxy)
            self.assertEqual(client.proxies.get('https'), https_proxy)
    
    @patch('ai.conversation.OpenAI', MockOpenAIClient)
    def test_client_with_proxies_not_supported(self):
        """Test creating client when proxies parameter is NOT supported"""
        http_proxy = "http://proxy.example.com:8080"
        https_proxy = "http://proxy.example.com:8443"
        
        # This should not raise an error even though MockOpenAIClient doesn't accept proxies
        client = safe_openai_client_factory(
            api_key="test-key",
            http_proxy=http_proxy,
            https_proxy=https_proxy
        )
        
        self.assertIsNotNone(client)
        self.assertEqual(client.api_key, "test-key")
        
        # Verify proxy environment variables were set as fallback
        self.assertEqual(os.environ.get('HTTP_PROXY'), http_proxy)
        self.assertEqual(os.environ.get('HTTPS_PROXY'), https_proxy)
        self.assertEqual(os.environ.get('http_proxy'), http_proxy)
        self.assertEqual(os.environ.get('https_proxy'), https_proxy)
    
    @patch('ai.conversation.OpenAI', MockOpenAIClient)
    def test_client_with_http_proxy_only(self):
        """Test creating client with only HTTP proxy configured"""
        http_proxy = "http://proxy.example.com:8080"
        
        client = safe_openai_client_factory(
            api_key="test-key",
            http_proxy=http_proxy
        )
        
        self.assertIsNotNone(client)
        self.assertEqual(os.environ.get('HTTP_PROXY'), http_proxy)
        self.assertEqual(os.environ.get('http_proxy'), http_proxy)
        # HTTPS proxy should not be set
        self.assertNotIn('HTTPS_PROXY', os.environ)
    
    @patch('ai.conversation.OpenAI', MockOpenAIClient)
    def test_client_with_https_proxy_only(self):
        """Test creating client with only HTTPS proxy configured"""
        https_proxy = "http://proxy.example.com:8443"
        
        client = safe_openai_client_factory(
            api_key="test-key",
            https_proxy=https_proxy
        )
        
        self.assertIsNotNone(client)
        self.assertEqual(os.environ.get('HTTPS_PROXY'), https_proxy)
        self.assertEqual(os.environ.get('https_proxy'), https_proxy)
        # HTTP proxy should not be set
        self.assertNotIn('HTTP_PROXY', os.environ)


def main():
    """Run tests"""
    print("=" * 70)
    print("OpenAI Client Proxy Compatibility Tests")
    print("=" * 70)
    print()
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClientProxyCompat)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("✅ All tests passed!")
        print("The safe_openai_client_factory correctly handles proxy compatibility")
    else:
        print("❌ Some tests failed")
        print(f"Failures: {len(result.failures)}, Errors: {len(result.errors)}")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
