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
        return pd.read_excel("mi inventario.xlsx")
    except FileNotFoundError:
        st.error("⚠️ No se encontró el archivo 'mi inventario.xlsx'. Asegúrate de que esté en la misma carpeta.")
        return None

df = cargar_datos()

if df is not None:
    # Limpieza automática de nombres de columnas (quita espacios raros)
    df.columns = df.columns.astype(str).str.strip()
    columnas_disponibles = list(df.columns)

    # Identificar automáticamente las mejores columnas para buscar y mostrar
    col_descripcion = next((c for c in columnas_disponibles if "texto" in c.lower() or "descrip" in c.lower() or "material" in c.lower()), columnas_disponibles[0])
    col_codigo = next((c for c in columnas_disponibles if "cod" in c.lower() or "id" in c.lower() or "num" in c.lower()), columnas_disponibles[0])
    col_ubicacion = next((c for c in columnas_disponibles if "ubic" in c.lower() or "pos" in c.lower()), None)
    col_stock = next((c for c in columnas_disponibles if "stock" in c.lower() or "cant" in c.lower() or "valioso" in c.lower()), None)
    col_unidad = next((c for c in columnas_disponibles if "umb" in c.lower() or "unid" in c.lower() or "med" in c.lower()), None)

    # Caja de texto para buscar
    consulta = st.text_input("🔍 Escriba el producto, descripción o código a buscar:")

    if consulta:
        # Extraer palabras clave de la consulta (por si escriben frases largas)
        palabras_ignorar = ["hola", "me", "das", "por", "favor", "el", "la", "los", "las", "un", "una", "de", "del", "buscar", "codigo"]
        palabras_clave = [p for p in consulta.lower().split() if p not in palabras_ignorar]
        
        # Si la frase quedó vacía tras limpiar, usamos la consulta original entera
        if not palabras_clave:
            palabras_clave = [consulta.lower()]

        # Filtrar el DataFrame buscando si CUALQUIERA de las palabras clave coincide
        mascara = pd.Series(False, index=df.index)
        for palabra in palabras_clave:
            coincide_desc = df[col_descripcion].astype(str).str.lower().str.contains(palabra, na=False)
            coincide_cod = df[col_codigo].astype(str).str.lower().str.contains(palabra, na=False)
            mascara = mascara | coincide_desc | coincide_cod
        
        resultados = df[mascara]

        if not resultados.empty:
            st.success(f"✅ Se encontraron {len(resultados)} resultados:")
            for _, fila in resultados.iterrows():
                st.write(f"🔹 **Código:** {fila[col_codigo]}")
                st.write(f"📝 **Descripción:** {fila[col_descripcion]}")
                if col_ubicacion: st.write(f"📍 **Ubicación:** {fila[col_ubicacion]}")
                if col_unidad: st.write(f"📦 **Unidad:** {fila[col_unidad]}")
                if col_stock: st.write(f"📊 **Stock:** {fila[col_stock]}")
                st.divider()
        else:
            # Búsqueda aproximada con la consulta entera en la descripción
            opciones = df[col_descripcion].astype(str).tolist()
            sugerencia = process.extractOne(consulta, opciones)
            
            st.error("❌ No se encontraron resultados exactos.")
            if sugerencia and sugerencia[1] > 50:  # Solo sugerir si se parece más de un 50%
                st.warning(f"💡 ¿Quisiste decir: **{sugerencia[0]}**?")
                
    # Pequeño panel informativo abajo
