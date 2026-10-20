# Impacto de las Fallas en el transporte y el alojamiento turístico de València

Práctica de la asignatura de adquisición y preparación de datos (Universidad de Alicante).

## Objetivo

Medir cuánto aumenta la demanda de transporte y alojamiento turístico en València durante
las Fallas (marzo), integrando datos abiertos oficiales en un almacén de datos, transformándolos
a datos enlazados (schema.org) y visualizando los resultados.

El impacto se calcula **comparando marzo con febrero y abril** en varios años: ninguna fuente
es "de Fallas", todas son series de todo el año.

## Preguntas

1. ¿Cuánta gente más llega a València en Fallas? (aeropuerto)
2. ¿Se llenan más los hoteles en marzo? (INE)
3. ¿Aumenta el uso del metro? (INE)
4. ¿Dónde se concentran los pisos turísticos y cuántos no están registrados? (Inside Airbnb + registro GVA)

## Fuentes

| Grupo | Bloque | Fuente | Granularidad |
|---|---|---|---|
| Demanda | Aeropuerto | Eurostat `avia_paoa` | Mes |
| Demanda | Hoteles | INE – Encuesta de Ocupación Hotelera | Mes |
| Demanda | Metro | INE – Estadística de Transporte de Viajeros | Mes |
| Demanda / Oferta | Pisos turísticos | Inside Airbnb | Fecha / piso |
| Oferta | Viviendas turísticas | GVA – Registro VUT | Vivienda |
| Contexto | Barrios | Ayuntamiento de València + Wikidata | Barrio |

Detalle de cada fuente, enlaces y avisos: [`datos/README.md`](datos/README.md).

## Estructura del repositorio

```
├── scripts/            Descarga automática de los datos
├── datos/
│   ├── raw/            Datos originales (no se suben: se regeneran con el script)
│   └── procesados/     Datos limpios tras el ETL
├── almacen/            Apartado 3: diseño y scripts SQL del almacén de datos
├── etl/                Apartado 4: transformaciones de Pentaho Data Integration
├── rdf/                Apartado 5: tripletas schema.org
├── visualizaciones/    Apartado 6
└── memoria/            Apartado 7
```

## Reproducir

```bash
pip install -r requirements.txt
python scripts/descargar_datos.py
```

Los datos se guardan en `datos/raw/`, y `datos/raw/MANIFIESTO.csv` registra la fuente,
URL y fecha de descarga de cada fichero.

## Autores

- (nombre 1)
- (nombre 2)
- (nombre 3)
- (nombre 4)

## Licencia

Código: MIT (ver [`LICENSE`](LICENSE)).
Los datos mantienen la licencia de su fuente original (INE, Eurostat, Inside Airbnb CC BY 4.0,
GVA CC BY, Ayuntamiento de València CC BY 4.0, Wikidata CC0).

## Referencias

- Eurostat – Air passenger transport by reporting airport: https://ec.europa.eu/eurostat/databrowser/view/avia_paoa/default/table
- INE – Encuesta de Ocupación Hotelera: https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736177015&menu=ultiDatos&idp=1254735576863
- INE – Estadística de Transporte de Viajeros: https://www.ine.es
- Inside Airbnb: https://insideairbnb.com/get-the-data/
- GVA – Registro de viviendas turísticas: https://dadesobertes.gva.es/es/dataset/tur-gestur-vt
- Portal de datos abiertos de València: https://opendata.vlci.valencia.es/
- Wikidata: https://www.wikidata.org/
