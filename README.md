# REMSA Plásticos — Sitio Web Corporativo

Plataforma web corporativa desarrollada en Django: presentación institucional,
catálogo de productos (preformas, botellas, garrafones y tapas en PET, PEAD) y
servicios configurables (personalización de garrafones, pigmentado,
protección UV) y un sistema de solicitudes de cotización B2B (sin ventas ni
pagos en línea).

## Stack

- Backend: Python 3.12 + Django 5 + Django REST Framework
- Base de datos: SQLite (desarrollo) / PostgreSQL (producción)
- Frontend: HTML5 + Bootstrap 5 + JavaScript ES6 (sin frameworks JS)
- Iconos: Bootstrap Icons
- Contenedores: Docker + docker-compose (Nginx + Gunicorn + PostgreSQL)

## Instalación en Windows 11 (desarrollo local)

1. **Requisitos**: Python 3.11+ (verifica con `python --version`).

2. Descomprime el proyecto, por ejemplo en `C:\proyectos\remsa_web`, y abre
   PowerShell en esa carpeta.

3. Crea y activa el entorno virtual:
   ```powershell
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```
   Si PowerShell bloquea el script, ejecuta una vez:
   `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

4. Instala dependencias:
   ```powershell
   pip install -r requirements.txt
   ```

5. Copia las variables de entorno:
   ```powershell
   copy .env.example .env
   ```
   Se deja tal cual para desarrollo (usa SQLite automáticamente).

6. Aplica migraciones y carga los datos de ejemplo:
   ```powershell
   python manage.py migrate
   python manage.py loaddata fixtures/datos_ejemplo.json
   python manage.py createsuperuser
   ```

7. Levanta el servidor:
   ```powershell
   python manage.py runserver
   ```
   - Sitio: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/

## Datos de ejemplo incluidos

El archivo `fixtures/datos_ejemplo.json` incluye:
- 4 categorías (Preformas, Botellas, Garrafones, Tapas)
- 8 productos de ejemplo con especificaciones básicas
- 3 servicios reales de REMSA (Personalización de garrafones, Pigmentado, Protección UV)
- 2 testimonios **de ejemplo**, claramente marcados para sustituir por reales
- Una `ConfiguracionSitio` con **datos de contacto placeholder** (teléfono,
  correo, dirección) que debes reemplazar desde Django Admin →
  "Configuración del Sitio" con los datos reales y verificados de la empresa.

Todo el contenido editorial (productos, categorías, servicios, banners,
testimonios, configuración) se administra desde `/admin/`, sin tocar código.

## Actualizar el catálogo desde Excel

La hoja `Catalogo` del archivo fuente `catalogo_REMSA_sin_repetidos.xlsx` es la
fuente de nombres y datos de producto. Primero valida el archivo y después
importa los cambios:

```powershell
python manage.py importar_catalogo_excel "C:\ruta\catalogo_REMSA_sin_repetidos.xlsx" --dry-run
python manage.py importar_catalogo_excel "C:\ruta\catalogo_REMSA_sin_repetidos.xlsx"
```

La importación crea o actualiza productos sin duplicar nombres, ignora filas
vacías y se detiene si detecta nombres repetidos o datos incompletos. Conserva
los registros anteriores en la base de datos, pero los que no estén en el
Excel dejan de aparecer en el catálogo público. Las imágenes ya asociadas a un
producto se conservan solo cuando su nombre coincide con el de una fila del
archivo; no se asignan imágenes de muestra a otros productos.
Los registros anteriores permanecen disponibles en sus páginas directas para
no romper enlaces ya publicados; no se incluyen en la búsqueda, los filtros,
la API pública ni el conocimiento de productos del chatbot.

La página pública muestra nombre, descripción, capacidad/medida, color, tipo y
especificaciones técnicas disponibles. La búsqueda y los filtros se basan en
los productos importados. Cada ficha ofrece un PDF con el logo REMSA. Para
actualizar nombres o características, corrige la hoja `Catalogo` y vuelve a
ejecutar el comando. Las fotografías correspondientes se administran desde
Django Admin en cada producto.

### Descripción y especificaciones de «Ver detalles»

Para completar los detalles de un producto, abre Django Admin → **Catálogo →
Productos** y edita el registro correspondiente:

1. La tarjeta del catálogo muestra la imagen, el nombre y `Descripción corta`.
   La capacidad, color, tipo y especificaciones se consultan con **Ver detalles**.
2. En **Descripción**, el campo `Descripción` (texto largo) se muestra en la
   ventana **Ver detalles**. Si se deja vacío, se utiliza `Descripción corta`
   del Excel.
3. En **Características**, completa material, capacidad/medida y color cuando
   esos datos estén confirmados.
4. En **Especificaciones adicionales del producto**, agrega una fila por dato.
   Por ejemplo, `Peso` / `19 g`, `Altura` / `169.5 mm`, `Ancho` / `43.2 mm`,
   `Rosca` / `Tapa de rosca 24 mm` o las capacidades publicadas. Los campos sin
   valor no se muestran.

La importación posterior del Excel sigue actualizando los campos que son
propiedad de la hoja, pero conserva la descripción larga escrita en Admin y
las especificaciones individuales. La especificación importada llamada
`Especificaciones técnicas` se actualiza con el Excel.

El catálogo público incluye únicamente las categorías Garrafones, Botellas,
Asas, Tapas, Preformas, Frascos y Garrafas. Solo aparecen categorías con
productos en el archivo; la opción Frascos se conserva porque fue solicitada,
pero la hoja actual no contiene productos de esa categoría y por ahora no
devuelve resultados.
Resinas, molido de PEAD, pigmentos, material reciclado y las demás categorías
no aparecen en el catálogo público, la API ni el conocimiento de productos del
chatbot.

### Solicitar el catálogo

La página inicial del catálogo muestra las líneas de producto y carga hasta 12
productos por página al elegir una categoría o buscar. Cada producto abre el
modal de solicitud con el producto precargado; el catálogo completo también
puede solicitarse desde la página principal. El formulario valida nombre,
empresa, correo, teléfono, producto de interés y aceptación del aviso de
privacidad (`paginas:privacidad`) antes de enviar.

El endpoint `POST /contacto/solicitar-catalogo/` verifica los datos en el
backend, aplica el límite antispam, guarda la solicitud en **Mensajes de
Contacto** y manda una notificación con fecha, página de origen y producto. El
correo destinatario se configura en Django Admin → **Configuración del Sitio**
→ `correo_notificaciones`; si queda vacío, se utiliza `COMERCIAL_EMAIL` del
archivo `.env`. El SMTP se configura mediante `EMAIL_*`. La respuesta de éxito
se muestra en el mismo modal. En desarrollo, el backend de correo de consola
imprime el mensaje en la terminal en lugar de entregarlo realmente.

El CAPTCHA es opcional. Para activarlo, registra el dominio con Google
reCAPTCHA y configura `RECAPTCHA_SITE_KEY` y `RECAPTCHA_SECRET_KEY` en el
entorno del servidor. La clave pública se renderiza en la página; la clave
secreta solo se utiliza para validar el token desde Django. Deja ambas
variables vacías para mantenerlo desactivado. Si solo se configura una clave,
el endpoint rechaza el envío y registra el error de configuración.

El diseño y el contenido del modal se editan en
`templates/catalogo/lista.html`; sus estilos están en
`static/css/catalogo.css` y su interacción en `static/js/catalogo.js`. El PDF
de cada producto se genera en `apps/catalogo/views.py` (vista
`ficha_producto_pdf`); el logo y la presentación se ajustan allí.

## Pruebas automatizadas

```powershell
python manage.py test
```
Incluye pruebas de catálogo (filtros, paginación, slugs, visibilidad),
solicitudes de catálogo (validación, CAPTCHA, privacidad, registro y correo) y
cotizaciones (carrito, generación de folio y bloqueo antispam por honeypot).

## Variables de entorno relevantes (`.env`)

| Variable | Descripción |
|---|---|
| `DJANGO_ENV` | `dev` (SQLite) o `prod` (PostgreSQL) |
| `DJANGO_SECRET_KEY` | Clave secreta única por entorno |
| `DJANGO_ALLOWED_HOSTS` | Dominios permitidos, separados por coma |
| `DB_*` | Credenciales de PostgreSQL (solo si `DJANGO_ENV=prod`) |
| `EMAIL_*` | SMTP para notificaciones y confirmaciones |
| `COMERCIAL_EMAIL` | Correo que recibe nuevas cotizaciones y mensajes |
| `RECAPTCHA_SITE_KEY` | Clave pública opcional de Google reCAPTCHA |
| `RECAPTCHA_SECRET_KEY` | Clave secreta opcional; solo se usa en el backend |
| `SHOW_WHATSAPP_FLOAT` | Muestra el botón flotante de WhatsApp (`True` / `False`; por defecto `False`) |

El botón de WhatsApp se conserva y puede reactivarse definiendo
`SHOW_WHATSAPP_FLOAT=True` en las variables de entorno del servidor y
reiniciando la aplicación.

## Chat REMSA

El widget global se incluye desde `templates/base.html`; su interfaz está en
`templates/includes/chatbot_widget.html` y el navegador se comunica con las
rutas Django `/api/chatbot/` y `/contacto/chatbot/solicitar-contacto/`. Las
respuestas comerciales se clasifican por reglas en `apps/core/chatbot.py`; el
chat no usa modelos de IA, APIs externas ni dependencias de chatbot.

Cuando la persona solicita información, cotización o hablar con ventas, el
formulario valida nombre, empresa, teléfono y correo y guarda el seguimiento
en **Mensajes de Contacto** (`MensajeContacto`). Producto y mensaje son
opcionales. Después se envía una notificación al destinatario de
`Configuración del Sitio → correo_notificaciones`; si está vacío, utiliza
`COMERCIAL_EMAIL` del entorno. Si el correo no se puede enviar, la solicitud
permanece guardada y el servidor registra el problema.

## Despliegue con Docker (producción)

1. Copia y completa `.env` con credenciales reales de PostgreSQL y SMTP,
   y define `DJANGO_ENV=prod`.
2. Levanta los servicios (PostgreSQL + Django/Gunicorn + Nginx):
   ```bash
   docker compose up -d --build
   ```
3. Crea el superusuario dentro del contenedor:
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```
4. El sitio queda disponible en el puerto 80 (Nginx sirve `/static/` y `/media/`
   directamente; Gunicorn atiende las peticiones dinámicas).

