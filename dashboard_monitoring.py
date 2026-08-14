import os

import pandas as pd
import plotly.express as px
import streamlit as st

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# =========================================================
# Configuration générale
# =========================================================

st.set_page_config(
    page_title="Monitoring du scoring crédit",
    page_icon="📊",
    layout="wide",
)

COULEURS_GROUPES = {
    "reference": "#2563EB",
    "production": "#DC2626",
}

SEUIL_ENDETTEMENT = 0.35


# =========================================================
# Connexion à NeonDB
# =========================================================

load_dotenv()

url_base_donnees = os.getenv("DATABASE_URL")

if not url_base_donnees:
    st.error(
        "La variable d'environnement DATABASE_URL "
        "n'est pas définie."
    )
    st.stop()


moteur_base_donnees = create_engine(
    url_base_donnees,
    pool_pre_ping=True,
)


# =========================================================
# Chargement des données
# =========================================================

@st.cache_data(ttl=60)
def charger_donnees():
    """Charge les prédictions stockées dans NeonDB."""

    requete = text(
        """
        SELECT
            id,
            timestamp,
            sk_id_curr,
            amt_credit,
            nbre_annee,
            nombre_enfants,
            anciennete_professionnelle,
            age,
            revenu_annuel,
            score_risque,
            seuil_decision,
            prediction,
            decision,
            raison,
            revenu_mensuel,
            montant_annuel_remboursement,
            montant_mensuel_remboursement,
            taux_endettement,
            seuil_endettement,
            temps_inference_ms,
            latence_application_ms,
            type_donnees
        FROM prediction_logs
        ORDER BY timestamp;
        """
    )

    with moteur_base_donnees.connect() as connexion:
        donnees_chargees = pd.read_sql_query(
            requete,
            connexion,
        )

    donnees_chargees["timestamp"] = pd.to_datetime(
        donnees_chargees["timestamp"],
        errors="coerce",
    )

    return donnees_chargees


try:
    donnees = charger_donnees()

except Exception as erreur:
    st.error(
        "Impossible de charger les données depuis NeonDB : "
        f"{erreur}"
    )
    st.stop()


if donnees.empty:
    st.warning("Aucune prédiction n'est disponible.")
    st.stop()


# =========================================================
# Préparation des données
# =========================================================

colonnes_numeriques = [
    "amt_credit",
    "nbre_annee",
    "nombre_enfants",
    "anciennete_professionnelle",
    "age",
    "revenu_annuel",
    "score_risque",
    "seuil_decision",
    "prediction",
    "revenu_mensuel",
    "montant_annuel_remboursement",
    "montant_mensuel_remboursement",
    "taux_endettement",
    "seuil_endettement",
    "temps_inference_ms",
    "latence_application_ms",
]

for colonne in colonnes_numeriques:
    if colonne in donnees.columns:
        donnees[colonne] = pd.to_numeric(
            donnees[colonne],
            errors="coerce",
        )


donnees_reference = donnees[
    donnees["type_donnees"] == "reference"
].copy()

donnees_production = donnees[
    donnees["type_donnees"] == "production"
].copy()


# =========================================================
# Fonctions utilitaires
# =========================================================

def formater_pourcentage(valeur):
    """Formate une proportion en pourcentage."""

    if pd.isna(valeur):
        return "N/A"

    return f"{valeur:.2%}"


def formater_duree(valeur):
    """Formate une durée en millisecondes."""

    if pd.isna(valeur):
        return "N/A"

    return f"{valeur:.2f} ms"


def formater_nombre(valeur):
    """Formate un nombre entier."""

    if pd.isna(valeur):
        return "N/A"

    return f"{int(valeur):,}".replace(",", " ")


def creer_histogramme_normalise(
    donnees_graphique,
    variable,
    titre,
    libelle_x,
    nombre_classes=25,
):
    """Crée un histogramme normalisé par groupe."""

    figure = px.histogram(
        donnees_graphique.dropna(
            subset=[variable, "type_donnees"]
        ),
        x=variable,
        color="type_donnees",
        nbins=nombre_classes,
        histnorm="percent",
        barmode="overlay",
        opacity=0.55,
        title=titre,
        labels={
            variable: libelle_x,
            "type_donnees": "Type de données",
        },
        color_discrete_map=COULEURS_GROUPES,
        category_orders={
            "type_donnees": [
                "reference",
                "production",
            ]
        },
    )

    figure.update_layout(
        yaxis_title="Proportion dans le groupe (%)",
        legend_title="Groupe",
        hovermode="x unified",
    )

    return figure


