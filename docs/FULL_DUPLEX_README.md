# Full-Duplex Bidirectional Call Handling

This feature enables real bidirectional conversations for inbound calls from specific extensions (1000-5000).

## Quick Start

### For Extensions 1000-5000
Calls from these extensions will have full-duplex conversations:
- Agent listens to caller speech
- Speech is transcribed (STT)
- Agent responds intelligently
- Response is spoken (TTS)
- Conversation continues naturally

### For Other Extensions
Calls from other extensions use TTS-only mode (original behavior):
- Agent plays pre-scripted responses
- No speech recognition
- Simulated conversation flow

## How It Works

```
┌─────────────────────────────────────┐
│  Caller dials from extension 1000  │
└────────────────┬────────────────────┘
                 │
                 ▼
        ┌────────────────┐
        │ Call Answered  │
        └────────┬───────┘
                 │
                 ▼
    ┌─────────────────────────┐
    │  Extension Check         │
    │  1000-5000?             │
    └────────┬────────────────┘
             │
     ┌───────┴────────┐
     │                │
     ▼                ▼
Full-Duplex      TTS-Only
   Mode            Mode
     │                │
     │                └─→ Play scripted conversation
     │
     └─→ Real conversation loop:
         1. Listen (record)
         2. Transcribe (STT)
         3. Process (AI Agent)
         4. Synthesize (TTS)
         5. Speak (play)
         6. Repeat
```

## Configuration

### Default Configuration (No Setup Required)

The system works out of the box with:
- **STT**: Whisper (local, base model)
- **TTS**: Coqui TTS (local, German Thorsten voice)
- **Extension Range**: 1000-5000

### Custom Configuration (Optional)

Create or edit `config/telephony.yml`:

```yaml
# Enable/disable full-duplex mode
full_duplex:
  enabled: true
  min_extension: 1000
  max_extension: 5000

# Choose STT provider
stt:
  provider: whisper  # whisper, google, or openai
  model: base
  language: de

# Choose TTS provider  
tts:
  provider: coqui    # coqui, polly, google, or openai
  model: tts_models/de/thorsten/tacotron2-DDC
  language: de
```

### Cloud Providers (Better Latency)

For production use, cloud providers offer lower latency:

```yaml
# Google Speech-to-Text
stt:
  provider: google
  api_key: ${STT_API_KEY}
  language: de-DE

# AWS Polly Text-to-Speech
tts:
  provider: polly
  api_key: ${TTS_API_KEY}
  language: de-DE
  voice: Marlene
```

Set environment variables:
```bash
export STT_API_KEY="your-google-api-key"
export TTS_API_KEY="your-aws-credentials"
```

## Testing

### Start the Test Agent

```bash
python test_inbound_agent.py
```

You should see:
```
🤖 AI Call Agent Test Mode - Full-Duplex Enabled
📞 Call extension 5000 from extension 1000-5000 for full-duplex mode
   (Real bidirectional conversation with STT/TTS)
```

### Make a Test Call

**Option 1: From Asterisk CLI**
```bash
asterisk -rx "originate PJSIP/1000 extension 5000"
```

**Option 2: From SIP Phone**
- Register as extension 1000
- Dial 5000
- Speak naturally when prompted

**Option 3: From Different Extension**
- Register as extension 999 (or any number not 1000-5000)
- Dial 5000
- Listen to pre-scripted conversation (TTS-only mode)

## Architecture

### Components

1. **TelephonyConfig**: Configuration loader with environment variable expansion
2. **FullDuplexHandler**: Main handler for bidirectional calls
   - `route_call()`: Routes based on extension
   - `handle_full_duplex_call()`: Manages dialog loop
   - `handle_tts_only_call()`: Fallback mode
   - `speak_to_caller()`: TTS integration
   - `listen_and_transcribe()`: STT integration

### Integration Points

- **ARI Client**: Asterisk REST Interface for call control
- **STT Engine**: Speech-to-Text (Whisper/Google/OpenAI)
- **TTS Engine**: Text-to-Speech (Coqui/Polly/Google/OpenAI)
- **Conversation Engine**: OpenAI GPT for intelligent responses

## Files

```
src/telephony/
├── __init__.py                    # Package initialization
└── ibound_full_duplex.py         # Full-duplex implementation

config/
└── telephony.yml                 # Configuration file

docs/
├── leitfaden_de.md              # German conversation guide
├── CHANGELOG.md                 # Detailed changelog
└── telephony_setup.md           # Complete setup guide

tests/
└── test_ibound_full_duplex.py   # Unit and integration tests
```

## German Conversation Guide

A comprehensive German conversation script is available in `docs/leitfaden_de.md`. This guide covers:

1. Initial greeting and introduction (Krypto X Pay)
2. Confirmation of customer issue
3. Explanation of AI-powered recovery service
4. Handling customer interest
5. Managing hesitation
6. Appointment confirmation
7. Question handling with examples
8. Professional closing

The guide is designed for fund recovery conversations and includes success rate statistics (87%) and detailed explanations of the AI analysis process.

## Troubleshooting

### Issue: High latency

**Solution**: Use cloud providers or GPU acceleration
```yaml
stt:
  provider: google  # Much faster than local Whisper
  
# Or enable GPU
stt:
  device: cuda
```

### Issue: Agent doesn't understand

**Solution**: Increase model size
```yaml
stt:
  model: small  # or medium for better accuracy
```

### Issue: Extension not detected

**Solution**: Check caller ID format and range
```python
# The system extracts numeric digits from caller ID
# "PJSIP/1000" → 1000 ✓
# "ext-2500" → 2500 ✓
# "unknown" → not detected ✗
```

## Performance Tips

### Local Deployment (CPU)
- Use `base` Whisper model
- Expect 2-3 second latency per turn
- Suitable for testing and low-volume

### Production (Cloud)
- Use Google STT + AWS Polly
- Expect < 1 second latency per turn
- Suitable for production use

### High-Performance (GPU)
- Use `medium` or `large` Whisper model
- Enable CUDA acceleration
- Expect < 1 second latency locally

## Documentation

- **Setup Guide**: `docs/telephony_setup.md` - Complete configuration guide
- **Changelog**: `docs/CHANGELOG.md` - All changes and features
- **German Script**: `docs/leitfaden_de.md` - Customer conversation guide
- **Tests**: `tests/test_ibound_full_duplex.py` - Test examples

## Next Steps

1. **Test locally**: Run `python test_inbound_agent.py` and make calls
2. **Configure providers**: Choose STT/TTS providers in `config/telephony.yml`
3. **Adjust range**: Modify extension range if needed
4. **Deploy to production**: Use cloud providers for better performance
5. **Monitor**: Track call quality, latency, and accuracy

## Support

For detailed information:
- Read `docs/telephony_setup.md` for setup instructions
- Check `docs/CHANGELOG.md` for technical details
- Review test cases in `tests/test_ibound_full_duplex.py`
- Examine inline code documentation in `src/telephony/ibound_full_duplex.py`

---

**Note**: This feature is backward compatible. Existing functionality remains unchanged for calls from extensions outside the 1000-5000 range.