## Estructura del proyecto

```
config/            Settings (base/dev/prod), urls, wsgi/asgi
apps/
  core/             Configuración global del sitio, utilidades, sitemap
  catalogo/         Categoría, Producto, Servicio + API REST de solo lectura
  cotizaciones/      Cliente, SolicitudCotizacion, carrito en sesión, folio y correos
  contacto/         Formulario de contacto con antispam
  paginas/          Home, Nosotros, Banners, Testimonios, legales
templates/          Plantillas HTML organizadas por app
static/             CSS (variables + base), JS modular, imágenes/logo
media/              Imágenes subidas desde el Admin (productos, banners, etc.)
fixtures/           datos_ejemplo.json
deploy/             Configuración de Nginx para producción
```

## Notas importantes

- **No se procesan pagos en línea.** El sitio opera bajo el modelo comercial
  de REMSA: solicitud de cotización → seguimiento comercial directo.
- **Contenido pendiente de validar con la empresa**: textos de Misión, Visión,
  Valores, certificaciones de calidad, dirección exacta, teléfono y correos
  oficiales están marcados como `[provisional]` en las plantillas y como
  comentarios en el fixture — deben confirmarse y actualizarse antes de
  publicar el sitio en producción.
- **Imágenes**: el proyecto no incluye fotografías reales de planta/productos
  (no se generaron ni inventaron). Se muestran marcadores de posición
  (`img-placeholder`) donde falta una imagen real; súbelas desde Django Admin
  en cada Producto/Categoría/Banner/Servicio.

## Progreso del proyecto

- [x] Fase 1 — Proyecto base, settings dev/prod, apps, conexión a BD
- [x] Fase 2 — Modelos y Django Admin
- [x] Fase 3 — Datos de ejemplo (fixtures)
- [x] Fase 4 — Layout base (navbar, footer, paleta, logo)
- [x] Fase 5 — Home
- [x] Fase 6 — Catálogo con filtros
- [x] Fase 7 — Detalle de producto
- [x] Fase 8 — Sistema de cotización
- [x] Fase 9 — Nosotros / Contacto / Servicios / Legales
- [x] Fase 10 — SEO (sitemap.xml, robots.txt, meta tags, JSON-LD) y accesibilidad básica
- [x] Fase 11 — API REST de solo lectura (DRF)
- [x] Fase 12 — Docker y despliegue (Dockerfile, docker-compose, Nginx)
