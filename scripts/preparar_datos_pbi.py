"""
Proyecto RECT - Etapa 4 (Conocimiento evidente)
Capa final de tratamiento para Power BI.

Toma los 4 archivos de datos/procesados/ (salida de las Etapas 2 y 3) y genera
tablas listas para un modelo estrella en Power BI:

  dim_departamento.csv   - 33 dominios departamentales homologados (+ código DIVIPOLA)
  dim_anio.csv           - años 2005-2025 (tabla de fechas compartida)
  fact_dane_tic.csv      - tenencia/uso TIC por departamento-año (DANE ENTIC y ECV)
  fact_gestores.csv      - una fila por instalación gestora autorizada (IDEAM)
  fact_encuesta_ns.csv   - una fila por encuestado único (Norte de Santander)
  fact_reciclaje_global.csv - % de RAEE reciclado por país/región-año (OWID)

Uso:  python preparar_datos_pbi.py <carpeta_entrada> <carpeta_salida>
"""
import sys, re, unicodedata
from pathlib import Path
import pandas as pd

ENT = Path(sys.argv[1] if len(sys.argv) > 1 else "datos/procesados")
SAL = Path(sys.argv[2] if len(sys.argv) > 2 else "datos/powerbi")
SAL.mkdir(parents=True, exist_ok=True)


def sin_tildes(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t))
    return "".join(c for c in t if not unicodedata.combining(c)).upper().strip()


# ---------------------------------------------------------------- departamentos
DEPTOS = {  # nombre canónico -> código DIVIPOLA
    "AMAZONAS": "91", "ANTIOQUIA": "05", "ARAUCA": "81", "ATLÁNTICO": "08",
    "BOGOTÁ D.C.": "11", "BOLÍVAR": "13", "BOYACÁ": "15", "CALDAS": "17",
    "CAQUETÁ": "18", "CASANARE": "85", "CAUCA": "19", "CESAR": "20",
    "CHOCÓ": "27", "CÓRDOBA": "23", "CUNDINAMARCA": "25", "GUAINÍA": "94",
    "GUAVIARE": "95", "HUILA": "41", "LA GUAJIRA": "44", "MAGDALENA": "47",
    "META": "50", "NARIÑO": "52", "NORTE DE SANTANDER": "54", "PUTUMAYO": "86",
    "QUINDÍO": "63", "RISARALDA": "66", "SAN ANDRÉS": "88", "SANTANDER": "68",
    "SUCRE": "70", "TOLIMA": "73", "VALLE DEL CAUCA": "76", "VAUPÉS": "97",
    "VICHADA": "99",
}
REGION = {  # regiones naturales (para segmentar)
    "Andina": ["ANTIOQUIA", "BOGOTÁ D.C.", "BOYACÁ", "CALDAS", "CUNDINAMARCA", "HUILA",
               "NORTE DE SANTANDER", "QUINDÍO", "RISARALDA", "SANTANDER", "TOLIMA"],
    "Caribe": ["ATLÁNTICO", "BOLÍVAR", "CESAR", "CÓRDOBA", "LA GUAJIRA", "MAGDALENA",
               "SUCRE", "SAN ANDRÉS"],
    "Pacífica": ["CAUCA", "CHOCÓ", "NARIÑO", "VALLE DEL CAUCA"],
    "Orinoquía": ["ARAUCA", "CASANARE", "META", "VICHADA"],
    "Amazonía": ["AMAZONAS", "CAQUETÁ", "GUAINÍA", "GUAVIARE", "PUTUMAYO", "VAUPÉS"],
}
REGION_DE = {d: r for r, ds in REGION.items() for d in ds}
CANON = {sin_tildes(d): d for d in DEPTOS}
CANON.update({"VALLE": "VALLE DEL CAUCA",
              "ARCHIPIELAGO DE SAN ANDRES, PROVIDENCIA Y SANTA CATALINA": "SAN ANDRÉS",
              "BOGOTA": "BOGOTÁ D.C.", "BOGOTA, D.C.": "BOGOTÁ D.C."})


def homologar_depto(x):
    return CANON.get(sin_tildes(x))


dim = pd.DataFrame({"departamento": list(DEPTOS), "cod_divipola": list(DEPTOS.values())})
dim["region"] = dim.departamento.map(REGION_DE)
dim.to_csv(SAL / "dim_departamento.csv", index=False, encoding="utf-8-sig")

