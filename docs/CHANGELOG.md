# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### German Customer Conversation Guide (Leitfaden)
- **File**: `docs/leitfaden_de.md`
- Added comprehensive German conversation script for customer interactions
- Includes multi-stage conversation flow for fund recovery service
- Covers scenarios: customer confirmation, interest, hesitation, appointment confirmation, questions, and closing
- Provides example responses for common customer questions
- Script is designed for Krypto X Pay FCA-licensed fund recovery service

#### Full-Duplex Bidirectional Inbound Call Handling
- **Module**: `src/telephony/ibound_full_duplex.py`
- **Configuration**: `config/telephony.yml`
- Implemented bidirectional call handling for extensions 1000-5000
- Features:
  - **Extension-based routing**: Calls from extensions 1000-5000 use full-duplex mode
  - **Fallback behavior**: Other extensions continue to use TTS-only mode
  - **Real-time dialog loop**: Listen → STT → Agent → TTS → Speak cycle
  - **Configurable STT providers**: Whisper (local), Google Speech-to-Text, OpenAI
  - **Configurable TTS providers**: Coqui TTS (local), AWS Polly, Google TTS, OpenAI
  - **Pluggable architecture**: Easy to add new STT/TTS providers
  - **Low latency streaming**: Optional real-time streaming for reduced response time

#### Configuration System
- **File**: `config/telephony.yml`
- YAML-based configuration for telephony settings
- Environment variable expansion support
- Configuration sections:
  - STT (Speech-to-Text) settings
  - TTS (Text-to-Speech) settings
  - Agent conversation settings
  - Full-duplex extension range configuration
  - Logging preferences

#### Testing Infrastructure
- **File**: `tests/test_ibound_full_duplex.py`
- Unit tests for `TelephonyConfig` class
- Unit tests for `FullDuplexHandler` class
- Integration tests for call routing
- Mock-based testing for external dependencies
- Tests cover:
  - Extension range detection (1000-5000)
  - Call routing logic (full-duplex vs TTS-only)
  - Audio conversion functionality
  - TTS/STT integration points

#### Documentation
- **File**: `docs/telephony_setup.md`
- Comprehensive setup guide for telephony system
- Instructions for configuring STT/TTS providers
- Local testing procedures
- Environment variable configuration
- Troubleshooting guide

### Changed

#### Inbound Test Agent
- **File**: `test_inbound_agent.py`
- Integrated `FullDuplexHandler` for advanced call handling
- Updated to support extension-based routing
- Enhanced logging to indicate full-duplex vs TTS-only mode
- Added telephony configuration support
- Improved documentation and usage instructions

### Technical Details

#### Full-Duplex Architecture
```
Incoming Call (ext 1000-5000)
    ↓
Answer & Initialize
    ↓
Start Recording
    ↓
┌─────────────────────────┐
│   Dialog Loop (Repeat)  │
│  ┌──────────────────┐  │
│  │ 1. Listen (Record) │  │
│  └────────┬──────────┘  │
│           ↓              │
│  ┌──────────────────┐  │
│  │ 2. STT Transcribe │  │
│  └────────┬──────────┘  │
│           ↓              │
│  ┌──────────────────┐  │
│  │ 3. Agent Process  │  │
│  └────────┬──────────┘  │
│           ↓              │
│  ┌──────────────────┐  │
│  │ 4. TTS Synthesize │  │
│  └────────┬──────────┘  │
│           ↓              │
│  ┌──────────────────┐  │
│  │ 5. Play Response  │  │
│  └──────────────────┘  │
└─────────────────────────┘
    ↓
End Call & Extract Info
```

#### Provider Support

**STT Providers:**
- Whisper (local, default) - Uses `faster-whisper`
- Google Speech-to-Text (cloud) - Requires API key
- OpenAI Whisper API (cloud) - Requires API key

**TTS Providers:**
- Coqui TTS (local, default) - German Thorsten voice
- AWS Polly (cloud) - Requires AWS credentials
- Google TTS (cloud) - Requires API key
- OpenAI TTS (cloud) - Requires API key

#### Configuration Options

Key configuration parameters in `config/telephony.yml`:
- `stt.provider`: STT provider selection
- `tts.provider`: TTS provider selection
- `full_duplex.min_extension`: Minimum extension for full-duplex (default: 1000)
- `full_duplex.max_extension`: Maximum extension for full-duplex (default: 5000)
- `agent.max_duration`: Maximum call duration in seconds
- `stream.chunk_duration_ms`: Audio chunk size for streaming

#### Environment Variables

New environment variables:
- `STT_API_KEY`: API key for cloud STT provider
- `TTS_API_KEY`: API key for cloud TTS provider
- `AGENT_ENDPOINT`: Optional external agent endpoint URL
- `TTS_VOICE`: Voice selection for TTS (provider-specific)

### Dependencies

No new dependencies added. Uses existing:
- `faster-whisper` - For STT
- `TTS` (Coqui) - For TTS
- `pyyaml` - For configuration
- `loguru` - For logging

### Breaking Changes

None. Changes are backward compatible:
- Existing TTS-only behavior preserved for extensions outside 1000-5000 range
- New functionality is opt-in via extension range
- Configuration file is optional (defaults provided)

### Migration Guide

For existing deployments:
1. No changes required for current functionality
2. To enable full-duplex mode:
   - Ensure calls originate from extensions 1000-5000
   - Optionally customize `config/telephony.yml`
   - Set environment variables for cloud providers if desired

### Testing

Run tests:
```bash
python tests/test_ibound_full_duplex.py
```

Or using pytest:
```bash
pytest tests/test_ibound_full_duplex.py -v
```

### Known Limitations

1. **Streaming STT**: Current implementation records audio chunks rather than true streaming. Real-time streaming can be enabled via configuration but requires additional setup.
2. **Latency**: Local STT/TTS providers (Whisper/Coqui) may have higher latency than cloud providers on CPU-only systems.
3. **Audio Format**: Currently supports 8kHz, mono, 16-bit PCM WAV (Asterisk standard).
4. **Concurrency**: Dialog loops are sequential; parallel processing within a single call not yet implemented.

### Future Enhancements

- [ ] True streaming STT with incremental transcription
- [ ] Voice activity detection (VAD) for better silence handling
- [ ] Multi-language support (auto-detection)
- [ ] WebRTC support for browser-based testing
- [ ] Call quality metrics and analytics
- [ ] Advanced dialog state management
- [ ] Emotion detection and sentiment analysis
- [ ] Custom wake words for conversation restart

### Security Considerations

- API keys should be stored in environment variables, not committed to source control
- Recording files contain sensitive conversation data - ensure proper access controls
- GDPR compliance: Recordings should be deleted after processing if not required
- Cloud providers: Review data residency and privacy policies

### Support

For issues or questions:
- Check `docs/telephony_setup.md` for setup guidance
- Review test cases in `tests/test_ibound_full_duplex.py` for usage examples
- Consult inline documentation in `src/telephony/ibound_full_duplex.py`

---

## [Previous Version]

(Previous changelog entries would go here)
