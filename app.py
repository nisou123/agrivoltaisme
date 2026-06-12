import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# ----------------------------
# CONFIGURATION
# ----------------------------

st.set_page_config(
    page_title="Base française des sites agrivoltaïques",
    layout="wide"
)

st.title(" Base française des sites agrivoltaïques")

# ----------------------------
# LECTURE DES DONNÉES
# ----------------------------

df = pd.read_excel("base_geolocalisee.xlsx")

# ----------------------------
# STATISTIQUES
# ----------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Nombre de sites",
        292
    )


with col2:
    st.metric(
        "Controverses",
        int(df["Controverse ?"].fillna(0).sum())
    )

with col3:
    st.metric(
        "Développeurs",
        df["Installateur"].nunique()-2
    )


st.divider()

# ----------------------------
# FILTRES
# ----------------------------

st.sidebar.header("Filtres")

departements = ["Tous"] + sorted(
    df["Département"].dropna().astype(str).unique().tolist()
)

departement = st.sidebar.selectbox(
    "Département",
    departements
)

technologies = ["Toutes"] + sorted(
    df["Technologie agrivoltaïque"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

technologie = st.sidebar.selectbox(
    "Technologie",
    technologies
)

controverse = st.sidebar.selectbox(
    "Controverse",
    ["Toutes", "Oui", "Non"]
)

# ----------------------------
# APPLICATION DES FILTRES
# ----------------------------

df_filtre = df.copy()

if departement != "Tous":

    df_filtre = df_filtre[
        df_filtre["Département"].astype(str)
        == departement
    ]

if technologie != "Toutes":

    df_filtre = df_filtre[
        df_filtre["Technologie agrivoltaïque"]
        .astype(str)
        == technologie
    ]

if controverse == "Oui":

    df_filtre = df_filtre[
        df_filtre["Controverse ?"] == 1
    ]

elif controverse == "Non":

    df_filtre = df_filtre[
        df_filtre["Controverse ?"] == 0
    ]

# ----------------------------
# CARTE
# ----------------------------

carte = folium.Map(
    location=[46.5, 2.5],
    zoom_start=6
)

for _, row in df_filtre.iterrows():

    lat = row.get("Latitude")
    lon = row.get("Longitude")

    if pd.isna(lat) or pd.isna(lon):
        continue

    couleur = (
        "red"
        if row["Controverse ?"] == 1
        else "green"
    )

    popup = f"""
    <b>{row['Nom']}</b><br>
    Commune : {row['Commune']}<br>
    Département : {row['Département']}<br>
    Technologie : {row['Technologie agrivoltaïque']}<br>
    Installateur : {row['Installateur']}<br>
    Etat : {row['Etat']}<br>
    """

    folium.Marker(
        [lat, lon],
        popup=popup,
        icon=folium.Icon(color=couleur)
    ).add_to(carte)

st.subheader(" Carte interactive")

st_folium(
    carte,
    width=1400,
    height=700
)

# ----------------------------
# TABLEAU DES DONNÉES
# ----------------------------

st.subheader("Données filtrées")

colonnes = [
    "Nom",
    "Commune",
    "Département",
    "Technologie agrivoltaïque",
    "Installateur",
    "Controverse ?"
]

st.dataframe(
    df_filtre[colonnes],
    use_container_width=True
)
nb_vides = df["Latitude"].isna().sum()

print(
    f"{nb_vides} sites sans coordonnées"
)