# =========================================================
# En-tête
# =========================================================

st.title("📊 Monitoring du modèle de scoring crédit")

st.caption(
    "Comparaison des données de référence avec les données "
    "de production simulées."
)


# =========================================================
# Barre latérale
# =========================================================

st.sidebar.header("Filtres")

types_disponibles = (
    donnees["type_donnees"]
    .dropna()
    .unique()
    .tolist()
)

types_selectionnes = st.sidebar.multiselect(
    "Type de données",
    options=types_disponibles,
    default=types_disponibles,
)

if st.sidebar.button(
    "Actualiser les données",
    width="stretch",
):
    st.cache_data.clear()
    st.rerun()


donnees_filtrees = donnees[
    donnees["type_donnees"].isin(
        types_selectionnes
    )
].copy()


st.sidebar.divider()

st.sidebar.write(
    f"**Référence :** {len(donnees_reference)} lignes"
)

st.sidebar.write(
    f"**Production :** {len(donnees_production)} lignes"
)


# =========================================================
# Calcul des KPI
# =========================================================

nombre_reference = len(donnees_reference)
nombre_production = len(donnees_production)

score_moyen = donnees_production[
    "score_risque"
].mean()

taux_refus = (
    donnees_production["prediction"]
    .eq(1)
    .mean()
)

taux_accord = (
    donnees_production["prediction"]
    .eq(0)
    .mean()
)

temps_inference_moyen = donnees_production[
    "temps_inference_ms"
].mean()

temps_inference_p95 = donnees_production[
    "temps_inference_ms"
].quantile(0.95)

latences_valides = donnees_production[
    "latence_application_ms"
].dropna()

latence_moyenne = latences_valides.mean()
latence_p95 = latences_valides.quantile(0.95)


# =========================================================
# Indicateurs principaux
# =========================================================

st.subheader("Indicateurs principaux")

colonne_1, colonne_2, colonne_3, colonne_4 = st.columns(4)

colonne_1.metric(
    "Clients de référence",
    formater_nombre(nombre_reference),
)

colonne_2.metric(
    "Prédictions en production",
    formater_nombre(nombre_production),
)

colonne_3.metric(
    "Score de risque moyen",
    formater_pourcentage(score_moyen),
)

colonne_4.metric(
    "Taux de refus",
    formater_pourcentage(taux_refus),
)


colonne_5, colonne_6, colonne_7, colonne_8 = st.columns(4)

colonne_5.metric(
    "Taux d'accord",
    formater_pourcentage(taux_accord),
)

colonne_6.metric(
    "Temps d'inférence moyen",
    formater_duree(temps_inference_moyen),
)

colonne_7.metric(
    "Latence moyenne",
    formater_duree(latence_moyenne),
)

colonne_8.metric(
    "Latence P95",
    formater_duree(latence_p95),
)


# =========================================================
# Comparaison des distributions
# =========================================================

st.divider()
st.header("Comparaison référence / production")

st.info(
    "Les graphiques sont normalisés en pourcentage. "
    "Les groupes peuvent donc être comparés même s'ils "
    "ne contiennent pas le même nombre de lignes."
)

if donnees_filtrees.empty:
    st.warning(
        "Sélectionne au moins un groupe dans la barre latérale."
    )

