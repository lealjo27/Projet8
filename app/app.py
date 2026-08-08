import joblib
import numpy as np
import pandas as pd
import re

MODEL_PATH = "app/model/model.pkl"
DATA_PATH = "app/data/clients_sample.parquet"

# Chargement
model = joblib.load(MODEL_PATH)
df = pd.read_parquet(DATA_PATH)

# Même nettoyage que pendant l’entraînement
df = df.rename(
    columns=lambda col: re.sub(r"[^A-Za-z0-9_]+", "_", col)
)

seuil_decision = 0.1598
seuil_endettement = 0.35

# Features attendues dans le bon ordre
features = list(model.feature_names_in_)

def predict_client(sk_id_curr, amt_credit, nbre_annee):
    if amt_credit <= 0:
        raise ValueError("AMT_CREDIT doit être supérieur à 0.")

    if nbre_annee <= 0:
        raise ValueError("NOMBRE_ANNEE doit être supérieur à 0.")

    amt_annuity = amt_credit / nbre_annee

    # Rechercher le client
    client = df.loc[df["SK_ID_CURR"] == sk_id_curr].copy()

    if client.empty:
        raise ValueError(f"Client {sk_id_curr} introuvable.")

    # Une seule ligne client
    client = client.iloc[[0]]

    # Remplacer par les valeurs du formulaire
    client.loc[:, "AMT_CREDIT"] = amt_credit
    client.loc[:, "AMT_ANNUITY"] = amt_annuity

    # Recalcul des variables liées au nouveau montant du crédit et de la durée
    revenu = float(client["AMT_INCOME_TOTAL"].iloc[0])

    if revenu < 0:
        raise ValueError("Le revenu doit être un nombre positif.")

    client.loc[:, "INCOME_CREDIT_PERC"] = revenu / amt_credit
    client.loc[:, "ANNUITY_INCOME_PERC"] = amt_annuity / revenu
    client.loc[:, "PAYMENT_RATE"] = amt_annuity / amt_credit

    # Préparer les 795 features
    X_client = client[features]
    X_client = X_client.replace([np.inf, -np.inf], np.nan)


    # Prédiction
    probability = float(model.predict_proba(X_client)[0, 1])

    prediction = int(probability >= seuil_decision)

    montant_mensuel = amt_annuity / 12 
    revenu_annuel = float(client["AMT_INCOME_TOTAL"].iloc[0])
    revenu_mensuel = revenu_annuel / 12

    taux_endettement = montant_mensuel / revenu_mensuel

    refus_modele = probability >= seuil_decision
    refus_endettement = taux_endettement > seuil_endettement

    prediction = int(refus_modele or refus_endettement)

    if refus_endettement:
        raison = "Taux d'endettement trop élevé"
    elif refus_modele:
        raison = "Risque client trop élevé"
    else:
        raison = "Critères respectés"



    return {
        "ID Client": int(sk_id_curr),
        "Montant crédit": float(amt_credit),
        "Durée en années": float(nbre_annee),
        "Montant à rembourser annuellement": round(amt_annuity, 2),
        "Montant mensuel à rembourser": round(montant_mensuel, 2),
        "Revenu mensuel": round(revenu_mensuel, 2),
        "Taux risque client": round(probability, 4),
        "Prediction": prediction,
        "seuil_decision": seuil_decision,
        "seuil_endettement": seuil_endettement,
        "Taux endettement du client": f"{taux_endettement * 100:.2f} %",
        "decision": "crédit refusé" if prediction else "crédit accordé",
        "Raison": raison,
    }

