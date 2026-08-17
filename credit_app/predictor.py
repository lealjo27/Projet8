import re
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

RACINE_PROJET = Path(__file__).resolve().parent.parent

CHEMIN_MODELE = RACINE_PROJET / "credit_app" / "model" / "model.pkl"
CHEMIN_DONNEES = (
    RACINE_PROJET
    / "credit_app"
    / "data"
    / "clients_sample.parquet"
)

SEUIL_DECISION = 0.1598
SEUIL_ENDETTEMENT = 0.35
NOMBRE_JOURS_PAR_AN = 365.25


# ------------------------------------------------------------------
# Chargement du modèle et des données
# ------------------------------------------------------------------

modele = joblib.load(CHEMIN_MODELE)

df = pd.read_parquet(CHEMIN_DONNEES)

# Même nettoyage que pendant l'entraînement
df = df.rename(
    columns=lambda colonne: re.sub(
        r"[^A-Za-z0-9_]+",
        "_",
        colonne,
    )
)

# Variables attendues par le modèle, dans le bon ordre
variables_modele = list(modele.feature_names_in_)

# Vérification réalisée une seule fois au démarrage
variables_absentes = [
    variable
    for variable in variables_modele
    if variable not in df.columns
]

if variables_absentes:
    raise RuntimeError(
        "Variables absentes des données client : "
        + ", ".join(variables_absentes[:10])
    )

# Création d'un index pour accélérer la recherche des clients
df_clients_indexe = (
    df.dropna(subset=["SK_ID_CURR"])
    .drop_duplicates(subset=["SK_ID_CURR"], keep="first")
    .copy()
)

df_clients_indexe["SK_ID_CURR"] = (
    df_clients_indexe["SK_ID_CURR"].astype(int)
)

# drop=False conserve SK_ID_CURR parmi les colonnes du modèle
df_clients_indexe = df_clients_indexe.set_index(
    "SK_ID_CURR",
    drop=False,
)


# ------------------------------------------------------------------
# Fonction de prédiction
# ------------------------------------------------------------------

def predict_client(
    sk_id_curr,
    amt_credit,
    nbre_annee,
    nombre_enfants,
    anciennete_professionnelle,
    age,
    revenu_annuel,
):
    """
    Calcule le risque de défaut et la décision d'octroi du crédit.

    Les informations saisies dans Gradio remplacent les anciennes
    valeurs présentes dans le profil du client.
    """

    # --------------------------------------------------------------
    # 1. Vérification des champs obligatoires
    # --------------------------------------------------------------

    champs_obligatoires = {
        "identifiant client": sk_id_curr,
        "montant du crédit": amt_credit,
        "durée du crédit": nbre_annee,
        "nombre d'enfants": nombre_enfants,
        "ancienneté professionnelle": anciennete_professionnelle,
        "âge": age,
        "revenu annuel": revenu_annuel,
    }

    champs_manquants = [
        nom
        for nom, valeur in champs_obligatoires.items()
        if valeur is None
    ]

    if champs_manquants:
        raise ValueError(
            "Champs obligatoires manquants : "
            + ", ".join(champs_manquants)
        )

    # --------------------------------------------------------------
    # 2. Conversion des types
    # --------------------------------------------------------------

    try:
        identifiant_client = int(sk_id_curr)
        montant_credit = float(amt_credit)
        duree_credit = float(nbre_annee)
        nombre_enfants = int(nombre_enfants)
        anciennete_professionnelle = float(
            anciennete_professionnelle
        )
        age = int(age)
        revenu_annuel = float(revenu_annuel)

    except (TypeError, ValueError) as erreur:
        raise ValueError(
            "Les informations saisies doivent être numériques."
        ) from erreur

    # --------------------------------------------------------------
    # 3. Validation des valeurs
    # --------------------------------------------------------------

    if montant_credit <= 0:
        raise ValueError(
            "Le montant du crédit doit être supérieur à 0."
        )

    if duree_credit <= 0:
        raise ValueError(
            "La durée du crédit doit être supérieure à 0."
        )

    if nombre_enfants < 0:
        raise ValueError(
            "Le nombre d'enfants ne peut pas être négatif."
        )

    if anciennete_professionnelle < 0:
        raise ValueError(
            "L'ancienneté professionnelle ne peut pas être négative."
        )

    if age < 18 or age > 100:
        raise ValueError(
            "L'âge doit être compris entre 18 et 100 ans."
        )

    if anciennete_professionnelle > age - 14:
        raise ValueError(
            "L'ancienneté professionnelle saisie est incohérente "
            "avec l'âge du client."
        )

    if revenu_annuel <= 0:
        raise ValueError(
            "Le revenu annuel doit être supérieur à 0."
        )

    # --------------------------------------------------------------
    # 4. Recherche du client
    # --------------------------------------------------------------
########### Code avant optimation########""
    # client = df.loc[
    #     df["SK_ID_CURR"] == identifiant_client
    # ].copy()

    # if client.empty:
    #     raise ValueError(
    #         f"Client {identifiant_client} introuvable."
    #     )

    # # Conservation d'une seule ligne
    # client = client.iloc[[0]].copy()
