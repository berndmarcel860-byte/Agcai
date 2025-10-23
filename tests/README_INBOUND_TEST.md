# Testing the Inbound Agent - Manual Testing Guide

This guide explains how to manually test the inbound AI agent using the lightweight test server.

## Overview

The test server (`tests/test_inbound_real_conversation.py`) provides a simple WebSocket-based simulation of an inbound AI agent without requiring Asterisk, OpenAI, or other infrastructure dependencies.

**Features:**
- ✅ Lightweight WebSocket server (Python + websockets)
- ✅ Simulates real agent conversation flow with stateful behavior
- ✅ Runs locally on localhost (secure, no external access)
- ✅ Detailed console logging of all messages
- ✅ No external API calls or credentials needed
- ✅ Easy to test with various WebSocket clients

## Quick Start

### Option 1: Using the Run Script (Recommended)

**On Linux/Mac:**
```bash
# Start the server
./scripts/run_test_inbound.sh

# In another terminal, start a test client
./scripts/run_test_inbound.sh --client
```

**On Windows:**
```cmd
REM Start the server
scripts\run_test_inbound.bat

REM In another terminal, start a test client
scripts\run_test_inbound.bat --client
```

### Option 2: Manual Setup

1. **Install dependencies:**
   ```bash
   pip install websockets
   ```

2. **Start the server:**
   ```bash
   python3 tests/test_inbound_real_conversation.py
   ```

3. **Connect with a client** (see options below)

## Testing with Different Clients

### Built-in Python Client

The easiest way to test is with the built-in Python client:

```bash
python3 tests/test_inbound_real_conversation.py --client
```

This will connect to the server and allow interactive conversation in your terminal.

### websocat (Recommended CLI Tool)

[websocat](https://github.com/vi/websocat) is a great command-line WebSocket client.

**Install:**
```bash
# On Linux (using cargo)
cargo install websocat

# On Mac
brew install websocat

# Or download binary from GitHub releases
```

**Use:**
```bash
websocat ws://localhost:8765
```

### wscat (Node.js-based)

If you have Node.js installed:

```bash
# Install globally
npm install -g wscat

# Connect
wscat -c ws://localhost:8765
```

### Custom Python Client

Create your own client script:

```python
import asyncio
import websockets

async def test_client():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        # Receive greeting
        greeting = await websocket.recv()
        print(f"Agent: {greeting}")
        
        # Send messages
        await websocket.send("Hallo!")
        response = await websocket.recv()
        print(f"Agent: {response}")

asyncio.run(test_client())
```

## Conversation Flow

The test agent simulates a realistic conversation flow:

1. **Initial Greeting**: Agent greets the caller
2. **Qualification**: Agent asks if caller lost money to fraud
3. **Information Gathering**: Agent asks about fraud type
4. **Service Explanation**: Agent explains the recovery service
5. **Appointment Scheduling**: Agent offers appointment times
6. **Confirmation & Closing**: Agent confirms appointment and closes

### Example Conversation

```
Agent: Guten Tag! Hier spricht der KI-Assistent vom Fund Recovery Service...
You: Hallo, ich brauche Hilfe

Agent: Ich bin hier, um Ihnen bei der Rückforderung von verlorenem Geld zu helfen...
You: Ja, ich habe Geld verloren

Agent: Das tut mir sehr leid zu hören...
You: Es war ein Krypto-Betrug

Agent: Ich verstehe. Kryptowährungsbetrug ist leider sehr verbreitet...
You: Ja, ich möchte mehr erfahren

Agent: Perfekt! Der erste Schritt wäre ein kostenloses Beratungsgespräch...
You: Morgen um 10 Uhr passt mir gut

Agent: Ausgezeichnet! Ich habe für Sie einen Termin für morgen um 10:00 Uhr vorgemerkt...
```

## Server Configuration

### Command-line Options

```bash
# Custom port
python3 tests/test_inbound_real_conversation.py --port 9000

# Custom host (use with caution - localhost is safer)
python3 tests/test_inbound_real_conversation.py --host 0.0.0.0 --port 8765

# Run as client
python3 tests/test_inbound_real_conversation.py --client
```

### Default Settings

- **Host**: `localhost` (127.0.0.1) - only accessible from your machine
- **Port**: `8765` - standard WebSocket testing port
- **Protocol**: WebSocket (ws://)

## What Gets Logged

The server logs all activity to the console:

```
🔌 New connection from ('127.0.0.1', 54321) (ID: client_1)
📤 [client_1] Agent: Guten Tag! Hier spricht der KI-Assistent...
📩 [client_1] User: Hallo
📤 [client_1] Agent: Ich bin hier, um Ihnen bei der Rückforderung...
📊 Conversation summary for client_1:
   - State: scheduled
   - Messages: 12
   - Fraud type: Kryptowährungsbetrug
   - Appointment: Morgen um 10:00 Uhr
```

## Testing Scenarios

### Scenario 1: Qualified Lead (Happy Path)
1. Connect to server
2. Respond positively about losing money
3. Mention a fraud type (crypto, investment, phishing)
4. Express interest in the service
5. Accept an appointment time

### Scenario 2: Unqualified Lead
1. Connect to server
2. Say you have not lost money
3. Observe polite closing

### Scenario 3: Interested but Hesitant
1. Connect to server
2. Say yes to losing money
3. Ask questions about the service
4. Eventually accept or decline appointment

## Troubleshooting

### "websockets library not installed"

```bash
pip install websockets
```

### "Address already in use"

Another process is using port 8765. Either:
- Stop the other process
- Use a different port: `--port 9000`

### "Connection refused"

Make sure the server is running:
```bash
python3 tests/test_inbound_real_conversation.py
```

Then connect with a client in a separate terminal.

### Server won't start

Check Python version:
```bash
python3 --version  # Should be 3.8 or higher
```

## Integration with Real Agent

This test server is designed to be a **standalone testing tool**. It simulates the conversation logic without requiring:
- Asterisk ARI
- OpenAI API
- TTS/STT models
- Database

The conversation flow and state machine are modeled after the real agent (`test_inbound_agent.py`) but simplified for testing.

## Security Notes

- ✅ Server binds to `localhost` by default (only accessible from your machine)
- ✅ No external network calls
- ✅ No sensitive data handling
- ✅ Safe for development testing

**Warning**: Do not bind to `0.0.0.0` on production or shared networks without proper security measures.

## Next Steps

Once you've tested the inbound behavior:

1. Review the conversation flow and state transitions
2. Modify `tests/test_inbound_real_conversation.py` to test different scenarios
3. Use this as a reference when implementing the real agent logic
4. Compare behavior with the full agent in `test_inbound_agent.py`

## Additional Resources

- **WebSocket Protocol**: https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API
- **websockets Library**: https://websockets.readthedocs.io/
- **websocat Tool**: https://github.com/vi/websocat

## Support

If you encounter issues:
1. Check the server logs for error messages
2. Verify Python version is 3.8+
3. Ensure websockets library is installed
4. Try the built-in client first: `--client` flag

For more help, open an issue on the GitHub repository.
