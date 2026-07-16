import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
import base64
import unicodedata
import re

# =====================================================
# EXPRESIONES REGULARES COMPILADAS (Para máxima velocidad)
# =====================================================
RE_FRACCION = re.compile(r'(\d+)/(\d+)')
RE_CARACTERES = re.compile(r'[^a-z0-9\s]')

def normalizar_texto(texto):
    texto = str(texto).lower()

    # Quitar tildes de forma eficiente
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

    # Normalización básica
    texto = texto.replace("v", "b").replace("-", "")
    
    # Mantener fracciones de tornillería
    texto = RE_FRACCION.sub(r'\1_\2', texto)
    texto = texto.replace("/", " ").replace("cab/hex", "cab hex")

    # Limpieza de caracteres no permitidos
    texto = RE_CARACTERES.sub(' ', texto)
    texto = " ".join(texto.split())

    # =====================================================
    # SINÓNIMOS Y ABREVIATURAS
    # =====================================================
    # Se añade espacio al final para búsquedas exactas limpias
    if "inductivo" in texto:
        texto += " induct"
    elif "induct" in texto:
        texto += " inductivo"

    if "cab hex" in texto:
        texto += " hexagonal"
    elif "hexagonal" in texto:
        texto += " cab hex hex"

    if "rodamiento" in texto:
        texto += " rod"
    elif "rod" in texto:
        texto += " rodamiento"

    if "valvula" in texto:
        texto += " valv"
    elif "valv" in texto:
        texto += " valvula"

    if "esmalte" in texto:
        texto += " pintura pintulux"
    elif "pintura" in texto:
        texto += " esmalte"

    if "bcc" in texto:
        texto += " bristol"
    elif "bristol" in texto:
        texto += " bcc"

    return texto

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
st.set_page_config(
    page_title="Consulta Inventario Repuestos",
    page_icon="⚙️",
    layout="centered"
)

