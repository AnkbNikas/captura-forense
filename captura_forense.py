#!/usr/bin/env python3
"""
captura_forense.py — Análisis forense preliminar de capturas de pantalla

Genera indicios técnicos sobre la posible edición de una imagen (captura de
pantalla, foto, documento escaneado...) combinando:

  1. Extracción de metadatos (EXIF / información del contenedor)
  2. Comprobación de plausibilidad como captura de pantalla (resolución)
  3. Análisis de Nivel de Error (ELA — Error Level Analysis)

IMPORTANTE: esta herramienta genera INDICIOS orientativos para apoyar el
trabajo de un perito informático. No constituye, por sí sola, una prueba
pericial ni una certificación de autenticidad. Ver el apartado "Límites y
buenas prácticas" del README.

Autora: Nieves Casquero — Perito Informático de Parte (Colegiada AEPEJU)
Licencia: MIT
"""

import argparse
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ExifTags

VERSION = "1.0.0"

# Resoluciones de pantalla habituales (ancho, alto) — iPhone, iPad y Android
# más comunes. Lista orientativa, no exhaustiva: sirve para detectar si una
# imagen NO coincide con ninguna resolución de pantalla típica (lo cual no
# prueba manipulación, pero sí es un dato a documentar).
RESOLUCIONES_COMUNES = {
    (1170, 2532): "iPhone 12/13 (estándar)",
    (1179, 2556): "iPhone 15/14 Pro",
    (1290, 2796): "iPhone 15/14 Pro Max",
    (1080, 2340): "Android genérico (19.5:9)",
    (1080, 2400): "Android genérico (20:9)",
    (1440, 3200): "Android gama alta (QHD+)",
    (750, 1334): "iPhone 6/7/8",
    (828, 1792): "iPhone 11/XR",
    (1125, 2436): "iPhone X/XS/11 Pro",
    (1242, 2688): "iPhone XS Max/11 Pro Max",
    (1668, 2388): "iPad Pro 11\"",
    (2048, 2732): "iPad Pro 12.9\"",
    (1920, 1080): "Monitor Full HD / captura de escritorio",
    (2560, 1440): "Monitor QHD / captura de escritorio",
    (3840, 2160): "Monitor 4K / captura de escritorio",
}

SOFTWARE_EDICION_CONOCIDO = [
    "photoshop", "gimp", "snapseed", "lightroom", "pixlr", "canva",
    "affinity", "picsart", "facetune", "photoscape",
]


# --------------------------------------------------------------------------- #
# 1. Metadatos
# --------------------------------------------------------------------------- #

def extraer_metadatos(img: Image.Image, path: Path):
    meta = {
        "formato": img.format,
        "modo_color": img.mode,
        "dimensiones": list(img.size),
        "tamano_bytes": path.stat().st_size,
    }

    exif_raw = {}
    try:
        exif = img.getexif()
        if exif:
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id, str(tag_id))
                exif_raw[tag] = str(value)
    except Exception:
        pass
    meta["exif"] = exif_raw

    # Chunks de texto embebidos en PNG (algunos editores dejan rastro aquí)
    if img.format == "PNG" and getattr(img, "text", None):
        meta["png_text_chunks"] = dict(img.text)

    return meta


def detectar_software_edicion(meta):
    campos_a_revisar = []
    campos_a_revisar.append(str(meta.get("exif", {}).get("Software", "")))
    for v in meta.get("png_text_chunks", {}).values():
        campos_a_revisar.append(str(v))

    encontrados = []
    texto_combinado = " ".join(campos_a_revisar).lower()
    for prog in SOFTWARE_EDICION_CONOCIDO:
        if prog in texto_combinado:
            encontrados.append(prog)
    return encontrados


# --------------------------------------------------------------------------- #
# 2. Plausibilidad como captura de pantalla
# --------------------------------------------------------------------------- #

def evaluar_plausibilidad(meta):
    w, h = meta["dimensiones"]
    coincidencia = RESOLUCIONES_COMUNES.get((w, h)) or RESOLUCIONES_COMUNES.get((h, w))

    tiene_exif_camara = any(
        k in meta.get("exif", {}) for k in ("Make", "Model", "FNumber", "ExposureTime", "GPSInfo")
    )

    return {
        "coincide_resolucion_conocida": coincidencia,
        "tiene_metadatos_de_camara": tiene_exif_camara,
    }


