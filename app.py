import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Campaña T3F", layout="wide")

st.title("📍 Buscador de Vecinos - Tres de Febrero")
st.markdown("Herramienta para logística territorial. Sube el Padrón PJ y busca afiliados cercanos.")

# Función para limpiar la dirección
def limpiar_direccion(texto):
    if not isinstance(texto, str):
        return None, None
    texto = texto.upper().strip()
    # Buscar PATRON: Letras seguidas de Numeros (Ej: ALPATACAL 3408)
    match = re.search(r"^([A-Z\s\.]+?)\s+(\d+)", texto)
    if match:
        return match.group(1).strip(), int(match.group(2))
    return None, None

# Paso 1: Cargar Archivo
uploaded_file = st.file_uploader("📂 Sube aquí tu archivo CSV (Padron PJ)", type=["csv"])

if uploaded_file is not None:
    try:
        # Leemos el archivo
        df = pd.read_csv(uploaded_file, encoding='latin-1')
        
        # Verificamos si tiene las columnas necesarias
        if 'Domicilio' in df.columns:
            st.success(f"✅ Archivo cargado correctamente. {len(df)} afiliados en la lista.")
            
            # Procesamos las direcciones (solo se hace una vez)
            if 'Calle_Limpia' not in df.columns:
                datos_limpios = df['Domicilio'].apply(lambda x: pd.Series(limpiar_direccion(x)))
                df['Calle_Limpia'] = datos_limpios[0]
                df['Altura_Limpia'] = datos_limpios[1]
                # Quitamos los que no tienen dirección leíble
                df = df.dropna(subset=['Calle_Limpia', 'Altura_Limpia'])

            st.divider()
            
            # Paso 2: Buscador
            col1, col2 = st.columns([2, 1])
            with col1:
                busqueda = st.text_input("🔍 Buscar Afiliado (Apellido o DNI):")

            if busqueda:
                # Filtramos
                filtro = df[df['Apellido'].str.contains(busqueda.upper(), na=False) | 
                           df['Matricula'].astype(str).str.contains(busqueda, na=False)]
                
                if not filtro.empty:
                    # Selector
                    opciones = {f"{row['Apellido']} {row['Nombre']} - {row['Calle_Limpia']} {int(row['Altura_Limpia'])}": i for i, row in filtro.iterrows()}
                    seleccion = st.selectbox("Resultados encontrados (Elige uno):", list(opciones.keys()))
                    
                    if seleccion:
                        idx = opciones[seleccion]
                        objetivo = df.loc[idx]
                        
                        st.info(f"📌 **CENTRO:** {objetivo['Apellido']} {objetivo['Nombre']} | {objetivo['Calle_Limpia']} {int(objetivo['Altura_Limpia'])}")
                        
                        # Paso 3: Buscar Vecinos
                        rango = st.slider("Radio de búsqueda (en numeración de calle):", 100, 800, 500)
                        
                        # Lógica: Misma calle, altura +/- rango
                        vecinos = df[
                            (df['Calle_Limpia'] == objetivo['Calle_Limpia']) &
                            (df['Altura_Limpia'] >= objetivo['Altura_Limpia'] - rango) &
                            (df['Altura_Limpia'] <= objetivo['Altura_Limpia'] + rango) &
                            (df['Matricula'] != objetivo['Matricula'])
                        ].copy()
                        
                        vecinos['Distancia'] = abs(vecinos['Altura_Limpia'] - objetivo['Altura_Limpia'])
                        vecinos = vecinos.sort_values('Distancia')
                        
                        st.write(f"**Se encontraron {len(vecinos)} afiliados en la misma calle:**")
                        st.dataframe(vecinos[['Apellido', 'Nombre', 'Domicilio', 'Distancia']])
                        
                else:
                    st.warning("No se encontraron resultados.")
        else:
            st.error("El archivo no tiene la columna 'Domicilio'. Verifica el CSV.")
            
    except Exception as e:
        st.error(f"Error leyendo el archivo: {e}")
