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

# Cargar el archivo CSV
df = pd.read_csv("invitae.csv")

# Filtrar: eliminar filas donde el Order ID no empiece con 'RQ' y tenga exactamente 7 dígitos después
df = df[df["Order ID"].astype(str).str.match(r"^RQ\d{7}$")]
df = df.drop_duplicates(subset="Order ID", keep="first")

st.title("📊 Dashboard de Diagnósticos Genéticos")

# Filtros laterales
with st.sidebar:
    st.header("Filtros")

    laboratorio = st.selectbox("Selecciona el laboratorio", ["Todos"] + sorted(df["Lab"].dropna().unique()))
    clasificacion = st.selectbox("Clasificación", ["Todas"] + sorted(df["VARIANT CLASSIFICATION"].dropna().unique()))
    resultado = st.selectbox("Resultado", ["Todos", "Positive", "Negative", "Unknown"])

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

# Mostrar tabla
st.dataframe(df_filtrado)

# Mostrar resumen
st.markdown(f"### Total de registros mostrados: {len(df_filtrado)}")

import plotly.express as px

st.markdown("---")
st.header("📈 Visualización Interactiva")

st.markdown(
    "Selecciona el tipo de visualización que deseas generar. Las gráficas son interactivas y puedes hacer zoom, pasar el mouse para ver detalles o descargar el gráfico."
)

# Menú para seleccionar tipo de gráfica
grafica = st.selectbox("📌 Tipo de visualización", [
    "📊 Clasificación de variantes",
    "🔬 Genes más frecuentes",
    "🧬 Zigosidad por clasificación",
    "🧁 Gráfico circular (pastel)",
    "🌡️ Mapa de calor GENE vs ZYGOSITY"
])

# Función para paleta azul personalizada
color_azul = px.colors.sequential.Blues

# Clasificación de variantes
if grafica == "📊 Clasificación de variantes":
    conteo = df_filtrado["VARIANT CLASSIFICATION"].value_counts().reset_index()
    conteo.columns = ["Clasificación", "Cantidad"]
    fig = px.bar(conteo, x="Clasificación", y="Cantidad", color="Clasificación",
                 color_discrete_sequence=color_azul)
    st.plotly_chart(fig, use_container_width=True)

# Genes más frecuentes
elif grafica == "🔬 Genes más frecuentes":
    genes_expandidos = df_filtrado["GENE"].dropna().str.split(";").explode().str.strip()
    top_genes = genes_expandidos.value_counts().head(10).reset_index()
    top_genes.columns = ["Gen", "Cantidad"]
    fig = px.bar(top_genes, x="Gen", y="Cantidad", color="Gen",
                 color_discrete_sequence=color_azul)
    st.plotly_chart(fig, use_container_width=True)

# Zigosidad por clasificación
elif grafica == "🧬 Zigosidad por clasificación":
    temp = df_filtrado[["ZYGOSITY", "VARIANT CLASSIFICATION"]].dropna()
    temp = temp.assign(ZYGOSITY=temp["ZYGOSITY"].str.split(";")).explode("ZYGOSITY")
    temp["ZYGOSITY"] = temp["ZYGOSITY"].str.strip()
    conteo = temp.groupby(["VARIANT CLASSIFICATION", "ZYGOSITY"]).size().reset_index(name="Cantidad")
    fig = px.bar(conteo, x="VARIANT CLASSIFICATION", y="Cantidad", color="ZYGOSITY",
                 barmode="group", color_discrete_sequence=color_azul)
    st.plotly_chart(fig, use_container_width=True)

# Gráfico circular (pastel)
elif grafica == "🧁 Gráfico circular (pastel)":
    conteo = df_filtrado["VARIANT CLASSIFICATION"].value_counts().reset_index()
    conteo.columns = ["Clasificación", "Cantidad"]
    fig = px.pie(conteo, names="Clasificación", values="Cantidad",
                 color_discrete_sequence=color_azul,
                 title="Distribución de Clasificaciones")
    st.plotly_chart(fig, use_container_width=True)

    # buf = io.BytesIO()
    # fig.write_image(buf, format="png")
    # st.download_button(
    #     label="📥 Descargar gráfica (PNG)",
    #     data=buf.getvalue(),
    #     file_name="grafica_pastel.png",
    #     mime="image/png"
    # )
    st.info("Para descargar la gráfica, haz clic en el ícono de cámara en la esquina superior derecha del gráfico.")

# Mapa de calor GENE vs ZYGOSITY
elif grafica == "🌡️ Mapa de calor GENE vs ZYGOSITY":
    temp = df_filtrado[["GENE", "ZYGOSITY"]].dropna()
    temp = temp.assign(GENE=temp["GENE"].str.split(";")).explode("GENE")
    temp = temp.assign(ZYGOSITY=temp["ZYGOSITY"].str.split(";")).explode("ZYGOSITY")
    temp["GENE"] = temp["GENE"].str.strip()
    temp["ZYGOSITY"] = temp["ZYGOSITY"].str.strip()

    pivot = temp.pivot_table(index="GENE", columns="ZYGOSITY", aggfunc=len, fill_value=0)
    fig = px.imshow(pivot, text_auto=True, color_continuous_scale=color_azul,
                    title="Mapa de Calor: GENE vs ZYGOSITY")
    st.plotly_chart(fig, use_container_width=True)

    # buf = io.BytesIO()
    # fig.write_image(buf, format="png")
    # st.download_button(
    #     label="📥 Descargar mapa de calor (PNG)",
    #     data=buf.getvalue(),
    #     file_name="heatmap_gene_zygosity.png",
    #     mime="image/png"
    # )
    st.info("Para descargar la gráfica, haz clic en el ícono de cámara en la esquina superior derecha del gráfico.")