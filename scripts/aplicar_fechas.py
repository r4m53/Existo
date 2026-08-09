#!/usr/bin/env python3
"""Aplica al contenido las correcciones de la tabla editable de fechas."""
from __future__ import annotations
import re
from pathlib import Path
from rescatar import RAIZ, leer_fechas_editables, slug

def main():
    cambios=0; tabla=leer_fechas_editables(); contenido=RAIZ/"contenido"
    for ruta in list(contenido.glob("*.md")):
        raw=ruta.read_text(encoding="utf-8").replace("\r\n","\n")
        cab,cuerpo=raw[4:].split("\n---\n",1)
        meta={}
        for linea in cab.splitlines():
            if ":" in linea:
                k,v=linea.split(":",1); meta[k.strip()]=v.strip()
        manual=tabla.get(meta.get("fuente_original","")) or tabla.get(slug(meta.get("titulo","")))
        if not manual: continue
        lineas=[x for x in cab.splitlines() if not x.startswith("fecha_mostrada:")]
        lineas=[f"fecha: {manual['fecha']}" if x.startswith("fecha:") else f"fecha_fuente: {manual['fuente']}" if x.startswith("fecha_fuente:") else x for x in lineas]
        indice=next(i for i,x in enumerate(lineas) if x.startswith("fecha:"))+1
        if manual.get("fecha_mostrada"): lineas.insert(indice,f"fecha_mostrada: {manual['fecha_mostrada']}")
        nuevo=manual["fecha"]+"-"+re.sub(r"^\d{4}-\d{2}-\d{2}-","",ruta.name)
        destino=ruta.with_name(nuevo)
        destino.write_text("---\n"+"\n".join(lineas)+"\n---\n"+cuerpo,encoding="utf-8")
        if destino!=ruta: ruta.unlink()
        cambios+=1
    print(f"Fechas aplicadas a {cambios} escrito(s).")

if __name__=="__main__": main()
