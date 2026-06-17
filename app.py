import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
st.set_page_config(
    page_title="Consulta Inventario Repuestos",
    page_icon="📦",
    layout="wide"
)

# =====================================================
# ESTILOS CSS
# =====================================================
st.markdown("""
<style>
    .main { background-color: #f5f7fa; }
    .block-container { max-width: 900px; padding-top: 2rem; }
    .titulo { text-align: center; color: #d71920; font-size: 32px; font-weight: 800; margin-bottom: 5px; }
    .subtitulo { text-align: center; color: #666; font-size: 16px; margin-bottom: 20px; }
    .card {
        background: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #d71920;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .stock-alto { color: #28a745; font-weight: bold; }
    .stock-medio { color: #ff9800; font-weight: bold; }
    .stock-bajo { color: #dc3545; font-weight: bold; }
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
        df["Material"] = df["Material"].astype(str).str.strip()
        df["Texto breve de material"] = df["Texto breve de material"].fillna("").astype(str).str.strip()
        df["Ubic."] = df["Ubic."].fillna("No asignada").astype(str).str.strip()
        df["UMB"] = df["UMB"].fillna("UN").astype(str).str.strip()
        df["Cantidad stock valorado"] = pd.to_numeric(df["Cantidad stock valorado"], errors="coerce").fillna(0)
        return df
    except Exception as e:
        st.error(f"Error cargando Excel: {e}")
        return None

df = cargar_datos()

# =====================================================
# INTERFAZ Y LOGO
# =====================================================
col_l, col_c, col_r = st.columns([1, 2, 1])
with col_c:
    try:
        st.image("logo.png", width=400)
    except:
        st.write("Logo no encontrado")

st.markdown("<div class='titulo'>Consulta de Inventario Almacén Repuestos</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitulo'>Búsqueda inteligente por código, descripción, medida y sinónimos</div>", unsafe_allow_html=True)
st.divider()

if df is None:
    st.stop()

# =====================================================
# FILTROS
# =====================================================
col1, col2 = st.columns([4, 1])
with col1:
    consulta = st.text_input("🔍 Buscar por código, nombre, medida o descripción", value="")
with col2:
    ubicaciones = ["Todas"] + sorted(df["Ubic."].unique().tolist())
    filtro_ubicacion = st.selectbox("Ubicación", ubicaciones)

# =====================================================
# LÓGICA DE BÚSQUEDA
# =====================================================
if consulta:
    df['search_col'] = df["Texto breve de material"] + " " + df["Material"]
    
    resultados_data = process.extract(
        consulta.lower(), 
        df['search_col'].tolist(), 
        scorer=fuzz.WRatio, 
        limit=30
    )
    
    indices = [df.index[i] for val, score, i in resultados_data if score > 60]
    resultados = df.loc[indices]

    if filtro_ubicacion != "Todas":
        resultados = resultados[resultados["Ubic."] == filtro_ubicacion]

    if not resultados.empty:
        st.success(f"Se encontraron {len(resultados)} resultado(s)")
        for _, fila in resultados.iterrows():
            stock = float(fila["Cantidad stock valorado"])
            clase = "stock-bajo" if stock <= 5 else ("stock-medio" if stock <= 15 else "stock-alto")
            
            # Cierre de triple comillas pegado al borde izquierdo para evitar el error de sintaxis
            st.markdown(f"""
<div class="card">
    <h4>{fila['Texto breve de material']}</h4>
    <b>Código:</b> {fila['Material']}<br>
    <b>Ubicación:</b> {fila['Ubic.']}<br>
    <b>Stock:</b> <span class="{clase}">{stock:,.0f} {fila['UMB']}</span>
</div>
""", unsafe_allow_html=True)
    else:
        st.error("No se encontraron resultados para tu búsqueda.")
else:
    st.info("Ingrese un código o descripción para comenzar a buscar.")
