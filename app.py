import streamlit as st
import pandas as pd
from rapidfuzz import process

# Configuración visual de la aplicación
st.set_page_config(page_title="Consulta de Inventario", page_icon="📦", layout="centered")

st.markdown("<h1 style='text-align: center;'>📦 Consulta de Inventario</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Busca códigos, descripciones o ubicaciones al instante</p>", unsafe_allow_html=True)
st.divider()

# Función optimizada para cargar la base de datos
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("mi inventario.xlsx")
        # Limpiamos posibles espacios invisibles en los títulos de las columnas
        df.columns = df.columns.astype(str).str.strip()
        return df
    except FileNotFoundError:
        st.error("⚠️ No se encontró el archivo 'mi inventario.xlsx' en el repositorio.")
        return None

df = cargar_datos()

if df is not None:
    # Definición exacta de tus columnas reales
    COL_CODIGO = "Material"
    COL_DESCRIPCION = "Texto breve de material"
    COL_UBICACION = "Ubic."
    COL_UNIDAD = "UMB"
    COL_STOCK = "Cantidad stock valorado"

    # Caja de texto limpia para el usuario
    consulta = st.text_input("🔍 Escriba el producto, descripción o código a buscar:", placeholder="Ej: trapero, de walt, 1170371...")

    if consulta:
        consulta_limpia = consulta.strip().lower()

        # Palabras comunes a ignorar si el usuario escribe una frase conversacional
        palabras_ignorar = ["hola", "me", "das", "por", "favor", "el", "la", "los", "las", "un", "una", "de", "del", "buscar", "codigo", "producto", "búscame", "buscame", "necesito", "stock"]
        palabras_clave = [p for p in consulta_limpia.split() if p not in palabras_ignorar]

        if palabras_clave:
            # FILTRADO CORREGIDO: Cada palabra clave ingresada DEBE existir como una palabra exacta o fragmento real
            # Esto evita que "medio" ruede y encuentre "intermedio" de manera incorrecta.
            mascara = pd.Series(True, index=df.index)
            
            for palabra in palabras_clave:
                # Comprobamos si la palabra está en el código o en la descripción de forma más estricta
                en_codigo = df[COL_CODIGO].astype(str).str.lower().str.contains(palabra, na=False)
                en_descripcion = df[COL_DESCRIPCION].astype(str).str.lower().str.contains(r'\b' + palabra + r'\b', regex=True, na=False)
                
                # Si la palabra es muy corta o tiene caracteres especiales, usamos una búsqueda normal para no romper el sistema
                if len(palabra) <= 3 or not palabra.isalnum():
                    en_descripcion = df[COL_DESCRIPCION].astype(str).str.lower().str.contains(palabra, na=False)
                
                mascara = mascara & (en_codigo | en_descripcion)

            resultados = df[mascara]
        else:
            resultados = pd.DataFrame()

        # Mostrar resultados de forma estética
        if not resultados.empty:
            st.success(f"✅ Se encontraron {len(resultados)} coincidencia(s):")
            
            for _, fila in resultados.iterrows():
                # Tarjeta limpia para cada producto
                with st.container():
                    st.markdown(f"### 🔹 {fila[COL_DESCRIPCION]}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"**🔢 Código:** `{fila[COL_CODIGO]}`")
                    with col2:
                        ub = fila[COL_UBICACION] if pd.notna(fila[COL_UBICACION]) else "No asignada"
                        st.markdown(f"**📍 Ubicación:** {ub}")
                    with col3:
                        stock_val = fila[COL_STOCK] if pd.notna(fila[COL_STOCK]) else 0
                        unidad_val = fila[COL_UNIDAD] if pd.notna(fila[COL_UNIDAD]) else "UN"
                        st.markdown(f"**📊 Stock:** {int(stock_val)} {unidad_val}")
                    
                    st.markdown("<div style='padding: 2px;'></div>", unsafe_allow_html=True)
                    st.divider()
        else:
            st.error("❌ No se encontraron resultados exactos con esos términos.")
            
            # Sistema de sugerencia inteligente por si se escribe con errores de ortografía
            lista_descripciones = df[COL_DESCRIPCION].astype(str).tolist()
            sugerencia = process.extractOne(consulta, lista_descripciones)
            
            if sugerencia and sugerencia[1] > 55:
                st.warning(f"💡 ¿Tal vez quisiste decir: **{sugerencia[0]}**?")
