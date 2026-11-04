# Modelo estrella — Etapa 5 (Análisis multidimensional)

`rect_estrella.db` es una base SQLite que reorganiza las tablas ya tratadas de
la Etapa 4 (`datos/powerbi/*.csv`) en una **constelación de hechos**: cuatro
tablas de hechos, cada una con su propio grano real, que comparten tres
dimensiones conformadas.

Se reconstruye por completo (no de forma incremental) con:

```bash
python scripts/construir_modelo_estrella.py
```

y se verifica con:

```bash
python scripts/verificar_modelo_estrella.py
```

El esquema (DDL comentado, con la justificación de cada tabla) está en
`scripts/esquema_estrella.sql`.

## Dimensiones

| Tabla | Clave | Jerarquía | Notas |
|---|---|---|---|
| `dim_departamento` | `id_departamento` | Región → Departamento | Incluye la fila sentinela `id_departamento = 0` ("SIN DESAGREGAR (nacional)") para los agregados nacionales de `fact_dane_tic`. |
| `dim_municipio` | `id_municipio` | Departamento → Municipio | Construida combinando los municipios distintos de `fact_gestores` y `fact_encuesta_ns` (este último siempre en Norte de Santander). |
| `dim_anio` | `id_anio` (= año) | Década → Año | `decada` se calcula a partir del año. |

## Tablas de hechos

| Tabla | Grano | Filas |
|---|---|---|
| `fact_gestores` | 1 instalación de gestor registrada (IDEAM) | 377 |
| `fact_encuesta_ns` | 1 persona encuestada (Norte de Santander) | 1 917 |
| `fact_dane_tic` | 1 observación de indicador TIC por dominio/año | 960 |
| `fact_reciclaje_global` | 1 observación de % reciclado por área/año | 637 |

Las medidas, su unidad, fórmula y función de agregación (additiva, semiadditiva
o no additiva) están documentadas en el informe técnico de esta etapa
(`static/etapa5/informe_tecnico.pdf`, sección "Granularidad, dimensiones,
atributos, claves, medidas y jerarquías") y como comentarios en
`rect_olap.py`.

## Consultas OLAP

El módulo `rect_olap.py` (raíz del proyecto) implementa las 5 operaciones
multidimensionales (drill-down, roll-up, slice, dice, pivot) como funciones
Python que arman SQL parametrizado según los filtros recibidos desde las
vistas Flask de `/etapa-5/<slug>`. No hay valores precalculados ni
simulados: cada consulta se ejecuta contra `rect_estrella.db` en el momento
en que se solicita la página.
