import pandas as pd

from credit_app.bdd.logger_db import log_to_postgres
from credit_app.predictor import df, predict_client


NOMBRE_CLIENTS = 500
GRAINE_ALEATOIRE = 42
JOURS_PAR_AN = 365.25


def convertir_age(jours_naissance):
    """Convertit DAYS_BIRTH en âge."""

    if pd.isna(jours_naissance):
        raise ValueError("L'âge du client est manquant.")

    age = round(abs(float(jours_naissance)) / JOURS_PAR_AN)

    if age < 18 or age > 100:
        raise ValueError(f"Âge invalide : {age}")

    return age


def convertir_anciennete(jours_emploi, age):
    """Convertit DAYS_EMPLOYED en années d'ancienneté."""

    if pd.isna(jours_emploi):
        return 0

    jours_emploi = float(jours_emploi)

    # Dans Home Credit, la valeur 365243 représente généralement
    # une ancienneté inconnue ou non applicable.
    if jours_emploi >= 365243:
        return 0

    anciennete = round(abs(jours_emploi) / JOURS_PAR_AN)

    # Respecte la validation de predict_client()
    anciennete_maximale = max(0, age - 14)

    return min(anciennete, anciennete_maximale)


def calculer_duree_credit(
    montant_credit,
    montant_annuel,
):
    """
    Estime la durée du crédit en années à partir du montant
    du crédit et de l'annuité présente dans les données.
    """

    if pd.isna(montant_annuel):
        raise ValueError("L'annuité du crédit est manquante.")

    montant_annuel = float(montant_annuel)

    if montant_annuel <= 0:
        raise ValueError("L'annuité du crédit est invalide.")

    duree_credit = montant_credit / montant_annuel

    # On impose au minimum une année.
    return max(1.0, duree_credit)


def verifier_colonnes():
    """Vérifie que les données nécessaires sont disponibles."""

    colonnes_obligatoires = [
        "SK_ID_CURR",
        "AMT_CREDIT",
        "AMT_ANNUITY",
        "CNT_CHILDREN",
        "DAYS_EMPLOYED",
        "DAYS_BIRTH",
        "AMT_INCOME_TOTAL",
    ]

    colonnes_absentes = [
        colonne
        for colonne in colonnes_obligatoires
        if colonne not in df.columns
    ]

    if colonnes_absentes:
        raise ValueError(
            "Colonnes absentes du fichier Parquet : "
            + ", ".join(colonnes_absentes)
        )

    return colonnes_obligatoires


def preparer_clients():
    """Sélectionne 50 clients possédant les données nécessaires."""

    colonnes_obligatoires = verifier_colonnes()

    donnees_valides = (
        df[colonnes_obligatoires]
        .drop_duplicates(subset=["SK_ID_CURR"])
        .dropna(
            subset=[
                "SK_ID_CURR",
                "AMT_CREDIT",
                "AMT_ANNUITY",
                "DAYS_BIRTH",
                "AMT_INCOME_TOTAL",
            ]
        )
        .copy()
    )

    # Contrôles métier minimaux
    donnees_valides = donnees_valides[
        (donnees_valides["AMT_CREDIT"] > 0)
        & (donnees_valides["AMT_ANNUITY"] > 0)
        & (donnees_valides["AMT_INCOME_TOTAL"] > 0)
        & (donnees_valides["CNT_CHILDREN"].fillna(0) >= 0)
    ]

    if len(donnees_valides) < NOMBRE_CLIENTS:
        raise ValueError(
            f"Seulement {len(donnees_valides)} clients valides "
            f"sont disponibles, au lieu de {NOMBRE_CLIENTS}."
        )

    return donnees_valides.sample(
        n=NOMBRE_CLIENTS,
        random_state=GRAINE_ALEATOIRE,
    )


def generer_logs_production():
    """
    Lance une prédiction pour 50 clients en utilisant exclusivement
    leurs données d'origine, puis enregistre les résultats dans NeonDB.
    """

    clients_selectionnes = preparer_clients()

    nombre_succes = 0
    nombre_erreurs = 0

    for numero, (_, ligne_client) in enumerate(
        clients_selectionnes.iterrows(),
        start=1,
    ):
        try:
            identifiant_client = int(
                ligne_client["SK_ID_CURR"]
            )

            montant_credit = float(
                ligne_client["AMT_CREDIT"]
            )

            nombre_enfants = int(
                ligne_client["CNT_CHILDREN"]
                if pd.notna(ligne_client["CNT_CHILDREN"])
                else 0
            )

            age = convertir_age(
                ligne_client["DAYS_BIRTH"]
            )

            anciennete_professionnelle = convertir_anciennete(
                ligne_client["DAYS_EMPLOYED"],
                age,
            )

            revenu_annuel = float(
                ligne_client["AMT_INCOME_TOTAL"]
            )

            duree_credit = calculer_duree_credit(
                montant_credit=montant_credit,
                montant_annuel=ligne_client["AMT_ANNUITY"],
            )

            resultat = predict_client(
                sk_id_curr=identifiant_client,
                amt_credit=montant_credit,
                nbre_annee=duree_credit,
                nombre_enfants=nombre_enfants,
                anciennete_professionnelle=(
                    anciennete_professionnelle
                ),
                age=age,
                revenu_annuel=revenu_annuel,
            )

            # Le script ne passe pas par Gradio.
            # La latence applicative n'est donc pas simulée.
            resultat["Source"] = "données originales Parquet"

            log_to_postgres(
                sk_id=identifiant_client,
                amt_credit=montant_credit,
                nbre_annee=duree_credit,
                result_dict=resultat,
                type_donnees="reference",
            )

            nombre_succes += 1

            print(
                f"✅ {numero}/{NOMBRE_CLIENTS} "
                f"— client {identifiant_client}"
            )

        except Exception as erreur:
            nombre_erreurs += 1

            print(
                f"❌ {numero}/{NOMBRE_CLIENTS} "
                f"— {erreur}"
            )

    print("\nGénération terminée")
    print(f"Succès : {nombre_succes}")
    print(f"Erreurs : {nombre_erreurs}")


if __name__ == "__main__":
    generer_logs_production()
