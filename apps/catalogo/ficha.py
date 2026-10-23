"""Ficha técnica normalizada de un Producto.

Los datos salen de los campos del modelo Producto (color, capacidad) y de sus
EspecificacionProducto (pares nombre/valor, incluida la celda libre
"Especificaciones técnicas" importada del Excel). Nada se inventa: lo que no
exista se devuelve vacío y el frontend muestra «No especificado».
"""
import re
import unicodedata

NUMBER = r'\d+(?:[.,]\d+)?'
PACKAGING_WORDS = ('empaque', 'embalaje', 'caja', 'bulto', 'paquete')
PACKAGING_RULES = (
    ('contenido', 'emp_contenido'),
    ('piezas', 'emp_contenido'),
    ('unidades', 'emp_contenido'),
    ('cantidad', 'emp_contenido'),
    ('peso', 'emp_peso'),
    ('alto', 'emp_alto'),
    ('altura', 'emp_alto'),
    ('largo', 'emp_largo'),
    ('longitud', 'emp_largo'),
    ('ancho', 'emp_ancho'),
    ('anchura', 'emp_ancho'),
)
LABEL_RULES = (
    ('color', 'color'),
    ('capacidad', 'nominal'),
    ('volumen', 'nominal'),
    ('peso', 'peso'),
    ('boca', 'boca'),
    ('rosca', 'boca'),
    ('altura', 'alto'),
    ('anchura', 'ancho'),
    ('ancho', 'ancho'),
)
LIST_FIELDS = {'color', 'caracteristicas'}
UNITS = {
    'nominal': 'ml',
    'alto': 'mm', 'ancho': 'mm',
    'emp_alto': 'mm', 'emp_largo': 'mm', 'emp_ancho': 'mm',
}
LABEL_VALUE = re.compile(rf'^(?P<label>[^\d:]+?)\s*[:\-]?\s*(?P<value>{NUMBER}.*)$')


def _plain(text):
    text = unicodedata.normalize('NFD', text or '')
    return ''.join(c for c in text if not unicodedata.combining(c)).casefold().strip()


def _classify(label):
    plain = _plain(label)
    if 'modelo' in plain:
        return 'modelo'
    if 'caracteristic' in plain:
        return 'caracteristicas'
    if any(word in plain for word in PACKAGING_WORDS):
        for needle, field in PACKAGING_RULES:
            if needle in plain:
                return field
        return 'emp_tipo'
    if 'peso' in plain and 'producto' in plain:
        return 'emp_peso'
    for needle, field in LABEL_RULES:
        if needle in plain:
            return field
    return None


def _with_unit(value, unit):
    value = ' '.join(value.split())
    match = re.fullmatch(rf'({NUMBER})\s*(?:{unit})?', value, re.IGNORECASE)
    if match:
        return f'{match.group(1).replace(",", ".")} {unit}'
    return value


def _split_values(field, value):
    if field == 'color':
        parts = re.split(r'[,;]', value)
    elif field == 'caracteristicas':
        parts = re.split(r'[;\n]', value)
    else:
        parts = [value]
    return [p.strip() for p in parts if p and p.strip()]


def _segments(spec_name, spec_value):
    """Devuelve (campo, valor) a partir de una fila de especificación."""
    field = _classify(spec_name)
    if field:
        yield field, spec_value
        return
    # Celda libre: «Etiqueta: valor; Etiqueta: valor» o líneas separadas.
    for piece in re.split(r'[;\n|]+', spec_value):
        piece = piece.strip()
        if not piece:
            continue
        if ':' in piece:
            label, value = piece.split(':', 1)
            field = _classify(label)
            if field and value.strip():
                yield field, value.strip()
            continue
        # Sin separador explícito, ej. «Altura 15 mm, Ancho 40.8 mm».
        for sub_piece in piece.split(','):
            sub_piece = sub_piece.strip()
            if not sub_piece:
                continue
            match = LABEL_VALUE.match(sub_piece)
            if not match:
                continue
            field = _classify(match.group('label'))
            if field:
                yield field, match.group('value').strip()


def build_ficha(producto):
    data = {name: [] for name in LIST_FIELDS}
    single = {}
    seen = {name: set() for name in LIST_FIELDS}

    def add(field, raw):
        raw = (raw or '').strip()
        if not raw:
            return
        if field in LIST_FIELDS:
            for item in _split_values(field, raw):
                if _plain(item) not in seen[field]:
                    seen[field].add(_plain(item))
                    data[field].append(item)
        else:
            value = _with_unit(raw, UNITS[field]) if field in UNITS else ' '.join(raw.split())
            single.setdefault(field, value)

    for spec in producto.especificaciones.all():
        for field, value in _segments(spec.nombre, spec.valor):
            add(field, value)

    add('color', producto.color)
    capacidad = (producto.capacidad or '').strip()
    if capacidad and re.search(
        r'\b\d+(?:[.,]\d+)?\s*(ml|l|lt|lts|litros?)\b', capacidad, re.IGNORECASE
    ):
        add('nominal', capacidad)

    description = (producto.descripcion or producto.descripcion_corta or '').strip()
    return {
        'categoria': producto.categoria.nombre,
        'general': {
            'modelo': single.get('modelo'),
            'material': producto.get_material_display() if producto.material else None,
            'capacidad': single.get('nominal'),
            'peso': single.get('peso'),
            'boca': single.get('boca'),
            'alto': single.get('alto'),
            'ancho': single.get('ancho'),
            'descripcion': description or None,
            'caracteristicas': data['caracteristicas'],
        },
        'colores': data['color'],
        'empaque': {  # solo datos de empaque presentes en la BD
            'tipo': single.get('emp_tipo'),
            'contenido': single.get('emp_contenido'),
            'peso': single.get('emp_peso'),
            'alto': single.get('emp_alto'),
            'largo': single.get('emp_largo'),
            'ancho': single.get('emp_ancho'),
        },
    }
