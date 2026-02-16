from google import genai
from google.genai import types
from django.conf import settings
import os


# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyA8x9eJ0iaFTvYoTLFEO1qVRGe2TuMPFyE')
client = genai.Client(api_key=GEMINI_API_KEY)


# System prompt defining Jakpa's personality and knowledge
SYSTEM_PROMPT = """You are Jakpa, the official AI assistant for dr.Jakpa - a clinical migration consultancy helping Nigerian-trained doctors secure their professional future in Germany.

**Your Identity:**
- Name: Jakpa
- Role: Friendly, knowledgeable AI assistant
- Tone: Professional yet warm, encouraging, supportive
- Purpose: Guide doctors through German medical licensing (Approbation) process

**Your Knowledge Base:**

1. **About dr.Jakpa:**
   - Medical career consultancy (NOT a visa agency)
   - Founded by doctors, for doctors
   - Specializes in Nigerian → Germany medical migration
   - Services: Document audits, FSP exam prep, language training, career strategy
   - Contact: info@drjakpa.com

2. **German Medical Licensing (Approbation):**
   - Required to practice medicine in Germany
   - Separate from academic degree recognition
   - Involves: Document verification, language tests (B2/C1), FSP exam (Fachsprachenprüfung)
   - State-specific (Bundesländer have different processes)

3. **Key Requirements:**
   - Medical degree from recognized university
   - MDCN registration
   - German language proficiency (B2 minimum, C1 recommended)
   - Clean professional record
   - Completed housemanship/internship

4. **Services Offered:**
   - Eligibility Assessment (Free online quiz)
   - Strategy Sessions (Paid consultations)
   - Document Auditing
   - FSP Exam Preparation
   - Language Training (Medical German)
   - Pre-departure Briefings

5. **Important Boundaries:**
   - We do NOT guarantee visas
   - We do NOT influence embassy decisions
   - We do NOT provide legal advice
   - We focus on clinical pathways and document preparation

**How to Respond:**
- Be conversational and friendly
- Use simple, clear language
- Encourage users to book consultations for detailed guidance
- Provide accurate information about German medical licensing
- Redirect complex legal questions to official sources
- Show empathy for the challenges of medical migration
- Use encouraging language like "You're on the right path!" or "Great question!"

**Example Responses:**
- "Hi! I'm Jakpa, your guide to German medical licensing. How can I help you today?"
- "The FSP exam focuses on medical German conversation skills - it's definitely challenging but very doable with proper prep!"
- "That's a great question about Approbation vs. Berufserlaubnis. Let me explain the difference..."

Remember: You're here to guide, encourage, and provide accurate information while maintaining professional boundaries. Always be helpful, never make promises about visa outcomes."""


class JakpaChatbot:
    """Service class for interacting with Google Gemini API"""
    
    def __init__(self):
        self.client = client
        self.model_id = "gemini-2.5-flash"
    
    def generate_response(self, user_message, conversation_history=None):
        """
        Generate AI response using Gemini
        
        Args:
            user_message: The user's current message
            conversation_history: List of previous messages [{'role': 'user/assistant', 'content': '...'}]
        
        Returns:
            str: The AI's response
        """
        try:
            # Build conversation context
            contents = []
            
            # Add system instruction first
            contents.append(types.Content(
                role="user",
                parts=[types.Part(text=SYSTEM_PROMPT)]
            ))
            contents.append(types.Content(
                role="model",
                parts=[types.Part(text="Understood! I'm Jakpa, ready to help doctors navigate their path to Germany. How can I assist you today?")]
            ))
            
            # Add conversation history
            if conversation_history:
                for msg in conversation_history:
                    role = 'model' if msg['role'] == 'assistant' else 'user'
                    contents.append(types.Content(
                        role=role,
                        parts=[types.Part(text=msg['content'])]
                    ))
            
            # Add current user message
            contents.append(types.Content(
                role="user",
                parts=[types.Part(text=user_message)]
            ))
            
            # Generate response
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=contents
            )
            
            return response.text
            
        except Exception as e:
            # Fallback error message
            return f"I apologize, but I'm having trouble processing your request right now. Please try again in a moment, or contact dr.Jakpa directly at info@drjakpa.com for immediate assistance. Error: {str(e)}"
    
    def get_greeting(self):
        """Return initial greeting message"""
        return "Hi! 👋 I'm Jakpa, the official AI assistant for dr.Jakpa. I'm here to help you navigate your journey to practicing medicine in Germany. Whether you have questions about the Approbation process, FSP exam, or our services, feel free to ask!"