else:
    # -----------------------------------------------------
    # Score de risque et montant du crédit
    # -----------------------------------------------------

    colonne_gauche, colonne_droite = st.columns(2)

    figure_scores = creer_histogramme_normalise(
        donnees_graphique=donnees_filtrees,
        variable="score_risque",
        titre="Distribution des scores de risque",
        libelle_x="Score de risque",
        nombre_classes=25,
    )

    seuils_disponibles = donnees[
        "seuil_decision"
    ].dropna()

    if not seuils_disponibles.empty:
        seuil_decision = seuils_disponibles.median()

        figure_scores.add_vline(
            x=seuil_decision,
            line_dash="dash",
            line_color="#F59E0B",
            annotation_text=(
                f"Seuil : {seuil_decision:.2%}"
            ),
        )

    colonne_gauche.plotly_chart(
        figure_scores,
        width="stretch",
    )

    figure_credit = creer_histogramme_normalise(
        donnees_graphique=donnees_filtrees,
        variable="amt_credit",
        titre="Distribution des montants de crédit",
        libelle_x="Montant du crédit",
        nombre_classes=30,
    )

    colonne_droite.plotly_chart(
        figure_credit,
        width="stretch",
    )


    # -----------------------------------------------------
    # Revenu et âge
    # -----------------------------------------------------

    colonne_gauche, colonne_droite = st.columns(2)

    figure_revenus = creer_histogramme_normalise(
        donnees_graphique=donnees_filtrees,
        variable="revenu_annuel",
        titre="Distribution des revenus annuels",
        libelle_x="Revenu annuel",
        nombre_classes=30,
    )

    colonne_gauche.plotly_chart(
        figure_revenus,
        width="stretch",
    )

    figure_age = creer_histogramme_normalise(
        donnees_graphique=donnees_filtrees,
        variable="age",
        titre="Distribution des âges",
        libelle_x="Âge",
        nombre_classes=20,
    )

    colonne_droite.plotly_chart(
        figure_age,
        width="stretch",
    )


    # -----------------------------------------------------
    # Durée et ancienneté
    # -----------------------------------------------------

    colonne_gauche, colonne_droite = st.columns(2)

    figure_duree = creer_histogramme_normalise(
        donnees_graphique=donnees_filtrees,
        variable="nbre_annee",
        titre="Distribution de la durée du crédit",
        libelle_x="Durée du crédit en années",
        nombre_classes=20,
    )

    colonne_gauche.plotly_chart(
        figure_duree,
        width="stretch",
    )

    figure_anciennete = creer_histogramme_normalise(
        donnees_graphique=donnees_filtrees,
        variable="anciennete_professionnelle",
        titre="Distribution de l'ancienneté professionnelle",
        libelle_x="Ancienneté professionnelle en années",
        nombre_classes=20,
    )

    colonne_droite.plotly_chart(
        figure_anciennete,
        width="stretch",
    )

# -----------------------------------------------------
# Nombre d'enfants
# -----------------------------------------------------

    repartition_enfants = (
        donnees_filtrees
        .dropna(
            subset=[
                "type_donnees",
                "nombre_enfants",
            ]
        )
        .groupby(
            [
                "type_donnees",
                "nombre_enfants",
            ],
            as_index=False,
        )
        .size()
        .rename(
            columns={
                "size": "effectif",
            }
        )
    )

    repartition_enfants["proportion"] = (
        repartition_enfants["effectif"]
        / repartition_enfants.groupby(
            "type_donnees"
        )["effectif"].transform("sum")
        * 100
    )

    figure_enfants = px.bar(
        repartition_enfants,
        x="nombre_enfants",
        y="proportion",
        color="type_donnees",
        barmode="group",
        title="Répartition du nombre d'enfants",
        labels={
            "nombre_enfants": "Nombre d'enfants",
            "proportion": "Proportion (%)",
            "type_donnees": "Type de données",
        },
        color_discrete_map=COULEURS_GROUPES,
    )

    figure_enfants.update_traces(
        texttemplate="%{y:.1f} %",
        textposition="outside",
    )

    figure_enfants.update_layout(
        yaxis_title="Proportion dans chaque groupe (%)",
        xaxis_title="Nombre d'enfants",
    )

    st.plotly_chart(
        figure_enfants,
        width="stretch",
    )


    # -----------------------------------------------------
    # Taux d'endettement et mensualité
    # -----------------------------------------------------

    colonne_gauche, colonne_droite = st.columns(2)

    figure_endettement = creer_histogramme_normalise(
        donnees_graphique=donnees_filtrees,
        variable="taux_endettement",
        titre="Distribution du taux d'endettement",
        libelle_x="Taux d'endettement",
        nombre_classes=25,
    )

    figure_endettement.add_vline(
        x=SEUIL_ENDETTEMENT,
        line_dash="dash",
        line_color="#F59E0B",
        annotation_text="Seuil : 35 %",
    )

    colonne_gauche.plotly_chart(
        figure_endettement,
        width="stretch",
    )

    figure_mensualite = creer_histogramme_normalise(
        donnees_graphique=donnees_filtrees,
        variable="montant_mensuel_remboursement",
        titre="Distribution des mensualités",
        libelle_x="Montant mensuel à rembourser",
        nombre_classes=25,
    )

    colonne_droite.plotly_chart(
        figure_mensualite,
        width="stretch",
    )


# =========================================================
# Analyse cumulée des distributions
# =========================================================

st.divider()
st.header("Analyse cumulée des distributions")

st.caption(
    "Les courbes cumulées facilitent la comparaison "
    "de distributions ayant des tailles différentes."
)

