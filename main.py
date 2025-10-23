"""
Main application entry point for AI call agent
"""
import signal
import sys
from loguru import logger

from src.config import Config
from src.database import Database
from src.ari import ARIClient
from src.ai import ConversationEngine
from src.tts import TextToSpeech
from src.stt import SpeechToText
from src.campaign import CampaignManager
from src.utils import setup_logging


class AICallAgent:
    """Main AI Call Agent application"""
    
    def __init__(self, config_file: str = ".env"):
        """Initialize AI Call Agent"""
        # Load configuration
        self.config = Config(config_file)
        
        # Setup logging
        setup_logging(log_level="INFO", log_file="logs/aiagent.log")
        
        # Initialize components
        self.database = None
        self.ari_client = None
        self.conversation_engine = None
        self.tts = None
        self.stt = None
        self.campaign_manager = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Received shutdown signal")
        self.shutdown()
        sys.exit(0)
        
    def initialize(self):
        """Initialize all components"""
        logger.info("Initializing AI Call Agent...")
        
        try:
            # Initialize database
            logger.info("Connecting to database...")
            self.database = Database(
                host=self.config.database.host,
                port=self.config.database.port,
                user=self.config.database.user,
                password=self.config.database.password,
                database=self.config.database.database
            )
            self.database.connect()
            self.database.initialize_schema()
            
            # Initialize ARI client
            logger.info("Connecting to Asterisk ARI...")
            self.ari_client = ARIClient(
                host=self.config.ari.host,
                port=self.config.ari.port,
                username=self.config.ari.user,
                password=self.config.ari.password,
                app_name=self.config.ari.app
            )
            self.ari_client.connect()
            
            # Initialize AI conversation engine
            logger.info("Initializing AI conversation engine...")
            self.conversation_engine = ConversationEngine(
                api_key=self.config.openai.api_key,
                model=self.config.openai.model
            )
            
            # Initialize TTS
            logger.info("Loading TTS model...")
            self.tts = TextToSpeech(
                model_name=self.config.tts.model,
                language=self.config.tts.language
            )
            self.tts.load_model()
            
            # Initialize STT
            logger.info("Loading STT model...")
            self.stt = SpeechToText(
                model_size=self.config.stt.model,
                language=self.config.stt.language
            )
            self.stt.load_model()
            
            # Initialize campaign manager
            logger.info("Initializing campaign manager...")
            self.campaign_manager = CampaignManager(
                ari_client=self.ari_client,
                conversation_engine=self.conversation_engine,
                tts=self.tts,
                stt=self.stt,
                database=self.database,
                caller_id=self.config.campaign.caller_id,
                max_concurrent_calls=self.config.campaign.max_concurrent_calls
            )
            
            logger.info("AI Call Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Call Agent: {e}")
            raise
            
    def run_campaign(self, campaign_name: str = None, leads_file: str = None):
        """
        Run outbound call campaign
        
        Args:
            campaign_name: Name of the campaign (optional)
            leads_file: Path to CSV file with leads (optional)
        """
        try:
            if not campaign_name:
                campaign_name = self.config.campaign.name
                
            # Create campaign
            campaign_id = self.campaign_manager.create_campaign(
                name=campaign_name,
                description="Automated outbound calls for Fund Recovery service"
            )
            
            # Load leads if file provided
            if leads_file:
                leads_data = self._load_leads_from_csv(leads_file)
                self.campaign_manager.add_leads(leads_data)
                
            # Start campaign
            logger.info(f"Starting campaign: {campaign_name}")
            self.campaign_manager.start_campaign(campaign_id)
            
        except Exception as e:
            logger.error(f"Error running campaign: {e}")
            raise
            
    def _load_leads_from_csv(self, csv_file: str) -> list:
        """Load leads from CSV file"""
        import csv
        
        leads = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    lead = {
                        'phone_number': row.get('phone_number', '').strip(),
                        'first_name': row.get('first_name', '').strip(),
                        'last_name': row.get('last_name', '').strip(),
                        'email': row.get('email', '').strip(),
                        'company': row.get('company', '').strip()
                    }
                    
                    if lead['phone_number']:
                        leads.append(lead)
                        
            logger.info(f"Loaded {len(leads)} leads from {csv_file}")
            return leads
            
        except Exception as e:
            logger.error(f"Error loading leads from CSV: {e}")
            return []
            
    def shutdown(self):
        """Shutdown the application"""
        logger.info("Shutting down AI Call Agent...")
        
        try:
            # Stop campaign
            if self.campaign_manager:
                self.campaign_manager.stop_campaign()
                
            # Disconnect ARI
            if self.ari_client:
                self.ari_client.disconnect()
                
            # Close database
            if self.database:
                self.database.close()
                
            logger.info("AI Call Agent shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Call Agent for Outbound Campaigns')
    parser.add_argument('--config', default='.env', help='Configuration file path')
    parser.add_argument('--campaign', help='Campaign name')
    parser.add_argument('--leads', help='CSV file with leads')
    parser.add_argument('--init-db', action='store_true', help='Initialize database only')
    
    args = parser.parse_args()
    
    try:
        # Create agent
        agent = AICallAgent(config_file=args.config)
        
        # Initialize
        agent.initialize()
        
        if args.init_db:
            logger.info("Database initialized successfully")
            return
            
        # Run campaign
        agent.run_campaign(
            campaign_name=args.campaign,
            leads_file=args.leads
        )
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
