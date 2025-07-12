# app.py


import streamlit as st
import pandas as pd
import io


# Protección con contraseña mejorada
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["auth"]["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("🔒 Ingresa la contraseña", type="password", on_change=password_entered, key="password")
        st.stop()
    elif not st.session_state["password_correct"]:
        st.text_input("🔒 Ingresa la contraseña", type="password", on_change=password_entered, key="password")
        st.error("Contraseña incorrecta")
        st.stop()

check_password()

# Cargar el archivo CSV y filtrar registros válidos desde el inicio
df_original = pd.read_csv("Lab01.csv")
df_validos = df_original[
    ~df_original["Order ID"].str.contains("duplicado|cancelado|borrador", case=False, na=False)
].drop_duplicates(subset="Order ID", keep="first")
df = df_validos.copy()

st.title("📊 Dashboard de Diagnósticos Genéticos")

# Filtros laterales
with st.sidebar:
    st.header("Filtros")

    laboratorio = st.selectbox("Selecciona el laboratorio", ["Todos"] + sorted(df["Lab"].dropna().unique()))
    clasificacion = st.selectbox("Clasificación", ["Todas"] + sorted(df["VARIANT CLASSIFICATION"].dropna().unique()))
    resultado = st.selectbox("Resultado", ["Todos", "Positive", "Negative", "Unknown"])
    tipo_entrada = st.selectbox("Tipo de entrada", ["Solo válidos", "Duplicados", "Cancelados", "Todos"])

    # Botón para cerrar sesión
    if st.button("🔒 Cerrar sesión"):
        st.session_state["password_correct"] = False
        st.rerun()

# Aplicar filtros
df_filtrado = df.copy()

if laboratorio != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Lab"] == laboratorio]

if clasificacion != "Todas":
    df_filtrado = df_filtrado[df_filtrado["VARIANT CLASSIFICATION"] == clasificacion]

if resultado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Result"] == resultado]

if tipo_entrada == "Solo válidos":
    df_filtrado = df_filtrado[~df_filtrado["Order ID"].str.contains("duplicado|cancelado|borrador", case=False, na=False)]
elif tipo_entrada == "Duplicados":
    df_filtrado = df_filtrado[df_filtrado["Order ID"].str.contains("duplicado", case=False, na=False)]
elif tipo_entrada == "Cancelados":
    df_filtrado = df_filtrado[df_filtrado["Order ID"].str.contains("cancelado|borrador", case=False, na=False)]

# Garantizar registros únicos por "Order ID" después de aplicar los filtros
df_filtrado = df_filtrado.drop_duplicates(subset="Order ID", keep="first")

# Mostrar tabla
st.dataframe(df_filtrado)

# Mostrar resumen
st.markdown(f"### Total de registros válidos de Lab01: {len(df_validos)}")

st.markdown("---")
st.header("📊 Panel Visual Interactivo")

import plotly.express as px

# Función para paleta azul personalizada
color_azul = px.colors.sequential.Blues

# Mostrar múltiples gráficas desde el inicio

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Clasificación de variantes")
    conteo = df_filtrado["VARIANT CLASSIFICATION"].value_counts().reset_index()
    conteo.columns = ["Clasificación", "Cantidad"]
    fig1 = px.bar(conteo, x="Clasificación", y="Cantidad", color="Clasificación",
                  color_discrete_sequence=color_azul)
    fig1.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        bargap=0.3
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("🔬 Genes más frecuentes")
    genes_expandidos = df_filtrado["GENE"].dropna().str.split(";").explode().str.strip()
    top_genes = genes_expandidos.value_counts().head(10).reset_index()
    top_genes.columns = ["Gen", "Cantidad"]
    fig2 = px.bar(top_genes, x="Gen", y="Cantidad", color="Gen",
                  color_discrete_sequence=color_azul)
    fig2.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        bargap=0.3
    )
    st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    st.subheader("📈 Distribución de Clasificaciones (Pastel)")
    conteo_pie = df_filtrado["VARIANT CLASSIFICATION"].value_counts().reset_index()
    conteo_pie.columns = ["Clasificación", "Cantidad"]
    fig3 = px.pie(
        conteo_pie,
        names="Clasificación",
        values="Cantidad",
        hole=0.4,
        color_discrete_sequence=color_azul
    )
    fig3.update_traces(
        textposition='inside',
        textinfo='percent+label',
        pull=[0.05]*len(conteo_pie)
    )
    fig3.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=20, l=20, r=20)
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("🧬 Zigosidad por Clasificación")
    temp = df_filtrado[["ZYGOSITY", "VARIANT CLASSIFICATION"]].dropna()
    temp = temp.assign(ZYGOSITY=temp["ZYGOSITY"].str.split(";")).explode("ZYGOSITY")
    temp["ZYGOSITY"] = temp["ZYGOSITY"].str.strip()
    conteo_bar = temp.groupby(["VARIANT CLASSIFICATION", "ZYGOSITY"]).size().reset_index(name="Cantidad")
    fig4 = px.bar(conteo_bar, x="VARIANT CLASSIFICATION", y="Cantidad", color="ZYGOSITY",
                  barmode="group", color_discrete_sequence=color_azul)
    fig4.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        bargap=0.25
    )
    st.plotly_chart(fig4, use_container_width=True)

st.subheader("🌡️ Mapa de Calor: GENE vs ZYGOSITY")
temp_heat = df_filtrado[["GENE", "ZYGOSITY"]].dropna()
temp_heat = temp_heat.assign(GENE=temp_heat["GENE"].str.split(";")).explode("GENE")
temp_heat = temp_heat.assign(ZYGOSITY=temp_heat["ZYGOSITY"].str.split(";")).explode("ZYGOSITY")
temp_heat["GENE"] = temp_heat["GENE"].str.strip()
temp_heat["ZYGOSITY"] = temp_heat["ZYGOSITY"].str.strip()

pivot = temp_heat.pivot_table(index="GENE", columns="ZYGOSITY", aggfunc=len, fill_value=0)
fig5 = px.imshow(pivot, text_auto=True, color_continuous_scale=color_azul)
fig5.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(t=20, b=20, l=20, r=20)
)
st.plotly_chart(fig5, use_container_width=True)