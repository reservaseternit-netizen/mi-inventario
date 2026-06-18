import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
import base64

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
st.set_page_config(
    page_title="Consulta Inventario Repuestos",
    page_icon="📦",
    layout="centered"
)

# =====================================================
# ESTILOS (AJUSTADOS PARA CERCANÍA Y COLOR NEGRO)
# =====================================================
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

# =====================================================
# CARGA DE DATOS
# =====================================================
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("mi inventario.xlsx")
        df.columns = df.columns.astype(str).str.strip()

        df["Material"] = df["Material"].fillna("").astype(str).str.strip()
        df["Texto breve de material"] = df["Texto breve de material"].fillna("").astype(str).str.strip()
        df["Ubic."] = df["Ubic."].fillna("No asignada").astype(str).str.strip()
        df["UMB"] = df["UMB"].fillna("UN").astype(str).str.strip()

        df["Cantidad stock valorado"] = (
            pd.to_numeric(df["Cantidad stock valorado"], errors="coerce")
            .fillna(0)
            .astype(int)
        )

        df["search_col"] = (df["Texto breve de material"] + " " + df["Material"]).str.lower()
        return df
    except Exception as e:
        st.error(f"Error cargando Excel: {e}")
        return None

df = cargar_datos()
if df is None:
    st.stop()

# =====================================================
# LOGO
# =====================================================
try:
    with open("logo.png", "rb") as image_file:
        encoded_logo = base64.b64encode(image_file.read()).decode()
    
    st.markdown(
        f"""
        <div class="logo-container">
            <img class="logo-img" src="data:image/png;base64,{encoded_logo}" alt="Logo Eternit">
        </div>
        """,
        unsafe_allow_html=True
    )
except Exception as e:
    st.error(f"No se pudo cargar el logo: {e}")
        
# =====================================================
# TÍTULOS (AHORA MÁS PEGADOS Y EN NEGRO)
# =====================================================
st.markdown("<div class='titulo'>Consulta de Inventario Almacén Repuestos</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitulo'>Busque por código, descripción o medida</div>", unsafe_allow_html=True)

st.divider()

# =====================================================
# FILTRO
# =====================================================
consulta = st.text_input("🔍 Buscar", placeholder="Ej: Rodamiento 6205").strip()

# =====================================================
# BÚSQUEDA Y RESULTADOS
# =====================================================
if consulta:
    consulta_lower = consulta.lower()

    if consulta_lower.isdigit():
        resultados = df[df["Material"].str.contains(consulta_lower, na=False)].copy()
    else:
        resultados_data = process.extract(
            consulta_lower,
            df["search_col"].tolist(),
            scorer=fuzz.token_set_ratio,
            limit=30
        )
        indices = [df.index[i] for _, score, i in resultados_data if score >= 60]
        resultados = df.loc[indices].copy()

    if not resultados.empty:
        st.caption(f"Se encontraron {len(resultados)} resultados para '{consulta}'")
        for _, fila in resultados.iterrows():
            with st.container(border=True):
                st.markdown(f"### 🔩 {fila['Texto breve de material']}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("**Código**")
                    st.write(fila["Material"])
                with col2:
                    st.write("**Ubicación**")
                    st.write(fila["Ubic."])
                with col3:
                    st.write("**Stock**")
                    st.write(f"{fila['Cantidad stock valorado']} {fila['UMB']}")
    else:
        st.warning("No se encontraron resultados.")
else:
    st.info("Ingrese un código o descripción para buscar.")
