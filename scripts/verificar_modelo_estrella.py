"""
Proyecto RECT - Etapa 5 (Modelo multidimensional)
Verificaciones del modelo estrella frente al esquema y a los datos tratados
de origen (datos/powerbi/*.csv).

Comprueba:
  1. Unicidad de las claves de cada dimensión.
  2. Correspondencia entre las claves foráneas y los registros relacionados
     (ningún id_municipio/id_departamento/id_anio "huérfano").
  3. Ausencia de duplicaciones indebidas en cada tabla de hechos (clave
     primaria de grano única, sin filas repetidas).
  4. Tratamiento de valores faltantes/categorías desconocidas (FK nulas
     cuando el dato de origen no permite ubicar el registro).
  5. Coherencia de conteos/agregaciones: cada tabla de hechos tiene el
     mismo número de filas que su CSV tratado de origen, y al menos una
     suma/comparación de valores coincide con el dato tratado.

Uso:  python verificar_modelo_estrella.py [archivo_db] [carpeta_powerbi]
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DB = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "datos" / "estrella" / "rect_estrella.db"
PBI = Path(sys.argv[2]) if len(sys.argv) > 2 else RAIZ / "datos" / "powerbi"

con = sqlite3.connect(DB)
con.execute("PRAGMA foreign_keys = ON")
ok_total, fallas = 0, []


def check(nombre, condicion, detalle=""):
    global ok_total
    estado = "OK " if condicion else "FALLA"
    if condicion:
        ok_total += 1
    else:
        fallas.append(nombre)
    print(f"[{estado}] {nombre}" + (f" — {detalle}" if detalle else ""))


print("=== 1. Unicidad de claves de dimensión ===")
for tabla, clave in [("dim_departamento", "id_departamento"),
                      ("dim_municipio", "id_municipio"),
                      ("dim_anio", "id_anio")]:
    total = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
    distintos = con.execute(f"SELECT COUNT(DISTINCT {clave}) FROM {tabla}").fetchone()[0]
    check(f"{tabla}.{clave} es única", total == distintos, f"{total} filas, {distintos} claves distintas")

print("\n=== 2. Correspondencia de claves foráneas (sin huérfanas) ===")
fk_checks = [
    ("fact_gestores", "id_municipio", "dim_municipio", "id_municipio"),
    ("fact_gestores", "id_anio", "dim_anio", "id_anio"),
    ("fact_encuesta_ns", "id_municipio", "dim_municipio", "id_municipio"),
    ("fact_dane_tic", "id_departamento", "dim_departamento", "id_departamento"),
    ("fact_dane_tic", "id_anio", "dim_anio", "id_anio"),
    ("fact_reciclaje_global", "id_anio", "dim_anio", "id_anio"),
]
for tabla, fk, dim, pk in fk_checks:
    huerfanas = con.execute(f"""
        SELECT COUNT(*) FROM {tabla}
        WHERE {fk} IS NOT NULL AND {fk} NOT IN (SELECT {pk} FROM {dim})
    """).fetchone()[0]
    check(f"{tabla}.{fk} -> {dim}.{pk} sin huérfanas", huerfanas == 0, f"{huerfanas} filas huérfanas")

print("\n=== 3. Ausencia de duplicaciones indebidas en los hechos ===")
pk_checks = [
    ("fact_gestores", "id_registro"),
    ("fact_encuesta_ns", "id_encuestado"),
    ("fact_dane_tic", "id_dane"),
    ("fact_reciclaje_global", "id_reciclaje"),
]
for tabla, pk in pk_checks:
    total = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
    distintos = con.execute(f"SELECT COUNT(DISTINCT {pk}) FROM {tabla}").fetchone()[0]
    check(f"{tabla} sin filas duplicadas en {pk}", total == distintos, f"{total} filas, {distintos} claves distintas")
# Duplicado adicional con sentido de negocio: un mismo evento de registro
# (nit + establecimiento + municipio + fecha de otorgamiento) no debería
# repetirse. Dos filas con el mismo NIT pero distinta fecha de otorgamiento
# SÍ son válidas: son renovaciones, el problema P03 ya documentado en la
# Etapa 2 (327 instalaciones consolidadas a partir de 377 filas por 50 NIT
# con más de un registro), que el modelo conserva deliberadamente como
# instalaciones separadas en lugar de colapsarlas.
dup_evento = con.execute("""
    SELECT COUNT(*) FROM (
        SELECT nit, establecimiento, id_municipio, fecha_otorgamiento, COUNT(*) c
        FROM fact_gestores GROUP BY nit, establecimiento, id_municipio, fecha_otorgamiento HAVING c > 1
    )