colonne_gauche, colonne_droite = st.columns(2)

figure_credit_ecdf = px.ecdf(
    donnees_filtrees.dropna(
        subset=["amt_credit", "type_donnees"]
    ),
    x="amt_credit",
    color="type_donnees",
    ecdfnorm="percent",
    title="Distribution cumulée des montants de crédit",
    labels={
        "amt_credit": "Montant du crédit",
        "type_donnees": "Type de données",
    },
    color_discrete_map=COULEURS_GROUPES,
)

figure_credit_ecdf.update_layout(
    yaxis_title="Proportion cumulée (%)",
)

colonne_gauche.plotly_chart(
    figure_credit_ecdf,
    width="stretch",
)


figure_revenus_ecdf = px.ecdf(
    donnees_filtrees.dropna(
        subset=["revenu_annuel", "type_donnees"]
    ),
    x="revenu_annuel",
    color="type_donnees",
    ecdfnorm="percent",
    title="Distribution cumulée des revenus annuels",
    labels={
        "revenu_annuel": "Revenu annuel",
        "type_donnees": "Type de données",
    },
    color_discrete_map=COULEURS_GROUPES,
)

figure_revenus_ecdf.update_layout(
    yaxis_title="Proportion cumulée (%)",
)

colonne_droite.plotly_chart(
    figure_revenus_ecdf,
    width="stretch",
)

# =========================================================
# Relations entre les variables
# =========================================================

st.divider()
st.header("Relations entre les variables")

colonne_gauche, colonne_droite = st.columns(2)

figure_credit_score = px.scatter(
    donnees_filtrees.dropna(
        subset=[
            "amt_credit",
            "score_risque",
            "type_donnees",
        ]
    ),
    x="amt_credit",
    y="score_risque",
    color="type_donnees",
    symbol="decision",
    opacity=0.65,
    title="Montant du crédit et score de risque",
    labels={
        "amt_credit": "Montant du crédit",
        "score_risque": "Score de risque",
        "type_donnees": "Type de données",
        "decision": "Décision",
    },
    color_discrete_map=COULEURS_GROUPES,
)

if not seuils_disponibles.empty:
    figure_credit_score.add_hline(
        y=seuil_decision,
        line_dash="dash",
        line_color="#F59E0B",
        annotation_text="Seuil de décision",
    )

colonne_gauche.plotly_chart(
    figure_credit_score,
    width="stretch",
)


figure_revenu_score = px.scatter(
    donnees_filtrees.dropna(
        subset=[
            "revenu_annuel",
            "score_risque",
            "type_donnees",
        ]
    ),
    x="revenu_annuel",
    y="score_risque",
    color="type_donnees",
    symbol="decision",
    opacity=0.65,
    title="Revenu annuel et score de risque",
    labels={
        "revenu_annuel": "Revenu annuel",
        "score_risque": "Score de risque",
        "type_donnees": "Type de données",
        "decision": "Décision",
    },
    color_discrete_map=COULEURS_GROUPES,
)

if not seuils_disponibles.empty:
    figure_revenu_score.add_hline(
        y=seuil_decision,
        line_dash="dash",
        line_color="#F59E0B",
        annotation_text="Seuil de décision",
    )

colonne_droite.plotly_chart(
    figure_revenu_score,
    width="stretch",
)


# =========================================================
# Comparaison des décisions
# =========================================================
# =========================================================
# Comparaison des décisions
# =========================================================

st.divider()
st.header("Comparaison des décisions")

repartition_decisions = (
    donnees_filtrees
    .dropna(
        subset=[
            "type_donnees",
            "decision",
        ]
    )
    .groupby(
        [
            "type_donnees",
            "decision",
        ],
        as_index=False,
    )
    .size()
    .rename(
        columns={
            "size": "effectif",
        }
    )
)

repartition_decisions["proportion"] = (
    repartition_decisions["effectif"]
    / repartition_decisions.groupby(
        "type_donnees"
    )["effectif"].transform("sum")
    * 100
)

figure_decisions_groupes = px.bar(
    repartition_decisions,
    x="decision",
    y="proportion",
    color="type_donnees",
    barmode="group",
    title="Taux d'accord et de refus par groupe",
    labels={
        "decision": "Décision",
        "proportion": "Proportion (%)",
        "type_donnees": "Type de données",
    },
    color_discrete_map=COULEURS_GROUPES,
)

figure_decisions_groupes.update_traces(
    texttemplate="%{y:.1f} %",
    textposition="outside",
)

