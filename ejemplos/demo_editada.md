# Informe de Análisis Forense Preliminar de Imagen

**Archivo analizado:** `captura_generica_editada.jpg`  
**Fecha de análisis (UTC):** 2026-08-30T10:44:25.687201+00:00  
**Formato:** JPEG — **Dimensiones:** 1080×500 px — **Tamaño:** 34923 bytes

## 1. Metadatos extraídos

| Campo EXIF | Valor |
|---|---|
| Software | Adobe Photoshop 26.0 |
| DateTime | 2026:08:29 23:47:12 |

⚠️ **Se han detectado referencias a software de edición de imagen en los metadatos:** photoshop. Esto no prueba manipulación del contenido, pero debe documentarse y valorarse junto al resto de indicios.

## 2. Plausibilidad como captura de pantalla

Las dimensiones **no coinciden** con ninguna resolución de pantalla común de la lista de referencia utilizada. Esto no prueba manipulación —puede tratarse de un recorte, una pantalla no catalogada o una imagen redimensionada—, pero es un dato a tener en cuenta.

## 3. Análisis de Nivel de Error (ELA)

Se ha recomprimido la imagen a calidad JPEG 90 y se ha calculado la diferencia respecto al original. Diferencia máxima detectada entre píxeles: **25** (escala 0-255).

Mapa de calor generado: `demo_editada_ela.png`

**Cómo interpretarlo:** en una imagen JPEG sin edición posterior, el nivel de error tiende a ser homogéneo en toda la superficie. Si el mapa de calor muestra una región claramente más brillante que el resto (bordes muy marcados, zonas de texto o rostros que destacan sobre un fondo oscuro en el mapa), es un indicio de que esa región ha tenido un historial de compresión distinto al resto — compatible con una edición localizada, un pegado ('paste') o una re-compresión parcial.

**El ELA no es concluyente por sí solo**: imágenes ya reconvertidas varias veces, capturas de muy baja calidad o formatos como PNG sin pérdida pueden dar resultados poco claros o falsos positivos/negativos. Debe interpretarse siempre junto con el resto de indicios (metadatos, contexto, coherencia del contenido).

## Límites de este análisis

- Este informe identifica **indicios técnicos**, no constituye una prueba pericial ni una certificación de autenticidad por sí sola.
- Una captura de pantalla, incluso sin señales de edición, **rompe la trazabilidad** respecto a la fuente original (mensaje, publicación, correo). Siempre que sea posible, es preferible acreditar el contenido desde su origen (extracción forense del dispositivo, cabeceras de correo, etc.).
- Para que este análisis tenga validez en un procedimiento judicial debe incorporarse a un informe pericial completo, firmado por un perito, con la metodología y las herramientas debidamente documentadas.

---

*Generado con captura_forense.py v1.0.0 — https://github.com/AnkbNikas/captura-forense*