# --------------------------------------------------------------------------- #
# 3. Error Level Analysis (ELA)
# --------------------------------------------------------------------------- #

def generar_ela(img: Image.Image, calidad=90, amplificacion=15):
    """Recomprime la imagen a la calidad JPEG indicada y calcula la
    diferencia píxel a píxel con el original. Zonas más brillantes en el
    resultado indican niveles de compresión distintos al resto de la imagen
    — un indicio (no una prueba) de edición localizada."""
    rgb = img.convert("RGB")

    buffer = io.BytesIO()
    rgb.save(buffer, "JPEG", quality=calidad)
    buffer.seek(0)
    recomprimida = Image.open(buffer)

    diff = Image.new("RGB", rgb.size)
    px_orig = rgb.load()
    px_recomp = recomprimida.load()
    px_diff = diff.load()

    max_diff = 0
    for y in range(rgb.height):
        for x in range(rgb.width):
            r1, g1, b1 = px_orig[x, y]
            r2, g2, b2 = px_recomp[x, y]
            dr, dg, db = abs(r1 - r2), abs(g1 - g2), abs(b1 - b2)
            max_diff = max(max_diff, dr, dg, db)
            px_diff[x, y] = (
                min(255, dr * amplificacion),
                min(255, dg * amplificacion),
                min(255, db * amplificacion),
            )

    return diff, max_diff


# --------------------------------------------------------------------------- #
# Informe
# --------------------------------------------------------------------------- #