# =====================================================
# ESTILOS CSS
# =====================================================
st.markdown("""
<style>
.block-container {
    max-width: 900px;
    padding-top: 1.5rem;
}
.logo-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: -10px;
}
.logo-img {
    max-width: 240px;
    width: 100%;
    height: auto;
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
}
.titulo {
    text-align: center;
    color: #000000;
    font-size: 32px;
    font-weight: 800;
    margin-top: 0px;
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

# =====================================================
# CARGA Y PREPROCESAMIENTO DE DATOS (CACHEADO)
# =====================================================
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("mi inventario.xlsx")
        df.columns = df.columns.astype(str).str.strip()

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

        # Vectorización de la columna de búsqueda para acelerar la carga inicial
        df["search_col"] = (
            df["Texto breve de material"].apply(normalizar_texto)
            + " "
            + df["Material"].apply(normalizar_texto)
        )
        
        return df
    except Exception as e:
        st.error(f"Error cargando Excel: {e}")
        return None

# =====================================================
# CARGA DE LOGO EN CACHÉ (Evita lecturas de disco repetidas)
# =====================================================
@st.cache_data
def cargar_logo_base64(ruta_imagen):
    try:
        with open(ruta_imagen, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except Exception:
        return None

df = cargar_datos()
if df is None:
    st.stop()

# Renderizar Logo si existe
encoded_logo = cargar_logo_base64("logo.png")
if encoded_logo:
    st.markdown(
        f"""
        <div class="logo-container">
            <img class="logo-img" src="data:image/png;base64,{encoded_logo}" alt="Logo Eternit">
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.warning("No se pudo encontrar o cargar 'logo.png'.")

# =====================================================
# TÍTULOS
# =====================================================
st.markdown("<div class='titulo'>El repuesto que necesitas está a un clic. ¡Consulta el inventario! 📦</div>", unsafe_allow_html=True)
st.divider()

# =====================================================
# FILTROS
# =====================================================
col1, col2, col3 = st.columns([4, 1, 2])

with col1:
    consulta = st.text_input(
        "🔍 Buscar descripción",
        placeholder="Ej: Rodamiento 6205"
    ).strip()

with col2:
    # Obtener letras únicas para la ubicación de manera óptima
    letras = sorted(
        df["Ubicación"]
        .astype(str)
        .str[0]
        .dropna()
        .unique()
    )

    filtro_ubicacion = st.selectbox(
        "📍 Ubicación",
        ["Todas"] + letras
    )

with col3:
    orden = st.selectbox(
        "↕ Orden",
        [
            "Relevancia",
            "Ubicación (Menor a Mayor)",
            "Descripción (A-Z)"
        ]
    )

# =====================================================
# BÚSQUEDA Y RESULTADOS
# =====================================================
if consulta or filtro_ubicacion != "Todas":

    # Filtrar primero por ubicación para reducir el espacio de búsqueda
    df_busqueda = df
    if filtro_ubicacion != "Todas":
        df_busqueda = df[df["Ubicación"].astype(str).str.startswith(filtro_ubicacion)]

    consulta_lower = normalizar_texto(consulta)
    consulta_normalizada = consulta_lower.replace("-", " ").replace("/", " ")
    palabras = consulta_normalizada.split()

    # -------------------------------------------------
    # CASO 1: BÚSQUEDA NUMÉRICA
    # -------------------------------------------------
    if consulta_lower.isdigit():
        cond_material = df_busqueda["Material"].astype(str).str.contains(consulta_lower, na=False)
        cond_texto = df_busqueda["Texto breve de material"].astype(str).str.contains(consulta_lower, case=False, na=False)
        
        resultados = df_busqueda[cond_material | cond_texto].copy()
        
        # Asignar Score vectorizado
        resultados["score"] = resultados["Texto breve de material"].astype(str).str.lower().apply(
            lambda x: 100 if consulta_lower in x else 0
        )

    # -------------------------------------------------
    # CASO 2: BÚSQUEDA POR TEXTO (Fuzzy o Coincidencia Exacta)
    # -------------------------------------------------
    else:
        def contar_coincidencias(texto):
            texto_clean = str(texto).lower().replace("-", " ").replace("/", " ")
            return sum(palabra in texto_clean for palabra in palabras)

        # Filtro de coincidencia de palabras exacta (Todas las palabras deben existir)
        # Optimizamos con una list comprehension rápida sobre search_col
        search_vals = df_busqueda["search_col"].values
        indices_exactos = [
            i for i, val in enumerate(search_vals)
            if all(palabra in val for palabra in palabras)
        ]
        coincidencias_exactas = df_busqueda.iloc[indices_exactos].copy()

        if not coincidencias_exactas.empty:
            resultados = coincidencias_exactas
            resultados["score"] = resultados["Texto breve de material"].apply(contar_coincidencias)
        else:
            # Si no hay coincidencias exactas, recurrir al Fuzzy Matching usando RapidFuzz (limitado a 40)
            lista_busqueda = df_busqueda["search_col"].tolist()
            resultados_data = process.extract(
                consulta_lower,
                lista_busqueda,
                scorer=fuzz.WRatio,
                limit=40
            )

            indices_validos = []
            scores = {}
            for texto_encontrado, score, indice_original in resultados_data:
                if score >= 55:
                    idx = df_busqueda.index[indice_original]
                    indices_validos.append(idx)
                    scores[idx] = score

            resultados = df_busqueda.loc[indices_validos].copy()
            resultados["score"] = resultados.index.map(scores)

    # -------------------------------------------------
    # PROCESAMIENTO DE CRITERIOS DE ORDENAMIENTO Y RENDERS
    # -------------------------------------------------
    if not resultados.empty:
        # Precalcular booleanos de stock y ubicación de forma vectorizada
        tiene_ubicacion = (resultados["Ubicación"] != "No asignada").astype(int)
        tiene_stock = (resultados["Libre utilización"] > 0).astype(int)
        resultados["prioridad_dispo"] = tiene_ubicacion + tiene_stock

        search_col_vals = resultados["search_col"].values
        
        # Precalcular columna "exacto" sin llamadas pesadas
        resultados["exacto"] = [
            int(all(p in x.replace("-", " ") for p in palabras)) 
            for x in search_col_vals
        ]

        # Prioridad y coincidencias de medidas
        medidas_busqueda = [p for p in palabras if "_" in p or p.isdigit()]
        
        resultados["coincidencia_medida_exacta"] = [
            sum(medida in x.split() for medida in medidas_busqueda)
            for x in search_col_vals
        ]

        resultados["prioridad_medida"] = [
            sum(20 if "_" in palabra else 5 if palabra.isdigit() else 1 
                for palabra in palabras if palabra in x.split())
            for x in search_col_vals
        ]

        # Orden por relevancia por defecto
        resultados = resultados.sort_values(
            by=[
                "exacto",
                "coincidencia_medida_exacta",
                "prioridad_medida",
                "score",
                "prioridad_dispo",
                "Libre utilización"
            ],
            ascending=[False, False, False, False, False, False]
        )

        # Aplicar ordenamientos personalizados si aplica
        if orden == "Ubicación (Menor a Mayor)":
            resultados["Letra"] = resultados["Ubicación"].str.extract(r"^([A-Za-z]+)")
            resultados["Numero"] = pd.to_numeric(
                resultados["Ubicación"].str.extract(r"(\d+)")[0],
                errors="coerce"
            )
            resultados["Sufijo"] = resultados["Ubicación"].str.extract(r"\d+([A-Za-z]*)$")[0].fillna("")
            
            resultados = resultados.sort_values(
                by=["Letra", "Numero", "Sufijo"],
                ascending=[True, True, True]
            )

        elif orden == "Descripción (A-Z)":
            resultados = resultados.sort_values(
                by="Texto breve de material",
                ascending=True
            )

        st.caption(
            f"Se encontraron {len(resultados)} resultados para "
            f"'{consulta}' (Ordenados por disponibilidad)"
        )

        # Renderizado de Tarjetas
        for _, fila in resultados.iterrows():
            con_stock = fila["Libre utilización"] > 0
            con_ubic = fila["Ubicación"] != "No asignada"

            if not con_stock and not con_ubic:
                titulo_tarjeta = f"⚠️ {fila['Texto breve de material']} (Código Sin Movimiento)"
            elif not con_stock:
                titulo_tarjeta = f"🔴 {fila['Texto breve de material']} (Sin Existencias)"
            else:
                titulo_tarjeta = f"⚙️ {fila['Texto breve de material']}"

            with st.container(border=True):
                st.markdown(f"### {titulo_tarjeta}")

                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1:
                    st.write("**Código**")
                    st.write(fila["Material"])

                with col_c2:
                    st.write("**Ubicación**")
                    st.write(fila["Ubicación"])

                with col_c3:
                    st.write("**Stock Disponible**")
                    if con_stock:
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
                st.markdown("#### 📋 Parametrización")

                col_c4, col_c5, col_c6, col_c7 = st.columns(4)
                with col_c4:
                    st.write("**Planificación**")
                    st.write(fila["Caract.planif.nec."])

                with col_c5:
                    st.write("**Punto Pedido**")
                    st.write(fila["Punto de pedido"])

                with col_c6:
                    st.write("**Stock Máximo**")
                    st.write(fila["Stock máximo"])

                with col_c7:
                    st.write("**Parte Crítica**")
                    if str(fila["Parte crítica"]).strip():
                        st.success("SI")
                    else:
                        st.write("NO")
    else:
        st.warning("No se encontraron resultados exactos o similares.")
else:
    st.info("Ingrese un código o descripción para buscar.")
