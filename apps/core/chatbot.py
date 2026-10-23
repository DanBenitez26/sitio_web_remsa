"""Respuestas comerciales por reglas para el chatbot de REMSA."""

import re
import unicodedata

from django.core.cache import cache

MAX_MESSAGE_LENGTH = 500
CHAT_RATE_LIMIT = 40
CHAT_RATE_WINDOW_SECONDS = 60

GREETING_REPLY = "¡Hola! Bienvenido a REMSA Plásticos. ¿En qué podemos ayudarte?"
INFORMATION_REPLY = (
    "Con gusto te atendemos. Déjanos tus datos de contacto y un asesor comercial "
    "se comunicará contigo."
)
QUOTE_REPLY = (
    "¡Con gusto! Indícanos qué producto te interesa y déjanos tus datos de contacto. "
    "Un asesor comercial dará seguimiento a tu solicitud."
)
PRODUCT_REPLY = (
    "Fabricamos envases, preformas y tapas de plástico. Si deseas conocer nuestros "
    "productos o solicitar una cotización, déjanos tus datos y un asesor comercial "
    "te atenderá."
)
CONTACT_REPLY = (
    "Claro, déjanos tus datos de contacto y un asesor comercial de REMSA se pondrá "
    "en contacto contigo."
)
UNKNOWN_REPLY = (
    "Para brindarte información precisa, te recomendamos contactar a nuestro equipo "
    "comercial. Déjanos tus datos y con gusto te atenderemos."
)


def normalize_text(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    without_accents = "".join(
        character for character in normalized
        if not unicodedata.combining(character)
    )
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", without_accents).lower()).strip()


def check_rate_limit(request):
    ip_address = request.META.get("REMOTE_ADDR") or "sin-ip"
    cache_key = f"chatbot-rate:{ip_address}"
    if cache.add(cache_key, 1, timeout=CHAT_RATE_WINDOW_SECONDS):
        return False
    try:
        attempts = cache.incr(cache_key)
    except ValueError:
        cache.set(cache_key, 1, timeout=CHAT_RATE_WINDOW_SECONDS)
        return False
    return attempts > CHAT_RATE_LIMIT


def _contains_any(message, phrases):
    for phrase in phrases:
        phrase_pattern = re.escape(phrase).replace("\\ ", r"\s+")
        if re.search(rf"\b{phrase_pattern}\b", message):
            return True
    return False


def respond_to_message(message, catalogue_url):
    """Clasifica la intención y devuelve una respuesta comercial acotada."""
    normalized = normalize_text(message)

    quote_terms = (
        "cotizar", "cotizacion", "cotizaciones", "precio", "precios",
        "cuanto cuesta", "cuanto cuestan", "presupuesto",
    )
    contact_terms = (
        "asesor", "vendedor", "ejecutivo comercial", "contacto",
        "hablar con alguien", "hablar con una persona",
    )
    information_terms = (
        "quiero informacion", "informes", "mas informacion",
        "informacion de productos", "quisiera conocer sus productos",
        "informacion",
    )
    product_terms = (
        "productos", "catalogo", "envases", "botellas", "garrafones",
        "garrafon", "preformas", "preforma", "tapas", "tapa",
    )
    greeting_terms = (
        "hola", "buenos dias", "buenas tardes", "buenas noches",
        "que tal", "saludos",
    )

    if _contains_any(normalized, quote_terms):
        return {
            "reply": QUOTE_REPLY,
            "show_form": True,
            "catalogue_url": "",
        }
    if _contains_any(normalized, contact_terms):
        return {
            "reply": CONTACT_REPLY,
            "show_form": True,
            "catalogue_url": "",
        }
    if _contains_any(normalized, information_terms):
        return {
            "reply": INFORMATION_REPLY,
            "show_form": True,
            "catalogue_url": "",
        }
    if _contains_any(normalized, product_terms):
        return {
            "reply": PRODUCT_REPLY,
            "show_form": True,
            "catalogue_url": catalogue_url,
        }
    if _contains_any(normalized, greeting_terms):
        return {
            "reply": GREETING_REPLY,
            "show_form": False,
            "catalogue_url": "",
        }
    return {
        "reply": UNKNOWN_REPLY,
        "show_form": True,
        "catalogue_url": "",
    }
