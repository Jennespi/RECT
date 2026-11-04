-- =========================================================================
-- Proyecto RECT - Etapa 5 (Modelo multidimensional)
-- Esquema del modelo estrella (constelación de hechos con dimensiones
-- conformadas), implementado en SQLite.
--
-- El proyecto no tiene un único proceso con un solo grano: la Etapa 4 ya
-- identificó cuatro fuentes con poblaciones distintas (instalaciones de
-- gestores, personas encuestadas, observaciones de indicadores TIC y
-- observaciones de reciclaje mundial). Forzarlas en una sola tabla de
-- hechos exigiría inventar un grano artificial que no corresponde a
-- ninguna de las cuatro preguntas de análisis. Por eso el modelo se
-- implementa como una constelación: cuatro tablas de hechos, cada una con
-- su propio grano, que comparten las dimensiones conformadas
-- dim_departamento, dim_municipio y dim_anio. Cada tabla de hechos sigue
-- siendo, individualmente, un esquema en estrella válido.
-- =========================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------- DIMENSIONES --

-- dim_departamento: nivel intermedio de la jerarquía territorial
-- (Región -> Departamento -> Municipio). Incluye una fila sentinela
-- (id_departamento = 0) para los registros de fact_dane_tic que son
-- agregados nacionales y no pertenecen a un departamento específico.
CREATE TABLE dim_departamento (
    id_departamento INTEGER PRIMARY KEY,
    departamento    TEXT UNIQUE NOT NULL,
    cod_divipola    TEXT,
    region          TEXT
);

-- dim_municipio: nivel más detallado de la jerarquía territorial.
-- Cada municipio pertenece a exactamente un departamento (FK), que a su
-- vez pertenece a una región: Región -> Departamento -> Municipio.
CREATE TABLE dim_municipio (
    id_municipio    INTEGER PRIMARY KEY,
    municipio       TEXT NOT NULL,
    id_departamento INTEGER NOT NULL REFERENCES dim_departamento(id_departamento),
    UNIQUE (municipio, id_departamento)
);

-- dim_anio: jerarquía temporal Década -> Año. Cubre 2005-2025, el rango
-- que necesitan las autorizaciones de gestores (desde 2005) y los demás
-- indicadores (hasta 2025).
CREATE TABLE dim_anio (
    id_anio INTEGER PRIMARY KEY,   -- = anio (p. ej. 2018)
    anio    INTEGER UNIQUE NOT NULL,
    decada  TEXT NOT NULL          -- '2000s', '2010s', '2020s'
);

-- ------------------------------------------------------- TABLAS DE HECHOS --

-- Grano: una fila = una instalación de gestor de RAEE/RESPEL registrada
-- en el IDEAM. Fuente: Etapa 2/3, datos/procesados/ideam_gestores_clean.csv.
CREATE TABLE fact_gestores (
    id_registro             INTEGER PRIMARY KEY,
    nit                     TEXT,
    empresa                 TEXT,
    establecimiento         TEXT,
    id_municipio            INTEGER REFERENCES dim_municipio(id_municipio),
    autoridad               TEXT,
    estado                  TEXT,     -- ACTIVO / INACTIVO
    latitud                 REAL,
    longitud                REAL,
    fecha_otorgamiento      TEXT,
    id_anio                 INTEGER REFERENCES dim_anio(id_anio),  -- anio_otorgamiento
    tiene_vigencia          TEXT,
    tipo_gestion_declarada  TEXT,
    declara_respel          INTEGER,  -- 1/0
    declara_raee            INTEGER,  -- 1/0
    registros_mismo_nit     INTEGER
);

-- Grano: una fila = una persona encuestada en el estudio de percepción
-- ciudadana sobre RAEE en Norte de Santander (sin año: estudio transversal
-- de un único levantamiento).
-- Fuente: datos/procesados/norte_santander_encuesta_clean.csv.
CREATE TABLE fact_encuesta_ns (
    id_encuestado             INTEGER PRIMARY KEY,
    id_municipio              INTEGER REFERENCES dim_municipio(id_municipio),
    ocupacion                 TEXT,
    zona                      TEXT,
    tiene_residuos             TEXT,
    sabe_raee                 TEXT,
    participo_jornada         TEXT,
    medio_enterado             TEXT,
    usa_apps                  TEXT,
    usaria_app_raee            TEXT,
    usaria_app_si              INTEGER,  -- 1/0
    canal_entrega              TEXT,
    canal_formal                TEXT,     -- 'Usa canal formal' / 'No usa canal formal'
    entrega_punto_autorizado   INTEGER,
    entrega_empresa_aseo       INTEGER,
    entrega_reciclador         INTEGER,
    entrega_regala             INTEGER,
    deja_en_casa                INTEGER,
    entrega_basura              INTEGER
);

-- Grano: una fila = una observación de un indicador TIC (tenencia de
-- computador/tablet, uso de internet, etc.) para un dominio territorial y
-- un año. Fuente: datos/procesados/dane_clean.csv (DANE ENTIC Hogares y
-- ECV). id_departamento = 0 cuando el dominio es un agregado nacional
-- (Total nacional, Cabecera, Centros poblados y rural disperso).
CREATE TABLE fact_dane_tic (
    id_dane             INTEGER PRIMARY KEY AUTOINCREMENT,
    dominio             TEXT NOT NULL,   -- Total nacional / Departamento / Cabecera / Centros poblados...
    id_departamento     INTEGER REFERENCES dim_departamento(id_departamento),
    id_anio             INTEGER REFERENCES dim_anio(id_anio),
    fuente              TEXT,
    indicador           TEXT,
    indicador_nombre    TEXT,
    valor               REAL,
    unidad              TEXT
);

-- Grano: una fila = una observación del % de RAEE reciclado para un área
-- (país, región/agregado o el mundo) en un año. Fuente: Our World in Data
-- (electronic-waste-recycling-rate.csv / master_indicadores_globales.csv).
-- 'area' es una dimensión degenerada (no hay tabla de países propia:
-- incluye agregados regionales y mundiales que no son departamentos de
-- Colombia, así que no comparte dim_departamento).
CREATE TABLE fact_reciclaje_global (
    id_reciclaje    INTEGER PRIMARY KEY AUTOINCREMENT,
    area            TEXT NOT NULL,
    tipo_area       TEXT NOT NULL,   -- País / Región / agregado / Mundo
    id_anio         INTEGER REFERENCES dim_anio(id_anio),
    pct_reciclado   REAL
);

CREATE INDEX idx_gestores_municipio ON fact_gestores(id_municipio);
CREATE INDEX idx_gestores_anio      ON fact_gestores(id_anio);
CREATE INDEX idx_encuesta_municipio ON fact_encuesta_ns(id_municipio);
CREATE INDEX idx_dane_departamento  ON fact_dane_tic(id_departamento);
CREATE INDEX idx_dane_anio          ON fact_dane_tic(id_anio);
CREATE INDEX idx_reciclaje_anio     ON fact_reciclaje_global(id_anio);
