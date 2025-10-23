#!/usr/bin/env python3
"""
Lightweight Test Server for Inbound Agent Manual Testing

This script provides a simple WebSocket server that simulates an inbound AI agent
for manual testing without requiring Asterisk, OpenAI, or other infrastructure.

Features:
- WebSocket server on localhost (secure, no external access)
- Stateful conversation flow simulating real agent behavior
- Console logging of all messages for debugging
- No external dependencies beyond Python websockets library
- Easy to run and test with any WebSocket client

Usage:
    python tests/test_inbound_real_conversation.py [--port 8765] [--host localhost]

Test with clients:
    # Python websocket client (see example below)
    python tests/test_inbound_real_conversation.py --client
    
    # websocat (if installed)
    websocat ws://localhost:8765
    
    # wscat (if installed via npm)
    wscat -c ws://localhost:8765
"""

import asyncio
import json
import logging
import argparse
import sys
from datetime import datetime
from typing import Dict, Optional
from enum import Enum

try:
    import websockets
    from websockets.server import serve
except ImportError:
    print("ERROR: websockets library not installed")
    print("Please install it with: pip install websockets")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Conversation states for the test agent"""
    INITIAL = "initial"
    GREETED = "greeted"
    QUALIFYING = "qualifying"
    QUALIFIED = "qualified"
    EXPLAINING_SERVICE = "explaining_service"
    SCHEDULING = "scheduling"
    SCHEDULED = "scheduled"
    CLOSED = "closed"


class TestInboundAgent:
    """
    Lightweight test agent simulating inbound conversation behavior.
    
    This agent implements a state machine that mimics the real agent's
    conversation flow but without external dependencies.
    """
    
    def __init__(self, client_id: str):
        """Initialize agent for a specific client session"""
        self.client_id = client_id
        self.state = ConversationState.INITIAL
        self.conversation_history = []
        self.user_name = None
        self.fraud_type = None
        self.lost_amount = None
        self.appointment_date = None
        
    def get_initial_greeting(self) -> str:
        """Get initial greeting message"""
        self.state = ConversationState.GREETED
        return (
            "Guten Tag! Hier spricht der KI-Assistent vom Fund Recovery Service. "
            "Vielen Dank, dass Sie unseren Test-Service anrufen. "
            "Wie kann ich Ihnen heute helfen?"
        )
        
    def process_message(self, user_message: str) -> str:
        """
        Process user message and return appropriate response based on state.
        
        Args:
            user_message: Message from the user
            
        Returns:
            Agent's response
        """
        # Store message in history
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Process based on current state
        response = self._generate_response(user_message)
        
        # Store response in history
        self.conversation_history.append({
            "role": "agent",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return response
        
    def _generate_response(self, user_message: str) -> str:
        """Generate contextual response based on conversation state"""
        message_lower = user_message.lower()
        
        # Initial greeting state
        if self.state == ConversationState.GREETED:
            self.state = ConversationState.QUALIFYING
            return (
                "Ich bin hier, um Ihnen bei der Rückforderung von verlorenem Geld zu helfen. "
                "Darf ich fragen, haben Sie Geld durch Betrug oder eine verdächtige "
                "Transaktion verloren?"
            )
            
        # Qualifying state - determining if user needs help
        elif self.state == ConversationState.QUALIFYING:
            if any(word in message_lower for word in ["ja", "yes", "verloren", "betrug", "scam"]):
                self.state = ConversationState.QUALIFIED
                return (
                    "Das tut mir sehr leid zu hören. Ich verstehe, wie frustrierend das sein kann. "
                    "Unser Fund Recovery Service hat vielen Menschen geholfen, ihr Geld zurückzubekommen. "
                    "Können Sie mir kurz sagen, um welche Art von Betrug es sich handelte?"
                )
            elif any(word in message_lower for word in ["nein", "no", "nicht"]):
                self.state = ConversationState.CLOSED
                return (
                    "Verstanden. Falls Sie in Zukunft Unterstützung benötigen, "
                    "stehen wir Ihnen gerne zur Verfügung. Vielen Dank für Ihren Anruf und einen schönen Tag!"
                )
            else:
                return (
                    "Ich verstehe. Lassen Sie mich die Frage umformulieren: "
                    "Haben Sie kürzlich Geld verloren, zum Beispiel durch Online-Betrug, "
                    "Krypto-Investitionen oder andere verdächtige Transaktionen?"
                )
                
        # Qualified state - gathering information
        elif self.state == ConversationState.QUALIFIED:
            # Extract any fraud type mentioned
            fraud_types = {
                "krypto": "Kryptowährungsbetrug",
                "crypto": "Kryptowährungsbetrug",
                "bitcoin": "Kryptowährungsbetrug",
                "investment": "Investitionsbetrug",
                "investition": "Investitionsbetrug",
                "phishing": "Phishing",
                "romance": "Romance Scam",
                "liebe": "Romance Scam"
            }
            
            for keyword, fraud in fraud_types.items():
                if keyword in message_lower:
                    self.fraud_type = fraud
                    break
            
            if not self.fraud_type:
                self.fraud_type = "nicht spezifizierter Betrug"
                
            self.state = ConversationState.EXPLAINING_SERVICE
            return (
                f"Ich verstehe. {self.fraud_type} ist leider sehr verbreitet. "
                "Die gute Nachricht ist, dass unser Service auf solche Fälle spezialisiert ist. "
                "Wir arbeiten mit Banken und Behörden zusammen, um verlorenes Geld zurückzufordern. "
                "Unsere Erfolgsquote liegt bei über 65%. "
                "Würden Sie gerne mehr über unseren Prozess erfahren?"
            )
            
        # Explaining service
        elif self.state == ConversationState.EXPLAINING_SERVICE:
            if any(word in message_lower for word in ["ja", "yes", "gerne", "interest"]):
                self.state = ConversationState.SCHEDULING
                return (
                    "Perfekt! Der erste Schritt wäre ein kostenloses Beratungsgespräch, "
                    "bei dem wir Ihren Fall im Detail besprechen. Das Gespräch dauert etwa 30 Minuten. "
                    "Hätten Sie diese Woche Zeit für einen Termin? "
                    "Zum Beispiel morgen um 10 Uhr oder übermorgen um 14 Uhr?"
                )
            else:
                return (
                    "Natürlich. Haben Sie noch Fragen zu unserem Service? "
                    "Ich kann Ihnen gerne mehr Details geben, bevor wir einen Termin vereinbaren."
                )
                
        # Scheduling appointment
        elif self.state == ConversationState.SCHEDULING:
            # Accept any response as appointment confirmation for testing
            if any(word in message_lower for word in ["morgen", "10", "14", "uhr", "passt", "ok", "gut"]):
                self.appointment_date = "Morgen um 10:00 Uhr"  # Mock appointment
                self.state = ConversationState.SCHEDULED
                return (
                    f"Ausgezeichnet! Ich habe für Sie einen Termin für morgen um 10:00 Uhr vorgemerkt. "
                    "Sie erhalten eine Bestätigungs-Email mit allen Details und dem Video-Call-Link. "
                    "Gibt es noch etwas, womit ich Ihnen helfen kann?"
                )
            else:
                return (
                    "Kein Problem. Welcher Termin würde Ihnen besser passen? "
                    "Wir haben auch Termine am Nachmittag oder nächste Woche verfügbar."
                )
                
        # Appointment scheduled - closing
        elif self.state == ConversationState.SCHEDULED:
            self.state = ConversationState.CLOSED
            return (
                "Vielen Dank für Ihr Vertrauen! Wir freuen uns auf das Gespräch mit Ihnen. "
                "Bis morgen um 10:00 Uhr. Auf Wiederhören!"
            )
            
        # Closed state
        elif self.state == ConversationState.CLOSED:
            return (
                "Das Gespräch wurde beendet. Vielen Dank! "
                "Sie können die Verbindung jetzt trennen."
            )
            
        # Default fallback
        return (
            "Entschuldigung, ich habe das nicht ganz verstanden. "
            "Können Sie das bitte nochmal formulieren?"
        )
        
    def get_conversation_summary(self) -> Dict:
        """Get summary of the conversation for logging"""
        return {
            "client_id": self.client_id,
            "state": self.state.value,
            "messages_exchanged": len(self.conversation_history),
            "fraud_type": self.fraud_type,
            "appointment_date": self.appointment_date,
            "conversation_history": self.conversation_history
        }


class TestInboundServer:
    """WebSocket server for testing inbound agent behavior"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """Initialize the test server"""
        self.host = host
        self.port = port
        self.active_sessions: Dict[str, TestInboundAgent] = {}
        self.connection_count = 0
        
    async def handle_client(self, websocket, path):
        """
        Handle incoming WebSocket connection from a client.
        
        Args:
            websocket: WebSocket connection
            path: Connection path (unused)
        """
        # Generate client ID
        self.connection_count += 1
        client_id = f"client_{self.connection_count}"
        client_address = websocket.remote_address
        
        logger.info(f"🔌 New connection from {client_address} (ID: {client_id})")
        
        # Create agent for this client
        agent = TestInboundAgent(client_id)
        self.active_sessions[client_id] = agent
        
        try:
            # Send initial greeting
            greeting = agent.get_initial_greeting()
            await self._send_message(websocket, greeting, client_id)
            
            # Handle messages
            async for message in websocket:
                # Log incoming message
                logger.info(f"📩 [{client_id}] User: {message}")
                
                # Process message and get response
                response = agent.process_message(message)
                
                # Send response
                await self._send_message(websocket, response, client_id)
                
                # If conversation is closed, wait a bit then close connection
                if agent.state == ConversationState.CLOSED:
                    await asyncio.sleep(1)
                    break
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 Connection closed by {client_id}")
        except Exception as e:
            logger.error(f"❌ Error handling client {client_id}: {e}")
        finally:
            # Log conversation summary
            summary = agent.get_conversation_summary()
            logger.info(f"📊 Conversation summary for {client_id}:")
            logger.info(f"   - State: {summary['state']}")
            logger.info(f"   - Messages: {summary['messages_exchanged']}")
            logger.info(f"   - Fraud type: {summary['fraud_type']}")
            logger.info(f"   - Appointment: {summary['appointment_date']}")
            
            # Clean up
            if client_id in self.active_sessions:
                del self.active_sessions[client_id]
                
    async def _send_message(self, websocket, message: str, client_id: str):
        """Send message to client and log it"""
        logger.info(f"📤 [{client_id}] Agent: {message}")
        await websocket.send(message)
        
    async def start(self):
        """Start the WebSocket server"""
        logger.info("=" * 70)
        logger.info("🤖 Test Inbound Agent Server")
        logger.info("=" * 70)
        logger.info(f"Server starting on {self.host}:{self.port}")
        logger.info("")
        logger.info("This server simulates an inbound AI agent for manual testing.")
        logger.info("Connect with any WebSocket client to start a conversation.")
        logger.info("")
        logger.info("Example client commands:")
        logger.info(f"  - websocat: websocat ws://{self.host}:{self.port}")
        logger.info(f"  - wscat:   wscat -c ws://{self.host}:{self.port}")
        logger.info(f"  - Python:  python {__file__} --client")
        logger.info("")
        logger.info("Press Ctrl+C to stop the server")
        logger.info("=" * 70)
        logger.info("")
        
        async with serve(self.handle_client, self.host, self.port):
            await asyncio.Future()  # Run forever


async def run_test_client(host: str = "localhost", port: int = 8765):
    """
    Run a simple test client for manual testing.
    
    This client connects to the server and allows interactive conversation.
    """
    uri = f"ws://{host}:{port}"
    
    print("=" * 70)
    print("🧪 Test WebSocket Client")
    print("=" * 70)
    print(f"Connecting to {uri}...")
    print("")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected! Waiting for agent greeting...\n")
            
            # Receive and print initial greeting
            greeting = await websocket.recv()
            print(f"Agent: {greeting}\n")
            
            # Interactive conversation loop
            while True:
                # Get user input
                try:
                    user_input = input("You: ").strip()
                    if not user_input:
                        continue
                        
                    # Exit commands
                    if user_input.lower() in ['exit', 'quit', 'bye']:
                        print("\nClosing connection...")
                        break
                        
                    # Send message
                    await websocket.send(user_input)
                    
                    # Receive response
                    response = await websocket.recv()
                    print(f"\nAgent: {response}\n")
                    
                except EOFError:
                    break
                except KeyboardInterrupt:
                    print("\n\nInterrupted by user")
                    break
                    
    except ConnectionRefusedError:
        print(f"❌ Error: Could not connect to {uri}")
        print("Make sure the server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Lightweight test server for inbound agent manual testing'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8765,
        help='Port to run server on (default: 8765)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='Host to bind to (default: localhost)'
    )
    parser.add_argument(
        '--client',
        action='store_true',
        help='Run as test client instead of server'
    )
    
    args = parser.parse_args()
    
    try:
        if args.client:
            # Run test client
            asyncio.run(run_test_client(args.host, args.port))
        else:
            # Run server
            server = TestInboundServer(args.host, args.port)
            asyncio.run(server.start())
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
