import streamlit as st
import pandas as pd
from rapidfuzz import fuzz

# Configuración visual avanzada en pantalla completa (Recomendado para datos industriales)
st.set_page_config(
    page_title="Consulta de Inventario Pro", 
    page_icon="📦", 
    layout="wide"  # Cambiado a wide para evitar que las columnas de datos se amontonen
)

# Estilos CSS personalizados para mejorar el contraste técnico
st.markdown("""
    <style>
    .main { background-color: #f9fafb; }
    div[data-testid="stMetricValue"] { font-size: 22px !important; color: #1E3A8A; font-weight: bold; }
    .repuesto-card {
        background-color: #ffffff;
        padding: 14px 18px;
        border-radius: 8px;
        border-left: 5px solid #1E3A8A;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado estilizado sin perder tu esencia original
col_logo, col_titulo = st.columns([1, 12])
with col_logo:
    st.markdown("<h1 style='text-align: center; margin-top: 5px; margin-bottom: 0px;'>📦</h1>", unsafe_allow_html=True)
with col_titulo:
    st.markdown("<h2 style='margin-bottom: 0px; margin-top: 5px; color: #1E3A8A;'>Consulta de Inventario Pro</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B7280; font-size: 14px; margin-top: 0px; margin-bottom: 0px;'>Búsqueda avanzada multi-criterio (Material, Medida, Código)</p>", unsafe_allow_html=True)

st.divider()

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("mi inventario.xlsx")
        df.columns = df.columns.astype(str).str.strip()
        
        # --- PRE-PROCESAMIENTO INTERNO DE DATOS SUCIOS ---
        df["Material"] = df["Material"].astype(str).str.strip()
        df["Texto breve de material"] = df["Texto breve de material"].fillna("").astype(str).str.strip()
        df["Ubic."] = df["Ubic."].fillna("No asignada").astype(str).str.strip()
        df["UMB"] = df["UMB"].fillna("UN").astype(str).str.strip()
        df["Cantidad stock valorado"] = pd.to_numeric(df["Cantidad stock valorado"], errors='coerce').fillna(0).astype(int)
        
        return df
    except FileNotFoundError:
        st.error("⚠️ No se encontró el archivo 'mi inventario.xlsx'.")
        return None

df = cargar_datos()

if df is not None:
    COL_CODIGO = "Material"
    COL_DESCRIPCION = "Texto breve de material"
    COL_UBICACION = "Ubic."
    COL_UNIDAD = "UMB"
    COL_STOCK = "Cantidad stock valorado"

    # Input de búsqueda limpio
    consulta = st.text_input(
        "🔍 Filtre por producto, material, medida o largo:", 
        placeholder="Ej: niple galvanizado
    
