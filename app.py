import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
import unicodedata
import re

# =====================================================
# CONFIGURACIÓN Y OPTIMIZACIÓN DE TEXTO
# =====================================================
st.set_page_config(page_title="Consulta Inventario", page_icon="⚙️", layout="centered")

def normalizar_texto(texto):
    texto = str(texto).lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = texto.replace("v", "b").replace("-", "")
    texto = re.sub(r'(\d+)/(\d+)', r'\1_\2', texto)
    texto = texto.replace("/", " ").replace("cab/hex", "cab hex")
    texto = re.sub(r'[^a-z0-9\s]', ' ', texto)
    return " ".join(texto.split())

@st.cache_data
def cargar_datos():
    df = pd.read_excel("mi inventario.xlsx")
    df.columns = df.columns.astype(str).str.strip()
    
    # Pre-procesamiento de columnas clave (Limpieza una sola vez)
    for col in ["Material", "Texto breve de material", "Ubicación", "Unidad medida base", "Caract.planif.nec.", "Parte crítica"]:
        df[col] = df[col].fillna("").astype(str).str.strip()
    
    # Limpieza numérica vectorizada
    for col in ["Libre utilización", "Punto de pedido", "Stock máximo"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    
    # Pre-computar columna de búsqueda
    df["search_col"] = (df["Texto breve de material"] + " " + df["Material"]).apply(normalizar_texto)
    return df

df = cargar_datos()

# =====================================================
# INTERFAZ (UI)
# =====================================================
st.markdown("<h1 style='text-align: center;'>Consulta de Inventario 📦</h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([4, 1, 2])
with col1:
    consulta = st.text_input("🔍 Buscar descripción", placeholder="Ej: Rodamiento 6205").strip()
with col2:
    letras = sorted(df["Ubicación"].str[0].dropna().unique().tolist())
    filtro_ubicacion = st.selectbox("📍 Ubicación", ["Todas"] + letras)
with col3:
    orden = st.selectbox("↕ Orden", ["Relevancia", "Ubicación (A-Z)", "Descripción (A-Z)"])

# =====================================================
# LÓGICA DE BÚSQUEDA VECTORIZADA
# =====================================================
if consulta or filtro_ubicacion != "Todas":
    # 1. Filtrado inicial
    df_busqueda = df.copy()
    if filtro_ubicacion != "Todas":
        df_busqueda = df_busqueda[df_busqueda["Ubicación"].str.startswith(filtro_ubicacion)]

    if consulta:
        consulta_norm = normalizar_texto(consulta)
        palabras = consulta_norm.split()
        
        # Filtro por coincidencia de todas las palabras (Vectorizado)
        mask = df_busqueda["search_col"].apply(lambda x: all(p in x for p in palabras))
        resultados = df_busqueda[mask].copy()

        # Si no hay resultados exactos, usar fuzzy (solo sobre los que ya pasaron el filtro de ubicación)
        if resultados.empty:
            match = process.extract(consulta_norm, df_busqueda["search_col"].tolist(), scorer=fuzz.WRatio, limit=20)
            indices = [m[2] for m in match if m[1] >= 55]
            resultados = df_busqueda.iloc[indices].copy()
            resultados["score"] = [m[1] for m in match if m[1] >= 55]
        else:
            resultados["score"] = 100

        # Ordenamiento
        if orden == "Descripción (A-Z)":
            resultados = resultados.sort_values("Texto breve de material")
        else:
            resultados = resultados.sort_values(["score", "Libre utilización"], ascending=False)

        # =====================================================
        # RENDERIZADO (MOSTRAR RESULTADOS)
        # =====================================================
        st.caption(f"Se encontraron {len(resultados)} resultados.")
        
        for _, fila in resultados.iterrows():
            color = "#e8f5e9" if fila["Libre utilización"] > 0 else "#ffebee"
            st.info(f"**{fila['Texto breve de material']}**")
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Código:** {fila['Material']}")
            c2.write(f"**Ubicación:** {fila['Ubicación']}")
            c3.markdown(f"<div style='background:{color}; text-align:center; padding:5px; border-radius:5px;'>{fila['Libre utilización']} {fila['Unidad medida base']}</div>", unsafe_allow_html=True)
            st.divider()
    else:
        st.write(df_busqueda)
