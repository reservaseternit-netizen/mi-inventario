import streamlit as st
import pandas as pd

st.set_page_config(page_title="Diagnóstico de Inventario", page_icon="📦")
st.title("📦 Diagnóstico de Columnas")

try:
    df = pd.read_excel("mi inventario.xlsx")
    st.success("¡Archivo Excel cargado correctamente!")
    
    # Esto nos va a mostrar en la página de internet la lista real de tus columnas
    st.subheader("📝 Las columnas reales de tu Excel son:")
    st.write(list(df.columns))
    
    st.subheader("👀 Vista previa de las primeras filas:")
    st.dataframe(df.head(3))

except FileNotFoundError:
    st.error("No se encontró el archivo 'mi inventario.xlsx'")
except Exception as e:
    st.error(f"Ocurrió un error al leer el Excel: {e}")
