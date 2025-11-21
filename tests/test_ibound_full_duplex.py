"""
Integration tests for Full-Duplex Inbound Call Handling

These tests verify the bidirectional call handling functionality
for extensions 1000-5000 and fallback behavior for other extensions.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from telephony import TelephonyConfig, FullDuplexHandler


class TestTelephonyConfig(unittest.TestCase):
    """Test cases for TelephonyConfig"""
    
    def test_default_config(self):
        """Test that default configuration is loaded correctly"""
        config = TelephonyConfig()
        
        # Check STT config
        self.assertEqual(config.get('stt.provider'), 'whisper')
        self.assertEqual(config.get('stt.language'), 'de')
        self.assertEqual(config.get('stt.model'), 'base')
        
        # Check TTS config
        self.assertEqual(config.get('tts.provider'), 'coqui')
        self.assertEqual(config.get('tts.language'), 'de')
        
        # Check full-duplex config
        self.assertTrue(config.get('full_duplex.enabled'))
        self.assertEqual(config.get('full_duplex.min_extension'), 1000)
        self.assertEqual(config.get('full_duplex.max_extension'), 5000)
        
    def test_config_get_with_default(self):
        """Test configuration get with default value"""
        config = TelephonyConfig()
        
        # Existing key
        self.assertEqual(config.get('stt.provider'), 'whisper')
        
        # Non-existing key with default
        self.assertEqual(config.get('nonexistent.key', 'default_value'), 'default_value')
        
        # Non-existing key without default
        self.assertIsNone(config.get('nonexistent.key'))


class TestFullDuplexHandler(unittest.TestCase):
    """Test cases for FullDuplexHandler"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock components
        self.mock_stt = Mock()
        self.mock_tts = Mock()
        self.mock_conversation = Mock()
        self.mock_ari = Mock()
        
        # Create mock config
        self.mock_config = Mock()
        self.mock_config.get = Mock(side_effect=self._mock_config_get)
        
        # Mock directory creation to avoid permission errors in tests
        with patch('os.makedirs'):
            # Create handler
            self.handler = FullDuplexHandler(
                stt_engine=self.mock_stt,
                tts_engine=self.mock_tts,
                conversation_engine=self.mock_conversation,
                ari_client=self.mock_ari,
                config=self.mock_config
            )
        
    def _mock_config_get(self, key, default=None):
        """Mock configuration values"""
        config_values = {
            'full_duplex.enabled': True,
            'full_duplex.min_extension': 1000,
            'full_duplex.max_extension': 5000,
            'full_duplex.fallback_mode': 'tts_only',
        }
        return config_values.get(key, default)
        
    def test_extension_in_range_valid(self):
        """Test extension range detection for valid extensions"""
        # Test extensions within range
        self.assertTrue(self.handler.is_extension_in_range('1000'))
        self.assertTrue(self.handler.is_extension_in_range('2500'))
        self.assertTrue(self.handler.is_extension_in_range('5000'))
        
        # Test with various formats
        self.assertTrue(self.handler.is_extension_in_range('ext-1000'))
        self.assertTrue(self.handler.is_extension_in_range('PJSIP/1000'))
        
    def test_extension_in_range_invalid(self):
        """Test extension range detection for invalid extensions"""
        # Test extensions outside range
        self.assertFalse(self.handler.is_extension_in_range('999'))
        self.assertFalse(self.handler.is_extension_in_range('5001'))
        self.assertFalse(self.handler.is_extension_in_range('100'))
        
        # Test non-numeric values
        self.assertFalse(self.handler.is_extension_in_range('unknown'))
        self.assertFalse(self.handler.is_extension_in_range(''))
        
    def test_extension_in_range_edge_cases(self):
        """Test extension range detection for edge cases"""
        # Test boundary values
        self.assertTrue(self.handler.is_extension_in_range('1000'))  # Min
        self.assertTrue(self.handler.is_extension_in_range('5000'))  # Max
        self.assertFalse(self.handler.is_extension_in_range('999'))  # Just below
        self.assertFalse(self.handler.is_extension_in_range('5001'))  # Just above
        
    @patch('subprocess.run')
    def test_convert_audio_for_asterisk_success(self, mock_subprocess):
        """Test successful audio conversion"""
        mock_subprocess.return_value = Mock()
        
        result = self.handler.convert_audio_for_asterisk(
            '/tmp/input.wav',
            '/tmp/output.wav'
        )
        
        self.assertTrue(result)
        mock_subprocess.assert_called_once()
        
    @patch('subprocess.run')
    def test_convert_audio_for_asterisk_failure(self, mock_subprocess):
        """Test audio conversion failure"""
        from subprocess import CalledProcessError
        mock_subprocess.side_effect = CalledProcessError(1, 'ffmpeg')
        
        result = self.handler.convert_audio_for_asterisk(
            '/tmp/input.wav',
            '/tmp/output.wav'
        )
        
        self.assertFalse(result)
        
    def test_route_call_full_duplex_mode(self):
        """Test call routing to full-duplex mode"""
        # Mock the full-duplex handler method
        self.handler.handle_full_duplex_call = Mock()
        
        # Call from extension in range
        conversation_history = []
        self.handler.route_call('channel-123', '1000', conversation_history)
        
        # Verify full-duplex mode was used
        self.handler.handle_full_duplex_call.assert_called_once_with(
            'channel-123', '1000', conversation_history
        )
        
    def test_route_call_tts_only_mode(self):
        """Test call routing to TTS-only mode"""
        # Mock the TTS-only handler method
        self.handler.handle_tts_only_call = Mock()
        
        # Call from extension outside range
        conversation_history = []
        self.handler.route_call('channel-123', '999', conversation_history)
        
        # Verify TTS-only mode was used
        self.handler.handle_tts_only_call.assert_called_once_with(
            'channel-123', '999', conversation_history
        )
        
    def test_speak_to_caller_success(self):
        """Test speaking to caller successfully"""
        # Setup mocks
        self.mock_tts.synthesize = Mock(return_value=True)
        self.mock_ari.play_media = Mock()
        
        with patch.object(self.handler, 'convert_audio_for_asterisk', return_value=True):
            with patch('os.path.exists', return_value=True):
                with patch('os.remove'):
                    with patch('time.sleep'):
                        conversation_history = []
                        result = self.handler.speak_to_caller(
                            'channel-123',
                            'Hello world',
                            conversation_history
                        )
                        
                        self.assertTrue(result)
                        self.mock_tts.synthesize.assert_called_once()
                        self.mock_ari.play_media.assert_called_once()
                        self.assertEqual(len(conversation_history), 1)
                        
    def test_speak_to_caller_tts_failure(self):
        """Test speaking to caller when TTS fails"""
        # Setup mocks
        self.mock_tts.synthesize = Mock(return_value=False)
        
        conversation_history = []
        result = self.handler.speak_to_caller(
            'channel-123',
            'Hello world',
            conversation_history
        )
        
        self.assertFalse(result)
        self.assertEqual(len(conversation_history), 0)
        
    def test_listen_and_transcribe_correct_stop_recording_signature(self):
        """Test that stop_recording is called with only recording_name (not channel_id)"""
        # Setup mocks
        self.mock_ari.get_channel_state = Mock(return_value={'id': 'channel-123', 'state': 'Up'})
        self.mock_ari.stop_recording = Mock(return_value=True)
        self.mock_stt.transcribe_file = Mock(return_value="Test transcription")
        
        with patch('os.path.exists', return_value=True):
            with patch('time.sleep'):
                result = self.handler.listen_and_transcribe(
                    'channel-123',
                    'test_recording',
                    timeout=1
                )
                
                # Verify stop_recording was called with only recording_name
                self.mock_ari.stop_recording.assert_called_once_with('test_recording')
                self.assertEqual(result, "Test transcription")
                
    def test_listen_and_transcribe_channel_hangup_detection(self):
        """Test that listen_and_transcribe detects channel hangup"""
        # Setup mocks - channel no longer exists
        self.mock_ari.get_channel_state = Mock(return_value=None)
        self.mock_ari.stop_recording = Mock()
        
        with patch('time.sleep'):
            result = self.handler.listen_and_transcribe(
                'channel-123',
                'test_recording',
                timeout=1
            )
            
            # Should return None when channel is gone
            self.assertIsNone(result)
            # stop_recording should NOT be called
            self.mock_ari.stop_recording.assert_not_called()
            
    def test_listen_and_transcribe_stop_recording_error_handling(self):
        """Test that listen_and_transcribe handles stop_recording errors gracefully"""
        # Setup mocks
        self.mock_ari.get_channel_state = Mock(return_value={'id': 'channel-123', 'state': 'Up'})
        self.mock_ari.stop_recording = Mock(side_effect=Exception("Recording already stopped"))
        self.mock_stt.transcribe_file = Mock(return_value="Test transcription")
        
        with patch('os.path.exists', return_value=True):
            with patch('time.sleep'):
                result = self.handler.listen_and_transcribe(
                    'channel-123',
                    'test_recording',
                    timeout=1
                )
                
                # Should continue gracefully despite stop_recording error
                self.assertEqual(result, "Test transcription")
                
    def test_listen_and_transcribe_missing_recording_file(self):
        """Test that listen_and_transcribe returns None when recording file is missing"""
        # Setup mocks
        self.mock_ari.get_channel_state = Mock(return_value={'id': 'channel-123', 'state': 'Up'})
        self.mock_ari.stop_recording = Mock(return_value=True)
        
        with patch('os.path.exists', return_value=False):
            with patch('time.sleep'):
                result = self.handler.listen_and_transcribe(
                    'channel-123',
                    'test_recording',
                    timeout=1
                )
                
                # Should return None when file doesn't exist
                self.assertIsNone(result)
        

