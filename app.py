from flask import Flask, render_template, redirect, url_for, abort

app = Flask(__name__)

# Menú principal "Etapa 1" 
ETAPA_1 = [
    {"slug": "problema", "num": 1, "label": "Problema y contexto"},
    {"slug": "pregunta", "num": 2, "label": "Pregunta principal y preguntas secundarias"},
    {"slug": "necesidades", "num": 3, "label": "Necesidades de información"},
    {"slug": "fuentes", "num": 4, "label": "Fuentes de datos"},
    {"slug": "dataset", "num": 5, "label": "Dataset"},
    {"slug": "diccionario", "num": 6, "label": "Diccionario de datos"},
    {"slug": "calidad", "num": 7, "label": "Calidad inicial de los datos"},
    {"slug": "limitaciones", "num": 8, "label": "Limitaciones y consideraciones"},
]

_BY_SLUG = {s["slug"]: s for s in ETAPA_1}


@app.context_processor
def inject_nav():
    return {"etapa1_sections": ETAPA_1}


@app.route("/")
def index():
    return redirect(url_for("etapa1", slug=ETAPA_1[0]["slug"]))


@app.route("/etapa-1/<slug>")
def etapa1(slug):
    section = _BY_SLUG.get(slug)
    if section is None:
        abort(404)
    i = ETAPA_1.index(section)
    prev_s = ETAPA_1[i - 1] if i > 0 else None
    next_s = ETAPA_1[i + 1] if i < len(ETAPA_1) - 1 else None
    return render_template(
        f"etapa1/{slug}.html",
        current=slug,
        section=section,
        prev_s=prev_s,
        next_s=next_s,
    )


if __name__ == "__main__":
    app.run(debug=True)
