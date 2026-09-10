from pathlib import Path

from flask import Flask, render_template, abort, send_from_directory

app = Flask(__name__)

DATOS_PROCESADOS = Path(__file__).resolve().parent / "datos" / "procesados"

# Etapa 1 — Del problema a los datos
ETAPA_1 = {
    "codigo": "R1",
    "numero": 1,
    "titulo": "Del problema a los datos",
    "subtitulo": "Definición del problema y de los datos",
    "endpoint": "etapa1",
    "sections": [
        {"slug": "problema", "num": 1, "label": "Problema y contexto"},
        {"slug": "pregunta", "num": 2, "label": "Pregunta principal y preguntas secundarias"},
        {"slug": "necesidades", "num": 3, "label": "Necesidades de información"},
        {"slug": "fuentes", "num": 4, "label": "Fuentes de datos"},
        {"slug": "dataset", "num": 5, "label": "Dataset"},
        {"slug": "diccionario", "num": 6, "label": "Diccionario de datos"},
        {"slug": "calidad", "num": 7, "label": "Calidad inicial de los datos"},
        {"slug": "limitaciones", "num": 8, "label": "Limitaciones y consideraciones"},
    ],
}

# Etapa 2 — Entender datos
ETAPA_2 = {
    "codigo": "R2",
    "numero": 2,
    "titulo": "Entender datos — Diagnóstico y Calidad de los Datos",
    "subtitulo": "Calidad de datos",
    "endpoint": "etapa2",
    "objetivo": (
        "Aplicar los conceptos fundamentales de calidad de datos mediante el "
        "perfilamiento, diagnóstico, medición y tratamiento del conjunto de datos "
        "seleccionado, identificando problemas que puedan afectar su uso."
    ),
    "sections": [
        {"slug": "objetivo", "num": 1, "label": "Objetivo y alcance"},
        {"slug": "descripcion", "num": 2, "label": "Descripción del conjunto de datos"},
        {"slug": "perfilamiento", "num": 3, "label": "Resultados del perfilamiento"},
        {"slug": "dimensiones", "num": 4, "label": "Dimensiones y métricas evaluadas"},
        {"slug": "problemas", "num": 5, "label": "Problemas identificados"},
        {"slug": "tratamiento", "num": 6, "label": "Acciones de tratamiento aplicadas"},
        {"slug": "comparacion", "num": 7, "label": "Comparación antes y después"},
        {"slug": "indicadores", "num": 8, "label": "Gráficas, tablas e indicadores"},
    ],
}

# Tarjetas de la página de inicio
ENTREGAS = [
    {
        "codigo": "R1",
        "titulo": ETAPA_1["titulo"],
        "descripcion": (
            "Definición del problema, preguntas de investigación, necesidades de "
            "información, fuentes, dataset inicial, diccionario y diagnóstico de calidad."
        ),
        "endpoint": ETAPA_1["endpoint"],
        "primer_slug": ETAPA_1["sections"][0]["slug"],
        "disponible": True,
    },
    {
        "codigo": "R2",
        "titulo": ETAPA_2["titulo"],
        "descripcion": ETAPA_2["objetivo"],
        "endpoint": ETAPA_2["endpoint"],
        "primer_slug": ETAPA_2["sections"][0]["slug"],
        "disponible": True,
    },
]


def _render_etapa(etapa, slug):
    secs = etapa["sections"]
    section = next((s for s in secs if s["slug"] == slug), None)
    if section is None:
        abort(404)
    i = secs.index(section)
    return render_template(
        f"{etapa['endpoint']}/{slug}.html",
        etapa=etapa,
        section=section,
        current=slug,
        prev_s=secs[i - 1] if i > 0 else None,
        next_s=secs[i + 1] if i < len(secs) - 1 else None,
    )


@app.route("/")
def index():
    return render_template("home.html", entregas=ENTREGAS)


@app.route("/datos/procesados/<path:nombre>")
def descargar_dataset(nombre):
    return send_from_directory(DATOS_PROCESADOS, nombre, as_attachment=True)


@app.route("/etapa-1/<slug>")
def etapa1(slug):
    return _render_etapa(ETAPA_1, slug)


@app.route("/etapa-2/<slug>")
def etapa2(slug):
    return _render_etapa(ETAPA_2, slug)


if __name__ == "__main__":
    app.run(debug=True)
