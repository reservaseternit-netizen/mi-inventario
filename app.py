import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
st.set_page_config(page_title="Consulta Inventario Repuestos", page_icon="📦", layout="wide")

# =====================================================
# ESTILOS MEJORADOS
# =====================================================
st.markdown("""
<style>
    /* Centrar contenido y mejorar tipografía */
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
# LOGO CENTRADO
# =====================================================
# Usamos columnas para centrar el logo
col_l, col_c, col_r = st.columns([1, 2, 1])
with col_c:
    try:
        # Nota: Asegúrate que logo.png sea de alta resolución.
        # Si usas un SVG, se verá perfecto a cualquier tamaño.
        st.image("logo.png", use_container_width=True) 
    except:
        st.write("Logo no encontrado")

st.markdown("<div class='titulo'>Consulta de Inventario</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitulo'>Búsqueda inteligente por código, descripción, medida y sinónimos</div>", unsafe_allow_html=True)
st.divider()

# ... (El resto de tu lógica de carga de datos se mantiene igual)

# =====================================================
# BÚSQUEDA OPTIMIZADA CON RAPIDFUZZ
# =====================================================
# Usaremos 'process.extract' que es mucho más rápido y preciso
if consulta:
    # Combinamos descripción y código para buscar en ambos
    df['search_col'] = df[COL_DESCRIPCION] + " " + df[COL_CODIGO].astype(str)
    
    # Búsqueda difusa de alta velocidad
    resultados_data = process.extract(
        consulta.lower(), 
        df['search_col'].tolist(), 
        scorer=fuzz.WRatio, 
        limit=30
    )
    
    # Filtrar solo resultados relevantes
    indices = [df.index[i] for val, score, i in resultados_data if score > 60]
    resultados = df.loc[indices]

    # ... (lógica de filtrado de ubicación y visualización)
