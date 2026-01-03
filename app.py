import streamlit as st
import pandas as pd
import re

# Configuración de página
st.set_page_config(page_title="Campaña T3F", layout="wide")

st.title("📍 Buscador de Vecinos - Tres de Febrero")
st.markdown("Herramienta de logística territorial. Base de datos integrada.")

# --- FUNCIÓN DE CARGA (Con Memoria Caché) ---
@st.cache_data
def cargar_datos():
    # Nombre EXACTO del archivo que subiste a GitHub
    nombre_archivo = "Padrón PJ 2022.xlsx - Todo Corte 18.csv"
    
    try:
        # Intentamos leerlo asumiendo que es un CSV separado por comas
        df = pd.read_csv(nombre_archivo, encoding='latin-1', sep=',')
        
        # Si vemos que se cargó todo en una sola columna (error común), probamos con punto y coma
        if df.shape[1] < 2:
             df = pd.read_csv(nombre_archivo, encoding='latin-1', sep=';')
             
        return df
    except FileNotFoundError:
        return None

# --- FUNCIÓN DE LIMPIEZA DE DIRECCIÓN ---
def limpiar_direccion(texto):
    if not isinstance(texto, str):
        return None, None
    texto = texto.upper().strip()
    # Busca el patrón: "CALLE 1234" al inicio
    match = re.search(r"^([A-Z\s\.]+?)\s+(\d+)", texto)
    if match:
        return match.group(1).strip(), int(match.group(2))
    return None, None

# --- INICIO DE LA APP ---
with st.spinner('Cargando padrón, por favor espera...'):
    df = cargar_datos()

if df is not None:
    # Verificamos si existe la columna Domicilio
    if 'Domicilio' in df.columns:
        
        # Procesamiento de direcciones (en tiempo real)
        if 'Calle_Limpia' not in df.columns:
            # Extraemos calle y altura
            datos_limpios = df['Domicilio'].apply(lambda x: pd.Series(limpiar_direccion(x)))
            df['Calle_Limpia'] = datos_limpios[0]
            df['Altura_Limpia'] = datos_limpios[1]
            # Filtramos los que tienen dirección válida
            df = df.dropna(subset=['Calle_Limpia', 'Altura_Limpia'])

        st.success(f"✅ Base de Datos Conectada: {len(df)} afiliados disponibles.")
        st.divider()
        
        # --- BUSCADOR ---
        col1, col2 = st.columns([2, 1])
        with col1:
            busqueda = st.text_input("🔍 Buscar Afiliado (Apellido o DNI):", placeholder="Escribe apellido o número...")

        if busqueda:
            # Filtro por Apellido o DNI
            filtro = df[df['Apellido'].str.contains(busqueda.upper(), na=False) | 
                       df['Matricula'].astype(str).str.contains(busqueda, na=False)]
            
            if not filtro.empty:
                # Menú desplegable para elegir al afiliado correcto
                opciones = {f"{row['Apellido']} {row['Nombre']} - {row['Calle_Limpia']} {int(row['Altura_Limpia'])}": i for i, row in filtro.iterrows()}
                seleccion = st.selectbox("Resultados encontrados:", list(opciones.keys()))
                
                if seleccion:
                    idx = opciones[seleccion]
                    objetivo = df.loc[idx]
                    
                    st.info(f"📌 **CENTRO:** {objetivo['Apellido']} {objetivo['Nombre']} | {objetivo['Calle_Limpia']} {int(objetivo['Altura_Limpia'])}")
                    
                    # --- CÁLCULO DE VECINOS ---
                    rango = st.slider("Radio de búsqueda (en numeración de calle):", 100, 800, 400)
                    
                    # Buscamos en la misma calle, con altura +/- rango
                    vecinos = df[
                        (df['Calle_Limpia'] == objetivo['Calle_Limpia']) &
                        (df['Altura_Limpia'] >= objetivo['Altura_Limpia'] - rango) &
                        (df['Altura_Limpia'] <= objetivo['Altura_Limpia'] + rango) &
                        (df['Matricula'] != objetivo['Matricula']) # Excluir al mismo objetivo
                    ].copy()
                    
                    # Calculamos distancia numérica
                    vecinos['Distancia'] = abs(vecinos['Altura_Limpia'] - objetivo['Altura_Limpia'])
                    vecinos = vecinos.sort_values('Distancia')
                    
                    st.write(f"**Se encontraron {len(vecinos)} afiliados cercanos en la misma calle:**")
                    st.dataframe(vecinos[['Apellido', 'Nombre', 'Domicilio', 'Distancia']], use_container_width=True)
            else:
                st.warning("No se encontraron resultados con ese dato.")
    else:
        st.error("Error: El archivo no tiene la columna 'Domicilio'.")
else:
    # Mensaje de error si no encuentra el archivo con el nombre exacto
    st.error("⚠️ No encuentro el archivo. Asegúrate de que en GitHub se llame exactamente: Padrón PJ 2022.xlsx - Todo Corte 18.csv")
