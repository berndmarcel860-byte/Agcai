"""
AI Conversation Engine using OpenAI
"""
from openai import OpenAI
from loguru import logger
from typing import List, Dict, Optional
import json


class ConversationEngine:
    """AI conversation engine for handling call dialogues"""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        """
        Initialize OpenAI conversation engine
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
        """
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = self._get_fund_recovery_prompt()
        
    def _get_fund_recovery_prompt(self) -> str:
        """Get system prompt for Fund Recovery service"""
        return """Du bist ein professioneller KI-Agent für einen Fund Recovery Service. 
Deine Aufgabe ist es, potenzielle Kunden anzurufen, die möglicherweise Opfer von Betrug geworden sind 
und Geld verloren haben.

Deine Ziele:
1. Qualifiziere den Lead - finde heraus, ob die Person Geld durch Betrug verloren hat
2. Erkläre den Fund Recovery Service professionell und empathisch
3. Vereinbare einen Termin für ein ausführliches Beratungsgespräch
4. Erfasse wichtige Informationen: Name, Art des Betrugs, verlorener Betrag

Gesprächsablauf:
1. Begrüßung: Stelle dich vor und erkläre den Anrufgrund
2. Qualifikation: Frage höflich, ob die Person durch Betrug Geld verloren hat
3. Interesse wecken: Erkläre, wie der Service helfen kann
4. Terminvereinbarung: Schlage konkrete Termine vor
5. Verabschiedung: Bestätige den Termin und bedanke dich

Wichtige Regeln:
- Sei empathisch und professionell
- Respektiere, wenn jemand kein Interesse hat
- Erfasse niemals sensible Bankdaten am Telefon
- Halte das Gespräch fokussiert und effizient (max. 3-5 Minuten)
- Sei ehrlich und transparent über den Service
- Spreche auf Deutsch

Antworte kurz und prägnant. Halte deine Antworten auf 2-3 Sätze begrenzt."""

    def start_conversation(self) -> List[Dict[str, str]]:
        """Start a new conversation"""
        return [{"role": "system", "content": self.system_prompt}]
        
    def get_response(self, conversation_history: List[Dict[str, str]], 
                    user_message: str) -> Optional[str]:
        """
        Get AI response for user message
        
        Args:
            conversation_history: List of previous messages
            user_message: Current user message
            
        Returns:
            AI response or None if failed
        """
        try:
            # Add user message to history
            conversation_history.append({"role": "user", "content": user_message})
            
            logger.info(f"Getting AI response for: {user_message[:50]}...")
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=conversation_history,
                temperature=0.7,
                max_tokens=150,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )
            
            # Extract response
            ai_message = response.choices[0].message.content
            
            # Add AI response to history
            conversation_history.append({"role": "assistant", "content": ai_message})
            
            logger.info(f"AI response: {ai_message[:50]}...")
            return ai_message
            
        except Exception as e:
            logger.error(f"Failed to get AI response: {e}")
            return None
            
    def extract_appointment_info(self, conversation_history: List[Dict[str, str]]) -> Optional[Dict]:
        """
        Extract appointment information from conversation
        
        Args:
            conversation_history: Full conversation history
            
        Returns:
            Dictionary with appointment info or None
        """
        try:
            # Create extraction prompt
            extraction_prompt = """Analysiere das Gespräch und extrahiere folgende Informationen im JSON-Format:
{
  "appointment_scheduled": true/false,
  "customer_name": "Name des Kunden",
  "appointment_date": "Terminvorschlag im Format YYYY-MM-DD HH:MM",
  "customer_interest_level": "high/medium/low",
  "fraud_type": "Art des Betrugs",
  "amount_lost": "Verlorener Betrag",
  "notes": "Weitere wichtige Notizen"
}

Wenn Informationen nicht verfügbar sind, setze null."""

            messages = conversation_history + [
                {"role": "user", "content": extraction_prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=300
            )
            
            # Parse JSON response
            extraction_text = response.choices[0].message.content
            
            # Extract JSON from response
            start_idx = extraction_text.find('{')
            end_idx = extraction_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = extraction_text[start_idx:end_idx]
                appointment_info = json.loads(json_str)
                logger.info(f"Extracted appointment info: {appointment_info}")
                return appointment_info
            else:
                logger.warning("No JSON found in extraction response")
                return None
                
        except Exception as e:
            logger.error(f"Failed to extract appointment info: {e}")
            return None
            
    def analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of customer response
        
        Args:
            text: Customer text to analyze
            
        Returns:
            Sentiment: 'positive', 'neutral', 'negative'
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Analysiere die Stimmung des folgenden Texts. Antworte nur mit: positive, neutral, oder negative."},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=10
            )
            
            sentiment = response.choices[0].message.content.strip().lower()
            
            if sentiment not in ['positive', 'neutral', 'negative']:
                sentiment = 'neutral'
                
            return sentiment
            
        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {e}")
            return 'neutral'
