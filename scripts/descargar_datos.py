#!/usr/bin/env python3
"""
Descarga automática de TODAS las fuentes del proyecto
"Impacto de las Fallas en el transporte y el alojamiento turístico de València".
No hay ningún dato introducido a mano: todo sale de fuentes oficiales descargables.

  Grupo     Bloque              Fuente                                    Granularidad
  -------   -----------------   ---------------------------------------   ------------
  DEMANDA   ✈️ aeropuerto        Eurostat avia_paoa (aeropuerto LEVC)      mes
  DEMANDA   🏨 hoteles           INE - Encuesta de Ocupación Hotelera      mes
  DEMANDA   🚇 metro             INE - Estadística Transporte Viajeros     mes
  DEMANDA   🏠 airbnb (reseñas)  Inside Airbnb                             fecha
  OFERTA    🏠 airbnb (anuncios) Inside Airbnb                             piso
  OFERTA    🏠 vut               GVA - Registro viviendas turísticas       vivienda
  CONTEXTO  🗺️ barrios           Ayuntamiento València + Wikidata          barrio

Uso:
    pip install -r requirements.txt
    python scripts/descargar_datos.py                     # todo
    python scripts/descargar_datos.py aeropuerto metro    # solo algunos bloques

Bloques: aeropuerto, hoteles, metro, airbnb, vut, barrios, wikidata
Resultado: datos/raw/<bloque>/...  +  datos/raw/MANIFIESTO.csv (inventario para el Apartado 2)
"""

import csv
import datetime as dt
import json
import re
import sys
import time
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent  # raíz del repositorio
RAW = RAIZ / "datos" / "raw"
MANIFIESTO = RAW / "MANIFIESTO.csv"
UA = {
    "User-Agent": "Mozilla/5.0 (practica-universitaria-UA; datos abiertos)",
    "Accept-Encoding": "gzip, deflate",  # sin brotli: evita errores de decodificación
}
TAM_MAX_MB = 300
HOY = dt.date.today().isoformat()

_manifiesto = []


# =========================================================================== utilidades
def log(msg):
    print(f"[{dt.datetime.now():%H:%M:%S}] {msg}", flush=True)


def get(url, **kw):
    for intento in range(3):
        try:
            r = requests.get(url, headers=UA, timeout=90, **kw)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            log(f"  ! intento {intento + 1}/3 fallido: {str(e)[:150]}")
            time.sleep(2 * (intento + 1))
    return None


def apuntar(grupo, bloque, fuente, destino, url, descripcion):
    _manifiesto.append({
        "grupo": grupo, "bloque": bloque, "fuente": fuente,
        "fichero": str(destino.relative_to(RAIZ)), "url": url,
        "descripcion": descripcion, "bytes": destino.stat().st_size, "fecha_descarga": HOY,
    })


def descargar(url, destino: Path, grupo, bloque, fuente, descripcion=""):
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists() and destino.stat().st_size > 0:
        log(f"  = ya existe {destino.relative_to(RAIZ)}")
    else:
        r = get(url, stream=True)
        if r is None:
            log(f"  ✗ no se pudo descargar {url}")
            return False
        tam = int(r.headers.get("Content-Length", 0))
        if tam and tam > TAM_MAX_MB * 1024 * 1024:
            log(f"  - omitido (>{TAM_MAX_MB} MB): {url}")
            return False
        with open(destino, "wb") as f:
            for trozo in r.iter_content(1 << 16):
                f.write(trozo)
        log(f"  ✓ {destino.relative_to(RAIZ)} ({destino.stat().st_size / 1e6:.1f} MB)")
    apuntar(grupo, bloque, fuente, destino, url, descripcion)
    return True


def escribir_csv(destino: Path, filas):
    destino.parent.mkdir(parents=True, exist_ok=True)
    columnas = list(dict.fromkeys(k for f in filas for k in f))
    with open(destino, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columnas)
        w.writeheader()
        w.writerows(filas)
    log(f"  ✓ {destino.relative_to(RAIZ)} ({len(filas)} filas)")


def nombre_seguro(texto, maximo=80):
    t = re.sub(r"[^\w\-]+", "_", texto.strip().lower(), flags=re.UNICODE)
    return t.strip("_")[:maximo] or "sin_nombre"


# =========================================================================== INE (genérico)
INE_API = "https://servicios.ine.es/wstempus/js/ES"
# "València" sí; "Comunitat Valenciana" no
FILTRO_VALENCIA = re.compile(r"val[eè]ncia(?!na)", re.I)


