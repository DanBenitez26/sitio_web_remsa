import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from django.urls import reverse

from .chatbot import MAX_MESSAGE_LENGTH, check_rate_limit, respond_to_message


@csrf_protect
@require_POST
def chatbot_response(request):
    if check_rate_limit(request):
        return JsonResponse(
            {"reply": "Has enviado varios mensajes seguidos. Espera un momento e inténtalo de nuevo."},
            status=429,
        )

    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"reply": "No pude leer el mensaje. Inténtalo de nuevo."}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({"reply": "El mensaje enviado no tiene un formato válido."}, status=400)

    message = payload.get("message")
    if not isinstance(message, str) or not message.strip():
        return JsonResponse({"reply": "Escribe tu consulta para ayudarte."}, status=400)
    if len(message) > MAX_MESSAGE_LENGTH:
        return JsonResponse(
            {"reply": f"El mensaje es demasiado largo. Usa hasta {MAX_MESSAGE_LENGTH} caracteres."},
            status=413,
        )

    result = respond_to_message(
        message.strip(),
        catalogue_url=reverse("catalogo:lista"),
    )
    return JsonResponse(result)
