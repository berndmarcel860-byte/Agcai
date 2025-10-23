"""
Call handler for managing individual calls
"""
import os
import time
from datetime import datetime
from typing import Optional, Dict
from loguru import logger

from ..ari import ARIClient
from ..ai import ConversationEngine
from ..tts import TextToSpeech
from ..stt import SpeechToText
from ..database import Database, CallRecord, ConversationLog, CallStatus


class CallHandler:
    """Handler for individual call sessions"""
    
    def __init__(self, ari_client: ARIClient, conversation_engine: ConversationEngine,
                 tts: TextToSpeech, stt: SpeechToText, database: Database,
                 audio_dir: str = "/tmp/audio"):
        self.ari = ari_client
        self.ai = conversation_engine
        self.tts = tts
        self.stt = stt
        self.db = database
        self.audio_dir = audio_dir
        
        # Create audio directory
        os.makedirs(audio_dir, exist_ok=True)
        
        # Call state
        self.channel_id: Optional[str] = None
        self.call_record_id: Optional[int] = None
        self.conversation_history = []
        self.recording_name: Optional[str] = None
        
    def initiate_call(self, phone_number: str, caller_id: str, 
                     campaign_id: int, lead_id: Optional[int] = None) -> bool:
        """
        Initiate an outbound call
        
        Args:
            phone_number: Number to call
            caller_id: Caller ID to display
            campaign_id: Campaign ID
            lead_id: Lead ID (optional)
            
        Returns:
            True if call initiated successfully
        """
        try:
            logger.info(f"Initiating call to {phone_number}")
            
            # Create call record in database
            with self.db.get_session() as session:
                call_record = CallRecord(
                    campaign_id=campaign_id,
                    lead_id=lead_id,
                    phone_number=phone_number,
                    call_status=CallStatus.INITIATED
                )
                session.add(call_record)
                session.flush()
                self.call_record_id = call_record.id
                
            # Originate call via ARI
            endpoint = f"PJSIP/{phone_number}"
            channel = self.ari.originate_call(
                endpoint=endpoint,
                caller_id=caller_id,
                timeout=30
            )
            
            if channel:
                self.channel_id = channel.get('id')
                
                # Update call record
                with self.db.get_session() as session:
                    call_record = session.query(CallRecord).get(self.call_record_id)
                    call_record.channel_id = self.channel_id
                    call_record.call_status = CallStatus.RINGING
                    
                logger.info(f"Call initiated successfully, channel: {self.channel_id}")
                return True
            else:
                # Update call record as failed
                with self.db.get_session() as session:
                    call_record = session.query(CallRecord).get(self.call_record_id)
                    call_record.call_status = CallStatus.FAILED
                    call_record.ended_at = datetime.utcnow()
                    
                logger.error("Failed to initiate call")
                return False
                
        except Exception as e:
            logger.error(f"Error initiating call: {e}")
            return False
            
    def handle_answer(self):
        """Handle call answer event"""
        try:
            logger.info(f"Call answered: {self.channel_id}")
            
            # Update call record
            with self.db.get_session() as session:
                call_record = session.query(CallRecord).get(self.call_record_id)
                call_record.call_status = CallStatus.ANSWERED
                call_record.answered_at = datetime.utcnow()
                
            # Start recording
            self.recording_name = f"call_{self.call_record_id}_{int(time.time())}"
            self.ari.start_recording(self.channel_id, self.recording_name)
            
            # Start conversation
            self._start_conversation()
            
        except Exception as e:
            logger.error(f"Error handling answer: {e}")
            
    def _start_conversation(self):
        """Start AI conversation"""
        try:
            # Initialize conversation
            self.conversation_history = self.ai.start_conversation()
            
            # Get initial greeting
            greeting = self.ai.get_response(
                self.conversation_history,
                "Beginne das Gespräch mit einer freundlichen Begrüßung."
            )
            
            if greeting:
                self._speak_and_log(greeting, "agent")
                
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            
    def _speak_and_log(self, text: str, speaker: str):
        """Speak text via TTS and log to database"""
        try:
            # Log conversation
            with self.db.get_session() as session:
                log_entry = ConversationLog(
                    call_record_id=self.call_record_id,
                    speaker=speaker,
                    message=text
                )
                session.add(log_entry)
                
            # Synthesize speech
            audio_file = os.path.join(self.audio_dir, f"tts_{int(time.time())}.wav")
            if self.tts.synthesize(text, audio_file):
                # Play audio via ARI
                self.ari.play_media(self.channel_id, f"sound:{audio_file}")
                
        except Exception as e:
            logger.error(f"Error speaking text: {e}")
            
    def handle_customer_speech(self, audio_file_path: str):
        """Handle customer speech input"""
        try:
            # Transcribe speech
            transcription = self.stt.transcribe_file(audio_file_path)
            
            if transcription:
                logger.info(f"Customer said: {transcription}")
                
                # Log customer speech
                with self.db.get_session() as session:
                    log_entry = ConversationLog(
                        call_record_id=self.call_record_id,
                        speaker="customer",
                        message=transcription
                    )
                    session.add(log_entry)
                    
                # Get AI response
                response = self.ai.get_response(self.conversation_history, transcription)
                
                if response:
                    self._speak_and_log(response, "agent")
                    
                    # Check if conversation should end
                    if self._should_end_conversation(response):
                        self.end_call()
                        
        except Exception as e:
            logger.error(f"Error handling customer speech: {e}")
            
    def _should_end_conversation(self, ai_response: str) -> bool:
        """Check if conversation should end"""
        end_phrases = [
            "auf wiedersehen",
            "vielen dank für ihre zeit",
            "ich werde ihnen",
            "bis zum termin"
        ]
        
        response_lower = ai_response.lower()
        return any(phrase in response_lower for phrase in end_phrases)
        
    def end_call(self):
        """End the call"""
        try:
            logger.info(f"Ending call: {self.channel_id}")
            
            # Stop recording
            if self.recording_name:
                self.ari.stop_recording(self.recording_name)
                
            # Hangup call
            if self.channel_id:
                self.ari.hangup_channel(self.channel_id)
                
            # Update call record
            with self.db.get_session() as session:
                call_record = session.query(CallRecord).get(self.call_record_id)
                call_record.call_status = CallStatus.COMPLETED
                call_record.ended_at = datetime.utcnow()
                
                if call_record.answered_at:
                    duration = (call_record.ended_at - call_record.answered_at).seconds
                    call_record.duration = duration
                    
            # Extract appointment info
            appointment_info = self.ai.extract_appointment_info(self.conversation_history)
            if appointment_info and appointment_info.get('appointment_scheduled'):
                self._create_appointment(appointment_info)
                
            logger.info("Call ended successfully")
            
        except Exception as e:
            logger.error(f"Error ending call: {e}")
            
    def _create_appointment(self, appointment_info: Dict):
        """Create appointment from extracted info"""
        try:
            from ..database import Appointment, AppointmentStatus, Lead, LeadStatus
            
            with self.db.get_session() as session:
                call_record = session.query(CallRecord).get(self.call_record_id)
                
                if call_record.lead_id:
                    # Create appointment
                    appointment = Appointment(
                        lead_id=call_record.lead_id,
                        call_record_id=self.call_record_id,
                        appointment_date=datetime.strptime(
                            appointment_info.get('appointment_date', ''),
                            '%Y-%m-%d %H:%M'
                        ) if appointment_info.get('appointment_date') else datetime.utcnow(),
                        appointment_type="Fund Recovery Consultation",
                        notes=appointment_info.get('notes', ''),
                        status=AppointmentStatus.SCHEDULED
                    )
                    session.add(appointment)
                    
                    # Update lead status
                    lead = session.query(Lead).get(call_record.lead_id)
                    lead.status = LeadStatus.APPOINTMENT_SCHEDULED
                    
                    if appointment_info.get('customer_name'):
                        name_parts = appointment_info['customer_name'].split(' ', 1)
                        lead.first_name = name_parts[0]
                        if len(name_parts) > 1:
                            lead.last_name = name_parts[1]
                            
                    logger.info("Appointment created successfully")
                    
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
