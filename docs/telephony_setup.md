# Telephony Setup Guide

This guide covers the setup and configuration of the full-duplex bidirectional call handling system for the AI Call Agent.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Configuration](#configuration)
4. [STT Provider Setup](#stt-provider-setup)
5. [TTS Provider Setup](#tts-provider-setup)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Configuration](#advanced-configuration)

---

## Overview

The telephony system provides bidirectional call handling with the following features:

- **Full-duplex mode** for extensions 1000-5000: Real conversations with STT and TTS
- **TTS-only mode** for other extensions: Automated playback without speech recognition
- **Configurable providers**: Choose between local and cloud STT/TTS services
- **Low latency**: Optimized dialog loop for natural conversation flow

### Architecture

```
┌─────────────┐
│   Caller    │ ← Extension 1000-5000 = Full-duplex
│ (Extension) │ ← Other extensions = TTS-only
└──────┬──────┘
       │
       ↓
┌──────────────────────────────┐
│    Asterisk ARI Bridge       │
└──────────────┬───────────────┘
               │
               ↓
┌──────────────────────────────┐
│   FullDuplexHandler          │
│   - Route by extension       │
│   - Manage dialog loop       │
└──────────────┬───────────────┘
               │
       ┌───────┴────────┐
       ↓                ↓
┌─────────────┐  ┌─────────────┐
│  STT Engine │  │  TTS Engine │
│  (Whisper)  │  │   (Coqui)   │
└─────────────┘  └─────────────┘
```

---

## Prerequisites

### System Requirements

- Ubuntu 22.04 LTS (or similar)
- Python 3.8+
- Asterisk 20.15.2 with ARI enabled
- At least 4GB RAM (8GB recommended for local STT/TTS)
- ffmpeg (for audio conversion)

### Install ffmpeg

```bash
sudo apt update
sudo apt install ffmpeg
```

### Python Dependencies

All required dependencies are in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Key dependencies:
- `faster-whisper` - Local STT
- `TTS` (Coqui) - Local TTS
- `pyyaml` - Configuration
- `ari` - Asterisk ARI client

---

## Configuration

### Configuration File

The main configuration file is `config/telephony.yml`. This file is optional; defaults will be used if not present.

#### Default Configuration

```yaml
# Speech-to-Text Configuration
stt:
  provider: whisper  # whisper, google, or openai
  model: base        # For Whisper: tiny, base, small, medium, large
  language: de
  device: cpu

# Text-to-Speech Configuration
tts:
  provider: coqui    # coqui, polly, google, or openai
  model: tts_models/de/thorsten/tacotron2-DDC
  language: de
  sample_rate: 8000
  channels: 1

# Full-Duplex Configuration
full_duplex:
  enabled: true
  min_extension: 1000
  max_extension: 5000
  fallback_mode: tts_only
```

### Environment Variables

The configuration system supports environment variable expansion. You can use `${VAR_NAME}` syntax:

```yaml
stt:
  api_key: ${STT_API_KEY}
  
tts:
  api_key: ${TTS_API_KEY}
```

#### Available Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `STT_API_KEY` | API key for cloud STT provider | Only for cloud STT |
| `TTS_API_KEY` | API key for cloud TTS provider | Only for cloud TTS |
| `AGENT_ENDPOINT` | External agent endpoint URL | Optional |
| `TTS_VOICE` | Voice selection (provider-specific) | Optional |
| `ASTERISK_SOUNDS_DIR` | Asterisk sounds directory | Optional (default: `/var/lib/asterisk/sounds/aiagent`) |
| `ASTERISK_RECORDINGS_DIR` | Asterisk recordings directory | Optional (default: `/var/spool/asterisk/recording`) |

---

## STT Provider Setup

### Option 1: Whisper (Local, Default)

Whisper is enabled by default and requires no additional configuration.

**Advantages:**
- No API costs
- Works offline
- Privacy-friendly (no data sent to cloud)

**Disadvantages:**
- Higher latency on CPU-only systems
- Requires more RAM (especially for larger models)

**Configuration:**

```yaml
stt:
  provider: whisper
  model: base  # Options: tiny, base, small, medium, large
  language: de
  device: cpu  # or cuda for GPU acceleration
```

**Model Selection Guide:**

| Model | Memory | Speed | Accuracy | Recommendation |
|-------|--------|-------|----------|----------------|
| tiny | ~1 GB | Very Fast | Lower | Testing only |
| base | ~1 GB | Fast | Good | **Recommended for CPU** |
| small | ~2 GB | Medium | Better | Good balance |
| medium | ~5 GB | Slow | Excellent | GPU recommended |
| large | ~10 GB | Very Slow | Best | GPU required |

### Option 2: Google Speech-to-Text (Cloud)

**Prerequisites:**
1. Google Cloud account
2. Speech-to-Text API enabled
3. Service account with credentials

**Setup:**

1. Create a Google Cloud project
2. Enable Speech-to-Text API
3. Create a service account and download JSON key
4. Set environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
export STT_API_KEY="your-api-key"
```

**Configuration:**

```yaml
stt:
  provider: google
  api_key: ${STT_API_KEY}
  language: de-DE
```

### Option 3: OpenAI Whisper API (Cloud)

**Prerequisites:**
1. OpenAI account
2. API key with Whisper API access

**Setup:**

```bash
export STT_API_KEY="sk-your-openai-api-key"
```

**Configuration:**

```yaml
stt:
  provider: openai
  api_key: ${STT_API_KEY}
  model: whisper-1
  language: de
```

---

## TTS Provider Setup

### Option 1: Coqui TTS (Local, Default)

Coqui TTS is enabled by default with a German voice model.

**Advantages:**
- No API costs
- Works offline
- High-quality German voices

**Disadvantages:**
- Slower than cloud TTS on CPU
- Requires model download on first run (~200 MB)

**Configuration:**

```yaml
tts:
  provider: coqui
  model: tts_models/de/thorsten/tacotron2-DDC
  language: de
```

**Available German Models:**
- `tts_models/de/thorsten/tacotron2-DDC` (default, high quality)
- `tts_models/de/thorsten/vits` (faster, good quality)

### Option 2: AWS Polly (Cloud)

**Prerequisites:**
1. AWS account
2. AWS credentials configured
3. Polly access enabled

**Setup:**

```bash
# Configure AWS credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="eu-central-1"
export TTS_API_KEY="${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}"
```

**Configuration:**

```yaml
tts:
  provider: polly
  api_key: ${TTS_API_KEY}
  language: de-DE
  voice: Marlene  # German female voice
  # Other options: Hans (male)
```

### Option 3: Google Text-to-Speech (Cloud)

**Prerequisites:**
1. Google Cloud account
2. Text-to-Speech API enabled
3. Service account credentials

**Setup:**

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
export TTS_API_KEY="your-api-key"
```

**Configuration:**

```yaml
tts:
  provider: google
  api_key: ${TTS_API_KEY}
  language: de-DE
  voice: de-DE-Wavenet-A  # Female voice
```

### Option 4: OpenAI TTS (Cloud)

**Prerequisites:**
1. OpenAI account
2. API key with TTS access

**Setup:**

```bash
export TTS_API_KEY="sk-your-openai-api-key"
```

**Configuration:**

```yaml
tts:
  provider: openai
  api_key: ${TTS_API_KEY}
  model: tts-1
  voice: nova  # Options: alloy, echo, fable, onyx, nova, shimmer
  language: de
```

---

## Testing

### Local Testing

#### 1. Start the Inbound Test Agent

```bash
python test_inbound_agent.py
```

You should see:
```
🤖 AI Call Agent Test Mode - Full-Duplex Enabled
📞 Call extension 5000 from extension 1000-5000 for full-duplex mode
   (Real bidirectional conversation with STT/TTS)
```

#### 2. Make a Test Call

**From Extension 1000 (Full-Duplex):**
```bash
# From Asterisk CLI or softphone
Dial("PJSIP/1000", "5000")
```

Expected behavior:
- Call is answered
- Greeting is played
- Agent listens for your speech
- Agent responds to what you say
- Conversation continues until you say goodbye

**From Extension 999 (TTS-Only):**
```bash
Dial("PJSIP/999", "5000")
```

Expected behavior:
- Call is answered
- Scripted conversation is played (no listening)
- Call ends automatically

### Testing with SIPp

For automated testing, you can use SIPp:

```bash
# Install SIPp
sudo apt install sipp

# Create basic call scenario
sipp -sf basic_call.xml -s 5000 -d 30000 localhost:5060
```

### Unit Tests

Run the test suite:

```bash
# Run all tests
python tests/test_ibound_full_duplex.py

# Or with pytest
pytest tests/test_ibound_full_duplex.py -v

# Run specific test class
python -m unittest tests.test_ibound_full_duplex.TestFullDuplexHandler

# Run with coverage
pytest --cov=src/telephony tests/test_ibound_full_duplex.py
```

---

## Troubleshooting

### Common Issues

#### Issue: "Model not loaded" error

**Cause:** STT or TTS model failed to load

**Solution:**
```bash
# Check if models are downloading
ls -la ~/.cache/huggingface/hub/  # For Whisper
ls -la ~/.local/share/tts/         # For Coqui TTS

# Re-download models
python -c "from faster_whisper import WhisperModel; WhisperModel('base')"
python -c "from TTS.api import TTS; TTS('tts_models/de/thorsten/tacotron2-DDC')"
```

#### Issue: "ffmpeg not found"

**Cause:** ffmpeg is not installed

**Solution:**
```bash
sudo apt install ffmpeg
which ffmpeg  # Should show /usr/bin/ffmpeg
```

#### Issue: Recording file not found

**Cause:** Asterisk recordings directory permissions or path mismatch

**Solution:**
```bash
# Check directory exists and has correct permissions
sudo mkdir -p /var/spool/asterisk/recording
sudo chown asterisk:asterisk /var/spool/asterisk/recording
sudo chmod 755 /var/spool/asterisk/recording

# Verify in .env file
grep ASTERISK_RECORDINGS_DIR .env
```

#### Issue: High latency in full-duplex mode

**Cause:** CPU-intensive STT/TTS processing

**Solutions:**
1. Use smaller Whisper model:
   ```yaml
   stt:
     model: tiny  # or base
   ```

2. Use cloud providers (lower latency):
   ```yaml
   stt:
     provider: google
   tts:
     provider: polly
   ```

3. Use GPU acceleration (if available):
   ```yaml
   stt:
     device: cuda
   ```

#### Issue: Agent doesn't understand speech

**Cause:** Poor audio quality or incorrect language setting

**Solutions:**
1. Check microphone/audio quality
2. Verify language setting:
   ```yaml
   stt:
     language: de  # Make sure this matches your speech
   ```
3. Increase Whisper model size:
   ```yaml
   stt:
     model: small  # Better accuracy
   ```

#### Issue: Extension not in range

**Cause:** Extension number extraction failed

**Debug:**
```python
# Check logs for extension detection
grep "Extension.*in range" logs/test_agent.log
```

**Solution:**
- Ensure caller ID contains numeric extension (1000-5000)
- Adjust range in config if needed:
  ```yaml
  full_duplex:
    min_extension: 900
    max_extension: 6000
  ```

---

## Advanced Configuration

### Streaming Configuration

Enable low-latency streaming (experimental):

```yaml
stt:
  stream:
    enabled: true
    chunk_duration_ms: 500      # Shorter = lower latency, more processing
    silence_threshold: 300      # ms of silence to detect end of speech

full_duplex:
  realtime_streaming: true
```

### Custom Agent Endpoint

Use an external agent service:

```yaml
agent:
  endpoint: https://your-agent-api.com/process
  model: gpt-4-turbo-preview
  max_duration: 300
  response_timeout: 30
```

### Multi-Language Support

```yaml
stt:
  language: en  # or de, fr, es, etc.
  
tts:
  language: en-US
  voice: en-US-Wavenet-D
```

### Logging Configuration

```yaml
logging:
  level: DEBUG  # DEBUG, INFO, WARNING, ERROR
  log_transcripts: true
  directory: logs/telephony
```

### Performance Tuning

For high-volume deployments:

```yaml
full_duplex:
  realtime_streaming: false  # Less resource intensive
  
stt:
  model: base  # Faster than large models
  device: cuda  # Use GPU if available
  
tts:
  provider: polly  # Cloud TTS is faster
```

---

## Production Deployment

### Checklist

- [ ] Configure cloud STT/TTS providers for better latency
- [ ] Set up monitoring and logging
- [ ] Configure appropriate extension ranges
- [ ] Test failover scenarios
- [ ] Set up proper audio file cleanup
- [ ] Configure recording retention policies (GDPR compliance)
- [ ] Set up API rate limiting if using cloud providers
- [ ] Monitor API costs for cloud services
- [ ] Configure proper error handling and retry logic
- [ ] Set up alerts for system failures

### Monitoring

Monitor these metrics:
- Call duration
- Transcription accuracy
- Response latency
- API error rates
- System resource usage (CPU, RAM)

### Security

- Store API keys in environment variables
- Use secure credential management (e.g., AWS Secrets Manager)
- Encrypt recordings at rest
- Implement access controls on recording files
- Regular security audits of dependencies
- GDPR compliance for call recordings

---

## Support

For additional help:
- **Documentation**: Check other docs in `docs/` directory
- **Tests**: Review `tests/test_ibound_full_duplex.py` for examples
- **Code**: See inline documentation in `src/telephony/ibound_full_duplex.py`
- **Issues**: Open an issue on GitHub

---

## Appendix

### Extension Range Reference

| Extension Range | Mode | Description |
|----------------|------|-------------|
| 1000-5000 | Full-Duplex | Real bidirectional conversation |
| < 1000 or > 5000 | TTS-Only | Automated playback only |

### Provider Comparison

| Feature | Whisper (Local) | Google STT | OpenAI | AWS Polly | Coqui (Local) |
|---------|----------------|------------|--------|-----------|---------------|
| Cost | Free | Pay per use | Pay per use | Pay per use | Free |
| Latency | Medium-High | Low | Low | Low | Medium |
| Privacy | High | Medium | Medium | Medium | High |
| Accuracy | High | Very High | Very High | N/A | High |
| Offline | ✅ | ❌ | ❌ | ❌ | ✅ |
| Setup | Easy | Medium | Easy | Medium | Easy |

### Quick Command Reference

```bash
# Start agent
python test_inbound_agent.py

# Run tests
python tests/test_ibound_full_duplex.py

# Check configuration
cat config/telephony.yml

# View logs
tail -f logs/test_agent.log
tail -f logs/telephony/*.log

# Test models
python -c "from faster_whisper import WhisperModel; print('Whisper OK')"
python -c "from TTS.api import TTS; print('TTS OK')"
```
