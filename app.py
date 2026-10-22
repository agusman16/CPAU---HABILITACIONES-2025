import pandas as pd
import streamlit as st

# Configuración de la página en ancho completo
st.set_page_config(
    page_title='Monitor de Habilitaciones CABA',
    page_icon='🗺️',
    layout='wide',
)

st.title('🗺️ Monitor Interactivo de Habilitaciones - CABA')
st.write(
    'Visualizador georreferenciado filtrado por Comuna, Barrio y Rubro en la'
    ' nube.'
)


# Cargar los datos optimizados
@st.cache_data
def cargar_datos():
  # Renombra o asegúrate de que el archivo en GitHub se llame datos_web.csv
  df = pd.read_csv('datos_web.csv')
  return df


try:
  df = cargar_datos()

  # --- BARRA LATERAL (FILTROS) ---
  st.sidebar.header('Filtros de Búsqueda')

  # 1. Filtro por Comuna
  if 'comuna' in df.columns:
    comunas = ['Todas'] + sorted(
        df['comuna'].dropna().astype(str).unique().tolist()
    )
    comuna_elegida = st.sidebar.selectbox('Seleccionar Comuna', comunas)
    if comuna_elegida != 'Todas':
      df = df[df['comuna'].astype(str) == comuna_elegida]

  # 2. Filtro por Barrio
  if 'barrio' in df.columns:
    barrios = ['Todos'] + sorted(
        df['barrio'].dropna().astype(str).unique().tolist()
    )
    barrio_elegido = st.sidebar.selectbox('Seleccionar Barrio', barrios)
    if barrio_elegido != 'Todos':
      df = df[df['barrio'].astype(str) == barrio_elegido]

  # 3. Filtro por Rubro
  if 'Rubro' in df.columns:
    rubros = ['Todos'] + sorted(
        df['Rubro'].dropna().astype(str).unique().tolist()
    )
    rubro_elegido = st.sidebar.selectbox('Seleccionar Rubro', rubros)
    if rubro_elegido != 'Todos':
      df = df[df['Rubro'].astype(str) == rubro_elegido]

  # --- CUERPO PRINCIPAL ---
  col1, col2 = st.columns([2, 1])

  with col1:
    st.metric(label='Habilitaciones Filtradas', value=f'{len(df):,}')

  # --- MAPA INTERACTIVO ---
  st.subheader('📍 Mapa de Ubicaciones')
  if 'lat' in df.columns and 'lon' in df.columns:
    # Filtramos valores nulos de coordenadas para evitar errores en el mapa
    df_mapa = df.dropna(subset=['lat', 'lon'])
    if not df_mapa.empty:
      st.map(df_mapa, latitude='lat', longitude='lon', zoom=11)
    else:
      st.warning('No hay coordenadas válidas para mostrar en el mapa.')
  else:
    st.error('El archivo no contiene las columnas lat y lon.')

  # --- TABLA DE DATOS ---
  st.subheader('📋 Detalle de Registros')
  st.dataframe(df, use_container_width=True)

  # Botón de descarga
  csv_export = df.to_csv(index=False).encode('utf-8')
  st.download_button(
      label='📥 Descargar datos filtrados en CSV',
      data=csv_export,
      file_name='habilitaciones_filtradas_web.csv',
      mime='text/csv',
  )

except Exception as e:
  st.error(
      'Error al cargar la aplicación. Asegúrate de haber subido'
      ' `datos_web.csv` con columnas `lat` y `lon` a tu repositorio de GitHub.'
  )
  st.write(f'Detalle técnico: {e}')