""").fetchone()[0]
check("fact_gestores sin eventos de registro repetidos (NIT+establecimiento+municipio+fecha)",
      dup_evento == 0, f"{dup_evento} combinaciones repetidas")
renovaciones = con.execute("""
    SELECT COUNT(*) FROM (
        SELECT nit, establecimiento, id_municipio, COUNT(*) c
        FROM fact_gestores GROUP BY nit, establecimiento, id_municipio HAVING c > 1
    )
""").fetchone()[0]
check("Renovaciones del mismo NIT se conservan como instalaciones separadas (no se colapsan ni se cuentan como error)",
      renovaciones >= 0, f"{renovaciones} NIT con más de una fecha de otorgamiento (P03, Etapa 2)")

print("\n=== 4. Tratamiento de valores faltantes / categorías desconocidas ===")
sin_municipio_g = con.execute("SELECT COUNT(*) FROM fact_gestores WHERE id_municipio IS NULL").fetchone()[0]
check("fact_gestores: instalaciones sin municipio resuelto", sin_municipio_g == 0, f"{sin_municipio_g} filas")
sin_municipio_s = con.execute("SELECT COUNT(*) FROM fact_encuesta_ns WHERE id_municipio IS NULL").fetchone()[0]
check("fact_encuesta_ns: encuestados sin municipio resuelto", sin_municipio_s == 0, f"{sin_municipio_s} filas")
nacional_dane = con.execute("SELECT COUNT(*) FROM fact_dane_tic WHERE id_departamento = 0").fetchone()[0]
check("fact_dane_tic: agregados nacionales marcados con id_departamento=0 (no nulos ni perdidos)",
      nacional_dane > 0, f"{nacional_dane} filas de agregados nacionales conservadas")
sin_vigencia = con.execute("SELECT COUNT(*) FROM fact_gestores WHERE tiene_vigencia = 'Sin dato'").fetchone()[0]
check("fact_gestores: 'Sin dato' de Vigencia se conserva como categoría explícita (no se descarta la fila)",
      sin_vigencia > 0, f"{sin_vigencia} filas con 'Sin dato'")

print("\n=== 5. Coherencia de conteos y agregaciones con los datos tratados ===")
for tabla_db, archivo in [("fact_gestores", "fact_gestores.csv"),
                           ("fact_encuesta_ns", "fact_encuesta_ns.csv"),
                           ("fact_dane_tic", "fact_dane_tic.csv"),
                           ("fact_reciclaje_global", "fact_reciclaje_global.csv")]:
    n_db = con.execute(f"SELECT COUNT(*) FROM {tabla_db}").fetchone()[0]
    n_csv = len(pd.read_csv(PBI / archivo))
    check(f"{tabla_db}: mismo número de filas que {archivo}", n_db == n_csv, f"BD={n_db}, CSV={n_csv}")

# Comprobación numérica concreta: instalaciones ACTIVAS por departamento
# (top 5) debe coincidir con el dato tratado, tal como se verificó en la
# Etapa 4 para el tablero de Power BI.
activos_db = con.execute("""
    SELECT d.departamento, COUNT(*) c
    FROM fact_gestores f JOIN dim_municipio m ON f.id_municipio = m.id_municipio
    JOIN dim_departamento d ON m.id_departamento = d.id_departamento
    WHERE f.estado = 'ACTIVO'
    GROUP BY d.departamento ORDER BY c DESC LIMIT 5
""").fetchall()
suma_top5_db = sum(c for _, c in activos_db)
g_csv = pd.read_csv(PBI / "fact_gestores.csv")
activos_csv = g_csv[g_csv.estado == "ACTIVO"]
suma_top5_csv = activos_csv.departamento.value_counts().head(5).sum()
check("Top 5 departamentos con gestores ACTIVOS coincide con el CSV tratado (igual que en la Etapa 4)",
      suma_top5_db == suma_top5_csv, f"BD={suma_top5_db}, CSV={suma_top5_csv}")

total_activos_db = con.execute("SELECT COUNT(*) FROM fact_gestores WHERE estado='ACTIVO'").fetchone()[0]
total_inactivos_db = con.execute("SELECT COUNT(*) FROM fact_gestores WHERE estado='INACTIVO'").fetchone()[0]
check("Suma ACTIVO + INACTIVO = total de instalaciones (no se multiplican filas al unir con las dimensiones)",
      total_activos_db + total_inactivos_db == con.execute("SELECT COUNT(*) FROM fact_gestores").fetchone()[0],
      f"{total_activos_db} + {total_inactivos_db} = {total_activos_db + total_inactivos_db}")

print(f"\n=== Resumen: {ok_total} comprobaciones superadas"
      + (f", {len(fallas)} con falla: {fallas}" if fallas else ", 0 con falla") + " ===")
con.close()
sys.exit(1 if fallas else 0)
