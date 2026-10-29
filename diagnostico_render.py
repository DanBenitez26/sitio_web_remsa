import os
import psycopg

url = os.environ.get("RENDER_DATABASE_URL")

if not url:
    raise SystemExit("Falta la variable RENDER_DATABASE_URL.")

if "sslmode=" not in url:
    url += "&sslmode=require" if "?" in url else "?sslmode=require"

with psycopg.connect(url, connect_timeout=15) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cur.fetchall()]

        print("=== TABLAS DE RENDER ===")
        for table in tables:
            print(table)

        print("\n=== CONTEOS DEL CATALOGO ===")
        targets = {
            "catalogo_categoria",
            "catalogo_producto",
            "catalogo_imagenproducto",
            "catalogo_especificacionproducto",
        }

        for table in tables:
            if table in targets:
                cur.execute(
                    f'SELECT COUNT(*) FROM "{table}"'
                )
                print(f"{table}: {cur.fetchone()[0]}")