# Quick Start Guide

## Prerequisites

1. Ubuntu 22.04 LTS
2. Asterisk 20.15.2 installed and running
3. MySQL/MariaDB installed
4. Python 3.8+
5. OpenAI API Key

## Installation (5 minutes)

### Step 1: Clone Repository

```bash
git clone https://github.com/berndmarcel860-byte/Agcai.git
cd Agcai
```

### Step 2: Run Setup

```bash
chmod +x setup.sh
./setup.sh
```

### Step 3: Configure Environment

```bash
nano .env
```

Minimum required settings:
```
# Database
DB_PASS=AiAgent990

# ARI
ARI_PASS=ai_agent_secure_password_123

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key-here

# Outbound
OUTBOUND_CALLER_ID=+49123456789
```

### Step 4: Initialize Database

```bash
source venv/bin/activate
python main.py --init-db
```

### Step 5: Start Campaign

```bash
python main.py --campaign "Test Campaign" --leads example_leads.csv
```

## First Call Test

### Prepare Test Leads

Edit `example_leads.csv`:
```csv
phone_number,first_name,last_name,email,company
+491234567890,Test,User,test@example.com,Test Company
```

### Run the Agent

```bash
python main.py --campaign "Fund Recovery Test" --leads example_leads.csv
```

### Monitor

Watch the logs:
```bash
tail -f logs/aiagent.log
```

## What Happens

1. Agent connects to Asterisk via ARI
2. Loads AI models (first time takes 2-5 minutes)
3. Reads leads from CSV file
4. Starts calling leads
5. Conducts AI-powered conversation
6. Records conversation
7. Schedules appointments if interested
8. Saves all data to database

## Verify Results

```bash
# Check database
mysql -u aiagent -p ai_calls

# View calls
SELECT * FROM call_records;

# View conversations
SELECT * FROM conversation_logs;

# View appointments
SELECT * FROM appointments;
```

## Troubleshooting

### "Cannot connect to database"

```bash
# Check MySQL is running
sudo systemctl status mysql

# Verify credentials
mysql -u aiagent -p -h 127.0.0.1
```

### "Cannot connect to ARI"

```bash
# Check Asterisk is running
sudo systemctl status asterisk

# Test ARI
curl -u ai_agent:ai_agent_secure_password_123 http://127.0.0.1:8088/ari/asterisk/info
```

### "OpenAI API Error"

- Verify your API key is correct
- Check you have credits available
- Ensure internet connection is working

### Models download slowly

First run downloads AI models (~500MB-2GB):
- Faster Whisper: ~150MB
- Coqui TTS: ~100MB

Be patient on first run.

## Next Steps

1. Review conversation logs
2. Adjust AI prompts in `src/ai/conversation.py`
3. Customize for your use case
4. Scale up with more leads
5. Monitor campaign statistics

## Support

- Check documentation in `docs/`
- Open an issue on GitHub
- Review logs in `logs/aiagent.log`