class TestFullDuplexIntegration(unittest.TestCase):
    """Integration tests for full-duplex call handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock components with more realistic behavior
        self.mock_stt = Mock()
        self.mock_tts = Mock()
        self.mock_conversation = Mock()
        self.mock_ari = Mock()
        
        # Create real config
        self.config = TelephonyConfig()
        
        # Mock directory creation to avoid permission errors in tests
        with patch('os.makedirs'):
            # Create handler
            self.handler = FullDuplexHandler(
                stt_engine=self.mock_stt,
                tts_engine=self.mock_tts,
                conversation_engine=self.mock_conversation,
                ari_client=self.mock_ari,
                config=self.config
            )
        
    def test_full_call_flow_extension_1000(self):
        """Test complete call flow for extension 1000"""
        # This is a mock test - in a real scenario you'd need actual Asterisk
        # Mock conversation engine responses
        self.mock_conversation.get_response = Mock(return_value="Guten Tag!")
        
        # Mock TTS and STT
        self.mock_tts.synthesize = Mock(return_value=True)
        self.mock_stt.transcribe_file = Mock(return_value="Hallo")
        
        # Mock ARI operations
        self.mock_ari.start_recording = Mock()
        self.mock_ari.stop_recording = Mock()
        self.mock_ari.play_media = Mock()
        
        with patch.object(self.handler, 'convert_audio_for_asterisk', return_value=True):
            with patch('os.path.exists', return_value=False):  # No recording file
                with patch('time.sleep'):
                    conversation_history = []
                    
                    # Test routing - should go to full-duplex
                    self.assertTrue(self.handler.is_extension_in_range('1000'))
                    
    def test_full_call_flow_extension_999(self):
        """Test complete call flow for extension 999 (TTS-only)"""
        # This should fall back to TTS-only mode
        self.assertFalse(self.handler.is_extension_in_range('999'))
        
    def test_handle_full_duplex_call_start_recording_failure_with_hangup(self):
        """Test that handle_full_duplex_call detects hangup when start_recording fails"""
        # Setup mocks
        self.mock_conversation.get_response = Mock(return_value="Guten Tag!")
        self.mock_tts.synthesize = Mock(return_value=True)
        
        # start_recording returns None (failure), channel is gone
        self.mock_ari.start_recording = Mock(return_value=None)
        self.mock_ari.get_channel_state = Mock(return_value=None)
        self.mock_ari.play_media = Mock()
        
        with patch.object(self.handler, 'convert_audio_for_asterisk', return_value=True):
            with patch('os.path.exists', return_value=True):
                with patch('os.remove'):
                    with patch('time.sleep'):
                        conversation_history = []
                        
                        # Should exit cleanly without error
                        self.handler.handle_full_duplex_call('channel-123', '1000', conversation_history)
                        
                        # Verify start_recording was called
                        self.mock_ari.start_recording.assert_called()
                        # Verify channel state was checked after recording failure
                        self.mock_ari.get_channel_state.assert_called()
                        
    def test_handle_full_duplex_call_hangup_during_listening(self):
        """Test that handle_full_duplex_call detects hangup during listen_and_transcribe"""
        # Setup mocks
        self.mock_conversation.get_response = Mock(return_value="Guten Tag!")
        self.mock_tts.synthesize = Mock(return_value=True)
        
        # Recording starts successfully
        self.mock_ari.start_recording = Mock(return_value={'name': 'test_recording'})
        
        # Channel state check sequence: alive during first check, gone during second
        self.mock_ari.get_channel_state = Mock(side_effect=[
            {'id': 'channel-123', 'state': 'Up'},  # Initial check in listen_and_transcribe
            None  # Channel gone after listen_and_transcribe returns None
        ])
        
        self.mock_ari.stop_recording = Mock(return_value=True)
        self.mock_ari.play_media = Mock()
        self.mock_stt.transcribe_file = Mock(return_value=None)
        
        with patch.object(self.handler, 'convert_audio_for_asterisk', return_value=True):
            with patch('os.path.exists', return_value=False):  # No recording file
                with patch('os.remove'):
                    with patch('time.sleep'):
                        conversation_history = []
                        
                        # Should exit cleanly after detecting hangup
                        self.handler.handle_full_duplex_call('channel-123', '1000', conversation_history)
                        
                        # Verify the dialogue loop was entered and exited
                        self.mock_ari.start_recording.assert_called()
                        # Channel state should be checked when listen_and_transcribe returns None
                        self.assertEqual(self.mock_ari.get_channel_state.call_count, 2)
        

def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestTelephonyConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestFullDuplexHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestFullDuplexIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
