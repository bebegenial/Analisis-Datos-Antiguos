import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')
#pip freeze > requirements.txt
##streamlit run main.py

# Configuración de la página
st.set_page_config(
    page_title="Análisis de Ventas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Función para cargar y procesar los datos
@st.cache_data
def load_data():
    try:
        # Cargar el archivo CSV
        df = pd.read_csv('Ventas.csv')
        
        # Convertir fechas
        df = df[df['Toma de contacto'].notna()]  # elimina filas con NaN
        df = df[df['Toma de contacto'].str.strip() != '']  # elimina filas con cadenas vacías o solo espacios
        df = df.reset_index(drop=True)  # reiniciar el índice después de eliminar filas

        # Convertir fechas
        df['Fecha de Creación'] = pd.to_datetime(df['Fecha de Creación'], format='%d/%m/%Y %H:%M')
        df['Fecha de Conversión'] = pd.to_datetime(df['Fecha de Conversión'], format='%d/%m/%Y', errors='coerce')
        df = df[(df['Fecha de Creación'].dt.year >= 2018) & (df['Fecha de Creación'].dt.year <= 2021)]
        df = df.reset_index(drop=True)  # reiniciar el índice después de eliminar filas
        
        # Crear columnas adicionales
        df['Año_Creacion'] = df['Fecha de Creación'].dt.year
        df['Mes_Creacion'] = df['Fecha de Creación'].dt.month
        df['Mes_Año_Creacion'] = df['Fecha de Creación'].dt.to_period('M')
        
        # Marcar si hubo conversión
        df['Convertido'] = df['Producto'].notna()
        
        # Calcular tiempo hasta conversión
        df['Dias_Hasta_Conversion'] = (df['Fecha de Conversión'] - df['Fecha de Creación']).dt.days.abs()
        
        return df
    except FileNotFoundError:
        st.error("No se encontró el archivo 'datos_ventas.csv'. Asegúrate de que esté en la misma carpeta.")
        return None
    except Exception as e:
        st.error(f"Error al cargar los datos: {str(e)}")
        return None

# Función principal
def main():
    st.title("📊 Análisis Completo de Datos de Ventas")
    st.markdown("---")
    
    # Cargar datos
    df = load_data()
    if df is None:
        return
    
    # Sidebar - Filtros
    st.sidebar.header("🎛️ Filtros de Control")
    
    # Filtro por fecha de creación
    min_date = df['Fecha de Creación'].min()
    max_date = df['Fecha de Creación'].max()
    
    fecha_inicio = st.sidebar.date_input(
        "Fecha de inicio",
        value=min_date,
        min_value=min_date,
        max_value=max_date
    )
    
    fecha_fin = st.sidebar.date_input(
        "Fecha de fin",
        value=max_date,
        min_value=min_date,
        max_value=max_date
    )
    
    # Filtro por toma de contacto
    tomas_contacto = ['Todos'] + list(df['Toma de contacto'].unique())
    toma_seleccionada = st.sidebar.multiselect(
        "Toma de contacto",
        options=tomas_contacto,
        default=[]
    )
    
    # Filtro por producto
    productos = ['Todos'] + list(df['Producto'].dropna().unique())
    producto_seleccionado = st.sidebar.multiselect(
        "Producto",
        options=productos,
        default=[]
    )
    
    # Aplicar filtros
    df_filtered = df[
        (df['Fecha de Creación'].dt.date >= fecha_inicio) &
        (df['Fecha de Creación'].dt.date <= fecha_fin)
    ]
    
    if toma_seleccionada:
        #df_filtered = df_filtered[df_filtered['Toma de contacto'] == toma_seleccionada]
        df_filtered = df_filtered[df_filtered['Toma de contacto'].isin(toma_seleccionada)]
    
    if producto_seleccionado:
        #df_filtered = df_filtered[df_filtered['Producto'] == producto_seleccionado]
        df_filtered = df_filtered[df_filtered['Toma de contacto'].isin(producto_seleccionado)]
    
    # Métricas principales
    st.header("📈 Métricas Principales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_registros = len(df_filtered)
    total_ventas = df_filtered['Convertido'].sum()
    tasa_conversion = (total_ventas / total_registros * 100) if total_registros > 0 else 0
    tiempo_promedio_conversion = df_filtered[df_filtered['Convertido']]['Dias_Hasta_Conversion'].mean()
    
    with col1:
        st.metric("Total de Registros", f"{total_registros:,}")
    
    with col2:
        st.metric("Total de Ventas", f"{total_ventas:,}")
    
    with col3:
        st.metric("Tasa de Conversión", f"{tasa_conversion:.2f}%")
    
    with col4:
        st.metric("Tiempo Prom. Conversión", f"{tiempo_promedio_conversion:.1f} días" if not pd.isna(tiempo_promedio_conversion) else "N/A")
    
    st.markdown("---")
    
    # Análisis por mes
    st.header("📅 Análisis Mensual")
    
    # Preparar datos mensuales
    monthly_data = df_filtered.groupby('Mes_Año_Creacion').agg({
        'Toma de contacto': 'count',
        'Convertido': 'sum'
    }).reset_index()

    monthly_data['Tasa_Conversion'] = (monthly_data['Convertido'] / monthly_data['Toma de contacto'] * 100)
    monthly_data['Mes_Año'] = monthly_data['Mes_Año_Creacion'].astype(str)

    # Gráfico de barras para "Toma de contacto"
    fig_contact_bars = px.bar(
        monthly_data,
        x='Mes_Año',
        y='Toma de contacto',
        title='Datos por Mes',
        labels={'Toma de contacto': 'Número de Datos'}
    )
    st.plotly_chart(fig_contact_bars, use_container_width=True)

    # Gráfico de barras para "Convertido" (Ventas)
    fig_sales_bars = px.bar(
        monthly_data,
        x='Mes_Año',
        y='Convertido',
        title='Ventas por Mes',
        labels={'Convertido': 'Número de Ventas'}
    )
    st.plotly_chart(fig_sales_bars, use_container_width=True)

    # Gráfico de línea para "Tasa de Conversión"
    fig_conversion_line = px.line(
        monthly_data,
        x='Mes_Año',
        y='Tasa_Conversion',
        title='Tasa de Conversión Mensual',
        markers=True,
        labels={'Tasa_Conversion': 'Tasa de Conversión (%)'}
    )
    st.plotly_chart(fig_conversion_line, use_container_width=True)
    
    # Análisis por año
    st.header("📊 Análisis Anual")
    
    yearly_data = df_filtered.groupby('Año_Creacion').agg({
        'Toma de contacto': 'count',
        'Convertido': 'sum'
    }).reset_index()
    
    # Convertir 'Año_Creacion' a entero
    yearly_data['Año_Creacion'] = yearly_data['Año_Creacion'].astype(int)
    
    yearly_data['Tasa_Conversion'] = (yearly_data['Convertido'] / yearly_data['Toma de contacto'] * 100)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_yearly_bars = px.bar(
            yearly_data, 
            x='Año_Creacion', 
            y=['Toma de contacto', 'Convertido'],
            title='Registros y Ventas por Año',
            barmode='group'
        )
        st.plotly_chart(fig_yearly_bars, use_container_width=True)
    
    with col2:
        fig_yearly_line = px.line(
            yearly_data,
            x='Año_Creacion',
            y='Tasa_Conversion',
            title='Tasa de Conversión por Año',
            markers=True
        )
        st.plotly_chart(fig_yearly_line, use_container_width=True)
    
    # Análisis por toma de contacto
    st.header("📞 Análisis por Toma de Contacto")
    
    contacto_data = df_filtered.groupby('Toma de contacto').agg(
        Total_Registros=('Toma de contacto', 'count'),
        Total_Ventas=('Convertido', 'sum')
    ).reset_index()
    contacto_data.columns = ['Toma de contacto', 'Total_Registros', 'Total_Ventas']
    contacto_data['Tasa_Conversion'] = (contacto_data['Total_Ventas'] / contacto_data['Total_Registros'] * 100)
    contacto_data = contacto_data.sort_values('Total_Ventas', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_contacto_pie = px.pie(
            contacto_data,
            values='Total_Ventas',
            names='Toma de contacto',
            title='Distribución de Ventas por Toma de Contacto'
        )
        st.plotly_chart(fig_contacto_pie, use_container_width=True)
    
    with col2:
        fig_contacto_bar = px.bar(
            contacto_data,
            x='Tasa_Conversion',
            y='Toma de contacto',
            orientation='h',
            title='Tasa de Conversión por Toma de Contacto',
            text='Tasa_Conversion'
        )
        fig_contacto_bar.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig_contacto_bar, use_container_width=True)
    
    # Tabla de resumen por toma de contacto
    st.subheader("Resumen por Toma de Contacto")
    contacto_display = contacto_data.copy()
    contacto_display['Tasa_Conversion'] = contacto_display['Tasa_Conversion'].round(2).astype(str) + '%'
    st.dataframe(contacto_display, use_container_width=True)
    
    # Análisis por producto
    st.header("🛍️ Análisis por Producto")
    
    producto_data = df_filtered[df_filtered['Convertido']].groupby('Producto').agg(
        Cantidad_Ventas=('Producto', 'count')
    ).reset_index()
    producto_data.columns = ['Producto', 'Cantidad_Ventas']
    producto_data = producto_data.sort_values('Cantidad_Ventas', ascending=False)
    #producto_data = df_filtered[df_filtered['Convertido']].groupby('Producto').size().reset_index(name='Cantidad_Ventas')
    #producto_data = producto_data.sort_values('Cantidad_Ventas', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_producto_bar = px.bar(
            producto_data.head(10),
            x='Cantidad_Ventas',
            y='Producto',
            orientation='h',
            title='Top 10 Productos más Vendidos'
        )
        st.plotly_chart(fig_producto_bar, use_container_width=True)
    
    with col2:
        fig_producto_pie = px.pie(
            producto_data.head(8),
            values='Cantidad_Ventas',
            names='Producto',
            title='Distribución de Ventas por Producto (Top 8)'
        )
        st.plotly_chart(fig_producto_pie, use_container_width=True)
    
    # Análisis adicionales
    st.header("🔍 Análisis Adicionales")
    
    # Análisis de tiempo hasta conversión
    col1, col2 = st.columns(2)
    
    with col1:
        if df_filtered[df_filtered['Convertido']]['Dias_Hasta_Conversion'].notna().any():
            fig_tiempo = px.histogram(
                df_filtered[df_filtered['Convertido']],
                x='Dias_Hasta_Conversion',
                title='Distribución del Tiempo hasta Conversión',
                nbins=20
            )
            st.plotly_chart(fig_tiempo, use_container_width=True)
    
    with col2:
        # Conversión por día de la semana
        df_filtered['Dia_Semana'] = df_filtered['Fecha de Creación'].dt.day_name()
        
        # Definir el orden deseado para los días de la semana
        orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Convertir 'Dia_Semana' a una categoría con el orden especificado
        df_filtered['Dia_Semana'] = pd.Categorical(df_filtered['Dia_Semana'], categories=orden_dias, ordered=True)
        
        dia_semana_data = df_filtered.groupby('Dia_Semana').agg({
            'Toma de contacto': 'count',
            'Convertido': 'sum'
        }).reset_index()
        dia_semana_data['Tasa_Conversion'] = (dia_semana_data['Convertido'] / dia_semana_data['Toma de contacto'] * 100)
        
        fig_dia_semana = px.bar(
            dia_semana_data,
            x='Dia_Semana',
            y='Tasa_Conversion',
            title='Tasa de Conversión por Día de la Semana'
        )
        st.plotly_chart(fig_dia_semana, use_container_width=True)
    
    # Tendencia temporal de conversión
    st.subheader("📈 Tendencia Temporal de Conversión")
    
    # Crear datos diarios
    df_filtered['Fecha_Solo'] = df_filtered['Fecha de Creación'].dt.date
    daily_data = df_filtered.groupby('Fecha_Solo').agg({
        'Toma de contacto': 'count',
        'Convertido': 'sum'
    }).reset_index()
    daily_data['Tasa_Conversion'] = (daily_data['Convertido'] / daily_data['Toma de contacto'] * 100)
    
    fig_tendencia = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Registros y Ventas Diarias', 'Tasa de Conversión Diaria'),
        vertical_spacing=0.1
    )
    
    fig_tendencia.add_trace(
        go.Scatter(x=daily_data['Fecha_Solo'], y=daily_data['Toma de contacto'],
                   mode='lines', name='Registros', line=dict(color='lightblue')),
        row=1, col=1
    )
    
    fig_tendencia.add_trace(
        go.Scatter(x=daily_data['Fecha_Solo'], y=daily_data['Convertido'],
                   mode='lines', name='Ventas', line=dict(color='darkblue')),
        row=1, col=1
    )
    
    fig_tendencia.add_trace(
        go.Scatter(x=daily_data['Fecha_Solo'], y=daily_data['Tasa_Conversion'],
                   mode='lines', name='Tasa Conversión (%)', line=dict(color='red')),
        row=2, col=1
    )
    
    fig_tendencia.update_layout(height=600, showlegend=True)
    st.plotly_chart(fig_tendencia, use_container_width=True)
    
    
        
    # Información del dataset
    st.sidebar.markdown("---")
    st.sidebar.header("ℹ️ Información del Dataset")
    st.sidebar.write(f"**Total de registros:** {len(df):,}")
    st.sidebar.write(f"**Registros filtrados:** {len(df_filtered):,}")
    st.sidebar.write(f"**Periodo:** {df['Fecha de Creación'].min().strftime('%Y-%m-%d')} a {df['Fecha de Creación'].max().strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    main()