# Datos del proyecto

Trazabilidad de la Etapa 1. Los archivos de `originales/` **no se modifican**: son las
descargas tal cual salieron de cada fuente. Todo lo de `procesados/` son derivados
(limpieza, reestructuración y consolidación) generados a partir de `originales/`.

```
datos/
  originales/   descargas sin tocar (una por fuente)
  procesados/   dataset consolidado de la Etapa 1
```

## originales/ — fuentes originales

| Archivo | Fuente | Formato | Descarga |
|---|---|---|---|
| `electronic-waste-recycling-rate.csv` | Our World in Data — Electronic waste recycling rate | CSV | Descarga directa ("Download full data") |
| `RAEE por operaciones de gestión de residuos.xml.gz` | Eurostat — WEEE by waste management operations (`env_waseleeos`) | XML/SDMX comprimido (gzip) | API SDMX 3.0 |
| `Households with a computer.csv` | ITU — Hogares con computador (i=8917) | CSV | Data Explorer |
| `Households with Internet access at home.csv` | ITU — Hogares con internet en casa (i=12047) | CSV | Data Explorer |
| `Individuals using the Internet.csv` | ITU — Individuos que usan internet (i=11624) | CSV | Data Explorer |
| `Individuals using a mobile cellular telephone.csv` | ITU — Individuos con telefonía móvil (i=9145) | CSV | Data Explorer |
| `Anexos_ENTIC_hogares_2020.xlsx` | DANE — ENTIC Hogares 2020 | XLSX | Anexos |
| `anexos_entic_hogares_2021.xlsx` | DANE — ENTIC Hogares 2021 | XLSX | Anexos |
| `anex-ENTICHogares-2024.xlsx` | DANE — ENTIC Hogares 2024 | XLSX | Anexos |
| `anex-ECV-Series-2024.xlsx` | DANE — ECV, Cuadros 5 y 18, serie 2018–2024 | XLSX | Anexos |
| `GESTORES_RESPEL_Y_RAEE_29_jul_26.xlsx` | IDEAM — Gestores RESPEL y RAEE (corte 29/07/2026) | XLSX | datos.gov.co |
| `norte_santander_percepcion_raee.csv` | Gobernación de Norte de Santander — Estudio de percepción ciudadana RAEE | CSV | datos.gov.co |

> El CSV de Norte de Santander se renombró (solo el nombre, no el contenido): el
> original de datos.gov.co traía un nombre demasiado largo para Git en Windows.
> Ver la tabla completa (institución, URL, periodo, variables, restricciones) en la
> vista **Fuentes de datos** de la app.

## procesados/ — dataset consolidado

| Archivo | Filas | Contenido | Esquema |
|---|---:|---|---|
| `master_indicadores_globales.csv` | 78 689 | OWID + Eurostat WEEE + ITU, serie por país y año | por confirmar al subir |
| `dane_clean.csv` | 960 | ENTIC Hogares (204: 34 dominios × 3 años × 2 indicadores) + ECV (756: 36 dominios × 7 años × 3 indicadores) | `departamento, año, indicador, valor` (+ encuesta) |
| `ideam_gestores_clean.csv` | 377 | Directorio de gestores RESPEL/RAEE por empresa | por confirmar al subir |
| `norte_santander_encuesta_clean.csv` | 2 033 | Encuesta de percepción ciudadana | por confirmar al subir |

**Total: 82 059 filas** (cumple el mínimo de 10 000). Los conteos derivados difieren
levemente de los crudos (p. ej. IDEAM 385 → 377) por la limpieza.

## Transformaciones aplicadas

- **Global:** unificación de OWID, Eurostat (`env_waseleeos`) e ITU en un formato largo país–año.
- **DANE:** extracción de los cuadros de ENTIC y de los Cuadros 5 y 18 de la ECV a formato
  `departamento, año, indicador, valor`.
- **IDEAM / Norte de Santander:** limpieza de columnas y normalización de texto.
- Verificación de los valores finales contra los archivos de `originales/` antes de consolidar.

## Notas de calidad detectadas al procesar

- **ECV vs ENTIC — no mezclar como una sola variable:** el Cuadro 5 de la ECV usa en 2024 un
  nombre de indicador algo distinto al de 2018–2023. Por eso el % de hogares con internet
  de la ECV se guarda como `pct_hogares_internet_v2`, separado del `pct_hogares_internet`
  de ENTIC: son mediciones parecidas pero de encuestas distintas del DANE. Llevar esto al
  diagnóstico de consistencia.
- Bug corregido durante la consolidación: una coincidencia de subcadena confundía
  "TOTAL NACIONAL" con "DEPARTAMENTOS"; se corrigió y se re-verificó.
