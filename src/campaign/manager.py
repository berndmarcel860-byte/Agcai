"""
Campaign manager for handling outbound call campaigns
"""
import time
from typing import List, Optional
from loguru import logger
from datetime import datetime

from ..database import Database, Campaign, Lead, CallRecord, CampaignStatus, LeadStatus, CallStatus
from ..ari import ARIClient
from ..ai import ConversationEngine
from ..tts import TextToSpeech
from ..stt import SpeechToText
from .call_handler import CallHandler


class CampaignManager:
    """Manages outbound call campaigns"""
    
    def __init__(self, ari_client: ARIClient, conversation_engine: ConversationEngine,
                 tts: TextToSpeech, stt: SpeechToText, database: Database,
                 caller_id: str, max_concurrent_calls: int = 5):
        self.ari = ari_client
        self.ai = conversation_engine
        self.tts = tts
        self.stt = stt
        self.db = database
        self.caller_id = caller_id
        self.max_concurrent_calls = max_concurrent_calls
        
        # Track active calls
        self.active_calls: dict = {}
        self.campaign_id: Optional[int] = None
        self.running = False
        
    def create_campaign(self, name: str, description: str = "") -> int:
        """
        Create a new campaign
        
        Args:
            name: Campaign name
            description: Campaign description
            
        Returns:
            Campaign ID
        """
        try:
            with self.db.get_session() as session:
                campaign = Campaign(
                    name=name,
                    description=description,
                    status=CampaignStatus.ACTIVE,
                    max_concurrent_calls=self.max_concurrent_calls
                )
                session.add(campaign)
                session.flush()
                campaign_id = campaign.id
                
            logger.info(f"Campaign created: {name} (ID: {campaign_id})")
            return campaign_id
            
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            raise
            
    def add_leads(self, leads_data: List[dict]) -> int:
        """
        Add leads to database
        
        Args:
            leads_data: List of lead dictionaries with phone_number, first_name, etc.
            
        Returns:
            Number of leads added
        """
        try:
            count = 0
            
            with self.db.get_session() as session:
                for lead_data in leads_data:
                    # Check if lead already exists
                    existing_lead = session.query(Lead).filter_by(
                        phone_number=lead_data['phone_number']
                    ).first()
                    
                    if not existing_lead:
                        lead = Lead(
                            phone_number=lead_data['phone_number'],
                            first_name=lead_data.get('first_name'),
                            last_name=lead_data.get('last_name'),
                            email=lead_data.get('email'),
                            company=lead_data.get('company'),
                            status=LeadStatus.NEW
                        )
                        session.add(lead)
                        count += 1
                        
            logger.info(f"Added {count} new leads")
            return count
            
        except Exception as e:
            logger.error(f"Error adding leads: {e}")
            return 0
            
    def start_campaign(self, campaign_id: int):
        """
        Start campaign and begin making calls
        
        Args:
            campaign_id: Campaign ID to run
        """
        try:
            self.campaign_id = campaign_id
            self.running = True
            
            logger.info(f"Starting campaign {campaign_id}")
            
            # Register ARI event handlers
            self._register_ari_handlers()
            
            # Main campaign loop
            while self.running:
                # Check if we can make more calls
                if len(self.active_calls) < self.max_concurrent_calls:
                    # Get next lead to call
                    lead = self._get_next_lead()
                    
                    if lead:
                        self._initiate_call(lead)
                    else:
                        logger.info("No more leads to call")
                        time.sleep(5)
                else:
                    # Wait for calls to complete
                    time.sleep(1)
                    
                # Clean up completed calls
                self._cleanup_completed_calls()
                
            logger.info("Campaign stopped")
            
        except Exception as e:
            logger.error(f"Error running campaign: {e}")
            raise
            
    def stop_campaign(self):
        """Stop the campaign"""
        self.running = False
        logger.info("Stopping campaign...")
        
    def _get_next_lead(self) -> Optional[Lead]:
        """Get next lead to call"""
        try:
            with self.db.get_session() as session:
                # Find leads that haven't been contacted or need callback
                lead = session.query(Lead).filter(
                    Lead.status.in_([LeadStatus.NEW, LeadStatus.CALLBACK_REQUESTED])
                ).first()
                
                if lead:
                    # Mark as contacted
                    lead.status = LeadStatus.CONTACTED
                    session.commit()
                    
                    # Detach from session
                    session.expunge(lead)
                    
                return lead
                
        except Exception as e:
            logger.error(f"Error getting next lead: {e}")
            return None
            
    def _initiate_call(self, lead: Lead):
        """Initiate call to lead"""
        try:
            # Create call handler
            call_handler = CallHandler(
                self.ari, self.ai, self.tts, self.stt, self.db
            )
            
            # Initiate call
            success = call_handler.initiate_call(
                phone_number=lead.phone_number,
                caller_id=self.caller_id,
                campaign_id=self.campaign_id,
                lead_id=lead.id
            )
            
            if success and call_handler.channel_id:
                # Track active call
                self.active_calls[call_handler.channel_id] = call_handler
                logger.info(f"Active calls: {len(self.active_calls)}")
                
        except Exception as e:
            logger.error(f"Error initiating call to {lead.phone_number}: {e}")
            
    def _register_ari_handlers(self):
        """Register ARI event handlers"""
        
        def on_stasis_start(event):
            """Handle StasisStart event (call answered)"""
            channel_id = event.get('channel', {}).get('id')
            
            if channel_id in self.active_calls:
                call_handler = self.active_calls[channel_id]
                call_handler.handle_answer()
                
        def on_channel_destroyed(event):
            """Handle ChannelDestroyed event (call ended)"""
            channel_id = event.get('channel', {}).get('id')
            
            if channel_id in self.active_calls:
                call_handler = self.active_calls[channel_id]
                call_handler.end_call()
                
        def on_channel_state_change(event):
            """Handle ChannelStateChange event"""
            channel_id = event.get('channel', {}).get('id')
            state = event.get('channel', {}).get('state')
            
            logger.debug(f"Channel {channel_id} state: {state}")
            
            # Handle different states
            if state == 'Ringing' and channel_id in self.active_calls:
                # Update call status
                call_handler = self.active_calls[channel_id]
                with self.db.get_session() as session:
                    call_record = session.query(CallRecord).get(call_handler.call_record_id)
                    if call_record:
                        call_record.call_status = CallStatus.RINGING
                        
            elif state == 'Up' and channel_id in self.active_calls:
                # Call answered
                on_stasis_start(event)
                
        # Register handlers
        self.ari.on('StasisStart', on_stasis_start)
        self.ari.on('ChannelDestroyed', on_channel_destroyed)
        self.ari.on('ChannelStateChange', on_channel_state_change)
        
        logger.info("ARI event handlers registered")
        
    def _cleanup_completed_calls(self):
        """Clean up completed calls"""
        completed_channels = []
        
        for channel_id, call_handler in self.active_calls.items():
            # Check if channel still exists
            channel_state = self.ari.get_channel_state(channel_id)
            
            if not channel_state or channel_state.get('state') == 'Down':
                completed_channels.append(channel_id)
                
        # Remove completed calls
        for channel_id in completed_channels:
            del self.active_calls[channel_id]
            logger.info(f"Removed completed call: {channel_id}")
            
    def get_campaign_stats(self, campaign_id: int) -> dict:
        """
        Get campaign statistics
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Dictionary with campaign statistics
        """
        try:
            with self.db.get_session() as session:
                # Count calls by status
                total_calls = session.query(CallRecord).filter_by(
                    campaign_id=campaign_id
                ).count()
                
                answered_calls = session.query(CallRecord).filter_by(
                    campaign_id=campaign_id,
                    call_status=CallStatus.ANSWERED
                ).count()
                
                completed_calls = session.query(CallRecord).filter_by(
                    campaign_id=campaign_id,
                    call_status=CallStatus.COMPLETED
                ).count()
                
                failed_calls = session.query(CallRecord).filter_by(
                    campaign_id=campaign_id,
                    call_status=CallStatus.FAILED
                ).count()
                
                # Count leads by status
                from ..database import Appointment
                appointments = session.query(Appointment).join(CallRecord).filter(
                    CallRecord.campaign_id == campaign_id
                ).count()
                
                return {
                    'total_calls': total_calls,
                    'answered_calls': answered_calls,
                    'completed_calls': completed_calls,
                    'failed_calls': failed_calls,
                    'appointments_scheduled': appointments,
                    'active_calls': len(self.active_calls)
                }
                
        except Exception as e:
            logger.error(f"Error getting campaign stats: {e}")
            return {}
