#!/usr/bin/env python3
"""Audita el archivo editorial y genera un informe de calidad reproducible."""
from __future__ import annotations
import hashlib, re
from collections import Counter
from datetime import datetime
from pathlib import Path

RAIZ=Path(__file__).resolve().parents[1]
MARCAS_TECNICAS=("bjbj","MSWordDoc","Microsoft Office Word","Normal.dot","_rels/","IHDR","themeManager","Content_Types","SummaryInformation")

def leer(ruta):
    raw=ruta.read_text(encoding="utf-8")
    cab,cuerpo=raw[4:].split("\n---\n",1); meta={}
    for linea in cab.splitlines():
        if ":" in linea:
            k,v=linea.split(":",1); meta[k.strip()]=v.strip()
    return meta,cuerpo.strip()

def main():
    piezas=[]; problemas=[]; huellas={}
    for ruta in sorted((RAIZ/"contenido").glob("*.md")):
        meta,cuerpo=leer(ruta); piezas.append((ruta,meta,cuerpo))
        hallazgos=[]
        marcas=[m for m in MARCAS_TECNICAS if m.lower() in cuerpo.lower()]
        if marcas: hallazgos.append("residuos tecnicos: "+", ".join(marcas))
        if any(m in cuerpo for m in ("Ã","Â","â€")): hallazgos.append("posible problema de codificacion")
        if len(cuerpo.split())<10: hallazgos.append("menos de 10 palabras")
        huella=hashlib.sha256(re.sub(r"\W+","",cuerpo.lower()).encode()).hexdigest()
        if huella in huellas: hallazgos.append("duplica "+huellas[huella].name)
        else: huellas[huella]=ruta
        if hallazgos: problemas.append((ruta,hallazgos))
    estados=Counter(meta.get("estado","sin-estado") for _,meta,_ in piezas)
    lineas=["# Informe de calidad","",f"Generado: {datetime.now().isoformat(timespec='seconds')}","",f"- Escritos auditados: {len(piezas)}",f"- Publicados: {estados['publicado']}",f"- Marcados para revision: {estados['revision']}",f"- Problemas tecnicos detectados: {len(problemas)}","","## Hallazgos tecnicos",""]
    lineas += [f"- `{ruta.name}`: {'; '.join(items)}" for ruta,items in problemas] or ["- Ninguno"]
    (RAIZ/"INFORME_CALIDAD.md").write_text("\n".join(lineas)+"\n",encoding="utf-8")
    print(f"Auditados {len(piezas)} escritos: {len(problemas)} problema(s) tecnico(s), {estados['revision']} en revision editorial.")
    return 1 if problemas else 0

if __name__=="__main__": raise SystemExit(main())
