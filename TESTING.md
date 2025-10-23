# Manual Testing Guide for AI Call Agent

This guide explains how to test the AI Call Agent manually by calling extension 5000 from extension 1000 before running full campaigns.

## Prerequisites

1. Asterisk 20.15.2 installed and running
2. Extensions configured (1000 and 5000)
3. ARI enabled and configured
4. All dependencies installed (`pip install -r requirements.txt`)
5. `.env` file configured with your settings
6. `ffmpeg` installed for audio conversion

## Asterisk Configuration

### 1. Extensions Configuration (`/etc/asterisk/extensions.conf`)

Make sure you have the following configuration:

```ini
[general]
static=yes
writeprotect=no
autofallthrough=yes

[internal]
; Test extension - calls AI agent
exten => 5000,1,NoOp(📞 Entering AI Agent Suite)
    same => n,Answer()
    same => n,Set(CHANNEL(language)=de)
    same => n,Stasis(aiagent)
    same => n,Hangup()

; Manual playback test (optional)
exten => 6000,1,NoOp(🔊 Testing playback)
    same => n,Answer()
    same => n,Playback(aiagent/tts_fac54a450425a413d778c2d2e3b4affd)
    same => n,Hangup()

; Your regular extension 1000 (for calling from)
exten => 1000,1,Dial(PJSIP/1000,20)
    same => n,Hangup()
```

### 2. ARI Configuration (`/etc/asterisk/ari.conf`)

```ini
[general]
enabled = yes
pretty = yes
websocket_write_timeout = 100

[ai_agent]
type = user
read_only = no
password = ai_agent_secure_password_123
```

### 3. HTTP Configuration (`/etc/asterisk/http.conf`)

```ini
[general]
enabled = yes
bindaddr = 127.0.0.1
bindport = 8088
```

### 4. Reload Asterisk

```bash
asterisk -rx "dialplan reload"
asterisk -rx "core reload"
```

## Directory Setup

The test script uses specific directories for audio files. Make sure they exist and have proper permissions:

```bash
# Create directories
sudo mkdir -p /var/lib/asterisk/sounds/aiagent
sudo mkdir -p /var/spool/asterisk/recording

# Set permissions (adjust as needed for your setup)
sudo chown -R asterisk:asterisk /var/lib/asterisk/sounds/aiagent
sudo chown -R asterisk:asterisk /var/spool/asterisk/recording
sudo chmod -R 755 /var/lib/asterisk/sounds/aiagent
sudo chmod -R 755 /var/spool/asterisk/recording
```

## Environment Configuration

Update your `.env` file with the Asterisk directory paths:

```bash
# Asterisk Directories
ASTERISK_SOUNDS_DIR=/var/lib/asterisk/sounds/aiagent
ASTERISK_RECORDINGS_DIR=/var/spool/asterisk/recording
```

## Running the Test

### 1. Start the Test Agent

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Run the test agent
python test_inbound_agent.py
```

You should see output like:

```
============================================================
🤖 AI Call Agent Test Mode
============================================================

📞 Call extension 5000 from extension 1000 to test the agent

Configuration:
  - ARI App: aiagent
  - ARI Host: 127.0.0.1:8088
  - Sounds Dir: /var/lib/asterisk/sounds/aiagent
  - Recordings Dir: /var/spool/asterisk/recording

Press Ctrl+C to stop
============================================================
```

### 2. Make a Test Call

From extension 1000, dial **5000**.

The AI agent will:
1. ✅ Answer the call
2. 🎙️ Start recording
3. 👋 Greet you in German
4. 💬 Have a sample conversation
5. 📴 End the call gracefully

### 3. Monitor the Output

Watch the console for detailed logging:

```
📞 Incoming call from 1000 on channel SIP/1000-00000001
✅ Call answered on channel SIP/1000-00000001
🎙️ Recording started: test_SIP/1000-00000001_1234567890
Agent says: Guten Tag! Willkommen beim Fund Recovery Service Test...
💬 Conversation started. Agent is ready to respond.
📴 Call ended from 1000, duration: 15s
```

## Audio Conversion

The test script automatically converts TTS-generated audio to Asterisk-compatible format:

- **Sample Rate**: 8000 Hz
- **Channels**: 1 (mono)
- **Codec**: pcm_s16le
- **Format**: WAV

This is done using ffmpeg:

```bash
ffmpeg -y -hide_banner -loglevel error \
  -f wav -i input.wav \
  -ac 1 -ar 8000 -acodec pcm_s16le output.wav
```

## Troubleshooting

### Issue: "ffmpeg not found"

**Solution**: Install ffmpeg

```bash
sudo apt update
sudo apt install ffmpeg
```

### Issue: "Failed to connect to ARI"

**Solution**: Check ARI configuration

```bash
# Test ARI connection
curl -u ai_agent:ai_agent_secure_password_123 http://127.0.0.1:8088/ari/asterisk/info

# Check Asterisk ARI status
asterisk -rx "ari show status"
```

### Issue: "Permission denied" when writing audio files

**Solution**: Fix directory permissions

```bash
sudo chown -R asterisk:asterisk /var/lib/asterisk/sounds/aiagent
sudo chmod -R 755 /var/lib/asterisk/sounds/aiagent
```

### Issue: No audio during call

**Solution**: Check audio file creation and playback

```bash
# List generated audio files
ls -lh /var/lib/asterisk/sounds/aiagent/

# Test playback manually
# Dial 6000 and replace filename with actual generated file
# Edit extensions.conf exten 6000 with your filename
```

### Issue: "Models downloading"

**Solution**: This is normal on first run. The TTS and STT models will download automatically. This can take 5-10 minutes depending on your connection.

## Checking Call Recordings

After a test call, check the recordings:

```bash
ls -lh /var/spool/asterisk/recording/
```

You should see files like `test_SIP-1000-00000001_1234567890.wav`

## Logs

Check the log file for detailed information:

```bash
tail -f logs/test_agent.log
```

## Testing Checklist

- [ ] Asterisk is running
- [ ] Extensions.conf configured with extension 5000
- [ ] ARI enabled and accessible
- [ ] Directories created with proper permissions
- [ ] `.env` file configured
- [ ] ffmpeg installed
- [ ] Test agent started successfully
- [ ] Models loaded (TTS and STT)
- [ ] Call from 1000 to 5000 works
- [ ] Call is answered
- [ ] AI greeting is played
- [ ] Audio is clear
- [ ] Recording is created
- [ ] Call ends gracefully

## Next Steps

Once manual testing is successful:

1. ✅ Verify audio quality is acceptable
2. ✅ Test with different phrases/questions
3. ✅ Check conversation logs in database (optional)
4. ✅ Review recordings for quality
5. 🚀 Move to campaign mode with `main.py`

## Differences from Campaign Mode

**Test Mode (test_inbound_agent.py):**
- Handles inbound calls only
- Extension 5000 → Stasis → AI Agent
- Interactive testing
- Simulated conversation flow
- No database persistence (optional)

**Campaign Mode (main.py):**
- Makes outbound calls
- Loads leads from CSV or database
- Manages multiple concurrent calls
- Full database persistence
- Campaign statistics

## Support

If you encounter issues:

1. Check logs: `logs/test_agent.log`
2. Check Asterisk logs: `/var/log/asterisk/full`
3. Verify ARI connection: `curl http://127.0.0.1:8088/ari/asterisk/info`
4. Check audio directory permissions
5. Ensure all dependencies are installed

For more help, refer to:
- **README.md**: Main documentation
- **QUICKSTART.md**: Setup guide
- **docs/asterisk_configuration.md**: Asterisk setup
