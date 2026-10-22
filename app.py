import pandas as pd
import streamlit as st

# Configuración de la página en ancho completo
st.set_page_config(
    page_title='Monitor de Habilitaciones CABA',
    page_icon='🏙️',
    layout='wide',
)

st.title('🏙️ Monitor Integral de Habilitaciones - CABA')
st.write(
    'Panel analítico con totales, porcentajes por rubro, mapeo general y'
    ' particularidades por barrio.'
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

  # --- SECCIÓN 1: MÉTRICAS GENERALES Y PORCENTAJES POR RUBRO ---
  st.markdown('---')
  st.subheader('📊 Resumen General y Porcentajes por Rubro')

  total_habilitaciones = len(df)
  st.metric(
      label='Total de Habilitaciones Analizadas',
      value=f'{total_habilitaciones:,}',
  )

  if 'Rubro' in df.columns and total_habilitaciones > 0:
    # Calcular cantidades y porcentajes
    rubro_counts = df['Rubro'].value_counts()
    rubro_pct = df['Rubro'].value_counts(normalize=True) * 100
    df_rubro = pd.DataFrame(
        {'Cantidad': rubro_counts, 'Porcentaje (%)': rubro_pct}
    ).reset_index()
    df_rubro.columns = ['Rubro', 'Cantidad', 'Porcentaje (%)']

    col_m1, col_m2 = st.columns([1, 1])

    with col_m1:
      st.markdown('**Distribución Porcentual**')
      st.dataframe(
          df_rubro.style.format({'Porcentaje (%)': '{:.2f}%'}),
          use_container_width=True,
          hide_index=True,
      )

    with col_m2:
      st.markdown('**Gráfico de Rubros**')
      st.bar_chart(df_rubro.set_index('Rubro')['Cantidad'])
  else:
    st.warning('No hay datos suficientes de rubros para mostrar.')

  # --- SECCIÓN 2: MAPA DE PUNTOS EN TODA LA CIUDAD ---
  st.markdown('---')
  st.subheader('🗺️ Distribución Geográfica (Puntos en la Ciudad)')

  if 'lat' in df.columns and 'lon' in df.columns:
    df_mapa = df.dropna(subset=['lat', 'lon'])
    if not df_mapa.empty:
      st.map(df_mapa, latitude='lat', longitude='lon', zoom=11)
      st.caption(
          f'Mostrando {len(df_mapa):,} puntos geolocalizados en el mapa.'
      )
    else:
      st.warning('No hay coordenadas válidas para mostrar en el mapa.')
  else:
    st.error('El archivo no contiene las columnas lat y lon.')

  # --- SECCIÓN 3: ESTADÍSTICAS POR BARRIO Y PARTICULARIDADES ---
  st.markdown('---')
  st.subheader('🏙️ Estadísticas y Particularidades por Barrio')

  if 'barrio' in df.columns and not df.empty:
    barrio_counts = df['barrio'].value_counts().reset_index()
    barrio_counts.columns = ['Barrio', 'Cantidad']

    col_b1, col_b2 = st.columns([1, 1])

    with col_b1:
      st.markdown('**Concentración por Barrio**')
      st.bar_chart(barrio_counts.set_index('Barrio'))

    with col_b2:
      st.markdown('🔍 **Particularidades y Zonas a Atender**')
      # Generar insights automáticos basados en los datos filtrados
      top_barrio = barrio_counts.iloc[0]['Barrio']
      top_cant = barrio_counts.iloc[0]['Cantidad']
      pct_top = (top_cant / total_habilitaciones) * 100 if total_habilitaciones > 0 else 0
      
      st.info(
          f'• **Mayor concentración:** El barrio con mayor actividad registrada es **{top_barrio}**, '
          f'acumulando **{top_cant:,}** habilitaciones ({pct_top:.1f}% del total filtrado).'
      )
      
      if len(barrio_counts) > 1:
        bottom_barrio = barrio_counts.iloc[-1]['Barrio']
        bottom_cant = barrio_counts.iloc[-1]['Cantidad']
        st.warning(
            f'• **Menor presencia:** El barrio con menor dinámica en esta selección es **{bottom_barrio}** '
            f'con solo **{bottom_cant}** registros a atender.'
        )
      
      st.success(
          '• **Control territorial:** Utilice los filtros laterales de Comuna y Rubro para aislar '
          'zonas específicas y detectar desequilibrios comerciales o áreas de oportunidad.'
      )
  else:
    st.warning('No hay datos de barrios disponibles.')

  # --- TABLA DE DATOS Y DESCARGA ---
  st.markdown('---')
  st.subheader('📋 Detalle Completo de Registros')
  st.dataframe(df, use_container_width=True)

  csv_export = df.to_csv(index=False).encode('utf-8')
  st.download_button(
      label='📥 Descargar datos filtrados en CSV',
      data=csv_export,
      file_name='habilitaciones_filtradas_reporte.csv',
      mime='text/csv',
  )

except Exception as e:
  st.error(
      'Error al cargar la aplicación. Asegúrate de tener `datos_web.csv` con'
      ' las columnas correctas en tu repositorio.'
  )
  st.write(f'Detalle técnico: {e}')
