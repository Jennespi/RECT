"""
Proyecto RECT - Etapa 5 (Modelo multidimensional)
Carga reproducible del modelo estrella en SQLite.

Toma las tablas ya tratadas y homologadas en la Etapa 4
(datos/powerbi/*.csv, generadas por scripts/preparar_datos_pbi.py a partir
de datos/procesados/) y las carga en datos/estrella/rect_estrella.db según
el esquema de scripts/esquema_estrella.sql: dimensiones conformadas
(dim_departamento, dim_municipio, dim_anio) y cuatro tablas de hechos
(fact_gestores, fact_encuesta_ns, fact_dane_tic, fact_reciclaje_global).

Correspondencia de variables originales -> campos del modelo: cada columna
de datos/powerbi/*.csv ya documenta en scripts/preparar_datos_pbi.py su
origen en datos/procesados/ (Etapa 2/3). Este script añade únicamente las
claves subrogadas (id_departamento, id_municipio, id_anio) y la jerarquía
temporal (decada), sin modificar ningún valor de negocio.

Uso:  python construir_modelo_estrella.py [carpeta_powerbi] [archivo_db]
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
PBI = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "datos" / "powerbi"
DB = Path(sys.argv[2]) if len(sys.argv) > 2 else RAIZ / "datos" / "estrella" / "rect_estrella.db"
ESQUEMA = Path(__file__).resolve().parent / "esquema_estrella.sql"

DB.parent.mkdir(parents=True, exist_ok=True)
if DB.exists():
    DB.unlink()  # recarga completa: procedimiento reproducible, no incremental

con = sqlite3.connect(DB)
con.executescript(ESQUEMA.read_text(encoding="utf-8"))
con.execute("PRAGMA foreign_keys = ON")

# --------------------------------------------------------- dim_departamento
dep = pd.read_csv(PBI / "dim_departamento.csv")
dep.insert(0, "id_departamento", range(1, len(dep) + 1))
# Fila sentinela para agregados nacionales (fact_dane_tic sin departamento)
dep_sentinela = pd.DataFrame([{
    "id_departamento": 0, "departamento": "SIN DESAGREGAR (nacional)",
    "cod_divipola": None, "region": None,
}])
dep_full = pd.concat([dep_sentinela, dep], ignore_index=True)
dep_full.to_sql("dim_departamento", con, if_exists="append", index=False)
id_dep = dict(zip(dep_full.departamento, dep_full.id_departamento))

# --------------------------------------------------------------- dim_anio
anio = pd.read_csv(PBI / "dim_anio.csv")
anio["decada"] = (anio.anio // 10 * 10).astype(str) + "s"
anio.insert(0, "id_anio", anio.anio)
anio.to_sql("dim_anio", con, if_exists="append", index=False)
anios_validos = set(anio.anio)

# ------------------------------------------------------------ dim_municipio
# Municipios de gestores (con su departamento real) + municipios de la
# encuesta (todos en Norte de Santander).
g_src = pd.read_csv(PBI / "fact_gestores.csv")
s_src = pd.read_csv(PBI / "fact_encuesta_ns.csv")
muni_g = g_src[["municipio", "departamento"]].drop_duplicates()
muni_s = s_src[["municipio"]].drop_duplicates()
muni_s["departamento"] = "NORTE DE SANTANDER"
muni = pd.concat([muni_g, muni_s], ignore_index=True).drop_duplicates()
muni = muni.dropna(subset=["municipio", "departamento"])
muni.insert(0, "id_municipio", range(1, len(muni) + 1))
muni_tabla = muni.rename(columns={"departamento": "departamento_nombre"})
muni_tabla["id_departamento"] = muni_tabla.departamento_nombre.map(id_dep)
muni_tabla[["id_municipio", "municipio", "id_departamento"]].to_sql(
    "dim_municipio", con, if_exists="append", index=False
)
id_muni = {
    (r.municipio, r.departamento_nombre): r.id_municipio for r in muni_tabla.itertuples()
}

# ---------------------------------------------------------- fact_gestores
g = g_src.copy()
g["id_municipio"] = [id_muni.get((m, d)) for m, d in zip(g.municipio, g.departamento)]
g["id_anio"] = g.anio_otorgamiento.where(g.anio_otorgamiento.isin(anios_validos))
g["id_anio"] = g["id_anio"].astype("Int64")
cols_g = ["id_registro", "nit", "empresa", "establecimiento", "id_municipio", "autoridad",
          "estado", "latitud", "longitud", "fecha_otorgamiento", "id_anio", "tiene_vigencia",
          "tipo_gestion_declarada", "declara_respel", "declara_raee", "registros_mismo_nit"]
g[cols_g].to_sql("fact_gestores", con, if_exists="append", index=False)

# ------------------------------------------------------- fact_encuesta_ns
s = s_src.copy()
s["id_municipio"] = [id_muni.get((m, "NORTE DE SANTANDER")) for m in s.municipio]
cols_s = ["id_encuestado", "id_municipio", "ocupacion", "zona", "tiene_residuos", "sabe_raee",
          "participo_jornada", "medio_enterado", "usa_apps", "usaria_app_raee", "usaria_app_si",
          "canal_entrega", "canal_formal", "entrega_punto_autorizado", "entrega_empresa_aseo",
          "entrega_reciclador", "entrega_regala", "deja_en_casa", "entrega_basura"]
s[cols_s].to_sql("fact_encuesta_ns", con, if_exists="append", index=False)

# --------------------------------------------------------- fact_dane_tic
d = pd.read_csv(PBI / "fact_dane_tic.csv")
d["id_departamento"] = d.departamento.map(id_dep).fillna(0).astype(int)
d["id_anio"] = d.anio.where(d.anio.isin(anios_validos))
cols_d = ["dominio", "id_departamento", "id_anio", "fuente", "indicador", "indicador_nombre",
          "valor", "unidad"]
d[cols_d].to_sql("fact_dane_tic", con, if_exists="append", index=False)

# ------------------------------------------------------ fact_reciclaje_global
r = pd.read_csv(PBI / "fact_reciclaje_global.csv")
r["id_anio"] = r.anio.where(r.anio.isin(anios_validos))
cols_r = ["area", "tipo_area", "id_anio", "pct_reciclado"]
r[cols_r].to_sql("fact_reciclaje_global", con, if_exists="append", index=False)

con.commit()

print("Modelo estrella cargado en", DB)
for t in ["dim_departamento", "dim_municipio", "dim_anio", "fact_gestores",
          "fact_encuesta_ns", "fact_dane_tic", "fact_reciclaje_global"]:
    n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t:24s} {n:>6} filas")
con.close()
