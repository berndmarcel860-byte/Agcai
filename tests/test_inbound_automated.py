#!/usr/bin/env python3
"""
Automated test for the test inbound agent server.

This test starts the server, performs a simple conversation exchange,
and verifies the behavior.
"""

import unittest
import asyncio
import sys
import os
from typing import Optional

# Add parent directory to path to import the test server
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import websockets
    from websockets.server import serve
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("Warning: websockets not installed, skipping automated tests")


# Only define tests if websockets is available
if WEBSOCKETS_AVAILABLE:
    # Import the server components
    from tests.test_inbound_real_conversation import TestInboundAgent, TestInboundServer
    
    class TestInboundAgentAutomated(unittest.TestCase):
        """Automated tests for the inbound agent test server"""
        
        def test_agent_state_machine(self):
            """Test the agent's state machine transitions"""
            agent = TestInboundAgent("test_client")
            
            # Initial state
            self.assertEqual(agent.state.value, "initial")
            
            # Get greeting
            greeting = agent.get_initial_greeting()
            self.assertIn("Fund Recovery Service", greeting)
            self.assertEqual(agent.state.value, "greeted")
            
            # First message - should move to qualifying
            response = agent.process_message("Hallo")
            self.assertIn("betrug", response.lower())
            self.assertEqual(agent.state.value, "qualifying")
            
            # Positive response - should qualify
            response = agent.process_message("Ja, ich habe Geld verloren")
            self.assertIn("leid", response.lower())
            self.assertEqual(agent.state.value, "qualified")
            
            # Provide fraud type
            response = agent.process_message("Es war ein Krypto-Betrug")
            self.assertEqual(agent.state.value, "explaining_service")
            self.assertEqual(agent.fraud_type, "Kryptowährungsbetrug")
            
            # Express interest
            response = agent.process_message("Ja, gerne")
            self.assertIn("Termin", response)
            self.assertEqual(agent.state.value, "scheduling")
            
            # Accept appointment
            response = agent.process_message("Morgen um 10 Uhr passt")
            self.assertIn("vorgemerkt", response)
            self.assertEqual(agent.state.value, "scheduled")
            self.assertIsNotNone(agent.appointment_date)
            
        def test_agent_rejection_path(self):
            """Test when user says they haven't lost money"""
            agent = TestInboundAgent("test_client")
            
            greeting = agent.get_initial_greeting()
            self.assertEqual(agent.state.value, "greeted")
            
            # First message
            agent.process_message("Hallo")
            self.assertEqual(agent.state.value, "qualifying")
            
            # Say no to losing money - note the agent needs to ask the question first
            # before we can say no. The first "Hallo" triggers the qualification question.
            # Let's send a clear negative response.
            response = agent.process_message("Nein")
            self.assertIn("schönen Tag", response)
            self.assertEqual(agent.state.value, "closed")
            
        def test_conversation_history(self):
            """Test that conversation history is tracked"""
            agent = TestInboundAgent("test_client")
            
            agent.get_initial_greeting()
            agent.process_message("Test message 1")
            agent.process_message("Test message 2")
            
            # Should have 4 entries (2 user, 2 agent responses)
            self.assertEqual(len(agent.conversation_history), 4)
            
            # Check structure
            self.assertEqual(agent.conversation_history[0]["role"], "user")
            self.assertEqual(agent.conversation_history[1]["role"], "agent")
            
        def test_conversation_summary(self):
            """Test conversation summary generation"""
            agent = TestInboundAgent("test_client_123")
            
            agent.get_initial_greeting()
            # Need to send initial message first to get to qualifying state
            agent.process_message("Hallo")
            # Then say yes to losing money - moves to qualified state
            agent.process_message("Ja, ich habe Geld verloren")
            # Then provide fraud type - this should be captured
            agent.process_message("Krypto-Betrug")
            
            summary = agent.get_conversation_summary()
            
            self.assertEqual(summary["client_id"], "test_client_123")
            self.assertIn("state", summary)
            self.assertEqual(summary["fraud_type"], "Kryptowährungsbetrug")
            self.assertGreater(summary["messages_exchanged"], 0)
            
    class TestInboundServerIntegration(unittest.IsolatedAsyncioTestCase):
        """Integration tests for the WebSocket server"""
        
        async def test_server_client_exchange(self):
            """Test a full server-client exchange"""
            # Use ephemeral port (0 = let OS choose)
            server_host = "localhost"
            server_port = 0  # OS will assign available port
            
            # Track the actual port assigned
            actual_port = None
            server = None
            server_task = None
            
            try:
                # Create server
                test_server = TestInboundServer(server_host, server_port)
                
                # Start server in background
                async def start_server():
                    nonlocal actual_port, server
                    server = await serve(
                        test_server.handle_client,
                        server_host,
                        server_port
                    )
                    # Get actual port assigned
                    actual_port = server.sockets[0].getsockname()[1]
                    
                    # Wait until closed
                    await asyncio.Future()
                
                server_task = asyncio.create_task(start_server())
                
                # Wait for server to start
                await asyncio.sleep(0.5)
                
                # Connect as client
                uri = f"ws://{server_host}:{actual_port}"
                async with websockets.connect(uri) as websocket:
                    # Receive greeting
                    greeting = await websocket.recv()
                    self.assertIsInstance(greeting, str)
                    self.assertIn("Fund Recovery", greeting)
                    
                    # Send a message
                    await websocket.send("Hallo, ich brauche Hilfe")
                    
                    # Receive response
                    response = await websocket.recv()
                    self.assertIsInstance(response, str)
                    self.assertGreater(len(response), 0)
                    
                    # Send qualification response
                    await websocket.send("Ja, ich habe Geld verloren")
                    
                    # Receive response
                    response = await websocket.recv()
                    self.assertIn("leid", response.lower())
                    
            finally:
                # Cleanup
                if server:
                    server.close()
                    await server.wait_closed()
                if server_task:
                    server_task.cancel()
                    try:
                        await server_task
                    except asyncio.CancelledError:
                        pass


def run_tests():
    """Run the automated tests"""
    if not WEBSOCKETS_AVAILABLE:
        print("Skipping tests - websockets library not available")
        print("Install with: pip install websockets")
        return
        
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add tests
    suite.addTests(loader.loadTestsFromTestCase(TestInboundAgentAutomated))
    suite.addTests(loader.loadTestsFromTestCase(TestInboundServerIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
