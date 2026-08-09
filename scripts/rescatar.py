#!/usr/bin/env python3
"""Rescata escritos del sitio antiguo sin modificar los originales."""
from __future__ import annotations
import hashlib, html, re, sys, unicodedata
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ARCHIVO = Path(r"C:\Users\ram5e\Dropbox\lanosrep\webs")
DESTINO = RAIZ / "contenido"

class ExtractorHTML(HTMLParser):
    def __init__(self):
        super().__init__(); self.partes=[]; self.omitir=0
    def handle_starttag(self, tag, attrs):
        if tag in {"script","style","head"}: self.omitir += 1
        elif not self.omitir and tag in {"br","p","div","tr","li","h1","h2","h3"}: self.partes.append("\n")
    def handle_endtag(self, tag):
        if tag in {"script","style","head"} and self.omitir: self.omitir -= 1
        elif not self.omitir and tag in {"p","div","tr","li","h1","h2","h3"}: self.partes.append("\n")
    def handle_data(self, data):
        if not self.omitir: self.partes.append(data)

def decodificar(datos):
    for enc in ("utf-8-sig","cp1252","latin-1"):
        try: return datos.decode(enc)
        except UnicodeDecodeError: pass
    return datos.decode("utf-8",errors="replace")

def limpiar(texto):
    texto=html.unescape(texto).replace("\xa0"," ").replace("\r\n","\n").replace("\r","\n")
    salida=[]
    for linea in (re.sub(r"[ \t]+"," ",x).strip() for x in texto.splitlines()):
        if linea: salida.append(linea)
        elif salida and salida[-1] != "": salida.append("")
    return "\n".join(salida).strip()

def reparar_mojibake(texto):
    if any(x in texto for x in ("Ã", "â€", "Â")):
        try: return texto.encode("cp1252").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError): pass
    return texto

def extraer_html(ruta):
    p=ExtractorHTML(); p.feed(decodificar(ruta.read_bytes())); return limpiar("".join(p.partes))