figure_decisions_groupes.update_layout(
    yaxis_title="Proportion dans chaque groupe (%)",
)

st.plotly_chart(
    figure_decisions_groupes,
    width="stretch",
)

# =========================================================
# Suivi de la production
# =========================================================

st.divider()
st.header("Suivi des prédictions en production")

if donnees_production.empty:
    st.warning(
        "Aucune donnée de production n'est disponible."
    )

else:
    colonne_gauche, colonne_droite = st.columns(2)

    figure_decisions = px.pie(
        donnees_production.dropna(
            subset=["decision"]
        ),
        names="decision",
        title="Répartition des décisions en production",
        color="decision",
        color_discrete_map={
            "crédit accordé": "#16A34A",
            "crédit refusé": "#DC2626",
        },
    )

    colonne_gauche.plotly_chart(
        figure_decisions,
        width="stretch",
    )


    figure_score_temps = px.line(
        donnees_production.dropna(
            subset=[
                "timestamp",
                "score_risque",
            ]
        ).sort_values("timestamp"),
        x="timestamp",
        y="score_risque",
        markers=True,
        title="Évolution des scores de risque",
        labels={
            "timestamp": "Date",
            "score_risque": "Score de risque",
        },
    )

    if not seuils_disponibles.empty:
        figure_score_temps.add_hline(
            y=seuil_decision,
            line_dash="dash",
            line_color="#F59E0B",
            annotation_text="Seuil de décision",
        )

    colonne_droite.plotly_chart(
        figure_score_temps,
        width="stretch",
    )


    # -----------------------------------------------------
    # Latence et inférence dans le temps
    # -----------------------------------------------------

    colonne_gauche, colonne_droite = st.columns(2)

    donnees_latence = (
        donnees_production
        .dropna(
            subset=[
                "timestamp",
                "latence_application_ms",
            ]
        )
        .sort_values("timestamp")
    )

    if donnees_latence.empty:
        colonne_gauche.info(
            "Aucune mesure de latence applicative disponible."
        )

    else:
        figure_latence = px.line(
            donnees_latence,
            x="timestamp",
            y="latence_application_ms",
            markers=True,
            title="Évolution de la latence applicative",
            labels={
                "timestamp": "Date",
                "latence_application_ms": (
                    "Latence applicative (ms)"
                ),
            },
        )

        colonne_gauche.plotly_chart(
            figure_latence,
            width="stretch",
        )


    donnees_inference = (
        donnees_production
        .dropna(
            subset=[
                "timestamp",
                "temps_inference_ms",
            ]
        )
        .sort_values("timestamp")
    )

    figure_inference = px.line(
        donnees_inference,
        x="timestamp",
        y="temps_inference_ms",
        markers=True,
        title="Évolution du temps d'inférence",
        labels={
            "timestamp": "Date",
            "temps_inference_ms": (
                "Temps d'inférence (ms)"
            ),
        },
    )

    colonne_droite.plotly_chart(
        figure_inference,
        width="stretch",
    )


# =========================================================
# Distribution des performances techniques
# =========================================================

st.divider()
st.header("Performances techniques")

colonne_gauche, colonne_droite = st.columns(2)

figure_inference_distribution = px.box(
    donnees_filtrees.dropna(
        subset=[
            "temps_inference_ms",
            "type_donnees",
        ]
    ),
    x="type_donnees",
    y="temps_inference_ms",
    color="type_donnees",
    points="outliers",
    title="Distribution du temps d'inférence",
    labels={
        "type_donnees": "Type de données",
        "temps_inference_ms": (
            "Temps d'inférence (ms)"
        ),
    },
    color_discrete_map=COULEURS_GROUPES,
)

colonne_gauche.plotly_chart(
    figure_inference_distribution,
    width="stretch",
)


if latences_valides.empty:
    colonne_droite.info(
        "Aucune mesure de latence applicative disponible."
    )

else:
    figure_latence_distribution = px.box(
        donnees_production.dropna(
            subset=["latence_application_ms"]
        ),
        y="latence_application_ms",
        points="outliers",
        title="Distribution de la latence en production",
        labels={
            "latence_application_ms": (
                "Latence applicative (ms)"
            ),
        },
    )

    colonne_droite.plotly_chart(
        figure_latence_distribution,
        width="stretch",
    )


# =========================================================
# Synthèse statistique
# =========================================================

st.divider()
st.header("Synthèse statistique")

