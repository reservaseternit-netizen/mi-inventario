import streamlit as stimport pandas as pdfrom rapidfuzz import process, fuzzimport base64import unicodedataimport re

def normalizar_texto(texto):

texto = str(texto).lower()

# Quitar tildes
texto = ''.join(
    c for c in unicodedata.normalize('NFD', texto)
    if unicodedata.category(c) != 'Mn'
)

# Normalización básica
texto = texto.replace("v", "b")
texto = texto.replace("-", "")
# Mantener medidas completas
# Mantener cualquier fracción de tornillería
texto = re.sub(
    r'(\d+)/(\d+)',
    r'\1_\2',
texto
)
texto = texto.replace("/", " ")
texto = texto.replace("cab/hex", "cab hex")

texto = re.sub(r'[^a-z0-9\s]', ' ', texto)

texto = " ".join(texto.split())

# =====================================================
# SINÓNIMOS Y ABREVIATURAS
# =====================================================

# Sensores
if "inductivo" in texto:
    texto += " induct"

if "induct" in texto:
    texto += " inductivo"

# Tornillería
if "cab hex" in texto:
    texto += " hexagonal"

if "hexagonal" in texto:
    texto += " cab hex hex"

# Rodamientos
if "rodamiento" in texto:
    texto += " rod"

if "rod" in texto:
    texto += " rodamiento"

# Válvulas
if "valvula" in texto:
    texto += " valv"

if "valv" in texto:
    texto += " valvula"

# Pinturas
if "esmalte" in texto:
    texto += " pintura pintulux"

if "pintura" in texto:
    texto += " esmalte"

# Bristol / BCC
if "bcc" in texto:
    texto += " bristol"

if "bristol" in texto:
    texto += " bcc"

return texto

=====================================================

CONFIGURACIÓN GENERAL

=====================================================

st.set_page_config(page_title="Consulta Inventario Repuestos",page_icon="⚙️",layout="centered")

=====================================================

ESTILOS (AJUSTADOS PARA CERCANÍA Y COLOR NEGRO)

=====================================================

st.markdown("""

<style>
.block-container {
    max-width: 900px;
    padding-top: 1.5rem; /* Reducido un poco el espacio superior total */
}

/* Contenedor del Logo con margen inferior reducido */
.logo-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: -10px; /* Margen negativo para acercar el título */
}

.logo-img {
    max-width: 240px;
    width: 100%;
    height: auto;
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
}

/* Título en NEGRO y más pegado arriba */
.titulo {
    text-align: center;
    color: #000000; /* Color Negro */
    font-size: 32px;
    font-weight: 800;
    margin-top: 0px;    /* Eliminado el margen superior */
    margin-bottom: 5px;
}

.subtitulo {
    text-align: center;
    color: #666;
    font-size: 16px;
    margin-bottom: 10px;
}
</style>

""", unsafe_allow_html=True)

=====================================================

CARGA DE DATOS

=====================================================

