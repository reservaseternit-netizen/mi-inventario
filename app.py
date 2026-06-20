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
# BÚSQUEDA Y RESULTADOS (ORDENADO POR DISPONIBILIDAD)
# =====================================================
if consulta:
    consulta_lower = consulta.lower()

    # Si es un código numérico directo
    if consulta_lower.isdigit():
        resultados = df[df["Material"].str.contains(consulta_lower, na=False)].copy()
    else:
        # Usamos WRatio para tolerancia a errores y palabras incompletas
        resultados_data = process.extract(
            consulta_lower,
            df["search_col"].tolist(),
            scorer=fuzz.WRatio, 
            limit=40  # Subimos el límite para capturar los códigos bloqueados/vacíos también
        )
        
        indices_validos = []
        for texto_encontrado, score, indice_original in resultados_data:
            if score >= 55:  
                indices_validos.append(df.index[indice_original])
        
        # Filtramos los resultados iniciales del DataFrame
        resultados = df.loc[indices_validos].copy()

    if not resultados.empty:
        # ---------------------------------------------------------
        # LÓGICA DE ORDENACIÓN PRIORITARIA
        # ---------------------------------------------------------
        # Creamos columnas temporales para calcular la prioridad de cada fila
        # Tiene ubicación real? (True=1, False=0)
        tiene_ubicacion = (resultados["Ubicación"] != "No asignada").astype(int)
        # Tiene stock real? (True=1, False=0)
        tiene_stock = (resultados["Libre utilización"] > 0).astype(int)
        
        # Calculamos un "Score de Disponibilidad"
        # Si tiene ambos (ubicación y stock) dará 2 -> Va de primero
        # Si tiene solo uno dará 1 -> Va en el medio
        # Si no tiene nada dará 0 -> Va al final del todo
        resultados["prioridad_dispo"] = tiene_ubicacion + tiene_stock
        
        # Ordenamos primero por el score de disponibilidad (de mayor a menor)
        # y como segundo criterio mantenemos el orden de similitud de texto si aplica
        if not consulta_lower.isdigit():
            # Creamos un mapeo para recordar el orden de coincidencia de rapidfuzz
            orden_similitud = {idx: i for i, idx in enumerate(indices_validos)}
            resultados["orden_texto"] = resultados.index.map(orden_similitud)
            
            resultados = resultados.sort_values(
                by=["prioridad_dispo", "Libre utilización"], 
                ascending=[False, True]
            )
        else:
            # Si fue búsqueda por código numérico, ordenamos solo por disponibilidad y luego por stock
            resultados = resultados.sort_values(
                by=["prioridad_dispo", "Libre utilización"],
                ascending=[False, False]
            )
        # ---------------------------------------------------------

        st.caption(f"Se encontraron {len(resultados)} resultados para '{consulta}' (Ordenados por disponibilidad)")
        
        for _, fila in resultados.iterrows():
            # Opcional: Podemos cambiar visualmente las tarjetas que están en cero o sin ubicación
            con_stock = fila['Libre utilización'] > 0
            con_ubic = fila['Ubicación'] != "No asignada"
            
            # Si el repuesto está muerto (sin stock y sin ubicación), le ponemos un aviso sutil
            if not con_stock and not con_ubic:
                titulo_tarjeta = f"⚠️ {fila['Texto breve de material']} (Código Sin Movimiento)"
            elif not con_stock:
                titulo_tarjeta = f"🔴 {fila['Texto breve de material']} (Sin Existencias)"
            else:
                titulo_tarjeta = f"📦 {fila['Texto breve de material']}"

            with st.container(border=True):

                st.markdown(f"### {titulo_tarjeta}")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Código**")
                st.write(fila["Material"])

            with col2:
                st.write("**Ubicación**")
                st.write(fila["Ubicación"])

            with col3:
                st.write("**Stock**")

            if con_stock:

                st.write(
                    f"**{fila['Libre utilización']} {fila['Unidad medida base']}**"
                )

            else:

                st.markdown(
                    f"<span style='color:red;'>{fila['Libre utilización']} {fila['Unidad medida base']}</span>",
                    unsafe_allow_html=True
                )

# =========================
# PARAMETRIZACIÓN
# =========================

st.divider()
st.markdown("#### ⚙️ Parametrización")


col4, col5, col6, col7 = st.columns(4)


with col4:
    st.write("**Planificación**")
    st.write(fila["Caract.planif.nec."])


with col5:
    st.write("**Punto Pedido**")
    st.write(fila["Punto de pedido"])


with col6:
    st.write("**Stock Máximo**")
    st.write(fila["Stock máximo"])


 with col7:
    st.write("**Parte Crítica**")

    if str(fila["Parte crítica"]).strip():

        st.write("SI")

    else:

        st.write("NO")