def descargar_ine(operacion, patrones_tabla, carpeta, grupo, bloque, meses=180):
    """Baja las tablas de una operación INE cuyo nombre contenga algún patrón,
    quedándose solo con las series de València."""
    r = get(f"{INE_API}/TABLAS_OPERACION/{operacion}")
    if r is None:
        return
    tablas = r.json()
    elegidas = [t for t in tablas if any(p in t.get("Nombre", "").lower() for p in patrones_tabla)]
    log(f"  {len(tablas)} tablas en {operacion}; {len(elegidas)} encajan con {patrones_tabla}")
    (RAW / carpeta).mkdir(parents=True, exist_ok=True)
    (RAW / carpeta / f"tablas_{operacion}.json").write_text(
        json.dumps(tablas, ensure_ascii=False, indent=1), "utf-8")

    for t in elegidas:
        tid, nombre = t["Id"], t["Nombre"]
        url = f"{INE_API}/DATOS_TABLA/{tid}?nult={meses}&tip=A"
        r = get(url)
        if r is None:
            continue
        filas = [{
            "tabla_id": tid, "tabla": nombre, "serie": s.get("Nombre"),
            "anyo": d.get("Anyo"), "mes": d.get("FK_Periodo"),
            "valor": d.get("Valor"), "secreto": d.get("Secreto"),
        } for s in r.json() if FILTRO_VALENCIA.search(s.get("Nombre", ""))
            for d in s.get("Data", [])]
        if not filas:
            log(f"  - tabla {tid} ({nombre[:50]}) sin series de València")
            continue
        destino = RAW / carpeta / f"{operacion}_{tid}_{nombre_seguro(nombre, 50)}.csv"
        escribir_csv(destino, filas)
        apuntar(grupo, bloque, f"INE {operacion}", destino, url, nombre)


# =========================================================================== bloques
def bloque_hoteles():
    log("🏨 Hoteles · INE Encuesta de Ocupación Hotelera (puntos turísticos)")
    descargar_ine("EOH", ["puntos tur"], "hoteles_ine", "DEMANDA", "hoteles")


def bloque_metro():
    log("🚇 Metro · INE Estadística de Transporte de Viajeros (metro por ciudades)")
    descargar_ine("TV", ["metro"], "metro_ine", "DEMANDA", "metro")


# ---- Eurostat
EUROSTAT_API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/avia_paoa"


def _jsonstat_a_filas(js):
    dims, tamanos = js["id"], js["size"]
    categorias = []
    for d in dims:
        cat = js["dimension"][d]["category"]
        idx, etiquetas = cat["index"], cat.get("label", {})
        orden = sorted(idx, key=idx.get) if isinstance(idx, dict) else idx
        categorias.append([(c, etiquetas.get(c, c)) for c in orden])
    for plano, valor in js.get("value", {}).items():
        resto, fila = int(plano), {}
        for d, n, cats in zip(reversed(dims), reversed(tamanos), reversed(categorias)):
            codigo, etiqueta = cats[resto % n]
            resto //= n
            fila[d] = codigo
            if etiqueta != codigo:
                fila[d + "_etiqueta"] = etiqueta
        fila["valor"] = valor
        yield fila


def bloque_aeropuerto():
    log("✈️ Aeropuerto · Eurostat avia_paoa (Valencia, LEVC)")
    r = get(EUROSTAT_API, params={"format": "JSON", "lang": "EN", "freq": "M", "rep_airp": "ES_LEVC"})
    if r is None:
        return
    filas = list(_jsonstat_a_filas(r.json()))
    for f in filas:
        m = re.match(r"(\d{4})-?M?(\d{2})", f.get("time", ""))
        f["anyo"], f["mes"] = (int(m[1]), int(m[2])) if m else (None, None)
    filas.sort(key=lambda f: (f.get("tra_meas", ""), f.get("time", "")))
    destino = RAW / "aeropuerto_eurostat" / "avia_paoa_valencia.csv"
    escribir_csv(destino, filas)
    apuntar("DEMANDA", "aeropuerto", "Eurostat avia_paoa", destino, r.url,
            "Pasajeros mensuales aeropuerto de Valencia")


# ---- Inside Airbnb
AIRBNB_PAGINA = "https://insideairbnb.com/get-the-data/"
AIRBNB_PATRON = re.compile(r"https?://data\.insideairbnb\.com/spain/vc/valencia/(\d{4}-\d{2}-\d{2})/")
AIRBNB_FICHEROS = {
    "data/listings.csv.gz": ("OFERTA", "Anuncios: barrio, precio, lat/lon, tipo, capacidad"),
    "data/reviews.csv.gz": ("DEMANDA", "Reseñas con fecha (proxy de estancias)"),
    "visualisations/neighbourhoods.geojson": ("CONTEXTO", "Polígonos de barrios"),
    "visualisations/neighbourhoods.csv": ("CONTEXTO", "Barrios y distritos"),
}


