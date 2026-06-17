import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
st.set_page_config(
    page_title="Consulta Inventario Repuestos - Eternit",
    page_icon="📦",
    layout="wide"
)

# =====================================================
# ESTILOS CSS
# =====================================================
st.markdown("""
<style>
    /* Estilo general */
    .main { background-color: #ffffff; }
    .block-container { max-width: 900px; padding-top: 2rem; }

    /* Títulos y Subtítulos */
    .titulo { text-align: center; color: #d71920; font-size: 32px; font-weight: 800; margin-bottom: 5px; }
    .subtitulo { text-align: center; color: #666; font-size: 16px; margin-bottom: 20px; }

    /* Contenedor del Logo Centrado */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 30px;
        width: 100%; /* Ocupa todo el ancho */
    }
    
    /* Imagen del Logo con ancho máximo controlado y alta resolución */
    .logo-container img {
        max-width: 400px; /* Tamaño máximo físico */
        height: auto;
        display: block; /* Asegura que el centrado flexbox funcione */
    }

    /* Estilos de Tarjetas de Resultado */
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
    
    /* Contenedor de Filtros */
    .filtros-container {
        display: flex;
        gap: 15px;
        margin-bottom: 20px;
        align-items: flex-end; /* Alinea los inputs en la base */
    }
    
    /* Ajuste de etiquetas de filtro */
    .stSelectbox label, .stTextInput label {
        font-weight: 600;
        color: #444;
    }
    
    /* Ícono de búsqueda en el input */
    .stTextInput div[data-baseweb="input"]::before {
        content: "🔍 ";
        padding-left: 10px;
        color: #888;
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
        df["Material"] = df["Material"].astype(str).str.strip()
        df["Texto breve de material"] = df["Texto breve de material"].fillna("").astype(str).str.strip()
        df["Ubic."] = df["Ubic."].fillna("No asignada").astype(str).str.strip()
        df["UMB"] = df["UMB"].fillna("UN").astype(str).str.strip()
        df["Cantidad stock valorado"] = pd.to_numeric(df["Cantidad stock valorado"], errors="coerce").fillna(0)
        
        # Columna de búsqueda en minúsculas para mayor eficiencia
        df['search_col'] = df["Texto breve de material"].str.lower() + " " + df["Material"].str.lower()
        return df
    except Exception as e:
        st.error(f"Error cargando Excel: {e}")
        return None

df = cargar_datos()

# =====================================================
# INTERFAZ - LOGO CENTRADO (MEJORADO)
# =====================================================
# Contenedor CSS para centrar y controlar el tamaño físico sin reescalar
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
try:
    # use_container_width=True carga la resolución completa
    # El CSS limita el ancho máximo a 400px
    st.image("logo.png", use_container_width=True)
except:
    st.error("No se pudo cargar 'logo.png'.")
st.markdown('</div>', unsafe_allow_html=True)

# Títulos
st.markdown("<div class='titulo'>Consulta de Inventario Almacén Repuestos</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitulo'>Búsqueda inteligente por código, descripción, medida y sinónimos</div>", unsafe_allow_html=True)
st.divider()

if df is None:
    st.stop()

# =====================================================
# FILTROS
# =====================================================
# Contenedor CSS para filtros
st.markdown('<div class="filtros-container">', unsafe_allow_html=True)

# Usamos la estructura de columnas original para la disposición
col1, col2 = st.columns([4, 1])
with col1:
    consulta = st.text_input("Buscar por código, nombre, medida o descripción", placeholder="Ejemplo: 1170371, escoba, trapero...")
with col2:
    ubicaciones = ["Todas"] + sorted(df["Ubic."].unique().tolist())
    filtro_ubicacion = st.selectbox("Ubicación", ubicaciones)

st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# LÓGICA DE BÚSQUEDA
# =====================================================
if consulta:
    # Filtrado previo por ubicación para mayor velocidad
    df_filtrado = df if filtro_ubicacion == "Todas" else df[df["Ubic."] == filtro_ubicacion]

    if not df_filtrado.empty:
        # Rapidfuzz sobre la serie directamente para usar índices reales
        resultados_data = process.extract(
            consulta.lower(), 
            df_filtrado['search_col'], 
            scorer=fuzz.WRatio, 
            limit=30
        )
        
        indices = [i for val, score, i in resultados_data if score > 60]
        resultados = df_filtrado.loc[indices]
    else:
        resultados = pd.DataFrame()

    # Mostrar resultados
    if not resultados.empty:
        st.success(f"Se encontraron {len(resultados)} resultado(s)")
        for _, fila in resultados.iterrows():
            stock = float(fila["Cantidad stock valorado"])
            clase = "stock-bajo" if stock <= 5 else ("stock-medio" if stock <= 15 else "stock-alto")
            
            st.markdown(f"""
            <div class="card">
                <h4>{fila['Texto breve de material']}</h4>
                <b>Código:
