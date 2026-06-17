import streamlit as st
import pandas as pd
from rapidfuzz import fuzz

# Configuración visual de la aplicación (Se usa un emoji de construcción/fábrica para Eternit)
st.set_page_config(page_title="Portal de Inventario | Eternit", page_icon="🏗️", layout="centered")

# --- ENCABEZADO PERSONALIZADO (Estilo Eternit Colombiana) ---
st.markdown(
    """
    <div style="text-align: center; padding-bottom: 10px;">
        <h1 style="color: #003366; margin-bottom: 5px; font-family: 'Segoe UI', Arial, sans-serif;">
            🏠 Consulta de Inventario y Repuestos
        </h1>
        <p style="color: #555555; font-size: 1.1rem; font-style: italic; margin-top: 0px;">
            Eternit Colombiana — Búsqueda Avanzada de Materiales, Tejas y Componentes
        </p>
    </div>
    """, 
    unsafe_allow_html=True
)
st.markdown("<p style='text-align: center; color: gray; font-size: 0.9rem;'>Filtro multi-criterio inteligente (Material, Medida, Código)</p>", unsafe_allow_html=True)
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
        st.error("⚠️ No se encontró el archivo 'mi inventario.xlsx'. Por favor verifique la ruta.")
        return None

df = cargar_datos()

if df is not None:
    COL_CODIGO = "Material"
    COL_DESCRIPCION = "Texto breve de material"
    COL_UBICACION = "Ubic."
    COL_UNIDAD = "UMB"
    COL_STOCK = "Cantidad stock valorado"

    # Input de búsqueda explicativo para el usuario (Alineado al contexto industrial/construcción)
    consulta = st.text_input(
        "🔍 Ingrese el producto, tipo de teja, repuesto o medida:", 
        placeholder="Ej: teja ondulada, perfil 7, niple galvanizado
