# API Documentation

## Database Models

### Lead

Represents a potential customer contact.

**Fields:**
- `id`: Primary key
- `phone_number`: Contact phone number (unique)
- `first_name`: First name
- `last_name`: Last name  
- `email`: Email address
- `company`: Company name
- `status`: Lead status (new, contacted, interested, not_interested, appointment_scheduled, callback_requested, do_not_call)
- `notes`: Additional notes
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Campaign

Represents an outbound calling campaign.

**Fields:**
- `id`: Primary key
- `name`: Campaign name
- `description`: Campaign description
- `status`: Campaign status (active, paused, completed)
- `max_concurrent_calls`: Maximum simultaneous calls
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### CallRecord

Tracks individual call attempts and results.

**Fields:**
- `id`: Primary key
- `campaign_id`: Foreign key to Campaign
- `lead_id`: Foreign key to Lead
- `phone_number`: Called number
- `channel_id`: Asterisk channel ID
- `call_status`: Call status (initiated, ringing, answered, completed, failed, busy, no_answer)
- `duration`: Call duration in seconds
- `started_at`: Call start time
- `answered_at`: Time call was answered
- `ended_at`: Call end time

### ConversationLog

Stores conversation transcript.

**Fields:**
- `id`: Primary key
- `call_record_id`: Foreign key to CallRecord
- `speaker`: Speaker (agent, customer)
- `message`: Message text
- `timestamp`: Message timestamp

### Appointment

Scheduled appointments from calls.

**Fields:**
- `id`: Primary key
- `lead_id`: Foreign key to Lead
- `call_record_id`: Foreign key to CallRecord
- `appointment_date`: Scheduled date/time
- `appointment_type`: Type of appointment
- `notes`: Additional notes
- `status`: Appointment status (scheduled, confirmed, completed, cancelled, no_show)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## Python API

### ARIClient

**Methods:**

```python
# Connect to ARI
client.connect()

# Originate call
channel = client.originate_call(
    endpoint="PJSIP/+491234567890",
    caller_id="+49987654321",
    timeout=30
)

# Answer channel
client.answer_channel(channel_id)

# Hangup channel
client.hangup_channel(channel_id)

# Play media
client.play_media(channel_id, "sound:hello-world")

# Start recording
client.start_recording(channel_id, "recording_name")

# Stop recording
client.stop_recording("recording_name")
```

### ConversationEngine

**Methods:**

```python
# Initialize
engine = ConversationEngine(api_key="sk-...", model="gpt-4-turbo-preview")

# Start conversation
history = engine.start_conversation()

# Get AI response
response = engine.get_response(history, "Hallo, wie geht es Ihnen?")

# Extract appointment info
appointment_info = engine.extract_appointment_info(history)

# Analyze sentiment
sentiment = engine.analyze_sentiment("Ich bin sehr interessiert!")
```

### TextToSpeech

**Methods:**

```python
# Initialize
tts = TextToSpeech(model_name="tts_models/de/thorsten/tacotron2-DDC")

# Load model
tts.load_model()

# Synthesize to file
tts.synthesize("Guten Tag!", "/tmp/output.wav")

# Synthesize to bytes
audio_bytes = tts.synthesize_to_bytes("Guten Tag!")
```

### SpeechToText

**Methods:**

```python
# Initialize
stt = SpeechToText(model_size="base", language="de")

# Load model
stt.load_model()

# Transcribe file
text = stt.transcribe_file("/tmp/audio.wav")

# Transcribe with timestamps
segments = stt.transcribe_with_timestamps("/tmp/audio.wav")

# Detect language
language = stt.detect_language("/tmp/audio.wav")
```

### CampaignManager

**Methods:**

```python
# Create campaign
campaign_id = manager.create_campaign(
    name="Fund Recovery Campaign",
    description="Lead generation for fund recovery service"
)

# Add leads
leads_data = [
    {"phone_number": "+491234567890", "first_name": "Max", "last_name": "Mustermann"}
]
manager.add_leads(leads_data)

# Start campaign
manager.start_campaign(campaign_id)

# Stop campaign
manager.stop_campaign()

# Get statistics
stats = manager.get_campaign_stats(campaign_id)
```
