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
# ESTILOS CSS
# =====================================================
st.markdown("""
<style>

.main {
    background-color: #f5f7fa;
}

.block-container {
    max-width: 1000px;
    padding-top: 2rem;
}

.titulo {
    text-align: center;
    color: #d71920;
    font-size: 36px;
    font-weight: 800;
    margin-top: 10px;
    margin-bottom: 5px;
}

.subtitulo {
    text-align: center;
    color: #666;
    font-size: 17px;
    margin-bottom: 20px;
}

.card {
    background: #ffffff;
    padding: 20px;
    border-radius: 12px;
    border-left: 5px solid #d71920;
    box-shadow: 0px 3px 8px rgba(0,0,0,0.08);
    margin-bottom: 15px;
}

.stock-alto {
    color: #28a745;
    font-weight: bold;
}

.stock-medio {
    color: #ff9800;
    font-weight: bold;
}

.stock-bajo {
    color: #dc3545;
    font-weight: bold;
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

        # Columna optimizada para búsquedas
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
# LOGO CENTRADO
# =====================================================

col1, col2, col3 = st.columns([1,5,1])

with col2:
    try:
        st.image(
            "logo.png",
            use_container_width=True
        )
    except:
        st.warning("Logo no encontrado")

# =====================================================
# TITULOS
# =====================================================

st.markdown(
    """
    <div class='titulo'>
        Consulta de Inventario Almacén Repuestos
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class='subtitulo'>
        Búsqueda inteligente por código, descripción, medida y sinónimos
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

# =====================================================
# FILTROS
# =====================================================

col1, col2 = st.columns([4,1])

with col1:

    consulta = st.text_input(
        "🔍 Buscar por código, nombre, medida o descripción",
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

    # ------------------------------------------
    # BÚSQUEDA DIRECTA POR CÓDIGO
    # ------------------------------------------

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

        coincidencias = [
            (df.index[i], score)
            for valor, score, i in resultados_data
            if score >= 60
        ]

        if coincidencias:

            resultados = df.loc[
                [x[0] for x in coincidencias]
            ].copy()

            resultados["score"] = [
                x[1] for x in coincidencias
            ]

        else:

            resultados = pd.DataFrame()

    # ------------------------------------------
    # FILTRO UBICACIÓN
    # ------------------------------------------

    if (
        filtro_ubicacion != "Todas"
        and not resultados.empty
    ):
        resultados = resultados[
            resultados["Ubic."] == filtro_ubicacion
        ]

    # ------------------------------------------
    # RESULTADOS
    # ------------------------------------------

    if not resultados.empty:

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Resultados",
                len(resultados)
            )

        with col2:
            st.metric(
                "Stock Total",
                int(
                    resultados[
                        "Cantidad stock valorado"
                    ].sum()
                )
            )

        with col3:
            st.metric(
                "Ubicaciones",
                resultados["Ubic."].nunique()
            )

        st.success(
            f"Se encontraron {len(resultados)} resultado(s)"
        )

        st.divider()

        for _, fila in resultados.iterrows():

            stock = float(
                fila["Cantidad stock valorado"]
            )

            if stock <= 5:
                clase = "stock-bajo"
            elif stock <= 15:
                clase = "stock-medio"
            else:
                clase = "stock-alto"

            st.markdown(
                f"""
                <div class="card">
                    <h4>{fila['Texto breve de material']}</h4>

                    <b>Código:</b> {fila['Material']}<br>

                    <b>Ubicación:</b> {fila['Ubic.']}<br>

                    <b>Stock:</b>
                    <span class="{clase}">
                        {stock:,.0f} {fila['UMB']}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

    else:

        st.error(
            "No se encontraron resultados para tu búsqueda."
        )

else:

    st.info(
        "Ingrese un código o descripción para comenzar a buscar."
    )
