#!/usr/bin/env python3
"""Importa la bandeja entrada/ y reconstruye el archivo."""
from __future__ import annotations
import re, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path
from rescatar import limpiar, decodificar, fecha_de, tema_de, tipo_de, slug

RAIZ=Path(__file__).resolve().parents[1]; ENTRADA=RAIZ/"entrada"; CONTENIDO=RAIZ/"contenido"; PROCESADOS=ENTRADA/"procesados"

def separar(raw):
    if raw.startswith("---\n") and "\n---\n" in raw[4:]:
        cab,cuerpo=raw[4:].split("\n---\n",1); meta={}
        for linea in cab.splitlines():
            if ":" in linea:
                k,v=linea.split(":",1); meta[k.strip()]=v.strip()
        return meta,limpiar(cuerpo)
    return {},limpiar(raw)

def main():
    PROCESADOS.mkdir(parents=True,exist_ok=True); CONTENIDO.mkdir(exist_ok=True)
    nuevos=0
    for ruta in sorted(p for p in ENTRADA.iterdir() if p.is_file() and p.suffix.lower() in {".txt",".md"}):
        meta,cuerpo=separar(decodificar(ruta.read_bytes()))
        if len(cuerpo)<20: print(f"Omitido (demasiado corto): {ruta.name}"); continue
        primera=next((x.strip("# ¡!¿? ") for x in cuerpo.splitlines() if x.strip()),ruta.stem)
        titulo=meta.get("titulo") or (ruta.stem if ruta.stem.lower() not in {"nuevo","texto","escrito"} else primera)
        fecha=meta.get("fecha"); fuente_fecha="fecha_indicada"
        if not fecha: fecha,fuente_fecha=fecha_de(ruta,cuerpo)
        tema=meta.get("tema") or tema_de(titulo,cuerpo); tipo=meta.get("tipo") or tipo_de(titulo,cuerpo,tema)
        nombre=f"{fecha}-{slug(titulo)}.md"; destino=CONTENIDO/nombre; n=2
        while destino.exists(): destino=CONTENIDO/f"{fecha}-{slug(titulo)}-{n}.md"; n+=1
        cab=f"---\ntitulo: {titulo}\nfecha: {fecha}\nfecha_fuente: {fuente_fecha}\ntipo: {tipo}\ntema: {tema}\ntema_fuente: {'indicada' if meta.get('tema') else 'clasificacion_automatica'}\nestado: publicado\nfuente_original: entrada/{ruta.name}\n---\n\n"
        destino.write_text(cab+cuerpo.rstrip()+"\n",encoding="utf-8")
        archivado=PROCESADOS/ruta.name
        if archivado.exists(): archivado=PROCESADOS/f"{ruta.stem}-{datetime.now():%Y%m%d%H%M%S}{ruta.suffix}"
        shutil.move(str(ruta),str(archivado)); nuevos+=1; print(f"Añadido: {titulo}")
    subprocess.run([sys.executable,str(RAIZ/"scripts"/"aplicar_fechas.py")],check=True)
    subprocess.run([sys.executable,str(RAIZ/"scripts"/"construir.py")],check=True)
    print(f"Listo: {nuevos} texto(s) nuevo(s).")
if __name__=="__main__": main()
