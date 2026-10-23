PUBLIC_CATALOG_CATEGORIES = (
    'Garrafones',
    'Botellas',
    'Asas',
    'Tapas',
    'Preformas',
    'Frascos',
    'Garrafas PET',
    'Garrafas PEAD',
)

PUBLIC_CATALOG_CATEGORY_KEYS = frozenset(
    category.casefold() for category in PUBLIC_CATALOG_CATEGORIES
)


def split_garrafas_category(category, *texts):
    """Convierte la categoría legada «Garrafas» en «Garrafas PET» o «Garrafas PEAD»."""
    if ' '.join(category.split()).casefold() != 'garrafas':
        return category
    haystack = ' '.join(texts).casefold()
    return 'Garrafas PEAD' if 'pead' in haystack or 'hdpe' in haystack else 'Garrafas PET'
