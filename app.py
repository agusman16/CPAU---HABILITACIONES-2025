import pandas as pd
import pydeck as pdk
import streamlit as st

# Configuración de la página en ancho completo
st.set_page_config(
    page_title='Monitor Avanzado de Habilitaciones CABA',
    page_icon='📊',
    layout='wide',
)

st.title('📊 Monitor Avanzado e Interactivo de Habilitaciones - CABA')
st.write(
    'Visualizador con estadísticas por rubro/barrio y mapa de calor interactivo.'
)


# Cargar los datos optimizados
@st.cache_data
def cargar_datos():
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

  # 2. Filtro por Barrio (Dinámico según la comuna si se desea)
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

  # --- CUERPO PRINCIPAL: MÉTRICAS ---
  st.metric(
      label='Total de Habilitaciones Filtradas', value=f'{len(df):,}'
  )

  # --- SECCIÓN DE ESTADÍSTICAS (GRÁFICOS) ---
  st.markdown('---')
  st.subheader('📈 Estadísticas y Distribución')

  col_est1, col_est2 = st.columns(2)

  with col_est1:
    st.markdown('**Cantidad por Rubro**')
    if 'Rubro' in df.columns and not df.empty:
      df_rubro = df['Rubro'].value_counts().reset_index()
      df_rubro.columns = ['Rubro', 'Cantidad']
      st.bar_chart(df_rubro.set_index('Rubro'))
    else:
      st.write('No hay datos suficientes.')

  with col_est2:
    st.markdown('**Cantidad por Barrio**')
    if 'barrio' in df.columns and not df.empty:
      df_barrio = df['barrio'].value_counts().reset_index()
      df_barrio.columns = ['Barrio', 'Cantidad']
      st.bar_chart(df_barrio.set_index('Barrio'))
    else:
      st.write('No hay datos suficientes.')

  # --- SECCIÓN DE MAPA DE CALOR INTERACTIVO ---
  st.markdown('---')
  st.subheader('🔥 Mapa de Calor Interactivo (Concentración)')

  if 'lat' in df.columns and 'lon' in df.columns:
    df_mapa = df.dropna(subset=['lat', 'lon'])
    if not df_mapa.empty:
      # Configuración de la capa de calor 3D (HexagonLayer) con PyDeck
      layer = pdk.Layer(
          'HexagonLayer',
          data=df_mapa,
          get_position=['lon', 'lat'],
          radius=200,  # Radio de agrupaicón en metros
          elevation_scale=50,
          elevation_range=[0, 1000],
          pickable=True,
          extruded=True,
          coverage=1,
      )

      # Centrar el mapa en base a los puntos filtrados
      view_state = pdk.ViewState(
          latitude=df_mapa['lat'].mean(),
          longitude=df_mapa['lon'].mean(),
          zoom=12,
          pitch=45,  # Inclinación para efecto 3D
      )

      # Renderizar el mapa interactivo
      r = pdk.Deck(
          layers=[layer],
          initial_view_state=view_state,
          tooltip={
              'html': '<b>Concentración de Habilitaciones:</b> {elevationValue}',
              'style': {'backgroundColor': 'steelblue', 'color': 'white'},
          },
      )
      st.pydeck_chart(r)
    else:
      st.warning('No hay coordenadas válidas para generar el mapa de calor.')
  else:
    st.error('El archivo no contiene las columnas lat y lon.')

  # --- TABLA DE DATOS Y DESCARGA ---
  st.markdown('---')
  st.subheader('📋 Detalle de Registros')
  st.dataframe(df, use_container_width=True)

  csv_export = df.to_csv(index=False).encode('utf-8')
  st.download_button(
      label='📥 Descargar datos filtrados en CSV',
      data=csv_export,
      file_name='habilitaciones_filtradas_estadisticas.csv',
      mime='text/csv',
  )

except Exception as e:
  st.error(
      'Error al cargar la aplicación. Asegúrate de tener `datos_web.csv` con'
      ' las columnas correctas en tu repositorio.'
  )
  st.write(f'Detalle técnico: {e}')