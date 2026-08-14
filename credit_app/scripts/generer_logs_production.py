import time

import pandas as pd

from credit_app.bdd.logger_db import log_to_postgres
from credit_app.predictor import df, predict_client


NOMBRE_CLIENTS = 98
GRAINE_ALEATOIRE = 123
JOURS_PAR_AN = 365.25

# Dérive simulée
HAUSSE_MONTANT_CREDIT = 1.20
BAISSE_REVENU = 0.85


def convertir_age(jours_naissance):
    """Convertit DAYS_BIRTH en âge."""

    age = round(
        abs(float(jours_naissance))
        / JOURS_PAR_AN
    )

    return min(max(age, 18), 100)


def convertir_anciennete(jours_emploi, age):
    """Convertit DAYS_EMPLOYED en ancienneté."""

    if pd.isna(jours_emploi):
        return 0

    jours_emploi = float(jours_emploi)

    # Valeur spéciale du dataset Home Credit
    if jours_emploi >= 365243:
        return 0

    anciennete = round(
        abs(jours_emploi)
        / JOURS_PAR_AN
    )

    anciennete_maximale = max(0, age - 14)

    return min(
        anciennete,
        anciennete_maximale,
    )


def calculer_duree_credit(
    montant_credit_original,
    annuite_originale,
):
    """Estime la durée depuis les données originales."""

    if pd.isna(annuite_originale):
        return 5.0

    annuite_originale = float(annuite_originale)

    if annuite_originale <= 0:
        return 5.0

    duree = (
        montant_credit_original
        / annuite_originale
    )

    return max(1.0, duree)


def recuperer_identifiants_reference():
    """
    Récupère les clients déjà utilisés comme référence
    pour éviter de les reprendre en production.
    """

    import os
    import psycopg2

    url_base_donnees = os.getenv("DATABASE_URL")

    requete = """
        SELECT DISTINCT sk_id_curr
        FROM prediction_logs
        WHERE type_donnees = 'reference';
    """

    with psycopg2.connect(url_base_donnees) as connexion:
        with connexion.cursor() as curseur:
            curseur.execute(requete)
            lignes = curseur.fetchall()

    return {
        ligne[0]
        for ligne in lignes
    }


def preparer_clients_production():
    """Sélectionne 100 clients absents de la référence."""

    identifiants_reference = (
        recuperer_identifiants_reference()
    )

    colonnes_obligatoires = [
        "SK_ID_CURR",
        "AMT_CREDIT",
        "AMT_ANNUITY",
        "CNT_CHILDREN",
        "DAYS_EMPLOYED",
        "DAYS_BIRTH",
        "AMT_INCOME_TOTAL",
    ]

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

    donnees_valides["SK_ID_CURR"] = (
        donnees_valides["SK_ID_CURR"]
        .astype(int)
    )

    # Retirer les clients déjà présents en référence
    donnees_valides = donnees_valides[
        ~donnees_valides["SK_ID_CURR"].isin(
            identifiants_reference
        )
    ]

    # Contrôles simples
    donnees_valides = donnees_valides[
        (donnees_valides["AMT_CREDIT"] > 0)
        & (donnees_valides["AMT_ANNUITY"] > 0)
        & (donnees_valides["AMT_INCOME_TOTAL"] > 0)
    ]

    if len(donnees_valides) < NOMBRE_CLIENTS:
        raise ValueError(
            "Pas assez de clients disponibles "
            "pour générer la production."
        )

    return donnees_valides.sample(
        n=NOMBRE_CLIENTS,
        random_state=GRAINE_ALEATOIRE,
    )


def generer_logs_production():
    """Génère 100 logs de production simulés."""

    clients = preparer_clients_production()

    nombre_succes = 0
    nombre_erreurs = 0

    for numero, (_, ligne) in enumerate(
        clients.iterrows(),
        start=1,
    ):
        try:
            identifiant_client = int(
                ligne["SK_ID_CURR"]
            )

            montant_original = float(
                ligne["AMT_CREDIT"]
            )

            revenu_original = float(
                ligne["AMT_INCOME_TOTAL"]
            )

            age = convertir_age(
                ligne["DAYS_BIRTH"]
            )

            anciennete = convertir_anciennete(
                ligne["DAYS_EMPLOYED"],
                age,
            )

            nombre_enfants = int(
                ligne["CNT_CHILDREN"]
                if pd.notna(ligne["CNT_CHILDREN"])
                else 0
            )

            duree_credit = calculer_duree_credit(
                montant_original,
                ligne["AMT_ANNUITY"],
            )

            # Application de la dérive simulée
            montant_production = (
                montant_original
                * HAUSSE_MONTANT_CREDIT
            )

            revenu_production = (
                revenu_original
                * BAISSE_REVENU
            )

            debut_traitement = time.perf_counter()

            resultat = predict_client(
                sk_id_curr=identifiant_client,
                amt_credit=montant_production,
                nbre_annee=duree_credit,
                nombre_enfants=nombre_enfants,
                anciennete_professionnelle=anciennete,
                age=age,
                revenu_annuel=revenu_production,
            )

            fin_traitement = time.perf_counter()

            resultat["Latence application ms"] = round(
                (
                    fin_traitement
                    - debut_traitement
                ) * 1000,
                2,
            )

            log_to_postgres(
                sk_id=identifiant_client,
                amt_credit=montant_production,
                nbre_annee=duree_credit,
                result_dict=resultat,
                type_donnees="production",
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
    print("Succès :", nombre_succes)
    print("Erreurs :", nombre_erreurs)


if __name__ == "__main__":
    generer_logs_production()
