import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================

st.set_page_config(
    page_title="Inventario Repuestos",
    page_icon="📦",
    layout="wide"
)

# =====================================================
# ESTILOS
# =====================================================

st.markdown("""
<style>

.block-container{
    max-width:1200px;
    padding-top:0.5rem;
}

.titulo{
    text-align:center;
    color:#d71920;
    font-size:32px;
    font-weight:700;
    margin-top:0px;
    margin-bottom:5px;
}

.subtitulo{
    text-align:center;
    color:#666;
    font-size:16px;
    margin-bottom:10px;
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

col1, col2, col3 = st.columns([1,2,1])

with col2:
    try:
        st.image(
            "logo.png",
            width=320
        )
    except:
        pass

# =====================================================
# TÍTULOS
# =====================================================

st.markdown(
    "<div class='titulo'>Inventario de Repuestos</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='subtitulo'>Consulte disponibilidad y ubicación de materiales en tiempo real</div>",
    unsafe_allow_html=True
)

st.divider()

# =====================================================
# BUSCADOR
# =====================================================

consulta = st.text_input(
    "",
    placeholder="🔍 Buscar por código, descripción o referencia..."
)

# =====================================================
# BÚSQUEDA
# =====================================================

if consulta:

    consulta = consulta.lower().strip()

    # Buscar por código
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

        resultados = df.loc[indices].copy()

    # =================================================
    # RESULTADOS
    # =================================================

    if not resultados.empty:

        st.success(
            f"Resultados encontrados: {len(resultados)}"
        )

        for _, fila in resultados.iterrows():

            stock = fila["Cantidad stock valorado"]

            with st.container(border=True):

                st.markdown(
                    f"#### 🔩 {fila['Texto breve de material']}"
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
                    st.write(
                        f"{stock:,.0f} {fila['UMB']}"
                    )

    else:

        st.warning(
            "No se encontraron resultados."
        )

else:

    st.info(
        "Ingrese un código o descripción para buscar."
    )