def bloque_airbnb():
    log("🏠 Airbnb · Inside Airbnb València")
    r = get(AIRBNB_PAGINA)
    if r is None:
        return
    fechas = AIRBNB_PATRON.findall(r.text)
    if not fechas:
        log("  ✗ no encuentro Valencia en la página de Inside Airbnb")
        return
    fecha = max(fechas)
    log(f"  captura más reciente: {fecha}")
    base = f"https://data.insideairbnb.com/spain/vc/valencia/{fecha}/"
    for rel, (grupo, desc) in AIRBNB_FICHEROS.items():
        descargar(base + rel, RAW / "airbnb" / fecha / rel.split("/")[-1],
                  grupo, "airbnb", "Inside Airbnb", desc)


# ---- CKAN (GVA y Ayuntamiento)
def ckan_paquete(portal, nombre_paquete, carpeta, grupo, bloque, formatos=("csv",)):
    r = get(f"{portal}/api/3/action/package_show", params={"id": nombre_paquete})
    if r is None:
        return
    pkg = r.json()["result"]
    (RAW / carpeta).mkdir(parents=True, exist_ok=True)
    (RAW / carpeta / f"{nombre_paquete}_metadatos.json").write_text(
        json.dumps(pkg, ensure_ascii=False, indent=1), "utf-8")
    vistos = set()
    for res in pkg.get("resources", []):
        fmt = (res.get("format") or "").lower().strip(".")
        if fmt in formatos and fmt not in vistos and res.get("url"):
            vistos.add(fmt)
            descargar(res["url"], RAW / carpeta / f"{nombre_paquete}.{fmt}",
                      grupo, bloque, portal.split("//")[1], pkg.get("title", nombre_paquete))


def ckan_busqueda(portal, q, carpeta, grupo, bloque, maximo=3, formatos=("csv", "geojson")):
    r = get(f"{portal}/api/3/action/package_search", params={"q": q, "rows": maximo})
    if r is None:
        return
    for pkg in r.json().get("result", {}).get("results", []):
        ckan_paquete(portal, pkg["name"], carpeta, grupo, bloque, formatos)


def bloque_vut():
    log("🏠 VUT · Registro oficial de viviendas turísticas (GVA)")
    ckan_paquete("https://dadesobertes.gva.es", "tur-gestur-vt", "vut_gva", "OFERTA", "vut")


def bloque_barrios():
    log("🗺️ Barrios · Ayuntamiento de València")
    ckan_busqueda("https://opendata.vlci.valencia.es", "barris", "barrios_valencia", "CONTEXTO", "barrios")


# ---- Wikidata
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
CONSULTA_BARRIOS = """
SELECT ?item ?itemLabel ?tipoLabel ?coord ?poblacion WHERE {
  VALUES ?tipo { wd:Q123705 wd:Q2198484 }
  ?item wdt:P31/wdt:P279* ?tipo ; wdt:P131+ wd:Q8818 .
  OPTIONAL { ?item wdt:P625 ?coord }
  OPTIONAL { ?item wdt:P1082 ?poblacion }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "es,ca,en". }
}"""


def bloque_wikidata():
    log("🗺️ Wikidata · barrios y distritos de València")
    r = get(WIKIDATA_SPARQL, params={"query": CONSULTA_BARRIOS, "format": "json"})
    if r is None:
        return
    filas = [{
        "wikidata_id": b["item"]["value"].rsplit("/", 1)[-1],
        "nombre": b.get("itemLabel", {}).get("value"),
        "tipo": b.get("tipoLabel", {}).get("value"),
        "coord_wkt": b.get("coord", {}).get("value"),
        "poblacion": b.get("poblacion", {}).get("value"),
    } for b in r.json()["results"]["bindings"]]
    destino = RAW / "wikidata" / "barrios_distritos_valencia.csv"
    escribir_csv(destino, filas)
    apuntar("CONTEXTO", "barrios", "Wikidata", destino, WIKIDATA_SPARQL, "Barrios y distritos de València")


# =========================================================================== main
BLOQUES = {
    "aeropuerto": bloque_aeropuerto,
    "hoteles": bloque_hoteles,
    "metro": bloque_metro,
    "airbnb": bloque_airbnb,
    "vut": bloque_vut,
    "barrios": bloque_barrios,
    "wikidata": bloque_wikidata,
}


def main():
    pedidos = sys.argv[1:] or list(BLOQUES)
    malos = [p for p in pedidos if p not in BLOQUES]
    if malos:
        sys.exit(f"Bloques desconocidos: {malos}. Opciones: {list(BLOQUES)}")
    RAW.mkdir(parents=True, exist_ok=True)
    for nombre in pedidos:
        try:
            BLOQUES[nombre]()
        except Exception as e:
            log(f"✗ error en '{nombre}': {e}")
    if _manifiesto:
        nuevo = not MANIFIESTO.exists()
        with open(MANIFIESTO, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(_manifiesto[0]))
            if nuevo:
                w.writeheader()
            w.writerows(_manifiesto)
        log(f"Inventario: {MANIFIESTO.relative_to(RAIZ)} (+{len(_manifiesto)} ficheros)")
    log("Hecho.")


if __name__ == "__main__":
    main()
