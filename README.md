# Existo

**Razono, siento; miento, luego sé que existo.**

Este repositorio conserva escritos históricos y permite sumar poesías, ensayos,
reflexiones y columnas financieras sin tener que editar el sitio a mano.

## Añadir un escrito

1. Guarda un archivo `.txt` o `.md` dentro de `entrada/`.
2. La primera línea puede ser el título. También puedes usar el nombre del archivo.
3. Ejecuta `python scripts/publicar.py`.

El proceso asigna fecha, tema y tipo, mueve el original a `entrada/procesados/`,
crea la versión editorial en `contenido/` y reconstruye `public/`.

Si quieres decidir los datos, comienza el archivo así:

```markdown
---
titulo: El precio de la paciencia
fecha: 2026-08-04
tipo: columna-financiera
tema: finanzas
---

Aquí comienza el texto.
```

Los tipos recomendados son `poesia`, `reflexion`, `ensayo` y
`columna-financiera`. Los temas son libres; los históricos se clasificaron como
amor y desamor, amistad y despedida, familia, fe y espiritualidad, identidad y
reflexión, México y otros.

## Organización

- `contenido/`: fuente editorial, un Markdown por escrito.
- `entrada/`: bandeja para textos nuevos.
- `public/`: sitio generado; no se guarda en Git porque siempre se reconstruye.
- `scripts/publicar.py`: flujo normal para añadir y construir.
- `scripts/rescatar.py`: importador histórico reproducible; no altera Dropbox.
- `INFORME_RESCATE.md`: duplicados y piezas pendientes de revisión.

Las fechas con `fecha_fuente: fecha_modificacion` son aproximadas y conviene
corregirlas cuando exista mejor evidencia. Las clasificaciones automáticas se
pueden editar directamente en la cabecera de cada Markdown.
