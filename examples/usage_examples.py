#!/usr/bin/env python3
"""
Example usage script for AI Call Agent

This script demonstrates various ways to use the AI Call Agent system.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import Config
from src.database import Database, Lead, LeadStatus
from src.campaign import CampaignManager
from src.ari import ARIClient
from src.ai import ConversationEngine
from src.tts import TextToSpeech
from src.stt import SpeechToText


def example_add_leads_programmatically():
    """Example: Add leads directly via code"""
    print("Example: Adding leads programmatically")
    
    # Initialize database
    config = Config()
    db = Database(
        host=config.database.host,
        port=config.database.port,
        user=config.database.user,
        password=config.database.password,
        database=config.database.database
    )
    db.connect()
    
    # Add leads
    leads_data = [
        {
            "phone_number": "+491234567890",
            "first_name": "Max",
            "last_name": "Mustermann",
            "email": "max@example.com",
            "company": "Example GmbH"
        },
        {
            "phone_number": "+491234567891",
            "first_name": "Anna",
            "last_name": "Schmidt",
            "email": "anna@example.com",
            "company": "Test AG"
        }
    ]
    
    with db.get_session() as session:
        for lead_data in leads_data:
            # Check if exists
            existing = session.query(Lead).filter_by(
                phone_number=lead_data["phone_number"]
            ).first()
            
            if not existing:
                lead = Lead(**lead_data)
                session.add(lead)
                print(f"Added lead: {lead_data['first_name']} {lead_data['last_name']}")
            else:
                # Don't log sensitive phone number in examples
                print(f"Lead already exists: {lead_data['first_name']} {lead_data['last_name']}")
    
    db.close()


def example_query_campaign_stats():
    """Example: Query campaign statistics"""
    print("\nExample: Querying campaign statistics")
    
    config = Config()
    db = Database(
        host=config.database.host,
        port=config.database.port,
        user=config.database.user,
        password=config.database.password,
        database=config.database.database
    )
    db.connect()
    
    from src.database import Campaign, CallRecord, CallStatus
    
    with db.get_session() as session:
        # Get all campaigns
        campaigns = session.query(Campaign).all()
        
        for campaign in campaigns:
            print(f"\nCampaign: {campaign.name}")
            print(f"Status: {campaign.status.value}")
            
            # Count calls by status
            total_calls = session.query(CallRecord).filter_by(
                campaign_id=campaign.id
            ).count()
            
            answered_calls = session.query(CallRecord).filter_by(
                campaign_id=campaign.id,
                call_status=CallStatus.ANSWERED
            ).count()
            
            print(f"Total calls: {total_calls}")
            print(f"Answered calls: {answered_calls}")
            if total_calls > 0:
                print(f"Answer rate: {answered_calls/total_calls*100:.1f}%")
    
    db.close()


def example_export_appointments():
    """Example: Export scheduled appointments"""
    print("\nExample: Exporting appointments")
    
    config = Config()
    db = Database(
        host=config.database.host,
        port=config.database.port,
        user=config.database.user,
        password=config.database.password,
        database=config.database.database
    )
    db.connect()
    
    from src.database import Appointment, Lead
    import csv
    
    with db.get_session() as session:
        appointments = session.query(Appointment).join(Lead).all()
        
        # Export to CSV
        with open('appointments_export.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Name', 'Phone', 'Email', 'Status', 'Notes'])
            
            for apt in appointments:
                lead = apt.lead
                writer.writerow([
                    apt.appointment_date.strftime('%Y-%m-%d %H:%M'),
                    f"{lead.first_name} {lead.last_name}",
                    lead.phone_number,
                    lead.email or '',
                    apt.status.value,
                    apt.notes or ''
                ])
        
        print(f"Exported {len(appointments)} appointments to appointments_export.csv")
    
    db.close()


def example_custom_campaign():
    """Example: Create and configure custom campaign"""
    print("\nExample: Creating custom campaign")
    
    config = Config()
    
    # Initialize all components
    db = Database(
        host=config.database.host,
        port=config.database.port,
        user=config.database.user,
        password=config.database.password,
        database=config.database.database
    )
    db.connect()
    
    ari_client = ARIClient(
        host=config.ari.host,
        port=config.ari.port,
        username=config.ari.user,
        password=config.ari.password,
        app_name=config.ari.app
    )
    
    conversation_engine = ConversationEngine(
        api_key=config.openai.api_key,
        model=config.openai.model
    )
    
    tts = TextToSpeech(
        model_name=config.tts.model,
        language=config.tts.language,
        use_gpu=config.tts.use_gpu
    )
    
    stt = SpeechToText(
        model_size=config.stt.model,
        language=config.stt.language,
        device=config.stt.device
    )
    
    # Create campaign manager
    campaign_manager = CampaignManager(
        ari_client=ari_client,
        conversation_engine=conversation_engine,
        tts=tts,
        stt=stt,
        database=db,
        caller_id=config.campaign.caller_id,
        max_concurrent_calls=2  # Custom: only 2 concurrent calls
    )
    
    # Create campaign
    campaign_id = campaign_manager.create_campaign(
        name="Custom VIP Campaign",
        description="High-value leads only"
    )
    
    print(f"Created campaign with ID: {campaign_id}")
    
    # Add VIP leads
    vip_leads = [
        {
            "phone_number": "+491234567899",
            "first_name": "VIP",
            "last_name": "Customer",
            "email": "vip@example.com"
        }
    ]
    
    count = campaign_manager.add_leads(vip_leads)
    print(f"Added {count} VIP leads")
    
    db.close()


if __name__ == '__main__':
    print("AI Call Agent - Usage Examples")
    print("=" * 50)
    
    # Run examples
    # example_add_leads_programmatically()
    # example_query_campaign_stats()
    # example_export_appointments()
    # example_custom_campaign()
    
    print("\nUncomment the examples you want to run in the script.")
    print("Make sure to configure .env file before running.")
