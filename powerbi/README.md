# Datos para Power BI — Etapa 4

Modelo en estrella generado desde `datos/procesados/` (Etapas 1 a 3) con
`scripts/preparar_datos_pbi.py`. Los CSV de `powerbi/datos/` se conectan
directamente desde Power BI (Obtener datos → Texto o CSV, uno por archivo).

## Regenerar los datos

```
pip install -r scripts/requirements.txt
python scripts/preparar_datos_pbi.py datos/procesados powerbi/datos
```

Entrada: los 4 archivos de `datos/procesados/`. Salida: 6 CSV en UTF-8 con BOM en
`powerbi/datos/`. El script imprime el número de filas de cada archivo al terminar.

## Tablas generadas

| Archivo | Tipo | Grano | Filas |
|---|---|---|---|
| `dim_departamento.csv` | Dimensión | 1 fila por departamento | 33 |
| `dim_anio.csv` | Dimensión | 1 fila por año (2005–2025) | 21 |
| `fact_dane_tic.csv` | Hechos | dominio × departamento × año × indicador | 960 |
| `fact_gestores.csv` | Hechos | 1 fila por instalación gestora (IDEAM) | 377 |
| `fact_encuesta_ns.csv` | Hechos | 1 fila por encuestado único (Norte de Santander) | 1 917 |
| `fact_reciclaje_global.csv` | Hechos | área × año (OWID) | 637 |

## Relaciones (varios a uno, filtro en una sola dirección)

- `fact_dane_tic[departamento]` → `dim_departamento[departamento]`
- `fact_gestores[departamento]` → `dim_departamento[departamento]`
- `fact_dane_tic[anio]` → `dim_anio[anio]`
- `fact_reciclaje_global[anio]` → `dim_anio[anio]`
- `fact_gestores[anio_otorgamiento]` → `dim_anio[anio]`

`fact_encuesta_ns` no se relaciona con ninguna dimensión (otra población, otra
unidad de análisis).

## Cifras de control (verificadas al ejecutar el script)

- Canal formal de entrega: 337 / 1 917 encuestados (17.6 %).
- Gestores con estado ACTIVO: 309.
- Top 5 departamentos con más gestores activos: 184 / 309 (59.5 %).
- Usaría una app para RAEE: 1 500 / 1 915 respuestas válidas (78.3 %).

## Limitación conocida

16 de los 377 gestores tienen `fecha_otorgamiento` real anterior a 2005 (1998–2004)
o posterior a 2025 (uno de 2026), fuera del rango de `dim_anio`. No cruzan con esa
dimensión por `anio_otorgamiento`, pero sí quedan incluidos por `departamento`.

## Transformaciones por fuente (resumen)

- **DANE**: homologación de 70 variantes de nombre a 33 departamentos; separación
  de los dominios agregados (Total nacional, Cabecera, Centros poblados y rural
  disperso) del dominio "Departamento".
- **IDEAM**: se elimina la columna `col` (100 % vacía); se agregan 8 banderas
  0/1 de autorización RESPEL/RAEE, `tipo_gestion_declarada`, `tiene_vigencia` y
  `registros_mismo_nit` (para detectar renovaciones de licencia).
- **Encuesta Norte de Santander**: se eliminan 116 duplicados exactos (reenvíos
  del formulario); el campo de dónde se entregan los residuos (multirrespuesta) se
  separa en banderas 0/1 y en un canal resumido; se homologan medio de entero y
  disposición a usar una app.
- **Global (OWID)**: solo el indicador `pct_raee_reciclado`, sin duplicados y sin
  los 16 valores fuera de 0–100 %.

## Siguiente paso

Abrir Power BI Desktop, conectar los 6 CSV de `powerbi/datos/`, armar las
relaciones de la tabla de arriba y construir los cuatro tableros de análisis.
Cuando el informe esté publicado, la URL se configura en `app.py`, en
`ETAPA_4["powerbi_embed_url"]` (o `powerbi_link_url`).
