"""
Basic tests for AI Call Agent
"""
import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestImports(unittest.TestCase):
    """Test that all modules can be imported"""
    
    def test_import_config(self):
        """Test config module import"""
        from src.config import Config
        self.assertIsNotNone(Config)
        
    def test_import_database(self):
        """Test database module import"""
        from src.database import Database, Lead, Campaign, CallRecord
        self.assertIsNotNone(Database)
        self.assertIsNotNone(Lead)
        self.assertIsNotNone(Campaign)
        self.assertIsNotNone(CallRecord)
        
    def test_import_ari(self):
        """Test ARI module import"""
        from src.ari import ARIClient
        self.assertIsNotNone(ARIClient)
        
    def test_import_ai(self):
        """Test AI module import"""
        from src.ai import ConversationEngine
        self.assertIsNotNone(ConversationEngine)
        
    def test_import_tts(self):
        """Test TTS module import"""
        from src.tts import TextToSpeech
        self.assertIsNotNone(TextToSpeech)
        
    def test_import_stt(self):
        """Test STT module import"""
        from src.stt import SpeechToText
        self.assertIsNotNone(SpeechToText)
        
    def test_import_campaign(self):
        """Test campaign module import"""
        from src.campaign import CampaignManager, CallHandler
        self.assertIsNotNone(CampaignManager)
        self.assertIsNotNone(CallHandler)


class TestConfiguration(unittest.TestCase):
    """Test configuration loading"""
    
    def test_config_creation(self):
        """Test creating config without .env file"""
        from src.config import Config
        
        # Should work with defaults even without .env file
        config = Config(env_file='.env.example')
        
        self.assertEqual(config.database.host, '127.0.0.1')
        self.assertEqual(config.database.port, 3306)
        self.assertEqual(config.ari.host, '127.0.0.1')
        self.assertEqual(config.ari.port, 8088)


if __name__ == '__main__':
    unittest.main()
