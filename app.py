import pandas as pd
import plotly.express as px
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title='Monitor de Habilitaciones CABA',
    page_icon='📊',
    layout='wide',
)

st.title('📊 Monitor de Habilitaciones Comerciales - CABA')
st.write(
    'Análisis territorial, distribución por rubros y estadísticas detalladas por'
    ' comuna.'
)


# Cargar los datos optimizados
@st.cache_data
def cargar_datos():
  df = pd.read_csv('datos_web.csv')
  return df


try:
  df = cargar_datos()

  # Limpiar espacios en blanco en los nombres de las columnas
  df.columns = df.columns.str.strip()

  # Detección inteligente de columnas (flexible ante mayúsculas/minúsculas)
  col_comuna = next(
      (c for c in df.columns if c.lower() in ['comuna', 'comunas']), None
  )
  col_barrio = next(
      (c for c in df.columns if c.lower() in ['barrio', 'barrios']), None
  )
  col_rubro = next(
      (c for c in df.columns if c.lower() in ['rubro', 'rubros']), None
  )
  col_lat = next(
      (c for c in df.columns if c.lower() in ['lat', 'latitud']), None
  )
  col_lon = next(
      (c for c in df.columns if c.lower() in ['lon', 'long', 'longitud']), None
  )
  col_rs = next(
      (c for c in df.columns if 'razon' in c.lower() or 'social' in c.lower()),
      df.columns[0],
  )

  # --- BARRA LATERAL (FILTROS) ---
  st.sidebar.header('Filtros de Búsqueda')

  if col_comuna:
    comunas = ['Todas'] + sorted(
        df[col_comuna].dropna().astype(str).unique().tolist()
    )
    comuna_elegida = st.sidebar.selectbox('Seleccionar Comuna', comunas)
    if comuna_elegida != 'Todas':
      df = df[df[col_comuna].astype(str) == comuna_elegida]

  if col_barrio:
    barrios = ['Todos'] + sorted(
        df[col_barrio].dropna().astype(str).unique().tolist()
    )
    barrio_elegido = st.sidebar.selectbox('Seleccionar Barrio', barrios)
    if barrio_elegido != 'Todos':
      df = df[df[col_barrio].astype(str) == barrio_elegido]

  if col_rubro:
    rubros = ['Todos'] + sorted(
        df[col_rubro].dropna().astype(str).unique().tolist()
    )
    rubro_elegido = st.sidebar.selectbox('Seleccionar Rubro', rubros)
    if rubro_elegido != 'Todos':
      df = df[df[col_rubro].astype(str) == rubro_elegido]

  total_habilitaciones = len(df)

  # Detectar año o período si existe
  anio_texto = '2025 / 2026'
  for col in df.columns:
    if 'anio' in col.lower() or 'año' in col.lower() or 'fecha' in col.lower():
      try:
        anios_unicos = df[col].astype(str).str.extract(r'(20\d\d)').dropna()
        if not anios_unicos.empty:
          anio_texto = ', '.join(anios_unicos[0].unique())
      except:
        pass

  # --- SECCIÓN 1: TOTALES Y PORCENTAJES ---
  st.markdown('---')
  st.subheader('📈 1. Totales, Año y Porcentajes por Rubro')

  col_m1, col_m2 = st.columns(2)
  with col_m1:
    st.metric(
        label='Habilitaciones Totales', value=f'{total_habilitaciones:,}'
    )
  with col_m2:
    st.metric(label='Año / Período del Registro', value=anio_texto)

  if col_rubro and total_habilitaciones > 0:
    rubro_counts = df[col_rubro].value_counts()
    rubro_pct = df[col_rubro].value_counts(normalize=True) * 100
    df_rubro = pd.DataFrame(
        {'Cantidad': rubro_counts, 'Porcentaje (%)': rubro_pct}
    ).reset_index()
    df_rubro.columns = ['Rubro', 'Cantidad', 'Porcentaje (%)']

    st.markdown('**Distribución Porcentual por Rubro:**')
    st.dataframe(
        df_rubro.style.format({'Porcentaje (%)': '{:.2f}%'}),
        use_container_width=True,
        hide_index=True,
    )
  else:
    st.warning(
        'No se encontró la columna de Rubro para calcular los porcentajes.'
    )

  # --- SECCIÓN 2: MAPA ---
  st.markdown('---')
  st.subheader('🗺️ 2. Mapa de Distribución Territorial (Puntos por Rubro)')

  if col_lat and col_lon:
    df_mapa = df.dropna(subset=[col_lat, col_lon])
    if not df_mapa.empty:
      fig_map = px.scatter_mapbox(
          df_mapa,
          lat=col_lat,
          lon=col_lon,
          color=col_rubro if col_rubro else None,
          hover_name=col_rs,
          hover_data=[col_barrio, col_comuna]
          if col_barrio and col_comuna
          else None,
          zoom=11,
          height=500,
      )
      fig_map.update_layout(
          mapbox_style='open-street-map', margin=dict(l=0, r=0, t=0, b=0)
      )
      st.plotly_chart(fig_map, use_container_width=True)
    else:
      st.warning('No hay coordenadas válidas para mostrar en el mapa.')
  else:
    st.error(
        'No se encontraron las columnas de latitud y longitud (`lat` / `lon`).'
    )

  # --- SECCIÓN 3: COMUNAS ---
  st.markdown('---')
  st.subheader('🏆 3. Detalle de Comunas con Más Habilitaciones')

  if col_comuna and not df.empty:
    comuna_counts = df[col_comuna].value_counts().reset_index()
    comuna_counts.columns = ['Comuna', 'Cantidad']

    col_c1, col_c2 = st.columns([1, 1])
    with col_c1:
      fig_comuna = px.bar(
          comuna_counts,
          x='Comuna',
          y='Cantidad',
          text='Cantidad',
          title='Habilitaciones por Comuna',
          color='Cantidad',
          color_continuousScale='Blues',
      )
      st.plotly_chart(fig_comuna, use_container_width=True)

    with col_c2:
      st.markdown('**Ranking de Comunas:**')
      st.dataframe(comuna_counts, use_container_width=True, hide_index=True)
  else:
    st.warning('No se encontró la columna de comuna.')

  # --- SECCIÓN 4: RUBROS POR COMUNA ---
  st.markdown('---')
  st.subheader('🔍 4. Detalle de Rubros Predominantes por Comuna')

  if col_comuna and col_rubro and not df.empty:
    tabla_cruce = (
        pd.crosstab(
            df[col_comuna], df[col_rubro], margins=True, margins_name='Total'
        )
        .reset_index()
    )
    st.markdown(
        'Matriz de distribución: Cantidad de habilitaciones por Rubro en cada'
        ' Comuna'
    )
    st.dataframe(tabla_cruce, use_container_width=True)

    st.markdown('**Rubro líder (mayoritario) por cada Comuna:**')
    df_lideres = (
        df.groupby([col_comuna, col_rubro])
        .size()
        .reset_index(name='Cantidad')
    )
    idx_max = df_lideres.groupby(col_comuna)['Cantidad'].idxmax()
    df_lideres_top = df_lideres.loc[idx_max].sort_values(
        by='Cantidad', ascending=False
    )
    df_lideres_top.columns = ['Comuna', 'Rubro Principal', 'Cantidad']
    st.dataframe(
        df_lideres_top, use_container_width=True, hide_index=True
    )
  else:
    st.warning('Se requieren las columnas de comuna y rubro para este análisis.')

  # --- TABLA COMPLETA Y DESCARGA ---
  st.markdown('---')
  st.subheader('📋 Detalle Completo de Registros')
  st.dataframe(df, use_container_width=True)

  csv_export = df.to_csv(index=False).encode('utf-8')
  st.download_button(
      label='📥 Descargar datos filtrados en CSV',
      data=csv_export,
      file_name='habilitaciones_filtradas_por_comuna.csv',
      mime='text/csv',
  )

except Exception as e:
  st.error(
      '❌ Ocurrió un error al cargar la aplicación. Aquí tienes el detalle'
      ' técnico exacto:'
  )
  st.exception(e)
