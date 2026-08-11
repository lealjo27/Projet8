import re

import joblib
import numpy as np
import pandas as pd


MODEL_PATH = "credit_app/model/model.pkl"
DATA_PATH = "credit_app/data/clients_sample.parquet"

SEUIL_DECISION = 0.1598
SEUIL_ENDETTEMENT = 0.35


# Chargement du modèle et des données
model = joblib.load(MODEL_PATH)
df = pd.read_parquet(DATA_PATH)

# Même nettoyage des noms de colonnes que pendant l'entraînement
df = df.rename(
    columns=lambda column: re.sub(r"[^A-Za-z0-9_]+", "_", column)
)

# Variables attendues par le modèle, dans le bon ordre
features = list(model.feature_names_in_)


def predict_client(sk_id_curr, amt_credit, nbre_annee):
    """Calcule le risque et la décision d'octroi d'un crédit."""

    # 1. Vérifier les champs obligatoires
    if sk_id_curr is None:
        raise ValueError("L'identifiant client est obligatoire.")

    if amt_credit is None:
        raise ValueError("Le montant du crédit est obligatoire.")

    if nbre_annee is None:
        raise ValueError("La durée du crédit est obligatoire.")

    # 2. Convertir et vérifier les types
    try:
        sk_id_curr = int(sk_id_curr)
        amt_credit = float(amt_credit)
        nbre_annee = float(nbre_annee)
    except (TypeError, ValueError) as error:
        raise ValueError(
            "L'identifiant, le montant et la durée doivent être numériques."
        ) from error

    # 3. Vérifier les plages de valeurs
    if amt_credit <= 0:
        raise ValueError(
            "Le montant du crédit doit être strictement supérieur à 0."
        )

    if nbre_annee <= 0:
        raise ValueError(
            "La durée du crédit doit être strictement supérieure à 0."
        )

    # Recherche du client
    client = df.loc[df["SK_ID_CURR"] == sk_id_curr].copy()

    if client.empty:
        raise ValueError(f"Client {sk_id_curr} introuvable.")

    # Conservation d'une seule ligne
    client = client.iloc[[0]].copy()

    # Vérification du revenu
    revenu_annuel = float(client["AMT_INCOME_TOTAL"].iloc[0])

    if revenu_annuel <= 0:
        raise ValueError(
            "Le revenu annuel doit être strictement supérieur à 0."
        )

    # Calcul des nouvelles mensualités
    montant_annuel = amt_credit / nbre_annee
    montant_mensuel = montant_annuel / 12
    revenu_mensuel = revenu_annuel / 12

    # Mise à jour des données du crédit
    client.loc[:, "AMT_CREDIT"] = amt_credit
    client.loc[:, "AMT_ANNUITY"] = montant_annuel

    # Recalcul des variables dépendantes
    client.loc[:, "INCOME_CREDIT_PERC"] = revenu_annuel / amt_credit
    client.loc[:, "ANNUITY_INCOME_PERC"] = montant_annuel / revenu_annuel
    client.loc[:, "PAYMENT_RATE"] = montant_annuel / amt_credit

    # Préparation des variables dans l'ordre attendu
    X_client = client[features].copy()
    X_client = X_client.replace([np.inf, -np.inf], np.nan)

    # Prédiction du risque
    probabilite = float(model.predict_proba(X_client)[0, 1])

    # Calcul du taux d'endettement
    taux_endettement = montant_mensuel / revenu_mensuel

    # Règles de décision
    refus_modele = probabilite >= SEUIL_DECISION
    refus_endettement = taux_endettement > SEUIL_ENDETTEMENT
    prediction = int(refus_modele or refus_endettement)

    if refus_endettement:
        raison = "Taux d'endettement trop élevé"
    elif refus_modele:
        raison = "Risque client trop élevé"
    else:
        raison = "Critères respectés"

    return {
        "ID Client": int(sk_id_curr),
        "Montant crédit": round(float(amt_credit), 2),
        "Durée en années": round(float(nbre_annee), 2),
        "Montant à rembourser annuellement": round(montant_annuel, 2),
        "Montant mensuel à rembourser": round(montant_mensuel, 2),
        "Revenu mensuel": round(revenu_mensuel, 2),
        "Taux risque client": round(probabilite, 4),
        "Prediction": prediction,
        "seuil_decision": SEUIL_DECISION,
        "seuil_endettement": SEUIL_ENDETTEMENT,
        "Taux endettement du client": (
            f"{taux_endettement * 100:.2f} %"
        ),
        "decision": (
            "crédit refusé" if prediction else "crédit accordé"
        ),
        "Raison": raison,
    }