pd.DataFrame({"anio": range(2005, 2026)}).to_csv(SAL / "dim_anio.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- DANE (P12, P13)
d = pd.read_csv(ENT / "dane_clean.csv")
d["departamento_h"] = d.departamento.map(homologar_depto)
zona = {"TOTAL NACIONAL": "Total nacional", "CABECERA": "Cabecera",
        "CENTROS POBLADOS Y RURAL DISPERSO": "Centros poblados y rural disperso"}
d["dominio"] = d.departamento.map(lambda x: zona.get(sin_tildes(x), "Departamento"))
d.loc[d.dominio == "Departamento", "dominio"] = "Departamento"
d["departamento"] = d.departamento_h
d = d.drop(columns="departamento_h")
etq = {
    "pct_hogares_computador_tablet": "Hogares con computador o tablet (ENTIC)",
    "pct_hogares_internet": "Hogares con internet (ENTIC)",
    "pct_hogares_internet_v2": "Hogares con internet (ECV)",
    "pct_personas_usan_computador": "Personas que usan computador (ECV)",
    "pct_personas_usan_internet": "Personas que usan internet (ECV)",
}
d["indicador_nombre"] = d.indicador.map(etq)
d["fuente"] = d.fuente.str.replace("DANE_ENTIC_Hogares", "DANE ENTIC").str.replace("DANE_ECV", "DANE ECV")
assert d.loc[d.dominio == "Departamento", "departamento"].notna().all()
d = d[["dominio", "departamento", "anio", "fuente", "indicador", "indicador_nombre", "valor", "unidad"]]
d.to_csv(SAL / "fact_dane_tic.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- IDEAM (P01-P04)
g = pd.read_csv(ENT / "ideam_gestores_clean.csv")
g = g.drop(columns=["col"], errors="ignore")                       # P02: columna 100 % vacía
g["departamento"] = g.Departamento.map(homologar_depto)
g["fecha_otorgamiento"] = pd.to_datetime(g["Fecha Otorgamiento"], dayfirst=True, errors="coerce")
g["anio_otorgamiento"] = g.fecha_otorgamiento.dt.year.astype("Int64")
respel = ["Almacenamiento", "Tratamiento", "Aprovechamiento", "Disposición Final"]
raee = ["Almacenamiento_1", "Tratamiento_1", "Aprovechamiento_1", "Disposición Final_1"]
si = lambda s: s.fillna("NO").astype(str).str.strip().str.upper().ne("NO")
for c in respel:
    g[f"respel_{sin_tildes(c).lower().replace(' ', '_')}"] = si(g[c])
for c, n in zip(raee, ["almacenamiento", "tratamiento", "aprovechamiento", "disposicion_final"]):
    g[f"raee_{n}"] = si(g[c])
g["declara_respel"] = g[[c for c in g if c.startswith("respel_")]].any(axis=1)
g["declara_raee"] = g[[c for c in g if c.startswith("raee_")]].any(axis=1)
g["tipo_gestion_declarada"] = "Sin corrientes detalladas"
g.loc[g.declara_respel, "tipo_gestion_declarada"] = "Solo RESPEL"
g.loc[g.declara_raee, "tipo_gestion_declarada"] = "Incluye RAEE"
nit = "NIT o Número de Identificación"
g["registros_mismo_nit"] = g.groupby(nit)[nit].transform("size")      # P03: renovaciones
g["tiene_vigencia"] = g.Vigencia.notna().map({True: "Con fecha", False: "Sin dato"})  # P01
g = g.rename(columns={"Municipio": "municipio", "Autoridad": "autoridad", "Empresa": "empresa",
                      "Nombre Establecimiento": "establecimiento", "Estado": "estado",
                      "Latitud": "latitud", "Longitud": "longitud", nit: "nit"})
cols = ["#", "nit", "empresa", "establecimiento", "departamento", "municipio", "autoridad", "estado",
        "latitud", "longitud", "fecha_otorgamiento", "anio_otorgamiento", "tiene_vigencia",
        "tipo_gestion_declarada", "declara_respel", "declara_raee", "registros_mismo_nit"] + \
       [c for c in g if c.startswith("respel_") or c.startswith("raee_")]
g = g[cols].rename(columns={"#": "id_registro"})
b = [c for c in g if g[c].dtype == bool]
g[b] = g[b].astype(int)  # 1/0 para sumar en DAX
g.to_csv(SAL / "fact_gestores.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- Encuesta NS (P08-P11)
s = pd.read_csv(ENT / "norte_santander_encuesta_clean.csv")
s = s.drop_duplicates().reset_index(drop=True)                     # P10: reenvíos
s.columns = ["municipio", "ocupacion", "entidad", "tiene_residuos", "donde_entrega", "sabe_raee",
             "participo_jornada", "medio_enterado", "usa_apps", "usaria_app_raee"]
s.insert(0, "id_encuestado", range(1, len(s) + 1))
s["ocupacion"] = s.ocupacion.str.strip().str.upper().replace({"PUBLICA": "PÚBLICA"})
s["ocupacion"] = s.ocupacion.replace({"PÚBLICA": "Empleado sector público", "PRIVADA": "Empleado sector privado",
                                      "TRABAJADOR INDEPENDIENTE": "Independiente", "DESEMPLEADO": "Desempleado",
                                      "AMA DE CASA": "Ama de casa", "PENSIONADO": "Pensionado",
                                      "ESTUDIANTE": "Estudiante"})
s["municipio"] = s.municipio.str.strip().str.upper()
am = {"LOS PATIOS", "VILLA DEL ROSARIO", "EL ZULIA", "SAN CAYETANO", "PUERTO SANTANDER"}
s["zona"] = s.municipio.map(lambda m: "Cúcuta" if m == "CÚCUTA" else
                            ("Área metropolitana" if m in am else "Resto del departamento"))
# Faltante != respuesta negativa (P11)
s["participo_jornada"] = s.participo_jornada.fillna("Sin respuesta")
# Canales de entrega (multirrespuesta) -> banderas + canal resumido
e = s.donde_entrega.fillna("").str.upper()
s["entrega_punto_autorizado"] = e.str.contains("PUNTOS DE RECOLECCI")
s["entrega_empresa_aseo"] = e.str.contains("EMPRESA DEL ASEO")
s["entrega_reciclador"] = e.str.contains("RECICLADORA")
s["entrega_regala"] = e.str.contains("REGALA")
s["deja_en_casa"] = e.str.contains("EN CASA|ALMACENADOS")
s["entrega_basura"] = e.str.contains("BASURA")
n_canales = s[[c for c in s if c.startswith("entrega_")] + ["deja_en_casa"]].sum(axis=1)
def canal(r, n):
    if n > 1: return "Varios canales"
    if r.entrega_punto_autorizado: return "Punto autorizado (formal)"
    if r.entrega_empresa_aseo: return "Empresa de aseo"
    if r.entrega_reciclador: return "Recicladora"
    if r.entrega_regala: return "Regala a conocidos"
    if r.deja_en_casa: return "Los deja en casa"
    if r.entrega_basura: return "Basura"
    return "Otra respuesta"
s["canal_entrega"] = [canal(r, n) for r, n in zip(s.itertuples(), n_canales)]
s["canal_formal"] = s.entrega_punto_autorizado.map({True: "Usa canal formal", False: "No usa canal formal"})
# Medio por el que se enteró
m = s.medio_enterado.fillna("").map(sin_tildes)
def medio(x):
    partes = [p.strip() for p in x.split(",") if p.strip()]
    if not partes: return "Sin respuesta"
    if len(partes) > 1: return "Varios medios"
    p = partes[0]
    if "NO SABIA" in p: return "No sabía que existe"
    for k, v in [("REDES", "Redes sociales"), ("DIRECTA", "Información directa"), ("CORREO", "Correo electrónico"),
                 ("SEDE", "Sede electrónica"), ("RADIO", "Radio"), ("TELEVISION", "Televisión"),
                 ("WHATSAPP", "WhatsApp")]:
        if k in p: return v
    return "Otro"
s["medio_enterado"] = m.map(medio)
# Disposición a usar app (P09: multivaloradas)
def app(x):
    if pd.isna(x): return "Sin respuesta"
    t = sin_tildes(x)
    partes = [p.strip() for p in t.split(",")]
    tiene_si = any(p == "SI" for p in partes)
    tiene_no = any(p.startswith("NO") for p in partes)
    if tiene_si and tiene_no: return "Respuesta ambigua"
    if tiene_si: return "Sí"
    if "CONOZCO DE TECNOLOGIA" in t or "ACCESO A INTERNET" in t: return "No: barrera tecnológica"
    if "INTERESA" in t: return "No: no le interesa"
    if partes == ["NO"]: return "No"
    return "Otra respuesta"
s["usaria_app_raee"] = s.usaria_app_raee.map(app)
s["usaria_app_si"] = s.usaria_app_raee.eq("Sí")
flags = [c for c in s if c.startswith("entrega_")] + ["deja_en_casa", "usaria_app_si"]
s[flags] = s[flags].astype(int)  # 1/0 para sumar en DAX
s = s.drop(columns=["entidad", "donde_entrega"])  # texto libre con 991 variantes; no se usa en el análisis
s.to_csv(SAL / "fact_encuesta_ns.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- Global OWID (P05-P07, P14)
gl = pd.read_csv(ENT / "master_indicadores_globales.csv").drop_duplicates()
o = gl[(gl.fuente == "OWID") & (gl.variable == "pct_raee_reciclado")].dropna(subset=["valor"])
o = o[(o.valor >= 0) & (o.valor <= 100)]
agregados = r"\(UN|\(UN SDG\)|World|Countries|States|Europe|Africa|Asia|America|Oceania"
o["tipo_area"] = o.pais_region.str.contains(agregados).map({True: "Región / agregado", False: "País"})
o.loc[o.pais_region == "World", "tipo_area"] = "Mundo"
o = o.rename(columns={"pais_region": "area", "valor": "pct_reciclado"})[["area", "tipo_area", "anio", "pct_reciclado"]]
o.to_csv(SAL / "fact_reciclaje_global.csv", index=False, encoding="utf-8-sig")

for f in sorted(SAL.glob("*.csv")):
    print(f"{f.name:28s} {len(pd.read_csv(f)):>6} filas")
