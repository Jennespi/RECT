from pathlib import Path

from flask import Flask, render_template, abort, request, send_from_directory

import rect_olap as olap

app = Flask(__name__)

DATOS_PROCESADOS = Path(__file__).resolve().parent / "datos" / "procesados"
ETAPA_3_ASSETS = Path(__file__).resolve().parent / "static" / "etapa3"
INFORME_PDF = ETAPA_3_ASSETS / "informe_tecnico.pdf"
ETAPA_5_ASSETS = Path(__file__).resolve().parent / "static" / "etapa5"
INFORME_PDF_5 = ETAPA_5_ASSETS / "informe_tecnico.pdf"

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

# Etapa 3 — Tratamiento de datos con SSIS
ETAPA_3 = {
    "codigo": "R3",
    "numero": 3,
    "titulo": "Tratamiento de datos — ETL con SSIS",
    "subtitulo": "Tratamiento de datos con SSIS",
    "endpoint": "etapa3",
    "video_youtube_id": "SM41JHEF8cE",
    "objetivo": (
        "Implementar y verificar un proceso ETL mediante SQL Server Integration "
        "Services (SSIS) para tratar los problemas de calidad identificados en la "
        "Etapa 2, mediante tres iteraciones documentadas, y publicar el informe "
        "técnico y el video de demostración en la aplicación."
    ),
    "sections": [
        {"slug": "objetivo", "num": 1, "label": "Objetivo y alcance"},
        {"slug": "resultados", "num": 2, "label": "Resultados y comparación de las iteraciones"},
        {"slug": "informe", "num": 3, "label": "Informe técnico"},
        {"slug": "video", "num": 4, "label": "Video de demostración"},
    ],
}

# Etapa 4 — Conocimiento evidente
ETAPA_4 = {
    "codigo": "R4",
    "numero": 4,
    "titulo": "Conocimiento evidente — Análisis exploratorio con Power BI",
    "subtitulo": "Conocimiento evidente",
    "endpoint": "etapa4",
    "objetivo": (
        "Realizar un análisis exploratorio del conjunto de datos que el equipo viene "
        "trabajando en su proyecto de minería de datos, para identificar conocimientos "
        "evidentes mediante indicadores, comparaciones y visualizaciones. Los "
        "resultados deben presentarse en tableros de Power BI e integrarse en la "
        "aplicación web del proyecto."
    ),
    # URL de "Publicar en la Web" de Power BI.
    "powerbi_embed_url": "https://app.powerbi.com/view?r=eyJrIjoiNjI5OWJmMDgtYTQzZS00NjE2LWIzZmYtZTUzZDhhOTJlMWZiIiwidCI6IjA3ZGE2N2EwLTFmNDMtNGU4Yy05NzdmLTVmODhiNjQ3MGVlNiIsImMiOjR9",
    # Enlace alternativo, si la licencia no permite insertar el informe.
    "powerbi_link_url": None,
    "sections": [
        {"slug": "objetivo", "num": 1, "label": "Objetivo y alcance"},
        {"slug": "modelo", "num": 2, "label": "Modelo de datos"},
        {"slug": "powerbi", "num": 3, "label": "Informe de Power BI"},
    ],
}

