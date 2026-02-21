from google import genai
from google.genai import types
from django.conf import settings
from django.utils.html import strip_tags
import os


# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)


# ─────────────────────────────────────────────
# Static base personality & site knowledge
# ─────────────────────────────────────────────
BASE_SYSTEM_PROMPT = """You are Jakpa, the official AI assistant for dr.Jakpa - a clinical migration consultancy helping Nigerian-trained doctors secure their professional future in Germany.

**Your Identity:**
- Name: Jakpa
- Role: Friendly, knowledgeable AI assistant
- Tone: Professional yet warm, encouraging, supportive
- Purpose: Guide doctors through German medical licensing (Approbation) process

**Core Knowledge:**

1. **About dr.Jakpa:**
   - Medical career consultancy (NOT a visa agency)
   - Founded by doctors, for doctors
   - Specializes in Nigerian → Germany medical migration
   - Contact: info@drjakpa.com

2. **German Medical Licensing (Approbation):**
   - Required to practice medicine in Germany
   - Involves: Document verification, language tests (B2/C1), FSP exam (Fachsprachenprüfung)
   - State-specific (Bundesländer have different processes)

3. **Key Requirements:**
   - Medical degree from a recognized university (Anabin database)
   - MDCN registration & completed housemanship/internship
   - German language proficiency (B2 minimum, C1 recommended)
   - Clean professional record

4. **Services Offered:**
   - Free Eligibility Assessment (online quiz at /eligibility/)
   - Strategy Sessions (paid 1-on-1 consultations — book at /bookings/)
   - Document Auditing
   - FSP Exam Preparation
   - Medical German Language Training
   - Pre-departure Briefings

5. **Bookings:**
   - Users can book a consultation session at https://drjakpa.com/bookings/
   - Sessions are paid and time-limited
   - Different durations available (1 hour, 2 hours, etc.)
   - Payment via screenshot confirmation

6. **Important Boundaries:**
   - We do NOT guarantee visas or embassy decisions
   - We do NOT provide legal advice
   - We do NOT guarantee job placements in Germany
   - We focus on clinical pathways and document preparation

**How to Respond:**
- Be conversational, friendly and encouraging
- Use simple, clear language (avoid jargon where possible)
- When relevant, point users to the eligibility quiz or booking page
- Provide accurate information about German medical licensing
- Show empathy for the challenges of medical migration
- Use encouraging language like "You're on the right path!" or "Great question!"
- Keep responses concise — 2–4 short paragraphs max unless detail is needed
- Format with bullet points where helpful

Remember: You're here to guide, encourage, and provide accurate information while maintaining professional boundaries. Never make promises about visa outcomes."""


# ─────────────────────────────────────────────
# Dynamic context builder
# ─────────────────────────────────────────────
def build_dynamic_context():
    """
    Fetches live data from the database (blog posts, testimonials, FAQs)
    and returns a formatted context string to append to the system prompt.
    """
    context_parts = []

    # ── 1. Published Blog Posts ──────────────────
    try:
        from blog.models import Post
        posts = Post.objects.published().select_related('author').prefetch_related('category').order_by('-published_date')[:20]

        if posts:
            blog_lines = []
            for post in posts:
                categories = ', '.join(c.name for c in post.category.all()) or 'General'
                excerpt = post.excerpt or ''
                if not excerpt and post.content:
                    # Strip HTML and take first 200 chars as excerpt
                    excerpt = strip_tags(post.content)[:200].strip()
                blog_lines.append(
                    f"  - \"{post.title}\" [{categories}]: {excerpt}"
                )

            context_parts.append(
                "**Our Blog — Published Articles (use these to answer content questions):**\n"
                + "\n".join(blog_lines)
            )
    except Exception:
        pass  # Don't crash if blog app is unavailable

    # ── 2. Testimonials ──────────────────────────
    try:
        from main.models import Testimonial
        testimonials = Testimonial.objects.filter(is_active=True).order_by('-created_at')[:5]

        if testimonials:
            lines = [f"  - {t.name} ({t.location}): \"{t.testimony[:150]}\"" for t in testimonials]
            context_parts.append(
                "**Recent Success Stories (use these to inspire and validate):**\n"
                + "\n".join(lines)
            )
    except Exception:
        pass

    # ── 3. FAQs ─────────────────────────────────
    try:
        from main.models import Faq
        faqs = Faq.objects.all().order_by('-created_at')[:10]

        if faqs:
            lines = [f"  Q: {faq.question}\n  A: {faq.answer}" for faq in faqs]
            context_parts.append(
                "**Frequently Asked Questions (answer these accurately):**\n"
                + "\n\n".join(lines)
            )
    except Exception:
        pass

    # ── 4. Available Session Times ───────────────
    try:
        from main.models import SessionTime
        from django.utils import timezone
        available = SessionTime.objects.filter(
            is_available=True,
            date__gte=timezone.now().date()
        ).order_by('date', 'time')[:8]

        if available:
            lines = [f"  - {s.date.strftime('%A, %b %d %Y')} at {s.time.strftime('%I:%M %p')}" for s in available]
            context_parts.append(
                "**Currently Available Booking Slots (mention these if asked about scheduling):**\n"
                + "\n".join(lines)
            )
    except Exception:
        pass

    if not context_parts:
        return ""

    return (
        "\n\n---\n"
        "**LIVE SITE DATA (use this to answer specific questions):**\n\n"
        + "\n\n".join(context_parts)
    )


def build_full_system_prompt():
    """Combines static personality prompt with live dynamic context."""
    dynamic = build_dynamic_context()
    return BASE_SYSTEM_PROMPT + dynamic


# ─────────────────────────────────────────────
# Chatbot Service Class
# ─────────────────────────────────────────────
class JakpaChatbot:
    """Service class for interacting with Google Gemini API"""

    def __init__(self):
        self.client = client
        self.model_id = "gemini-2.5-flash"

    def generate_response(self, user_message, conversation_history=None):
        """
        Generate AI response using Gemini with dynamic site context.

        Args:
            user_message: The user's current message
            conversation_history: List of previous messages [{'role': 'user/assistant', 'content': '...'}]

        Returns:
            str: The AI's response
        """
        try:
            # Build conversation context
            contents = []

            # Build full prompt with live data injected
            full_prompt = build_full_system_prompt()

            # Inject system prompt as opening turn
            contents.append(types.Content(
                role="user",
                parts=[types.Part(text=full_prompt)]
            ))
            contents.append(types.Content(
                role="model",
                parts=[types.Part(text="Understood! I'm Jakpa, ready to help doctors navigate their path to Germany. I have access to our latest blog articles, FAQs, testimonials, and available booking slots. How can I assist you today?")]
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
            return (
                "I apologize, but I'm having trouble processing your request right now. "
                "Please try again in a moment, or contact dr.Jakpa directly at info@drjakpa.com "
                f"for immediate assistance."
            )

    def get_greeting(self):
        """Return initial greeting message"""
        return (
            "Hi! 👋 I'm Jakpa, the official AI assistant for dr.Jakpa. "
            "I'm here to help you navigate your journey to practicing medicine in Germany. "
            "I can answer questions about the Approbation process, our blog articles, services, "
            "booking sessions, and more. What would you like to know?"
        )
