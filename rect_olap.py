"""
Proyecto RECT - Etapa 5 (Modelo multidimensional)
Capa de consultas OLAP sobre el modelo estrella (datos/estrella/rect_estrella.db).

Implementa las cinco operaciones de análisis multidimensional que pide la
guía -drill-down, roll-up, slice, dice y pivot- como funciones Python que
arman y ejecutan SQL parametrizado sobre las tablas de hechos y las
dimensiones conformadas (dim_departamento, dim_municipio, dim_anio). Cada
función recalcula las medidas desde la tabla de hechos en cada llamada: no
hay resultados cacheados ni gráficas que solo cambian de tipo visual.

Una función por vista/pregunta de análisis (ver app.py, sección ETAPA_5):
  - cubo_territorial   (Vista 2 - Territorial): drill-down / roll-up sobre
    la jerarquía Región -> Departamento -> Municipio.
  - cubo_temporal      (Vista 3 - Temporal): drill-down / roll-up sobre la
    jerarquía Década -> Año.
  - cubo_composicion   (Vista 1 - Composición): slice y pivot sobre
    ocupación, zona y canal de entrega.
  - cubo_multivariado  (Vista 4 - Multivariado): dice (filtro combinado
    sobre 2+ dimensiones) y pivot.

Todas devuelven dict con: 'filas' (resultado agregado), 'medida', 'nivel'
y los parámetros efectivamente aplicados, para que las plantillas de Flask
muestren con claridad qué filtro/nivel generó cada resultado.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "datos" / "estrella" / "rect_estrella.db"

NIVELES_TERRITORIO = ["region", "departamento", "municipio"]
NIVELES_TIEMPO = ["decada", "anio"]


def conectar():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


# ============================================================ VISTA 2 =====
# Territorial — Drill-down / Roll-up sobre Región -> Departamento -> Municipio
def cubo_territorial(nivel="departamento", region=None, departamento=None, estado="ACTIVO"):
    """
    nivel: 'region' (roll-up más alto), 'departamento' (nivel por defecto,
           igual al tablero de la Etapa 4) o 'municipio' (drill-down más
           detallado). Medida: conteo de instalaciones de gestores
           (additivo: COUNT(*) es correcto en los tres niveles porque el
           grano de fact_gestores es 1 fila = 1 instalación).
    region / departamento: filtros de slice/dice para acotar el drill-down
           (p. ej. ver solo los municipios de un departamento).
    estado: 'ACTIVO', 'INACTIVO' o None (todas).
    """
    if nivel not in NIVELES_TERRITORIO:
        nivel = "departamento"
    cols = {
        "region": "d.region AS etiqueta",
        "departamento": "d.departamento AS etiqueta",
        "municipio": "m.municipio AS etiqueta",
    }
    group_by = {"region": "d.region", "departamento": "d.departamento", "municipio": "m.municipio"}

    where, params = ["f.id_municipio IS NOT NULL"], []
    if estado:
        where.append("f.estado = ?")
        params.append(estado)
    if region:
        where.append("d.region = ?")
        params.append(region)
    if departamento:
        where.append("d.departamento = ?")
        params.append(departamento)

    sql = f"""
        SELECT {cols[nivel]},
               COUNT(*) AS instalaciones,
               COUNT(DISTINCT f.nit) AS empresas_distintas
        FROM fact_gestores f
        JOIN dim_municipio m ON f.id_municipio = m.id_municipio
        JOIN dim_departamento d ON m.id_departamento = d.id_departamento
        WHERE {' AND '.join(where)}
        GROUP BY {group_by[nivel]}
        ORDER BY instalaciones DESC
    """
    con = conectar()
    filas = [dict(r) for r in con.execute(sql, params)]
    total = con.execute(
        f"""SELECT COUNT(*) FROM fact_gestores f JOIN dim_municipio m ON f.id_municipio = m.id_municipio
            JOIN dim_departamento d ON m.id_departamento = d.id_departamento WHERE {' AND '.join(where)}""",
        params,
    ).fetchone()[0]
    con.close()
    return {
        "filas": filas, "nivel": nivel, "medida": "Instalaciones de gestores (COUNT)",
        "total": total, "filtros": {"region": region, "departamento": departamento, "estado": estado},
    }


# ============================================================= VISTA 3 =====
# Temporal — Drill-down / Roll-up sobre Década -> Año
def cubo_temporal(nivel="anio", fuente="gestores", anio_desde=None, anio_hasta=None):
    """
    nivel: 'decada' (roll-up) o 'anio' (drill-down, nivel por defecto).
    fuente: 'gestores' (autorizaciones otorgadas, additivo COUNT),
            'dane' (indicador DANE ECV: % hogares con internet, promedio
            porque es un porcentaje: no puede sumarse entre años),
            'reciclaje' (% RAEE reciclado mundial, promedio por el mismo motivo).
    """
    if nivel not in NIVELES_TIEMPO:
        nivel = "anio"
    con = conectar()
    etiqueta = "a.decada AS etiqueta" if nivel == "decada" else "a.anio AS etiqueta"
    group_by = "a.decada" if nivel == "decada" else "a.anio"

    where, params = [], []
    if anio_desde:
        where.append("a.anio >= ?"); params.append(anio_desde)
    if anio_hasta:
        where.append("a.anio <= ?"); params.append(anio_hasta)
    clausula_where = f"WHERE {' AND '.join(where)}" if where else ""

    if fuente == "gestores":
        sql = f"""
            SELECT {etiqueta}, COUNT(*) AS valor
            FROM fact_gestores f JOIN dim_anio a ON f.id_anio = a.id_anio
            {clausula_where}
            GROUP BY {group_by} ORDER BY {group_by}
        """
        medida = "Autorizaciones otorgadas a gestores (COUNT, additiva)"
    elif fuente == "dane":
        sql = f"""
            SELECT {etiqueta}, ROUND(AVG(f.valor), 2) AS valor
            FROM fact_dane_tic f JOIN dim_anio a ON f.id_anio = a.id_anio
            WHERE f.indicador = 'pct_hogares_internet_v2' AND f.dominio = 'Total nacional'
            {(' AND ' + ' AND '.join(where)) if where else ''}
            GROUP BY {group_by} ORDER BY {group_by}
        """
        medida = "% hogares con internet, ECV (AVG, no additiva: es un porcentaje)"
    else:  # reciclaje
        sql = f"""
            SELECT {etiqueta}, ROUND(AVG(f.pct_reciclado), 2) AS valor
            FROM fact_reciclaje_global f JOIN dim_anio a ON f.id_anio = a.id_anio
            WHERE f.area = 'World'
            {(' AND ' + ' AND '.join(where)) if where else ''}
            GROUP BY {group_by} ORDER BY {group_by}
        """
        medida = "% RAEE reciclado, mundial (AVG, no additiva: es un porcentaje)"

    filas = [dict(r) for r in con.execute(sql, params)]
    con.close()
    return {"filas": filas, "nivel": nivel, "fuente": fuente, "medida": medida,
            "filtros": {"anio_desde": anio_desde, "anio_hasta": anio_hasta}}


# ============================================================= VISTA 1 =====
# Composición — Slice y Pivot sobre ocupación / zona / canal de entrega
def cubo_composicion(fila="ocupacion", columna="canal_formal", zona=None, tiene_raee="NO"):
    """
    fila / columna: nombres de columna de fact_encuesta_ns usados como ejes
           de la matriz (pivot: intercambiar fila <-> columna reordena la
           misma consulta sin cambiar el resultado agregado).
    zona: slice opcional ('Cúcuta', 'Área metropolitana', 'Resto del
          departamento' o None para todas las zonas).
    tiene_raee: slice sobre tiene_residuos ('SI'/'NO'/None). Por defecto
          'NO' replica la selección documentada en la Etapa 4 (personas sin
          RAEE en casa en el momento de la encuesta).
    """
    columnas_validas = {"ocupacion", "zona", "canal_formal", "sabe_raee", "participo_jornada"}
    if fila not in columnas_validas:
        fila = "ocupacion"
    if columna not in columnas_validas:
        columna = "canal_formal"

    where, params = [], []
    if zona:
        where.append("zona = ?"); params.append(zona)
    if tiene_raee:
        where.append("tiene_residuos = ?"); params.append(tiene_raee)
    clausula_where = f"WHERE {' AND '.join(where)}" if where else ""

    con = conectar()
    total = con.execute(f"SELECT COUNT(*) FROM fact_encuesta_ns {clausula_where}", params).fetchone()[0]
    matriz = con.execute(f"""
        SELECT {fila} AS fila, {columna} AS columna, COUNT(*) AS encuestados
        FROM fact_encuesta_ns {clausula_where}
        GROUP BY {fila}, {columna} ORDER BY {fila}, encuestados DESC
    """, params).fetchall()
    con.close()
    return {
        "filas": [dict(r) for r in matriz], "fila_eje": fila, "columna_eje": columna,
        "total": total, "medida": "Encuestados (COUNT)",
        "filtros": {"zona": zona, "tiene_residuos": tiene_raee},
    }


# ============================================================= VISTA 4 =====
# Multivariado — Dice (filtro combinado) y Pivot
def cubo_multivariado(sabe_raee=None, participo_jornada=None, zona=None,
                       fila="canal_formal", columna="usaria_app_raee"):
    """
    sabe_raee / participo_jornada / zona: hasta tres filtros simultáneos
           sobre dimensiones distintas (dice real: no es un único slice).
    fila / columna: ejes de la matriz final (pivot).
    """
    columnas_validas = {"canal_formal", "usaria_app_raee", "ocupacion", "zona", "sabe_raee", "participo_jornada"}
    if fila not in columnas_validas:
        fila = "canal_formal"
    if columna not in columnas_validas:
        columna = "usaria_app_raee"

    where, params = [], []
    if sabe_raee:
        where.append("sabe_raee = ?"); params.append(sabe_raee)
    if participo_jornada:
        where.append("participo_jornada = ?"); params.append(participo_jornada)
    if zona:
        where.append("zona = ?"); params.append(zona)
    clausula_where = f"WHERE {' AND '.join(where)}" if where else ""

    con = conectar()
    total = con.execute(f"SELECT COUNT(*) FROM fact_encuesta_ns {clausula_where}", params).fetchone()[0]
    matriz = con.execute(f"""
        SELECT {fila} AS fila, {columna} AS columna, COUNT(*) AS encuestados,
               ROUND(100.0 * SUM(CASE WHEN canal_formal = 'Usa canal formal' THEN 1 ELSE 0 END) / COUNT(*), 1)
                   AS pct_canal_formal
        FROM fact_encuesta_ns {clausula_where}
        GROUP BY {fila}, {columna} ORDER BY {fila}, encuestados DESC
    """, params).fetchall()
    con.close()
    return {
        "filas": [dict(r) for r in matriz], "fila_eje": fila, "columna_eje": columna,
        "total": total, "medida": "Encuestados (COUNT) y % que usa canal formal (proporción)",
        "filtros": {"sabe_raee": sabe_raee, "participo_jornada": participo_jornada, "zona": zona},
    }


# --------------------------------------------- matrices (una por vista) ---
def matriz_territorial(nivel="departamento", region=None, departamento=None, limite=12):
    """Matriz que cruza el nivel territorial vigente con el estado de la
    instalación (ACTIVO / INACTIVO), independiente del filtro de estado que
    se use para los indicadores — para que la matriz siempre muestre ambos
    estados a la vez."""
    if nivel not in NIVELES_TERRITORIO:
        nivel = "departamento"
    cols = {"region": "d.region AS etiqueta", "departamento": "d.departamento AS etiqueta",
            "municipio": "m.municipio AS etiqueta"}
    group_by = {"region": "d.region", "departamento": "d.departamento", "municipio": "m.municipio"}
    where, params = ["1=1"], []
    if region:
        where.append("d.region = ?"); params.append(region)
    if departamento:
        where.append("d.departamento = ?"); params.append(departamento)
    sql = f"""
        SELECT {cols[nivel]},
               SUM(CASE WHEN f.estado = 'ACTIVO' THEN 1 ELSE 0 END) AS "ACTIVO",
               SUM(CASE WHEN f.estado = 'INACTIVO' THEN 1 ELSE 0 END) AS "INACTIVO",
               COUNT(*) AS total
        FROM fact_gestores f
        JOIN dim_municipio m ON f.id_municipio = m.id_municipio
        JOIN dim_departamento d ON m.id_departamento = d.id_departamento
        WHERE {' AND '.join(where)}
        GROUP BY {group_by[nivel]} ORDER BY total DESC LIMIT {int(limite)}
    """
    con = conectar()
    filas = [dict(r) for r in con.execute(sql, params)]
    con.close()
    return {"filas": filas, "columnas": ["ACTIVO", "INACTIVO"], "nivel": nivel}


def matriz_temporal():
    """Matriz Década x indicador: cruza la misma jerarquía temporal con
    los tres indicadores de la vista (autorizaciones, % internet, %
    reciclaje), cada uno con su propia unidad y función de agregación."""
    con = conectar()
    autor = {r["etiqueta"]: r["valor"] for r in
             (dict(x) for x in con.execute(
                 "SELECT a.decada AS etiqueta, COUNT(*) AS valor FROM fact_gestores f "
                 "JOIN dim_anio a ON f.id_anio = a.id_anio GROUP BY a.decada"))}
    internet = {r["etiqueta"]: r["valor"] for r in
                (dict(x) for x in con.execute(
                    "SELECT a.decada AS etiqueta, ROUND(AVG(f.valor), 1) AS valor FROM fact_dane_tic f "
                    "JOIN dim_anio a ON f.id_anio = a.id_anio "
                    "WHERE f.indicador = 'pct_hogares_internet_v2' AND f.dominio = 'Total nacional' "
                    "GROUP BY a.decada"))}
    reciclaje = {r["etiqueta"]: r["valor"] for r in
                 (dict(x) for x in con.execute(
                     "SELECT a.decada AS etiqueta, ROUND(AVG(f.pct_reciclado), 1) AS valor FROM fact_reciclaje_global f "
                     "JOIN dim_anio a ON f.id_anio = a.id_anio WHERE f.area = 'World' GROUP BY a.decada"))}
    con.close()
    decadas = sorted(set(autor) | set(internet) | set(reciclaje))
    filas = [{
        "decada": d,
        "autorizaciones": autor.get(d),
        "pct_internet": internet.get(d),
        "pct_reciclaje": reciclaje.get(d),
    } for d in decadas]
    return {"filas": filas}


def pivotear(filas, campo_valor="encuestados"):
    """Convierte una lista de filas {'fila', 'columna', campo_valor: ...}
    (formato largo, el que devuelven cubo_composicion y cubo_multivariado)
    en una matriz ancha {filas, columnas, datos} lista para una tabla HTML.
    Esta es la operación de pivot: la misma consulta agregada, reordenada."""
    filas_unicas = sorted({r["fila"] for r in filas})
    columnas_unicas = sorted({r["columna"] for r in filas})
    datos = {f: {c: None for c in columnas_unicas} for f in filas_unicas}
    for r in filas:
        datos[r["fila"]][r["columna"]] = r[campo_valor]
    return {"filas": filas_unicas, "columnas": columnas_unicas, "datos": datos}


# ----------------------------------------------------------- utilidades ---
def valores_distintos(tabla, columna):
    """Lista de valores distintos de una columna, para poblar los <select>
    de filtros en las plantillas de Flask."""
    con = conectar()
    vals = [r[0] for r in con.execute(f"SELECT DISTINCT {columna} FROM {tabla} WHERE {columna} IS NOT NULL ORDER BY {columna}")]
    con.close()
    return vals
