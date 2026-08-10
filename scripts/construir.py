#!/usr/bin/env python3
"""Construye el sitio estático a partir de los Markdown en contenido/."""
from __future__ import annotations
import html, json, re, shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

RAIZ=Path(__file__).resolve().parents[1]; CONTENIDO=RAIZ/"contenido"; PUBLIC=RAIZ/"public"
# Velocidad media usada únicamente para la métrica estimada de lectura en GA4.
PALABRAS_POR_MINUTO=220

def leer(ruta):
    raw=ruta.read_text(encoding="utf-8")
    if not raw.startswith("---\n"): raise ValueError(f"Falta cabecera en {ruta.name}")
    cab,cuerpo=raw[4:].split("\n---\n",1); meta={}
    for linea in cab.splitlines():
        if ":" in linea:
            k,v=linea.split(":",1); meta[k.strip()]=v.strip()
    meta.update({"cuerpo":cuerpo.strip(),"slug":ruta.stem}); return meta

def cuerpo_html(texto):
    bloques=[]
    for bloque in re.split(r"\n\s*\n",texto.strip()):
        lineas="<br>\n".join(html.escape(x) for x in bloque.splitlines())
        bloques.append(f"<p>{lineas}</p>")
    return "\n".join(bloques)

def fecha_legible(valor):
    try: return datetime.strptime(valor,"%Y-%m-%d").strftime("%d · %m · %Y")
    except ValueError: return valor

def mostrar_fecha(pieza): return pieza.get("fecha_mostrada") or fecha_legible(pieza.get("fecha",""))

def contar_palabras(texto):
    return len(re.findall(r"\b\w+\b",texto,flags=re.UNICODE))

def plantilla(titulo,contenido,base="",descripcion="Archivo personal de escritos"):
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(titulo)}</title><meta name="description" content="{html.escape(descripcion)}"><link rel="stylesheet" href="{base}estilo.css"><link rel="stylesheet" href="{base}identidad.css"><script async src="https://www.googletagmanager.com/gtag/js?id=G-9NKC49H0D8"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-9NKC49H0D8');</script></head><body>{contenido}<script src="{base}sitio.js"></script><script src="{base}analytics.js"></script></body></html>'''

def main():
    piezas=[leer(p) for p in CONTENIDO.glob("*.md")]; piezas.sort(key=lambda x:(x.get("fecha",""),x.get("titulo","")))
    if PUBLIC.exists(): shutil.rmtree(PUBLIC)
    (PUBLIC/"escritos").mkdir(parents=True); shutil.copy2(RAIZ/"static"/"estilo.css",PUBLIC/"estilo.css"); shutil.copy2(RAIZ/"static"/"identidad.css",PUBLIC/"identidad.css"); shutil.copy2(RAIZ/"static"/"sitio.js",PUBLIC/"sitio.js"); shutil.copy2(RAIZ/"static"/"analytics.js",PUBLIC/"analytics.js"); shutil.copy2(RAIZ/"static"/"logo.png",PUBLIC/"logo.png")
    for p in piezas:
        tipo=p.get("tipo","texto").replace("-"," "); tema=p.get("tema","otros").replace("-"," ")
        palabras=contar_palabras(p["cuerpo"]); lectura=max(1,(palabras+PALABRAS_POR_MINUTO-1)//PALABRAS_POR_MINUTO)
        datos={"slug":p["slug"],"title":p.get("titulo","Sin título"),"date":p.get("fecha",""),"topic":p.get("tema",""),"type":p.get("tipo",""),"word_count":palabras,"estimated_read_time":lectura}
        atributos=" ".join(f'data-article-{k.replace("_","-")}="{html.escape(str(v),quote=True)}"' for k,v in datos.items() if v!="")
        aviso='<p class="aviso">Recuperación parcial del archivo original; requiere revisión.</p>' if p.get("estado")=="revision" else ''
        articulo=f'''<header class="cabecera mínima"><a class="marca" href="../index.html">Existo</a></header><main class="lectura"><a class="volver" href="../index.html">← Todos los escritos</a><article data-analytics-article {atributos}><div class="metadatos"><span>{html.escape(mostrar_fecha(p))}</span><span>{html.escape(tipo)}</span><span>{html.escape(tema)}</span></div><h1>{html.escape(p.get('titulo','Sin título'))}</h1>{aviso}<div class="texto" data-article-body>{cuerpo_html(p['cuerpo'])}</div></article></main><footer>Existo · Archivo personal</footer>'''
        (PUBLIC/"escritos"/f"{p['slug']}.html").write_text(plantilla(p.get("titulo","Escrito"),articulo,"../"),encoding="utf-8")
    temas=Counter(p.get("tema","otros") for p in piezas); tipos=Counter(p.get("tipo","texto") for p in piezas)
    filtros_tema=''.join(f'<button data-filtro="tema" data-valor="{html.escape(k)}">{html.escape(k.replace("-"," "))} <small>{v}</small></button>' for k,v in sorted(temas.items()))
    filtros_tipo=''.join(f'<option value="{html.escape(k)}">{html.escape(k.replace("-"," "))} ({v})</option>' for k,v in sorted(tipos.items()))
    tarjetas=[]
    for p in piezas:
        extracto=re.sub(r"\s+"," ",p["cuerpo"]).strip()[:190]
        revision='<span>revisión pendiente</span>' if p.get('estado')=='revision' else ''
        tarjetas.append(f'''<article class="tarjeta" data-fecha="{html.escape(p.get('fecha',''))}" data-tema="{html.escape(p.get('tema','otros'))}" data-tipo="{html.escape(p.get('tipo','texto'))}" data-busca="{html.escape((p.get('titulo','')+' '+p['cuerpo']).lower())}"><div class="fecha">{html.escape(mostrar_fecha(p))}</div><h2><a href="escritos/{p['slug']}.html">{html.escape(p.get('titulo','Sin título'))}</a></h2><p>{html.escape(extracto)}…</p><div class="etiquetas"><span>{html.escape(p.get('tipo','texto').replace('-',' '))}</span><span>{html.escape(p.get('tema','otros').replace('-',' '))}</span>{revision}</div></article>''')
    inicio=f'''<header class="cabecera"><img class="logo" src="logo.png" alt="Existo — Razono, siento; miento, luego sé que existo"><a class="marca" href="index.html">Existo</a><p>Textos, poesías, reflexiones y columnas. Un archivo vivo para recorrer libremente o por fecha.</p><div class="resumen"><strong>{len(piezas)}</strong> escritos <span>·</span> <strong>{len(temas)}</strong> temas</div></header><main><section class="controles" aria-label="Buscar y filtrar"><label>Buscar<input id="buscar" type="search" placeholder="Una palabra, un título…"></label><label>Tipo<select id="tipo"><option value="">Todos</option>{filtros_tipo}</select></label><label>Orden<select id="orden"><option value="azar">Al azar</option><option value="cronologico">Cronológico</option></select></label><div class="temas"><button class="activo" data-filtro="tema" data-valor="">todos</button>{filtros_tema}</div></section><p id="resultado" class="resultado"></p><section id="archivo" class="archivo">{''.join(tarjetas)}</section></main><footer>Existo · Archivo personal</footer>'''
    (PUBLIC/"index.html").write_text(plantilla("Existo — Archivo de escritos",inicio),encoding="utf-8")
    (PUBLIC/"archivo.json").write_text(json.dumps([{k:v for k,v in p.items() if k!="cuerpo"} for p in piezas],ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Sitio construido con {len(piezas)} escritos en {PUBLIC}")
if __name__=="__main__": main()
