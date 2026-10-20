# Datos del proyecto: impacto de las Fallas en València

**Todo es descargable de fuentes oficiales. No hay ningún dato introducido a mano.**

## Ejecutar

```bash
pip install -r requirements.txt
python descargar_datos.py                    # todo
python descargar_datos.py aeropuerto metro   # solo algunos bloques
```

Todo queda en `datos/raw/` y cada fichero se apunta en `datos/raw/MANIFIESTO.csv`
(grupo, fuente, URL, fecha de descarga): es vuestro inventario para el Apartado 2.

## Fuentes

| Grupo | Bloque | Fuente | Enlace | Cada cuánto | Carpeta |
|---|---|---|---|---|---|
| Demanda | ✈️ Aeropuerto | Eurostat `avia_paoa` | https://ec.europa.eu/eurostat/databrowser/view/avia_paoa/default/table | Mes | `aeropuerto_eurostat/` |
| Demanda | 🏨 Hoteles | INE – Encuesta de Ocupación Hotelera | https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736177015&menu=ultiDatos&idp=1254735576863 | Mes | `hoteles_ine/` |
| Demanda | 🚇 Metro | INE – Estadística de Transporte de Viajeros | https://www.ine.es (buscad "Estadística de Transporte de Viajeros" → metro por ciudades) | Mes | `metro_ine/` |
| Demanda | 🏠 Airbnb (reseñas) | Inside Airbnb | https://insideairbnb.com/get-the-data/ | Fecha | `airbnb/` |
| Oferta | 🏠 Airbnb (anuncios) | Inside Airbnb | (mismo) | Piso | `airbnb/` |
| Oferta | 🏠 Viviendas turísticas | GVA – Registro VUT | https://dadesobertes.gva.es/es/dataset/tur-gestur-vt | Vivienda | `vut_gva/` |
| Contexto | 🗺️ Barrios | Ayuntamiento de València | https://opendata.vlci.valencia.es/ | Barrio | `barrios_valencia/` |
| Contexto | 🗺️ Barrios (IDs) | Wikidata | https://query.wikidata.org/ | Barrio | `wikidata/` |

Si queréis descargar alguno a mano desde la web, son esos mismos enlaces.

## Cómo se ven las Fallas

Ningún fichero es "de Fallas": son datos de todo el año. El impacto se calcula comparando
**marzo (Fallas) con febrero y abril**, en varios años.

## Qué mirar en cada fichero

- **Aeropuerto:** columna `tra_meas`. Usad una sola medida (p. ej. `PAS_CRD`, pasajeros transportados).
- **Hoteles y metro (INE):** la columna `serie` lleva varias cosas pegadas
  ("València. Viajeros. Extranjeros…"). Separarla en Pentaho = *Splitting* (Apartado 4).
  `mes` va de 1 a 12.
- **Airbnb:** `listings` para el mapa; `reviews` contando reseñas por mes para ver el pico de marzo.
- **VUT:** filtrad el municipio València. No trae coordenadas → geocodificar direcciones = *enriquecer* (Apartado 4).
  Comparar VUT con Airbnb permite estimar pisos anunciados sin registrar.

## Valores raros esperables (para el Apartado 4)
- 2020–2021: sin Fallas en marzo (COVID).
- Finales de 2024 y 2025: la DANA afectó al metro.
- Marzo 2026: huelga en Metrovalencia.
- Datos INE con `secreto = true`: ocultos por confidencialidad → valores ausentes.

## Licencias
Eurostat: libre citando la fuente. INE: libre citando la fuente. Inside Airbnb: CC BY 4.0.
GVA: CC BY. Ayuntamiento de València: CC BY 4.0. Wikidata: CC0.