# Etapa 5 — Análisis multidimensional
ETAPA_5 = {
    "codigo": "R5",
    "numero": 5,
    "titulo": "Análisis multidimensional — Modelo estrella y OLAP",
    "subtitulo": "Análisis multidimensional",
    "endpoint": "etapa5",
    "objetivo": (
        "Diseñar e implementar un modelo multidimensional (constelación de hechos "
        "con dimensiones conformadas) sobre los datos tratados del proyecto RECT, "
        "consultable desde SQLite, y construir cuatro vistas interactivas en Flask "
        "que permitan explorar los resultados mediante operaciones de drill-down, "
        "roll-up, slice, dice y pivot, documentando los conocimientos "
        "multidimensionales que de ellas se derivan."
    ),
    "sections": [
        {"slug": "objetivo", "num": 1, "label": "Objetivo y alcance"},
        {"slug": "modelo", "num": 2, "label": "Modelo estrella"},
        {"slug": "tablas", "num": 3, "label": "Explorar las tablas"},
        {"slug": "composicion", "num": 4, "label": "Vista 1 · Composición"},
        {"slug": "territorial", "num": 5, "label": "Vista 2 · Territorial"},
        {"slug": "temporal", "num": 6, "label": "Vista 3 · Temporal"},
        {"slug": "multivariado", "num": 7, "label": "Vista 4 · Multivariado"},
        {"slug": "conclusiones", "num": 8, "label": "Conocimientos y conclusiones"},
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
    {
        "codigo": "R3",
        "titulo": ETAPA_3["titulo"],
        "descripcion": ETAPA_3["objetivo"],
        "endpoint": ETAPA_3["endpoint"],
        "primer_slug": ETAPA_3["sections"][0]["slug"],
        "disponible": True,
    },
    {
        "codigo": "R4",
        "titulo": ETAPA_4["titulo"],
        "descripcion": ETAPA_4["objetivo"],
        "endpoint": ETAPA_4["endpoint"],
        "primer_slug": ETAPA_4["sections"][0]["slug"],
        "disponible": True,
    },
    {
        "codigo": "R5",
        "titulo": ETAPA_5["titulo"],
        "descripcion": ETAPA_5["objetivo"],
        "endpoint": ETAPA_5["endpoint"],
        "primer_slug": ETAPA_5["sections"][0]["slug"],
        "disponible": True,
    },
]


def _render_etapa(etapa, slug, **extra):
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
        **extra,
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


@app.route("/etapa-3/<slug>")
def etapa3(slug):
    return _render_etapa(
        ETAPA_3,
        slug,
        informe_pdf_existe=INFORME_PDF.exists(),
    )


@app.route("/etapa-4/<slug>")
def etapa4(slug):
    return _render_etapa(ETAPA_4, slug)


@app.route("/etapa-5/<slug>")
def etapa5(slug):
    extra = {"informe_pdf_existe": INFORME_PDF_5.exists()}

    if slug == "tablas":
        tablas = olap.listar_tablas()
        nombre = request.args.get("tabla") or (tablas[0]["nombre"] if tablas else None)
        extra["tablas"] = tablas
        extra["tabla_actual"] = nombre
        extra["preview"] = olap.previsualizar_tabla(nombre) if nombre else None

    elif slug == "territorial":
        nivel = request.args.get("nivel", "departamento")
        region = request.args.get("region") or None
        departamento = request.args.get("departamento") or None
        estado = request.args.get("estado", "ACTIVO")
        if estado == "TODOS":
            estado = None
        extra["cubo"] = olap.cubo_territorial(nivel=nivel, region=region, departamento=departamento, estado=estado)
        extra["matriz"] = olap.matriz_territorial(nivel=nivel, region=region, departamento=departamento)
        extra["regiones"] = olap.valores_distintos("dim_departamento", "region")
        extra["departamentos"] = olap.valores_distintos("dim_departamento", "departamento")
        activos = olap.cubo_territorial(nivel="departamento", estado="ACTIVO")
        extra["indicadores"] = [
            {"valor": activos["total"], "etiqueta": "Instalaciones ACTIVAS (nacional)"},
            {"valor": sum(1 for f in activos["filas"] if f["instalaciones"] > 0),
             "etiqueta": "Departamentos con cobertura activa"},
            {"valor": f"{round(100 * sum(f['instalaciones'] for f in activos['filas'][:5]) / activos['total'], 1)} %"
             if activos["total"] else "0 %", "etiqueta": "Participación del top 5 departamentos"},
        ]

    elif slug == "temporal":
        nivel = request.args.get("nivel", "anio")
        fuente = request.args.get("fuente", "gestores")
        extra["cubo"] = olap.cubo_temporal(nivel=nivel, fuente=fuente)
        extra["matriz"] = olap.matriz_temporal()
        gestores_total = olap.cubo_temporal(nivel="decada", fuente="gestores")["filas"]
        dane_dec = olap.cubo_temporal(nivel="decada", fuente="dane")["filas"]
        recic_dec = olap.cubo_temporal(nivel="decada", fuente="reciclaje")["filas"]
        extra["indicadores"] = [
            {"valor": sum(f["valor"] for f in gestores_total), "etiqueta": "Autorizaciones otorgadas (2005-2025)"},
            {"valor": f"{dane_dec[-1]['valor']} %" if dane_dec else "—",
             "etiqueta": f"% hogares con internet ({dane_dec[-1]['etiqueta']})" if dane_dec else "% hogares con internet"},
            {"valor": f"{recic_dec[-1]['valor']} %" if recic_dec else "—",
             "etiqueta": f"% RAEE reciclado mundial ({recic_dec[-1]['etiqueta']})" if recic_dec else "% RAEE reciclado mundial"},
        ]

    elif slug == "composicion":
        zona = request.args.get("zona") or None
        tiene_raee = request.args.get("tiene_raee", "NO")
        if tiene_raee == "TODOS":
            tiene_raee = None
        fila = request.args.get("fila", "ocupacion")
        columna = request.args.get("columna", "canal_formal")
        cubo = olap.cubo_composicion(fila=fila, columna=columna, zona=zona, tiene_raee=tiene_raee)
        extra["cubo"] = cubo
        extra["matriz"] = olap.pivotear(cubo["filas"], "encuestados")
        extra["zonas"] = olap.valores_distintos("fact_encuesta_ns", "zona")
        canal_formal = sum(r["encuestados"] for r in cubo["filas"] if r.get("columna") == "Usa canal formal" or r.get("fila") == "Usa canal formal")
        extra["indicadores"] = [
            {"valor": cubo["total"], "etiqueta": "Encuestados en la selección"},
            {"valor": f"{round(100 * canal_formal / cubo['total'], 1)} %" if cubo["total"] else "0 %",
             "etiqueta": "% que usa canal formal"},
            {"valor": len({r["fila"] for r in cubo["filas"]}), "etiqueta": f"Categorías distintas de {fila}"},
        ]

    elif slug == "multivariado":
        sabe_raee = request.args.get("sabe_raee") or None
        participo_jornada = request.args.get("participo_jornada") or None
        zona = request.args.get("zona") or None
        fila = request.args.get("fila", "canal_formal")
        columna = request.args.get("columna", "usaria_app_raee")
        cubo = olap.cubo_multivariado(sabe_raee=sabe_raee, participo_jornada=participo_jornada,
                                       zona=zona, fila=fila, columna=columna)
        extra["cubo"] = cubo
        extra["matriz"] = olap.pivotear(cubo["filas"], "encuestados")
        extra["zonas"] = olap.valores_distintos("fact_encuesta_ns", "zona")
        total = cubo["total"] or 1
        canal_formal = sum(r["encuestados"] for r in cubo["filas"] if r.get("fila") == "Usa canal formal")
        usaria_si = sum(r["encuestados"] for r in cubo["filas"] if r.get("columna") == "Sí")
        extra["indicadores"] = [
            {"valor": cubo["total"], "etiqueta": "Encuestados en la selección (dice)"},
            {"valor": f"{round(100 * canal_formal / total, 1)} %", "etiqueta": "% que usa canal formal"},
            {"valor": f"{round(100 * usaria_si / total, 1)} %", "etiqueta": "% que usaría una app para RAEE"},
        ]

    return _render_etapa(ETAPA_5, slug, **extra)


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
