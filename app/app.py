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

    # Préparer les 795 features
    X_client = client[features]
    X_client = X_client.replace([np.inf, -np.inf], np.nan)

    # Prédiction
    probability = float(model.predict_proba(X_client)[0, 1])
    prediction = int(model.predict(X_client)[0])

    montant_mensuel = amt_annuity / 12 

    return {
        "sk_id_curr": int(sk_id_curr),
        "amt_credit": float(amt_credit),
        "nombre_annees": float(nbre_annee),
        "montant_annuel": round(amt_annuity, 2),
        "montant_mensuel": round(montant_mensuel, 2),
        "risk_probability": round(probability, 4),
        "prediction": prediction,
        "decision": "crédit refusé" if prediction == 1 else "crédit accordé",
    }