########### Code avant optimation########""

    try:
        client = df_clients_indexe.loc[[identifiant_client]].copy()


    except KeyError as erreur:
        raise ValueError(
            f"Client {identifiant_client} introuvable."
        ) from erreur


    # --------------------------------------------------------------
    # 5. Calcul des données financières
    # --------------------------------------------------------------

    montant_annuel = montant_credit / duree_credit
    montant_mensuel = montant_annuel / 12
    revenu_mensuel = revenu_annuel / 12

    taux_endettement = (
        montant_mensuel / revenu_mensuel
    )

    # --------------------------------------------------------------
    # 6. Mise à jour des données saisies
    # --------------------------------------------------------------

    # Variables financières
    if "AMT_CREDIT" in client.columns:
        client.loc[:, "AMT_CREDIT"] = montant_credit

    if "AMT_ANNUITY" in client.columns:
        client.loc[:, "AMT_ANNUITY"] = montant_annuel

    if "AMT_INCOME_TOTAL" in client.columns:
        client.loc[:, "AMT_INCOME_TOTAL"] = revenu_annuel

    # Nombre d'enfants
    if "CNT_CHILDREN" in client.columns:
        client.loc[:, "CNT_CHILDREN"] = nombre_enfants

    # Home Credit représente l'âge avec un nombre de jours négatif
    if "DAYS_BIRTH" in client.columns:
        client.loc[:, "DAYS_BIRTH"] = -round(
            age * NOMBRE_JOURS_PAR_AN
        )

    # Ancienneté professionnelle en jours négatifs
    if "DAYS_EMPLOYED" in client.columns:
        client.loc[:, "DAYS_EMPLOYED"] = -round(
            anciennete_professionnelle
            * NOMBRE_JOURS_PAR_AN
        )

    # Certaines versions du dataset peuvent contenir directement
    # des variables exprimées en années.
    if "AGE" in client.columns:
        client.loc[:, "AGE"] = age

    if "YEARS_BIRTH" in client.columns:
        client.loc[:, "YEARS_BIRTH"] = age

    if "YEARS_EMPLOYED" in client.columns:
        client.loc[
            :,
            "YEARS_EMPLOYED",
        ] = anciennete_professionnelle

    # --------------------------------------------------------------
    # 7. Recalcul des variables dépendantes
    # --------------------------------------------------------------

    if "INCOME_CREDIT_PERC" in client.columns:
        client.loc[
            :,
            "INCOME_CREDIT_PERC",
        ] = revenu_annuel / montant_credit

    if "ANNUITY_INCOME_PERC" in client.columns:
        client.loc[
            :,
            "ANNUITY_INCOME_PERC",
        ] = montant_annuel / revenu_annuel

    if "PAYMENT_RATE" in client.columns:
        client.loc[
            :,
            "PAYMENT_RATE",
        ] = montant_annuel / montant_credit

    # --------------------------------------------------------------
    # 8. Préparation des variables du modèle
    # --------------------------------------------------------------


    donnees_client = client[variables_modele].copy()

    donnees_client = donnees_client.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    # --------------------------------------------------------------
    # 9. Prédiction et mesure du temps d'inférence
    # --------------------------------------------------------------

    debut_inference = time.perf_counter()

    probabilite_risque = float(
        modele.predict_proba(donnees_client)[0, 1]
    )

    fin_inference = time.perf_counter()

    temps_inference_ms = (
        fin_inference - debut_inference
    ) * 1000

    # --------------------------------------------------------------
    # 10. Application des règles de décision
    # --------------------------------------------------------------

    refus_modele = (
        probabilite_risque >= SEUIL_DECISION
    )

    refus_endettement = (
        taux_endettement > SEUIL_ENDETTEMENT
    )

    prediction = int(
        refus_modele or refus_endettement
    )

    if refus_endettement:
        raison = "Taux d'endettement trop élevé"

    elif refus_modele:
        raison = "Risque client trop élevé"

    else:
        raison = "Critères respectés"

    decision = (
        "crédit refusé"
        if prediction == 1
        else "crédit accordé"
    )

    # --------------------------------------------------------------
    # 11. Résultat envoyé à Gradio et NeonDB
    # --------------------------------------------------------------

    return {
    # ----------------------------------------------------------
    # 1. Informations renseignées dans le formulaire
    # ----------------------------------------------------------
    "Identifiant client": identifiant_client,
    "Montant du crédit": round(montant_credit, 2),
    "Durée du crédit en années": round(duree_credit, 2),
    "Nombre d'enfants": nombre_enfants,
    "Ancienneté professionnelle en années": round(
        anciennete_professionnelle,
        2,
    ),
    "Âge": age,
    "Revenu annuel": round(revenu_annuel, 2),

    # ----------------------------------------------------------
    # 2. Éléments calculés et renvoyés par le modèle
    # ----------------------------------------------------------
    "Score de risque": round(
        probabilite_risque,
        4,
    ),
    "Seuil de décision": SEUIL_DECISION,
    "Prédiction": prediction,
    "Décision": decision,
    "Raison": raison,

    # ----------------------------------------------------------
    # 3. Indicateurs financiers calculés
    # ----------------------------------------------------------
    "Revenu mensuel": round(revenu_mensuel, 2),
    "Montant annuel à rembourser": round(
        montant_annuel,
        2,
    ),
    "Montant mensuel à rembourser": round(
        montant_mensuel,
        2,
    ),
    "Taux d'endettement": round(
        taux_endettement,
        4,
    ),
    "Taux d'endettement en pourcentage": (
        f"{taux_endettement * 100:.2f} %"
    ),
    "Seuil d'endettement": SEUIL_ENDETTEMENT,

    # ----------------------------------------------------------
    # 4. Métriques techniques
    # ----------------------------------------------------------
    "Temps d'inférence en ms": round(
        temps_inference_ms,
        2,
    ),
}

