import streamlit as st
import pandas as pd
import re

# Configuración de página
st.set_page_config(page_title="Campaña T3F", layout="wide")

st.title("📍 Buscador de Vecinos - Tres de Febrero")
st.markdown("Herramienta de logística territorial. (Modo: Coincidencia Flexible)")

# --- 1. FUNCIÓN DE CARGA ---
@st.cache_data
def cargar_datos():
    nombre_archivo = "datos.csv" 
    try:
        df = pd.read_csv(nombre_archivo, encoding='latin-1', sep=',')
        if df.shape[1] < 2:
             df = pd.read_csv(nombre_archivo, encoding='latin-1', sep=';')
        return df
    except FileNotFoundError:
        return None

# --- 2. FUNCIÓN DE NORMALIZACIÓN DE CALLES ---
def normalizar_calle(texto_calle):
    if not isinstance(texto_calle, str):
        return ""
    
    # Pasamos a mayúsculas
    calle = texto_calle.upper().strip()
    
    # LISTA COMPLETA DE PREFIJOS A ELIMINAR
    # Eliminamos rangos y títulos para que "DR DE LA ROSA" sea igual a "DE LA ROSA"
    palabras_basura = [
        "AV.", "AV ", "AVENIDA ", 
        "CALLE ", 
        "PJE.", "PJE ", "PASAJE ", 
        "GRL.", "GRL ", "GRAL ", "GRAL. ", "GENERAL ", 
        "DR.", "DR ", "DOC ", "DOCTOR ",
        "ING.", "ING ", "INGENIERO ",
        "ARQ.", "ARQ ", "ARQUITECTO ",
        "PROF.", "PROF ", "PROFESOR ",
        "CNEL.", "CNEL ", "CORONEL ",
        "TTE.", "TTE ", "TENIENTE ",
        "SGTO.", "SGTO ", "SARGENTO ",
        "CAP.", "CAP ", "CAPITAN ",
        "MJOR.", "MJOR ", "MAYOR ",
        "CMTE.", "CMTE ", "COMANDANTE ",
        "ALTE.", "ALTE ", "ALMIRANTE ",
        "MONS.", "MONS ", "MONSEÑOR ",
        "PBRO.", "PBRO ", "PRESBITERO ",
        "INT.", "INT ", "INTENDENTE "
    ]
    
    for palabra in palabras_basura:
        if calle.startswith(palabra):
            calle = calle.replace(palabra, "")
            
    return calle.strip()

# --- 3. FUNCIÓN DE EXTRACCIÓN ---
def limpiar_direccion(texto):
    if not isinstance(texto, str):
        return None, None, None
    texto = texto.upper().strip()
    
    # Regex: Busca letras seguidas de números
    match = re.search(r"^([A-Z\s\.\d]+?)\s+(\d+)", texto)
    if match:
        calle_raw = match.group(1).strip()
        altura = int(match.group(2))
        calle_norm = normalizar_calle(calle_raw) # Generamos la versión limpia
        return calle_raw, altura, calle_norm
    return None, None, None

# --- INICIO DE LA APP ---
with st.spinner('Procesando datos con lógica flexible...'):
    df = cargar_datos()

if df is not None:
    if 'Domicilio' in df.columns:
        
        # Procesamos las direcciones
        if 'Calle_Norm' not in df.columns:
            datos_limpios = df['Domicilio'].apply(lambda x: pd.Series(limpiar_direccion(x)))
            df['Calle_Original'] = datos_limpios[0]
            df['Altura_Limpia'] = datos_limpios[1]
            df['Calle_Norm'] = datos_limpios[2]
            
            df = df.dropna(subset=['Calle_Norm', 'Altura_Limpia'])

        st.success(f"✅ Base lista: {len(df)} afiliados.")
        st.divider()

        # --- SELECTOR DE MODO ---
        modo_busqueda = st.radio("Modo:", ["👤 Buscar Persona", "🏠 Buscar Calle"], horizontal=True)
        st.divider()

        # MODO 1: PERSONA
        if "Persona" in modo_busqueda:
            col1, col2 = st.columns([2, 1])
            with col1:
                busqueda = st.text_input("🔍 Apellido o DNI:", placeholder="Ej: ERNANDES")

            if busqueda:
                filtro = df[df['Apellido'].str.contains(busqueda.upper(), na=False) | 
                           df['Matricula'].astype(str).str.contains(busqueda, na=False)]
                
                if not filtro.empty:
                    opciones = {f"{row['Apellido']} {row['Nombre']} - {row['Calle_Original']} {int(row['Altura_Limpia'])}": i for i, row in filtro.iterrows()}
                    seleccion = st.selectbox("Resultados:", list(opciones.keys()))
                    
                    if seleccion:
                        idx = opciones[seleccion]
                        objetivo = df.loc[idx]
                        
                        st.info(f"📌 **CENTRO:** {objetivo['Apellido']} {objetivo['Nombre']} | {objetivo['Calle_Original']} {int(objetivo['Altura_Limpia'])}")
                        
                        rango = st.slider("Radio (numeración):", 100, 1000, 500)
                        
                        # FILTRO POR CALLE NORMALIZADA
                        vecinos = df[
                            (df['Calle_Norm'] == objetivo['Calle_Norm']) & 
                            (df['Altura_Limpia'] >= objetivo['Altura_Limpia'] - rango) &
                            (df['Altura_Limpia'] <= objetivo['Altura_Limpia'] + rango) &
                            (df['Matricula'] != objetivo['Matricula'])
                        ].copy()
                        
                        vecinos['Distancia'] = abs(vecinos['Altura_Limpia'] - objetivo['Altura_Limpia'])
                        vecinos = vecinos.sort_values('Distancia')
                        
                        st.write(f"**Vecinos en la misma calle:** {len(vecinos)}")
                        st.dataframe(vecinos[['Apellido', 'Nombre', 'Domicilio', 'Distancia']], use_container_width=True)
                else:
                    st.warning("No encontrado.")

        # MODO 2: CALLE
        else:
            col1, col2 = st.columns(2)
            with col1:
                # Mostramos las calles ORIGINALES para elegir
                calle_input = st.selectbox("Calle:", sorted(df['Calle_Original'].unique()))
            with col2:
                altura_input = st.number_input("Altura (Opcional):", min_value=0, step=100)
            
            if calle_input:
                # Buscamos por la versión normalizada
                calle_norm_seleccionada = df[df['Calle_Original'] == calle_input]['Calle_Norm'].iloc[0]
                filtro_calle = df[df['Calle_Norm'] == calle_norm_seleccionada].copy()
                
                if altura_input > 0:
                    rango = st.slider("Radio:", 100, 1000, 500)
                    filtro_calle = filtro_calle[
                        (filtro_calle['Altura_Limpia'] >= altura_input - rango) &
                        (filtro_calle['Altura_Limpia'] <= altura_input + rango)
                    ]
                    filtro_calle['Diferencia'] = abs(filtro_calle['Altura_Limpia'] - altura_input)
                    filtro_calle = filtro_calle.sort_values('Diferencia')
                else:
                    filtro_calle = filtro_calle.sort_values('Altura_Limpia')

                st.success(f"🏘️ Encontrados: {len(filtro_calle)}")
                st.dataframe(filtro_calle[['Apellido', 'Nombre', 'Domicilio', 'Altura_Limpia']], use_container_width=True)

    else:
        st.error("Error: Columna 'Domicilio' no encontrada.")
else:
