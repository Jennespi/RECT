# RECT — Residuos electrónicos y consumo tecnológico

Bitácora técnica del proyecto de Minería de Datos: cómo se relaciona el crecimiento del
consumo tecnológico en los hogares con la capacidad de gestión formal de los residuos
electrónicos (RAEE), a nivel global, nacional (Colombia) y regional (Norte de Santander).

Aplicación Flask que documenta cada entrega del proyecto — problema, datos, calidad,
análisis — a medida que avanza.

**App publicada:** [rect-tfdr.onrender.com](https://rect-tfdr.onrender.com/)

## Integrantes

- Jennifer Espitia
- Richard Barajas
- Cristian Leonardo Moscoso

## Entregas

| Código | Título | Rama |
|---|---|---|
| R1 | Del problema a los datos | `feature/etapa-1` |
| R2 | Entender datos — Diagnóstico y Calidad de los Datos | `feature/etapa-2` |

Cada entrega tiene su propio menú dentro de la app (ver `/`).

## Datos

- `datos/originales/` — descargas tal cual, sin modificar (trazabilidad).
- `datos/procesados/` — dataset consolidado (4 archivos, 82 059 registros), descargable
  desde la vista **Dataset** de la app.
- Detalle de fuentes, transformaciones y notas de calidad en [`datos/README.md`](datos/README.md).

## Cómo correr en local

```bash
pip install -r requirements.txt
python app.py
```

Abre `http://127.0.0.1:5000`.

## Estructura

```
app.py                  rutas y configuración de las entregas
templates/
  layout.html            esqueleto común (head, footer)
  base.html               header + menú de una entrega
  home.html                página de inicio (tarjetas de entregas)
  etapa1/                  vistas de R1
  etapa2/                  vistas de R2
static/                 CSS y JS
datos/                  originales y procesados, con su propio README
```

## Despliegue

Servido con Gunicorn (`Procfile`). Rama de despliegue: `main`.