@st.cache_datadef cargar_datos():try:df = pd.read_excel("mi inventario.xlsx")df.columns = df.columns.astype(str).str.strip()

    df["Material"] = df["Material"].fillna("").astype(str).str.strip()
    df["Texto breve de material"] = df["Texto breve de material"].fillna("").astype(str).str.strip()
    df["Ubicación"] = (
        df["Ubicación"]
        .fillna("No asignada")
        .astype(str)
        .str.strip()
    )
    
    df["Unidad medida base"] = (
        df["Unidad medida base"]
        .fillna("UN")
        .astype(str)
        .str.strip()
    )

    df["Libre utilización"] = (
        pd.to_numeric(df["Libre utilización"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    df["Caract.planif.nec."] = (
        df["Caract.planif.nec."]
        .fillna("")
        .astype(str)
         .str.strip()
    )

    df["Punto de pedido"] = (
        pd.to_numeric(df["Punto de pedido"], errors="coerce")
        .fillna(0)
    )

    df["Stock máximo"] = (
        pd.to_numeric(df["Stock máximo"], errors="coerce")
        .fillna(0)   
    )

    df["Parte crítica"] = (
        df["Parte crítica"]
        .fillna("")
        .astype(str)
        .str.strip()
    )


    df["search_col"] = (
        df["Texto breve de material"]
        .fillna("")
        .apply(normalizar_texto)
        + " "
        + df["Material"]
        .fillna("")
        .astype(str)
        .apply(normalizar_texto)
    )
    
    return df
except Exception as e:
    st.error(f"Error cargando Excel: {e}")
    return None
    

df = cargar_datos()if df is None:st.stop()

=====================================================

LOGO

=====================================================

try:with open("logo.png", "rb") as image_file:encoded_logo = base64.b64encode(image_file.read()).decode()

st.markdown(
    f"""
    <div class="logo-container">
        <img class="logo-img" src="data:image/png;base64,{encoded_logo}" alt="Logo Eternit">
    </div>
    """,
    unsafe_allow_html=True
)

except Exception as e:st.error(f"No se pudo cargar el logo: {e}")

=====================================================

TÍTULOS (AHORA MÁS PEGADOS Y EN NEGRO)

=====================================================

st.markdown("<div class='titulo'>Consulta de Inventario Almacén Repuestos</div>", unsafe_allow_html=True)st.markdown("<div class='subtitulo'>Busque por código, descripción o medida</div>", unsafe_allow_html=True)

st.divider()

=====================================================

FILTRO

=====================================================

consulta = st.text_input("🔍 Buscar", placeholder="Ej: Rodamiento 6205").strip()

=====================================================

BÚSQUEDA Y RESULTADOS (MEJORADA)

=====================================================

if consulta:

consulta_lower = normalizar_texto(consulta)

consulta_normalizada = (
    consulta_lower
    .replace("-", " ")
    .replace("/", " ")
)

palabras = consulta_normalizada.split()

# -------------------------------------------------
# SI ES NUMÉRICO
# -------------------------------------------------
if consulta_lower.isdigit():

    resultados = df[
        (
            df["Material"]
            .astype(str)
            .str.contains(
                consulta_lower,
                na=False
            )
        )
        |
        (
            df["Texto breve de material"]
            .astype(str)
            .str.contains(
                consulta_lower,
                case=False,
                na=False
            )
        )
    ].copy()

    resultados["score"] = resultados[
        "Texto breve de material"
    ].astype(str).str.lower().apply(
        lambda x: 100 if consulta_lower in x else 0
    )

# -------------------------------------------------
# SI ES TEXTO
# -------------------------------------------------
else:

    def contar_coincidencias(texto):

        texto = (
            str(texto)
            .lower()
            .replace("-", " ")
            .replace("/", " ")
        )

        return sum(
            palabra in texto
            for palabra in palabras
        )

    coincidencias_exactas = df[
        df["search_col"].apply(
            lambda x:
            all(
                palabra in x
                for palabra in palabras
            )
        )
    ].copy()

    if not coincidencias_exactas.empty:

        resultados = coincidencias_exactas.copy()

        resultados["score"] = resultados[
            "Texto breve de material"
        ].apply(contar_coincidencias)

    else:

        resultados_data = process.extract(
            consulta_lower,
            df["search_col"].tolist(),
            scorer=fuzz.WRatio,
            limit=40
        )

        indices_validos = []
        scores = {}

        for texto_encontrado, score, indice_original in resultados_data:

            if score >= 55:

                idx = df.index[indice_original]

                indices_validos.append(idx)

                scores[idx] = score

        resultados = df.loc[indices_validos].copy()

        resultados["score"] = (
            resultados.index.map(scores)
        )

# -------------------------------------------------
# ORDENAMIENTO
# -------------------------------------------------
if not resultados.empty:

    tiene_ubicacion = (
        resultados["Ubicación"] != "No asignada"
    ).astype(int)

    tiene_stock = (
        resultados["Libre utilización"] > 0
    ).astype(int)

    resultados["prioridad_dispo"] = (
        tiene_ubicacion + tiene_stock
    )

    resultados["exacto"] = (
        resultados["search_col"]
        .apply(
            lambda x:
            all(
                palabra in x.replace("-", " ")
                for palabra in palabras
            )
        )
    ).astype(int)

    # Coincidencia exacta de medidas
    medidas_busqueda = [
        p for p in palabras
        if "_" in p or p.isdigit()
    ]

    resultados["coincidencia_medida_exacta"] = resultados["search_col"].apply(
        lambda x: sum(
            medida in x.split()
            for medida in medidas_busqueda
        )
    )

    # Prioridad por coincidencia de palabras/medidas
    resultados["prioridad_medida"] = resultados["search_col"].apply(
        lambda x: sum(
            20 if "_" in palabra else
            5 if palabra.isdigit() else
            1
            for palabra in palabras
            if palabra in x.split()
        )
    )

    resultados = resultados.sort_values(
        by=[
            "exacto",
            "coincidencia_medida_exacta",
            "prioridad_medida",
            "score",
            "prioridad_dispo",
            "Libre utilización"
        ],
        ascending=[
            False,
            False,
            False,
            False,
            False,
            False

        ]
    )

    st.caption(
        f"Se encontraron {len(resultados)} resultados para "
        f"'{consulta}' (Ordenados por disponibilidad)"
    )

    for _, fila in resultados.iterrows():

        con_stock = (
            fila["Libre utilización"] > 0
        )

        con_ubic = (
            fila["Ubicación"] != "No asignada"
        )

        if not con_stock and not con_ubic:

            titulo_tarjeta = (
                f"⚠️ {fila['Texto breve de material']} "
                f"(Código Sin Movimiento)"
            )

        elif not con_stock:

            titulo_tarjeta = (
                f"🔴 {fila['Texto breve de material']} "
                f"(Sin Existencias)"
            )

        else:

            titulo_tarjeta = (
                f"⚙️ {fila['Texto breve de material']}"
            )

        with st.container(border=True):

            st.markdown(
                f"### {titulo_tarjeta}"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.write("**Código**")
                st.write(fila["Material"])

            with col2:

                st.write("**Ubicación**")
                st.write(fila["Ubicación"])

            with col3:

                st.write("**Stock Disponible**")

                if fila["Libre utilización"] > 0:

                    st.markdown(
                        f"""
                        <div style="
                            background-color:#e8f5e9;
                            border-radius:10px;
                            padding:10px;
                            text-align:center;
                            font-weight:bold;
                            font-size:28px;
                            color:#1b5e20;
                        ">
                            {fila['Libre utilización']} {fila['Unidad medida base']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                else:

                    st.markdown(
                        f"""
                        <div style="
                            background-color:#ffebee;
                            border-radius:10px;
                            padding:10px;
                            text-align:center;
                            font-weight:bold;
                            font-size:28px;
                            color:#c62828;
                        ">
                            {fila['Libre utilización']} {fila['Unidad medida base']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
            st.divider()

            st.markdown(
                "#### 📋 Parametrización"
            )

            col4, col5, col6, col7 = st.columns(4)

            with col4:

                st.write("**Planificación**")
                st.write(
                    fila["Caract.planif.nec."]
                )

            with col5:

                st.write("**Punto Pedido**")
                st.write(
                    fila["Punto de pedido"]
                )

            with col6:

                st.write("**Stock Máximo**")
                st.write(
                    fila["Stock máximo"]
                )

            with col7:

                st.write("**Parte Crítica**")

                if str(
                    fila["Parte crítica"]
                ).strip():

                    st.success("SI")

                else:

                    st.write("NO")

else:

    st.warning(
        "No se encontraron resultados "
        "exactos o similares."
    )

else:

st.info(
    "Ingrese un código o descripción "
    "para buscar."
)
