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
# ESTILOS CSS (MEJORADOS)
# =====================================================
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    /* Contenedor principal centrado y con ancho máximo */
    .block-container { max-width: 900px; padding-top: 2rem; }
    
    /* Estilo para el título principal */
    .titulo { text-align: center; color: #d71920; font-size: 32px; font-weight: 800; margin-bottom: 5px; margin-top: 15px; }
    
    /* Estilo para el subtítulo */
    .subtitulo { text-align: center; color: #666; font-size: 16px; margin-bottom: 25px; }
    
    /* Estilo para las tarjetas de resultados */
    .card {
        background: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #d71920;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    
    /* Clases de stock */
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
        # Intenta cargar el archivo Excel. Asegúrate de que el nombre sea correcto.
        df = pd.read_excel("mi inventario.xlsx")
        
        # Limpieza y normalización de datos
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
# INTERFAZ Y CABECERA (CORREGIDA)
# =====================================================
# Estructura de 3 columnas para centrar el logo de forma precisa
col_l, col_c, col_r = st.columns([1, 1.5, 1])

with col_c:
    try:
        # Se ha eliminado 'use_container_width=True' y se usa 'width=400' 
        # junto con una imagen de alta resolución para evitar cortes y pixelado.
        st.image("logo.png", width=400, output_format="PNG")
    except:
        st.write("Logo no encontrado. Asegúrate de que 'logo.png' esté en la carpeta.")

# Títulos y línea divisoria
st.markdown("<div class='titulo'>Consulta de Inventario Almacén Repuestos</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitulo'>Búsqueda inteligente por código, descripción, medida y sinónimos</div>", unsafe_allow_html=True)
st.divider()

# Detener si no se cargaron datos
if df is None:
    st.stop()

# =====================================================
# FILTROS
# =====================================================
# Estructura de 2 columnas para el buscador y el selector de ubicación
col1, col2 = st.columns([4, 1])

with col1:
    # Aseguramos que 'consulta' siempre tenga un valor inicial para evitar NameError
    consulta = st.text_input("🔍 Buscar por código, nombre, medida o descripción", placeholder="Ejemplo: 1170371, escoba, trapero...", value="")

with col2:
    ubicaciones = ["Todas"] + sorted(df["Ubic."].unique().tolist())
    filtro_ubicacion = st.selectbox("Ubicación", ubicaciones, index=0)

# =====================================================
# LÓGICA DE BÚSQUEDA Y VISUALIZACIÓN
# =====================================================
if consulta:
    # 1. Preparar datos para búsqueda inteligente
    # Combinamos descripción y código para una búsqueda más robusta
    df['search_col'] = df["Texto breve de material"] + " " + df["Material"]
    
    # 2. Ejecutar búsqueda difusa (Fuzzy Search) con RapidFuzz
    # fuzz.WRatio es un buen equilibrio para textos generales
    resultados_data = process.extract(
        consulta.lower(), 
        df['search_col'].tolist(), 
        scorer=fuzz.WRatio, 
        limit=30
    )
    
    # 3. Filtrar resultados por score (umbral de 60 para relevancia)
    indices = [df.index[i] for val, score, i in resultados_data if score > 60]
    resultados = df.loc[indices]

    # 4. Aplicar filtro de ubicación secundario
    if filtro_ubicacion != "Todas":
        resultados = resultados[resultados["Ubic."] == filtro_ubicacion]

    # 5. Visualizar resultados
    if not resultados.empty:
        st.success(f"Se encontraron {len(resultados)} resultado(s)")
        
        for _, fila in resultados.iterrows():
            stock = float(fila["Cantidad stock valorado"])
            # Determinar la clase CSS del stock
            clase = "stock-bajo" if stock <= 5 else ("stock-medio" if stock <= 15 else "stock-alto")
            
            # Formatear y renderizar la tarjeta
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
    # Mensaje inicial si no hay búsqueda
    st.info("Ingrese un código o descripción para comenzar a buscar.")
