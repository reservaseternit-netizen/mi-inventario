import streamlit as st
import pandas as pd
from rapidfuzz import fuzz


# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================

st.set_page_config(
    page_title="Consulta Inventario Repuestos",
    page_icon="📦",
    layout="wide"
)


# =====================================================
# ESTILOS
# =====================================================

st.markdown("""
<style>

.main{
    background-color:#f5f7fa;
}

.titulo{
    text-align:center;
    color:#d71920;
    font-size:34px;
    font-weight:bold;
}

.subtitulo{
    text-align:center;
    color:#666666;
    font-size:16px;
}

.card{
    background:white;
    padding:18px;
    border-radius:12px;
    box-shadow:0px 2px 10px rgba(0,0,0,0.08);
    margin-bottom:12px;
}

.stock-alto{
    color:#28a745;
    font-weight:bold;
}

.stock-medio{
    color:#ff9800;
    font-weight:bold;
}

.stock-bajo{
    color:#dc3545;
    font-weight:bold;
}

</style>
""", unsafe_allow_html=True)



# =====================================================
# LOGO
# =====================================================

try:
    st.image("logo.png", width=300)
except:
    pass


st.markdown(
    "<div class='titulo'>Consulta de Inventario Almacén Repuestos</div>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='subtitulo'>Búsqueda inteligente por código, descripción, medida y sinónimos</div>",
    unsafe_allow_html=True
)


st.divider()



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

        df["Cantidad stock valorado"] = pd.to_numeric(
            df["Cantidad stock valorado"],
            errors="coerce"
        ).fillna(0)


        return df


    except Exception as e:

        st.error(f"Error cargando Excel: {e}")

        return None



df = cargar_datos()


if df is None:
    st.stop()



# =====================================================
# COLUMNAS
# =====================================================

COL_CODIGO = "Material"
COL_DESCRIPCION = "Texto breve de material"
COL_UBICACION = "Ubic."
COL_UNIDAD = "UMB"
COL_STOCK = "Cantidad stock valorado"



# =====================================================
# SINÓNIMOS
# =====================================================

SINONIMOS = {

    "trapero": "trapeador",
    "trapo": "trapeador",

    "escova": "escoba",
    "escobas": "escoba",

    "vinipel": "pelicula plastica stretch",
    "stretch": "pelicula plastica stretch",

    "perica": "llave ajustable",

    "cinta transparente": "tape",

    "amarras": "cinta plastica",
    "cinchos": "cinta plastica"

}



# =====================================================
# FILTROS
# =====================================================

col1, col2 = st.columns([4,1])


with col1:

    consulta = st.text_input(
        "🔍 Buscar por código, nombre, medida o descripción",
        placeholder="Ejemplo: 1170371, escova, trapero..."
    )


with col2:

    ubicaciones = [
        "Todas"
    ] + sorted(
        df[COL_UBICACION]
        .fillna("No asignada")
        .unique()
        .tolist()
    )


    filtro_ubicacion = st.selectbox(
        "Ubicación",
        ubicaciones
    )



# =====================================================
# BÚSQUEDA
# =====================================================

if consulta:


    consulta_limpia = consulta.lower().strip()


    for alias, real in SINONIMOS.items():

        if alias in consulta_limpia:

            consulta_limpia = consulta_limpia.replace(
                alias,
                real
            )



    codigo_exacto = df[
        df[COL_CODIGO]
        .astype(str)
        .str.strip()
        ==
        consulta.strip()
    ]



    if not codigo_exacto.empty:

        resultados = codigo_exacto.copy()


    else:


        palabras = consulta_limpia.split()


        df_resultados = df.copy()


        def evaluar_fila(fila):

            texto = (
                f"{fila[COL_DESCRIPCION]} "
                f"{fila[COL_CODIGO]}"
            ).lower()


            score = 0


            for palabra in palabras:


                if palabra in texto:

                    score += 100


                else:

                    score += fuzz.partial_ratio(
                        palabra,
                        texto
                    )


            return score



        df_resultados["Score"] = df_resultados.apply(
            evaluar_fila,
            axis=1
        )



        resultados = df_resultados[
            df_resultados["Score"] >= 60
        ].sort_values(
            "Score",
            ascending=False
        )




    if filtro_ubicacion != "Todas":

        resultados = resultados[
            resultados[COL_UBICACION]
            ==
            filtro_ubicacion
        ]



    if not resultados.empty:


        st.success(
            f"Se encontraron {len(resultados)} resultado(s)"
        )


        for _, fila in resultados.head(30).iterrows():


            stock = float(
                fila[COL_STOCK]
            )


            clase_stock = "stock-alto"


            if stock <= 5:

                clase_stock = "stock-bajo"


            elif stock <= 15:

                clase_stock = "stock-medio"



            st.markdown(
                f"""

                <div class="card">

                <h4>{fila[COL_DESCRIPCION]}</h4>

                <b>Código:</b>
                {fila[COL_CODIGO]}
                <br>

                <b>Ubicación:</b>
                {fila[COL_UBICACION]}
                <br>

                <b>Stock:</b>

                <span class="{clase_stock}">
                {stock:,.0f} {fila[COL_UNIDAD]}
                </span>


                </div>

                """,
                unsafe_allow_html=True
            )


    else:

        st.error(
            "No se encontraron resultados."
        )



else:


    st.info(
        "Ingrese un código o descripción para buscar."
    )