def extraer_doc(ruta):
    fragmentos=[]
    for bloque in re.findall(rb"[\x09\x0a\x0d\x20-\x7e\x80-\xfe]{5,}",ruta.read_bytes()):
        texto=reparar_mojibake(limpiar(bloque.decode("cp1252",errors="ignore"))).replace("Ą","¡").replace("ż","¿"); letras=sum(c.isalpha() for c in texto)
        basura=texto.count("ÿ")+texto.count("þ")
        raros=len(re.findall(r'''[^A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ¿¡.,;:!?\'"()…—–\-/%$#@&\s]''',texto))
        limite_raros=0 if len(texto)<12 else max(2,len(texto)//25)
        if letras>=3 and basura<max(3,len(texto)//20) and raros<=limite_raros: fragmentos.append(texto)
    if not fragmentos: return ""
    metadatos=("Microsoft Word","Word.Document","SummaryInformation","Times New Roman","theme/","<?xml","xmlns:","Content_Types")
    utiles=[x for x in fragmentos if not any(m in x for m in metadatos)]
    if not utiles: return ""
    mayor=max(utiles,key=lambda x:(len(x.split()),len(x)))
    if len(mayor.split())<80 and sum(len(x.split()) for x in utiles)>len(mayor.split())*2:
        resultado=limpiar("\n".join(utiles))
    else:
        resultado=mayor
    tecnicos=("bjbj","IHDR","_rels/","MSWordDoc","Microsoft Word","Microsoft Office","Word.Document","Normal.dot","Normal","Title","Heyman Asociados","Heyman y Asociados","Gerente de Inversiones","Institutional asset","Administradores de inversiones","Masaryk ","Polanco, ","Tel/Fax","Email:","Website:")
    lineas=[x for x in resultado.splitlines() if x.strip() and not any(x.strip().startswith(m) for m in tecnicos)]
    if lineas:
        inicio=normalizar(lineas[0])[:18]
        for i,linea in enumerate(lineas[1:],1):
            repetida=normalizar(linea)
            if i>=8 and " " not in linea.strip() and re.search(r"[A-Z]{2,}.*\d|\d.*[A-Z]{2,}",linea):
                lineas=lineas[:i]
                break
            if i>=len(lineas)//2 and inicio and len(repetida)>=6 and (repetida.startswith(inicio) or inicio.startswith(repetida)):
                lineas=lineas[:i]
                break
    for i,linea in enumerate(lineas):
        firma=linea.strip()
        if i>=len(lineas)//2 and re.fullmatch(r"[A-ZÁÉÍÓÚÜÑ]{3,20}",firma):
            return "\n".join(lineas[:i+1]).strip()
    return "\n".join(lineas).strip()

def sin_acentos(texto): return "".join(c for c in unicodedata.normalize("NFKD",texto) if not unicodedata.combining(c))
def slug(texto): return (re.sub(r"[^a-z0-9]+","-",sin_acentos(texto).lower()).strip("-")[:72] or "sin-titulo")

def titulo_de(ruta,texto):
    nombre=re.sub(r"(?:\s+\d+-\d+|\.+)$","",ruta.stem).replace("_"," ").strip()
    primera=next((x.strip(" ¡!¿?\t") for x in texto.splitlines() if x.strip()),"")
    return (primera[:100] if nombre.lower() in {"principal","rincon","cimientos","index","main"} else nombre) or "Sin título"

MESES="enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre"
def fecha_de(ruta,texto):
    m=re.search(r"(?i)\b((?:19|20)\d{2})[-/]([01]?\d)[-/]([0-3]?\d)\b",texto)
    if m: return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}","fecha_en_texto"
    m=re.search(r"(?i)\b([0-3]?\d)\s+de\s+("+MESES+r")\s+(?:de\s+)?((?:19|20)\d{2})\b",texto)
    if m: return f"{m.group(3)}-{MESES.split('|').index(m.group(2).lower())+1:02d}-{int(m.group(1)):02d}","fecha_en_texto"
    m=re.match(r"^(\d{2})(\d{2})(\d{2})\b",ruta.stem)
    if m: return f"20{m.group(1)}-{m.group(2)}-{m.group(3)}","fecha_en_nombre"
    return datetime.fromtimestamp(ruta.stat().st_mtime).strftime("%Y-%m-%d"),"fecha_modificacion"

def tema_de(titulo,texto):
    muestra=sin_acentos((titulo+" "+texto[:2500]).lower())
    reglas=[("finanzas",("mercado","inversion","accion","bono","financier","pemex","economia")),("mexico",("mexico","mexicano","patria")),("familia",("mama","madre","padre","familia")),("fe-y-espiritualidad",("dios","oracion","cielo","juan pablo","alma")),("amistad-y-despedida",("amigo","adios","despedida","itam","aleja")),("amor-y-desamor",("amor","te amo","beso","corazon","hermosa","lagrima")),("identidad-y-reflexion",("anti yo","reflexion","filosofia","vida","destino","sueno"))]
    puntaje,tema=max((sum(muestra.count(p) for p in palabras),tema) for tema,palabras in reglas)
    return tema if puntaje else "otros"

def tipo_de(titulo,texto,tema):
    if tema=="finanzas": return "columna-financiera"
    lineas=[x for x in texto.splitlines() if x.strip()]; promedio=sum(map(len,lineas))/max(1,len(lineas))
    if len(texto)>4500 or promedio>100: return "ensayo"
    if "reflex" in titulo.lower() or "filosof" in titulo.lower(): return "reflexion"
    return "poesia"

def normalizar(texto): return re.sub(r"[^a-z0-9]+","",sin_acentos(texto).lower())
def candidatos():
    ps=list((ARCHIVO/"poesias").glob("*.txt"))+[p for p in (ARCHIVO/"poesias").glob("*.doc") if not p.name.startswith("~$")]+list((ARCHIVO/"myweb"/"Personal"/"escritos").glob("*.htm*"))
    ps += [p for p in (ARCHIVO/"poesias"/"imagenes").glob("*.txt") if not re.search(r"\s\d+-\d+$",p.stem)]
    return list(dict.fromkeys(ps))

def grupos_fragmentos():
    grupos={}
    for ruta in (ARCHIVO/"poesias"/"imagenes").glob("*.txt"):
        m=re.match(r"^(.*?)\s+(\d+)-(\d+)$",ruta.stem)
        if m: grupos.setdefault(m.group(1).lower(),[]).append((int(m.group(2)),ruta))
    for clave,partes in grupos.items():
        ordenadas=[p for _,p in sorted(partes)]
        texto=limpiar("\n\n".join(limpiar(decodificar(p.read_bytes())) for p in ordenadas))
        texto=re.sub(r"(?m)^[•>]\s?","",texto)
        lineas=texto.splitlines()
        if clave=="el sin por que del destino":
            inicio=next((i for i,x in enumerate(lineas) if "sinpor" in normalizar(x)),0)
            lineas=lineas[inicio:]
            texto="\n".join(lineas).strip()
        for i,linea in enumerate(lineas):
            if i>=len(lineas)//2 and normalizar(linea)=="ramse":
                texto="\n".join(lineas[:i+1]).strip(); break
        yield ordenadas[0],texto

def escribir(ruta,texto,numero,estado="publicado"):
    titulo=titulo_de(ruta,texto); fecha,fecha_fuente=fecha_de(ruta,texto); tema=tema_de(titulo,texto); tipo=tipo_de(titulo,texto,tema)
    if slug(titulo)=="de-esos-amores-que-al-recordar-vuelven-a-nacer": fecha,fecha_fuente="2005-04-27","fecha_historica_conocida"
    destino=DESTINO/f"{fecha}-{slug(titulo)}.md"
    if destino.exists(): destino=DESTINO/f"{fecha}-{slug(titulo)}-{numero:02d}.md"
    fuente=ruta.relative_to(ARCHIVO).as_posix()
    cab=f"---\ntitulo: {titulo}\nfecha: {fecha}\nfecha_fuente: {fecha_fuente}\ntipo: {tipo}\ntema: {tema}\ntema_fuente: clasificacion_automatica\nestado: {estado}\nfuente_original: {fuente}\n---\n\n"
    destino.write_text(cab+texto.rstrip()+"\n",encoding="utf-8")
    return destino

def main():
    if not ARCHIVO.exists(): print(f"No se encontró {ARCHIVO}",file=sys.stderr); return 1
    DESTINO.mkdir(parents=True,exist_ok=True)
    for p in DESTINO.glob("*.md"): p.unlink()
    vistos={}; titulos={}; duplicados=[]; fragmentos_omitidos=[]; fallos=[]; revisiones=[]; creados=[]
    for ruta in candidatos():
        texto=extraer_doc(ruta) if ruta.suffix.lower()==".doc" else extraer_html(ruta) if ruta.suffix.lower() in {".htm",".html"} else limpiar(decodificar(ruta.read_bytes()))
        if len(texto)<80: fallos.append(ruta); continue
        huella=hashlib.sha256(normalizar(texto).encode()).hexdigest()
        if huella in vistos: duplicados.append((ruta,vistos[huella])); continue
        estado="revision" if ruta.stem.lower()=="calaveritas" else "publicado"
        if estado=="revision": revisiones.append(ruta)
        vistos[huella]=ruta; titulos[slug(titulo_de(ruta,texto))]=ruta; creados.append(escribir(ruta,texto,len(creados)+1,estado))
    for ruta,texto in grupos_fragmentos():
        clave=slug(titulo_de(ruta,texto))
        if clave in titulos: fragmentos_omitidos.append((ruta,titulos[clave])); continue
        if len(texto)<80: fallos.append(ruta); continue
        huella=hashlib.sha256(normalizar(texto).encode()).hexdigest()
        if huella in vistos: duplicados.append((ruta,vistos[huella])); continue
        revisiones.append(ruta); vistos[huella]=ruta; titulos[clave]=ruta; creados.append(escribir(ruta,texto,len(creados)+1,"revision"))
    lineas=["# Informe de rescate","",f"Generado: {datetime.now().isoformat(timespec='seconds')}","",f"- Piezas recuperadas: {len(creados)}",f"- Duplicados exactos omitidos: {len(duplicados)}",f"- Archivos sin texto suficiente: {len(fallos)}","","## Duplicados omitidos",""]
    lineas += [f"- `{reparar_mojibake(str(a.relative_to(ARCHIVO)))}` -> `{reparar_mojibake(str(b.relative_to(ARCHIVO)))}`" for a,b in duplicados] or ["- Ninguno"]
    lineas += ["","## Fragmentos redundantes omitidos",""] + ([f"- `{reparar_mojibake(str(a.relative_to(ARCHIVO)))}` -> `{reparar_mojibake(str(b.relative_to(ARCHIVO)))}`" for a,b in fragmentos_omitidos] if fragmentos_omitidos else ["- Ninguno"])
    lineas += ["","## Revision manual pendiente",""] + ([f"- `{reparar_mojibake(str(p.relative_to(ARCHIVO)))}` (recuperacion parcial)" for p in revisiones]+[f"- `{reparar_mojibake(str(p.relative_to(ARCHIVO)))}` (sin texto suficiente)" for p in fallos] if revisiones or fallos else ["- Ninguna"])
    (RAIZ/"INFORME_RESCATE.md").write_text("\n".join(lineas)+"\n",encoding="utf-8")
    print(f"Recuperadas {len(creados)} piezas; {len(duplicados)} duplicados; {len(revisiones)+len(fallos)} para revisión.")
    return 0
if __name__=="__main__": raise SystemExit(main())
