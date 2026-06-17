import streamlit as st
import pandas as pd
from rapidfuzz import fuzz
from io import BytesIO

# ==========================================
# CONFIGURACIÓN DE LA APP
# ==========================================

st.set_page_config(
    page_title="Consulta de Inventario Pro",
    page_icon="📦",
    layout="centered"
)

st.markdown("""
<style>
.stTextInput > div > div > input {
    font-size:18px;
}

.resultado-card {
    padding:15px;
    border-radius:10px;
    border:1px solid #ddd;
    margin-bottom:10px;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    "<h1 style='text-align:center;'>📦 Consulta de Inventario</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<p style='text-align:center;color:gray;'>Búsqueda inteligente por producto, medida o código</p>",
    unsafe_allow_html=True
)

st.divider()

# ==========================================
# CARGA DE DATOS
# ==========================================

@st.cache_data
def cargar_datos():

    try:

        df = pd.read_excel("mi inventario.xlsx")

        df.columns = df.columns.astype(str).str.strip()

        # Limpieza de datos
        df["Material"] = df["Material"].fillna("").astype(str).str.strip()

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
            .astype(int)
        )

        # Campo optimizado para búsqueda
        df["BUSQUEDA"] = (
            df["Material"].astype(str) + " " +
            df["Texto breve de material"].astype(str)
        ).str.lower()

        return df

    except FileNotFoundError:
        st.error("⚠️ No se encontró el archivo 'mi inventario.xlsx'")
        return None

    except Exception as e:
        st.error(f"❌ Error al cargar archivo: {e}")
        return None


df = cargar_datos()

# ==========================================
# PROCESO DE BÚSQUEDA
# ==========================================

if df is not None:

    COL_CODIGO = "Material"
    COL_DESCRIPCION = "Texto breve de material"
    COL_UBICACION = "Ubic."
    COL_UNIDAD = "UMB"
    COL_STOCK = "Cantidad stock valorado"

    consulta = st.text_input(
        "🔍 Buscar producto",
        placeholder="Ej: niple galvanizado 1/8 x 1"
    )

    if st.button("🗑 Limpiar búsqueda"):
        st.rerun()

    if consulta:

        consulta_limpia = consulta.lower().strip()

        palabras_ignorar = {
            "hola", "me", "das", "por", "favor",
            "el", "la", "los", "las",
            "un", "una", "de", "del",
            "buscar", "codigo", "producto",
            "búscame", "buscame",
            "necesito", "stock",
            "con", "para"
        }

        palabras_clave = [
            palabra
            for palabra in consulta_limpia.split()
            if palabra not in palabras_ignorar
        ]

        resultados = pd.DataFrame()

        # ======================================
        # BÚSQUEDA DIRECTA POR CÓDIGO
        # ======================================

        if consulta_limpia.isdigit():

            resultados = df[
                df[COL_CODIGO]
                .astype(str)
                .str.contains(
                    consulta_limpia,
                    case=False,
                    na=False
                )
            ].copy()

            resultados["Score_Busqueda"] = 100

        # ======================================
        # BÚSQUEDA INTELIGENTE
        # ======================================

        elif palabras_clave:

            df_resultados = df.copy()

            def evaluar_fila(texto_producto):

                score_total = 0
                coincidencias = 0

                for palabra in palabras_clave:

                    if palabra in texto_producto:

                        score_total += 120
                        coincidencias += 1

                    else:

                        similitud = fuzz.partial_ratio(
                            palabra,
                            texto_producto
                        )

                        if similitud >= 75:

                            score_total += similitud
                            coincidencias += 1

                if coincidencias == 0:
                    return 0

                score_total = (
                    score_total *
                    (coincidencias / len(palabras_clave))
                )

                return score_total

            df_resultados["Score_Busqueda"] = (
                df_resultados["BUSQUEDA"]
                .apply(evaluar_fila)
            )

            umbral = 60 * len(palabras_clave)

            resultados = (
                df_resultados[
                    df_resultados["Score_Busqueda"] >= umbral
                ]
                .sort_values(
                    by="Score_Busqueda",
                    ascending=False
                )
            )

        # ======================================
        # RESULTADOS
        # ======================================

        if not resultados.empty:

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Coincidencias",
                    len(resultados)
                )

            with col2:
                st.metric(
                    "Stock Total",
                    int(resultados[COL_STOCK].sum())
                )

            st.success(
                f"✅ Se encontraron {len(resultados)} resultado(s)"
            )

            st.divider()

            for fila in resultados.head(20).itertuples():

                with st.container():

                    st.markdown(
                        f"### 🔹 {getattr(fila, COL_DESCRIPCION)}"
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(
                            f"**🔢 Código:** `{getattr(fila, COL_CODIGO)}`"
                        )

                    with col2:
                        st.markdown(
                            f"**📍 Ubicación:** {getattr(fila, COL_UBICACION)}"
                        )

                    with col3:
                        st.markdown(
                            f"**📊 Stock:** {getattr(fila, COL_STOCK)} {getattr(fila, COL_UNIDAD)}"
                        )

                    stock = getattr(fila, COL_STOCK)

                    if stock <= 0:
                        st.error("🔴 Sin stock")

                    elif stock < 5:
                        st.warning("🟡 Stock bajo")

                    else:
                        st.success("🟢 Disponible")

                    score = round(
                        getattr(fila, "Score_Busqueda"),
                        1
                    )

                    st.progress(min(int(score), 100))
                    st.caption(
                        f"Relevancia: {score}%"
                    )

                    st.divider()

            # ==================================
            # EXPORTAR RESULTADOS
            # ==================================

            buffer = BytesIO()

            with pd.ExcelWriter(
                buffer,
                engine="openpyxl"
            ) as writer:

                resultados.drop(
                    columns=["BUSQUEDA"],
                    errors="ignore"
                ).to_excel(
                    writer,
                    index=False
                )

            st.download_button(
                "📥 Descargar resultados en Excel",
                data=buffer.getvalue(),
                file_name="resultados_inventario.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        else:

            st.error(
                "❌ No se encontraron coincidencias para esa búsqueda."
            )
