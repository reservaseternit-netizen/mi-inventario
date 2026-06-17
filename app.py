import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================

st.set_page_config(
    page_title="Consulta Inventario Repuestos",
    page_icon="📦",
    layout="centered"
)

# =====================================================
# ESTILOS
# =====================================================

st.markdown("""
<style>

.block-container{
    max-width:900px;
    padding-top:2rem;
}

.titulo{
    text-align:center;
    color:#d71920;
    font-size:34px;
    font-weight:800;
    margin-top:10px;
    margin-bottom:5px;
}

.subtitulo{
    text-align:center;
    color:#666;
    font-size:16px;
    margin-bottom:20px;
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

        df["Material"] = (
            df["Material"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df["Texto breve de material"] = (
            df["Texto breve de material"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df["Ubic."] = (
            df["Ubic."]
            .fillna("No asignada")
            .astype(str)
            .str.strip()
        )

        df["UMB"] = (
            df["UMB"]
            .fillna("UN")
            .astype(str)
            .str.strip()
        )

        df["Cantidad stock valorado"] = (
            pd.to_numeric(
                df["Cantidad stock valorado"],
                errors="coerce"
            )
            .fillna(0)
        )

        df["search_col"] = (
            df["Texto breve de material"]
            + " "
            + df["Material"]
        ).str.lower()

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

col1, col2, col3 = st.columns([1,5,1])

with col2:
    try:
        st.image(
            "logo.png",
            use_container_width=True
        )
    except:
        pass

# =====================================================
# TITULOS
# =====================================================

st.markdown(
    "<div class='titulo'>Consulta de Inventario Almacén Repuestos</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='subtitulo'>Busque por código, descripción o medida</div>",
    unsafe_allow_html=True
)

st.divider()

# =====================================================
# FILTROS
# =====================================================

col1, col2 = st.columns([4,1])

with col1:

    consulta = st.text_input(
        "🔍 Buscar",
        placeholder="Ej: Rodamiento 6205"
    )

with col2:

    ubicaciones = (
        ["Todas"]
        + sorted(df["Ubic."].unique().tolist())
    )

    filtro_ubicacion = st.selectbox(
        "Ubicación",
        ubicaciones
    )

# =====================================================
# BÚSQUEDA
# =====================================================

if consulta:

    consulta = consulta.lower().strip()

    if consulta.isdigit():

        resultados = df[
            df["Material"]
            .astype(str)
            .str.contains(
                consulta,
                na=False
            )
        ].copy()

    else:

        resultados_data = process.extract(
            consulta,
            df["search_col"].tolist(),
            scorer=fuzz.token_set_ratio,
            limit=30
        )

        indices = [
            df.index[i]
            for valor, score, i in resultados_data
            if score >= 60
        ]

        resultados = df.loc[indices]

    if filtro_ubicacion != "Todas":

        resultados = resultados[
            resultados["Ubic."] == filtro_ubicacion
        ]

    if not resultados.empty:

        for _, fila in resultados.iterrows():

            stock = int(fila["Cantidad stock valorado"])

            with st.container(border=True):

                st.markdown(
                    f"### 🔩 {fila['Texto breve de material']}"
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write("**Código**")
                    st.write(fila["Material"])

                with col2:
                    st.write("**Ubicación**")
                    st.write(fila["Ubic."])

                with col3:
                    st.write("**Stock**")
                    st.write(f"{stock} {fila['UMB']}")

else:

    st.warning(
        "No se encontraron resultados."
    )

else:

    st.info(
        "Ingrese un código o descripción para buscar."
    )
