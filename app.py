import streamlit as st
import pandas as pd
from rapidfuzz import process

# Configuración de la interfaz
st.set_page_config(page_title="Consulta de Inventario", page_icon="📦")
st.title("📦 Consulta de Inventario")

# Función para cargar tu Excel
@st.cache_data
def cargar_datos():
    try:
        # Lee el archivo con el nombre exacto que tienes a la izquierda
        return pd.read_excel("mi inventario.xlsx")
    except FileNotFoundError:
        st.error("⚠️ No se encontró el archivo 'mi inventario.xlsx'. Asegúrate de que esté en la misma carpeta.")
        return None

df = cargar_datos()

if df is not None:
    # Caja de texto para buscar
    consulta = st.text_input("🔍 Escriba el producto, descripción o código:")

    if consulta:
        consulta_minuscula = consulta.lower()

        # Buscar coincidencias en la columna de descripción
        resultados = df[
            df["texto breve del material"]
            .astype(str)
            .str.lower()
            .str.contains(consulta_minuscula, na=False)
        ]

        if not resultados.empty:
            st.success(f"Se encontraron {len(resultados)} resultados:")
            for _, fila in resultados.iterrows():
                st.write(f"🔹 **Código:** {fila['codigo']}")
                st.write(f"📝 **Descripción:** {fila['texto breve del material']}")
                st.write(f"📍 **Ubicación:** {fila['ubic.']}")
                st.write(f"📦 **Unidad:** {fila['umb']}")
                st.write(f"📊 **Stock:** {fila['cantidad stock valioso']}")
                st.divider()
        else:
            # Si se escribe mal, busca aproximados con RapidFuzz
            opciones = df["texto breve del material"].astype(str).tolist()
            sugerencia = process.extractOne(consulta, opciones)
            
            st.error("❌ No se encontraron resultados exactos.")
            if sugerencia:
                st.warning(f"💡 ¿Quisiste decir: **{sugerencia[0]}**?")