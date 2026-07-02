import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
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

@st.cache_data
def charger_donnees():
    return pd.read_excel("base_geolocalisee.xlsx")

df = charger_donnees()

# ----------------------------
# STATISTIQUES
# ----------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Nombre de sites",
        len(df)
    )

with col2:
    st.metric(
        "Controverses",
        int(df["Controverse ?"].fillna(0).sum())
    )

with col3:
    st.metric(
        "Développeurs",
        df["Installateur"].dropna().nunique()
    )

st.divider()

# ----------------------------
# OUTILS POUR LES CHAMPS MULTI-VALEURS
# ----------------------------
# Certaines cellules contiennent plusieurs valeurs séparées par une virgule
# (ex: un site qui s'étend sur plusieurs communes : "Channay, Nicey").
# Ces fonctions permettent de proposer chaque valeur individuellement dans
# les filtres, et de faire matcher un site dès qu'UNE de ses valeurs
# correspond au filtre choisi.

def valeurs_eclatees(serie):
    """Renvoie la liste triée des valeurs uniques, en éclatant les cellules
    contenant plusieurs valeurs séparées par des virgules."""
    valeurs = set()
    for cellule in serie.dropna().astype(str):
        for item in cellule.split(","):
            item = item.strip()
            if item:
                valeurs.add(item)
    return sorted(valeurs)


def contient_valeur(cellule, valeur_cherchee):
    """Vérifie si valeur_cherchee fait partie des valeurs d'une cellule
    (potentiellement multi-valeurs séparées par des virgules)."""
    if pd.isna(cellule):
        return False
    parties = [p.strip() for p in str(cellule).split(",")]
    return valeur_cherchee in parties

# ----------------------------
# FILTRES
# ----------------------------

st.sidebar.header("Filtres")

departements = ["Tous"] + valeurs_eclatees(df["Département"])
departement = st.sidebar.selectbox("Département", departements)

communes = ["Toutes"] + valeurs_eclatees(df["Commune"])
commune = st.sidebar.selectbox("Commune", communes)

technologies = ["Toutes"] + valeurs_eclatees(df["Technologie agrivoltaïque"])
technologie = st.sidebar.selectbox("Technologie", technologies)

developpeurs = ["Tous"] + valeurs_eclatees(df["Installateur"])
developpeur = st.sidebar.selectbox("Développeur", developpeurs)

controverse = st.sidebar.selectbox("Controverse", ["Toutes", "Oui", "Non"])

# ----------------------------
# APPLICATION DES FILTRES
# ----------------------------

df_filtre = df.copy()

if departement != "Tous":
    df_filtre = df_filtre[
        df_filtre["Département"].apply(lambda x: contient_valeur(x, departement))
    ]

if commune != "Toutes":
    df_filtre = df_filtre[
        df_filtre["Commune"].apply(lambda x: contient_valeur(x, commune))
    ]

if technologie != "Toutes":
    df_filtre = df_filtre[
        df_filtre["Technologie agrivoltaïque"].apply(
            lambda x: contient_valeur(x, technologie)
        )
    ]

if developpeur != "Tous":
    df_filtre = df_filtre[
        df_filtre["Installateur"].apply(lambda x: contient_valeur(x, developpeur))
    ]

if controverse == "Oui":
    df_filtre = df_filtre[df_filtre["Controverse ?"] == 1]
elif controverse == "Non":
    df_filtre = df_filtre[df_filtre["Controverse ?"] == 0]

# ----------------------------
# OUTILS DE FORMATAGE
# ----------------------------

def fmt(valeur, unite="", decimales=None):
    """Formate une valeur pour l'affichage, gère les valeurs manquantes."""
    if pd.isna(valeur):
        return "Non renseigné"
    if decimales is not None:
        try:
            valeur = round(float(valeur), decimales)
        except (TypeError, ValueError):
            pass
    return f"{valeur}{unite}"


def fmt_annee(valeur):
    if pd.isna(valeur):
        return "Non renseigné"
    try:
        return str(int(valeur))
    except (TypeError, ValueError):
        return str(valeur)


def construire_popup(row):
    return f"""
    <div style="font-size:13px; line-height:1.5;">
    <b style="font-size:14px;">{fmt(row.get('Nom'))}</b><br>
    <hr style="margin:4px 0;">
    <b>Localisation</b><br>
    Commune : {fmt(row.get('Commune'))}<br>
    Département : {fmt(row.get('Département'))}<br>
    <br>
    <b>Caractéristiques</b><br>
    Technologie : {fmt(row.get('Technologie agrivoltaïque'))}<br>
    Type d'exploitation : {fmt(row.get("Type d'exploitation"))}<br>
    Statut de l'exploitation : {fmt(row.get("Statut de l'exploitation agricole"))}<br>
    État : {fmt(row.get('Etat'))}<br>
    Année de mise en service : {fmt_annee(row.get('Année de mise en service'))}<br>
    <br>
    <b>Production</b><br>
    Puissance installée : {fmt(row.get('Puissance installée (MWc)'), " MWc", 2)}<br>
    Énergie produite : {fmt(row.get('Energie produite (MWh/an)'), " MWh/an", 1)}<br>
    <br>
    <b>Surfaces</b><br>
    Surface panneaux solaires : {fmt(row.get('Surface de panneaux solaires (ha)'), " ha", 2)}<br>
    Surface champs (AV) : {fmt(row.get('Surface de champs en AV (ha) '), " ha", 2)}<br>
    Surface témoin : {fmt(row.get('Surface témoin (ha)'), " ha", 2)}<br>
    <br>
    <b>Culture</b><br>
    Type de culture / élevage : {fmt(row.get('Type de culture / élevage'))}<br>
    <br>
    Installateur : {fmt(row.get('Installateur'))}<br>
    </div>
    """

# ----------------------------
# CARTE
# ----------------------------

carte = folium.Map(location=[46.5, 2.5], zoom_start=6)

# Les sites proches géographiquement sont regroupés dans un cluster
# (cercle avec un chiffre) qui se déploie automatiquement au zoom,
# plutôt que d'afficher des pins superposés et illisibles.
cluster = MarkerCluster().add_to(carte)

for _, row in df_filtre.iterrows():

    lat = row.get("Latitude")
    lon = row.get("Longitude")

    if pd.isna(lat) or pd.isna(lon):
        continue

    couleur = "red" if row["Controverse ?"] == 1 else "green"

    popup_html = construire_popup(row)

    folium.Marker(
        [lat, lon],
        popup=folium.Popup(popup_html, max_width=320),
        tooltip=row.get("Nom"),
        icon=folium.Icon(color=couleur)
    ).add_to(cluster)

st.subheader(" Carte interactive")

st_folium(carte, width=1400, height=700)

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
    "Etat",
    "Statut de l'exploitation agricole",
    "Puissance installée (MWc)",
    "Energie produite (MWh/an)",
    "Surface de panneaux solaires (ha)",
    "Surface de champs en AV (ha) ",
    "Surface témoin (ha)",
    "Type de culture / élevage",
    "Année de mise en service",
    "Type d'exploitation",
    "Controverse ?"
]

st.dataframe(df_filtre[colonnes], use_container_width=True)

st.markdown("---")

st.subheader(" Sources des données")

st.markdown("""
- Données issues de : [Zoé Zerbib; Frédéric Wurtz; Xavier Arnauld de Sartre, 2025, "Base de données recensant des sites agrivoltaïques en France"](https://entrepot.recherche.data.gouv.fr/dataset.xhtml?persistentId=doi:10.57745/2GPGSY )

- Les coordonnées géographiques sont estimées à partir du département lorsque la commune n'est pas disponible.
""")
