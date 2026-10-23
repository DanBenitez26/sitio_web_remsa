from .base import *  # noqa: F401,F403
import environ

env = environ.Env()

# — Seguridad —
DEBUG = False
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", default="").split(",") if h.strip()]

# Render expone el hostname público automáticamente
RENDER_HOST = env("RENDER_EXTERNAL_HOSTNAME", default="")
if RENDER_HOST:
    ALLOWED_HOSTS.append(RENDER_HOST)
    CSRF_TRUSTED_ORIGINS = [f"https://{RENDER_HOST}"]
CSRF_TRUSTED_ORIGINS = list(globals().get("CSRF_TRUSTED_ORIGINS", [])) + env.list(
    "CSRF_TRUSTED_ORIGINS", default=[]
)

# — Base de Datos PostgreSQL —
DATABASES = {
    "default": env.db_url("DATABASE_URL")
}
DATABASES["default"]["OPTIONS"] = {"sslmode": env("DB_SSLMODE", default="require")}
DATABASES["default"]["CONN_MAX_AGE"] = 60

# — Archivos estáticos con WhiteNoise —
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# — Seguridad adicional para producción —
# Render termina TLS en su proxy; sin esto SECURE_SSL_REDIRECT entra en bucle
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True