variables_comparaison = [
    "amt_credit",
    "nbre_annee",
    "nombre_enfants",
    "anciennete_professionnelle",
    "age",
    "revenu_annuel",
    "score_risque",
    "taux_endettement",
]

noms_variables = {
    "amt_credit": "Montant du crédit",
    "nbre_annee": "Durée du crédit",
    "nombre_enfants": "Nombre d'enfants",
    "anciennete_professionnelle": (
        "Ancienneté professionnelle"
    ),
    "age": "Âge",
    "revenu_annuel": "Revenu annuel",
    "score_risque": "Score de risque",
    "taux_endettement": "Taux d'endettement",
}

lignes_statistiques = []

for variable in variables_comparaison:
    reference = donnees_reference[variable].dropna()
    production = donnees_production[variable].dropna()

    moyenne_reference = reference.mean()
    moyenne_production = production.mean()

    mediane_reference = reference.median()
    mediane_production = production.median()

    if (
        pd.notna(moyenne_reference)
        and moyenne_reference != 0
    ):
        evolution_moyenne = (
            (
                moyenne_production
                - moyenne_reference
            )
            / moyenne_reference
            * 100
        )
    else:
        evolution_moyenne = pd.NA

    lignes_statistiques.append(
        {
            "Variable": noms_variables[variable],
            "Moyenne référence": moyenne_reference,
            "Moyenne production": moyenne_production,
            "Évolution moyenne (%)": evolution_moyenne,
            "Médiane référence": mediane_reference,
            "Médiane production": mediane_production,
        }
    )


statistiques_groupes = pd.DataFrame(
    lignes_statistiques
)

st.dataframe(
    statistiques_groupes,
    width="stretch",
    hide_index=True,
    column_config={
        "Moyenne référence": (
            st.column_config.NumberColumn(
                format="%.2f",
            )
        ),
        "Moyenne production": (
            st.column_config.NumberColumn(
                format="%.2f",
            )
        ),
        "Évolution moyenne (%)": (
            st.column_config.NumberColumn(
                format="%.2f %%",
            )
        ),
        "Médiane référence": (
            st.column_config.NumberColumn(
                format="%.2f",
            )
        ),
        "Médiane production": (
            st.column_config.NumberColumn(
                format="%.2f",
            )
        ),
    },
)


# =========================================================
# Dernières prédictions
# =========================================================

st.divider()
st.header("Dernières prédictions")

colonnes_tableau = [
    "timestamp",
    "sk_id_curr",
    "amt_credit",
    "nbre_annee",
    "age",
    "revenu_annuel",
    "score_risque",
    "prediction",
    "decision",
    "temps_inference_ms",
    "latence_application_ms",
]

dernieres_predictions = (
    donnees_production
    .sort_values(
        "timestamp",
        ascending=False,
    )
    .head(20)


    .copy()
)

dernieres_predictions = dernieres_predictions.rename(
    columns={
        "timestamp": "Date",
        "sk_id_curr": "Client",
        "amt_credit": "Montant du crédit",
        "nbre_annee": "Durée",
        "age": "Âge",
        "revenu_annuel": "Revenu annuel",
        "score_risque": "Score de risque",
        "prediction": "Prédiction",
        "decision": "Décision",
        "temps_inference_ms": "Inférence (ms)",
        "latence_application_ms": "Latence (ms)",
    }
)

st.dataframe(
    dernieres_predictions,
    width="stretch",
    hide_index=True,
    column_config={
        "Date": st.column_config.DatetimeColumn(
            format="DD/MM/YYYY HH:mm:ss",
        ),
        "Montant du crédit": (
            st.column_config.NumberColumn(
                format="%.2f €",
            )
        ),
        "Durée": st.column_config.NumberColumn(
            format="%.2f ans",
        ),
        "Revenu annuel": (
            st.column_config.NumberColumn(
                format="%.2f €",
            )
        ),
        "Score de risque": (
            st.column_config.NumberColumn(
                format="%.4f",
            )
        ),
        "Inférence (ms)": (
            st.column_config.NumberColumn(
                format="%.2f ms",
            )
        ),
        "Latence (ms)": (
            st.column_config.NumberColumn(
                format="%.2f ms",
            )
        ),
    },
)


# =========================================================
# Note méthodologique
# =========================================================

st.divider()

st.caption(
    "Les données de production sont simulées à des fins "
    "pédagogiques. Les histogrammes sont normalisés pour "
    "permettre la comparaison entre les groupes de tailles "
    "différentes. Le rapport Evidently reste la référence "
    "pour la détection statistique du drift."
)