def construir_informe(path, meta, plausibilidad, software_edicion, max_diff, ela_path, calidad):
    lines = []
    lines.append("# Informe de Análisis Forense Preliminar de Imagen\n")
    lines.append(f"**Archivo analizado:** `{path.name}`  ")
    lines.append(f"**Fecha de análisis (UTC):** {datetime.now(timezone.utc).isoformat()}  ")
    lines.append(f"**Formato:** {meta['formato']} — **Dimensiones:** "
                 f"{meta['dimensiones'][0]}×{meta['dimensiones'][1]} px — "
                 f"**Tamaño:** {meta['tamano_bytes']} bytes\n")

    lines.append("## 1. Metadatos extraídos\n")
    if meta["exif"]:
        lines.append("| Campo EXIF | Valor |")
        lines.append("|---|---|")
        for k, v in meta["exif"].items():
            lines.append(f"| {k} | {v} |")
    else:
        lines.append("No se han encontrado datos EXIF en el archivo "
                     "(habitual en capturas de pantalla nativas, que suelen guardarse en PNG sin EXIF).")

    if software_edicion:
        lines.append(f"\n⚠️ **Se han detectado referencias a software de edición de imagen en los "
                     f"metadatos:** {', '.join(software_edicion)}. Esto no prueba manipulación del "
                     f"contenido, pero debe documentarse y valorarse junto al resto de indicios.")

    lines.append("\n## 2. Plausibilidad como captura de pantalla\n")
    if plausibilidad["coincide_resolucion_conocida"]:
        lines.append(f"Las dimensiones coinciden con una resolución de pantalla habitual: "
                     f"**{plausibilidad['coincide_resolucion_conocida']}**.")
    else:
        lines.append("Las dimensiones **no coinciden** con ninguna resolución de pantalla común "
                     "de la lista de referencia utilizada. Esto no prueba manipulación —puede "
                     "tratarse de un recorte, una pantalla no catalogada o una imagen redimensionada—, "
                     "pero es un dato a tener en cuenta.")

    if plausibilidad["tiene_metadatos_de_camara"]:
        lines.append("\n⚠️ **La imagen contiene metadatos típicos de fotografía de cámara** "
                     "(modelo de dispositivo, apertura, GPS...), lo cual es inusual en una captura "
                     "de pantalla genuina y debe documentarse.")

    lines.append("\n## 3. Análisis de Nivel de Error (ELA)\n")
    lines.append(f"Se ha recomprimido la imagen a calidad JPEG {calidad} y se ha calculado la "
                 f"diferencia respecto al original. Diferencia máxima detectada entre píxeles: "
                 f"**{max_diff}** (escala 0-255).\n")
    lines.append(f"Mapa de calor generado: `{ela_path.name}`\n")
    lines.append("**Cómo interpretarlo:** en una imagen JPEG sin edición posterior, el nivel de "
                 "error tiende a ser homogéneo en toda la superficie. Si el mapa de calor muestra "
                 "una región claramente más brillante que el resto (bordes muy marcados, zonas de "
                 "texto o rostros que destacan sobre un fondo oscuro en el mapa), es un indicio de "
                 "que esa región ha tenido un historial de compresión distinto al resto — compatible "
                 "con una edición localizada, un pegado ('paste') o una re-compresión parcial.\n")
    lines.append("**El ELA no es concluyente por sí solo**: imágenes ya reconvertidas varias veces, "
                 "capturas de muy baja calidad o formatos como PNG sin pérdida pueden dar resultados "
                 "poco claros o falsos positivos/negativos. Debe interpretarse siempre junto con el "
                 "resto de indicios (metadatos, contexto, coherencia del contenido).\n")

    lines.append("## Límites de este análisis\n")
    lines.append("- Este informe identifica **indicios técnicos**, no constituye una prueba pericial "
                 "ni una certificación de autenticidad por sí sola.")
    lines.append("- Una captura de pantalla, incluso sin señales de edición, **rompe la trazabilidad** "
                 "respecto a la fuente original (mensaje, publicación, correo). Siempre que sea posible, "
                 "es preferible acreditar el contenido desde su origen (extracción forense del "
                 "dispositivo, cabeceras de correo, etc.).")
    lines.append("- Para que este análisis tenga validez en un procedimiento judicial debe "
                 "incorporarse a un informe pericial completo, firmado por un perito, con la "
                 "metodología y las herramientas debidamente documentadas.")

    lines.append("\n---\n")
    lines.append(f"*Generado con captura_forense.py v{VERSION} — "
                 "https://github.com/AnkbNikas/captura-forense*")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(
        prog="captura_forense",
        description="Genera indicios técnicos de edición en una imagen/captura de pantalla "
                     "(metadatos + Error Level Analysis)."
    )
    parser.add_argument("imagen", help="Ruta a la imagen a analizar")
    parser.add_argument("--salida", default="informe_captura", help="Nombre base de los ficheros de salida")
    parser.add_argument("--calidad", type=int, default=90, help="Calidad JPEG usada para el ELA (por defecto 90)")
    parser.add_argument("--amplificacion", type=int, default=15, help="Factor de amplificación del mapa ELA (por defecto 15)")
    args = parser.parse_args()

    path = Path(args.imagen)
    if not path.exists():
        print(f"Error: el archivo '{args.imagen}' no existe.", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Analizando: {path}")
    img = Image.open(path)

    meta = extraer_metadatos(img, path)
    software_edicion = detectar_software_edicion(meta)
    plausibilidad = evaluar_plausibilidad(meta)

    print("[*] Ejecutando Error Level Analysis...")
    ela_img, max_diff = generar_ela(img, calidad=args.calidad, amplificacion=args.amplificacion)

    ela_path = Path(f"{args.salida}_ela.png")
    ela_img.save(ela_path)

    informe_md = construir_informe(path, meta, plausibilidad, software_edicion, max_diff, ela_path, args.calidad)
    md_path = Path(f"{args.salida}.md")
    md_path.write_text(informe_md, encoding="utf-8")

    json_path = Path(f"{args.salida}.json")
    json_path.write_text(json.dumps({
        "archivo": str(path),
        "metadatos": meta,
        "plausibilidad": plausibilidad,
        "software_edicion_detectado": software_edicion,
        "ela_max_diff": max_diff,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[+] Informe Markdown: {md_path}")
    print(f"[+] Mapa ELA:         {ela_path}")
    print(f"[+] Datos JSON:       {json_path}")


if __name__ == "__main__":
    main()
