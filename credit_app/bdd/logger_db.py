import os

import psycopg2


# ------------------------------------------------------------------
# Connexion
# ------------------------------------------------------------------

def obtenir_url_base_donnees():
    """Récupère l'URL de connexion à NeonDB."""

    url_base_donnees = os.getenv("DATABASE_URL")

    if not url_base_donnees:
        raise ValueError(
            "La variable d'environnement DATABASE_URL "
            "n'est pas définie."
        )

    return url_base_donnees


def obtenir_connexion():
    """Ouvre une connexion à NeonDB."""

    return psycopg2.connect(
        obtenir_url_base_donnees()
    )


# ------------------------------------------------------------------
# Test de connexion
# ------------------------------------------------------------------

def test_connection():
    """Teste la connexion à NeonDB."""

    connexion = None

    try:
        connexion = obtenir_connexion()

        with connexion.cursor() as curseur:
            curseur.execute("SELECT version();")
            version = curseur.fetchone()[0]

        print(
            "✅ Connexion à NeonDB réussie ! "
            f"Version : {version}"
        )

        return True

    except Exception as erreur:
        print(
            "❌ Échec de la connexion à NeonDB : "
            f"{erreur}"
        )

        return False

    finally:
        if connexion is not None:
            connexion.close()


# ------------------------------------------------------------------
# Création et mise à jour de la table
# ------------------------------------------------------------------

def create_predictions_logs_table():
    """
    Crée la table prediction_logs si elle n'existe pas.

    Si l'ancienne table contenant score_result existe déjà,
    les nouvelles colonnes sont ajoutées sans supprimer les données.
    """

    connexion = None

    try:
        connexion = obtenir_connexion()

        with connexion.cursor() as curseur:
            # Création de la table pour une nouvelle base
            curseur.execute(
                """
                CREATE TABLE IF NOT EXISTS prediction_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ
                        DEFAULT CURRENT_TIMESTAMP,

                    sk_id_curr INTEGER,
                    amt_credit DOUBLE PRECISION,
                    nbre_annee DOUBLE PRECISION,

                    nombre_enfants INTEGER,
                    anciennete_professionnelle
                        DOUBLE PRECISION,
                    age INTEGER,
                    revenu_annuel DOUBLE PRECISION,

                    score_risque DOUBLE PRECISION,
                    seuil_decision DOUBLE PRECISION,
                    prediction INTEGER,
                    decision TEXT,
                    raison TEXT,

                    revenu_mensuel DOUBLE PRECISION,
                    montant_annuel_remboursement
                        DOUBLE PRECISION,
                    montant_mensuel_remboursement
                        DOUBLE PRECISION,
                    taux_endettement DOUBLE PRECISION,
                    seuil_endettement DOUBLE PRECISION,

                    temps_inference_ms DOUBLE PRECISION,
                    latence_application_ms
                        DOUBLE PRECISION,

                    type_donnees TEXT
                        DEFAULT 'production'
                );
                """
            )

            # Mise à jour compatible avec ton ancienne table
            curseur.execute(
                """
                ALTER TABLE prediction_logs
                    ADD COLUMN IF NOT EXISTS
                        nombre_enfants INTEGER,
                    ADD COLUMN IF NOT EXISTS
                        anciennete_professionnelle
                            DOUBLE PRECISION,
                    ADD COLUMN IF NOT EXISTS
                        age INTEGER,
                    ADD COLUMN IF NOT EXISTS
                        revenu_annuel DOUBLE PRECISION,
                    ADD COLUMN IF NOT EXISTS
                        score_risque DOUBLE PRECISION,
                    ADD COLUMN IF NOT EXISTS
                        seuil_decision DOUBLE PRECISION,
                    ADD COLUMN IF NOT EXISTS
                        prediction INTEGER,
                    ADD COLUMN IF NOT EXISTS
                        decision TEXT,
                    ADD COLUMN IF NOT EXISTS
                        raison TEXT,
                    ADD COLUMN IF NOT EXISTS
                        revenu_mensuel DOUBLE PRECISION,
                    ADD COLUMN IF NOT EXISTS
                        montant_annuel_remboursement
                            DOUBLE PRECISION,
                    ADD COLUMN IF NOT EXISTS
                        montant_mensuel_remboursement
                            DOUBLE PRECISION,
                    ADD COLUMN IF NOT EXISTS
                        taux_endettement DOUBLE PRECISION,
                    ADD COLUMN IF NOT EXISTS
                        seuil_endettement DOUBLE PRECISION,
                    ADD COLUMN IF NOT EXISTS
                        temps_inference_ms DOUBLE PRECISION,
                    ADD COLUMN IF NOT EXISTS
                        latence_application_ms
                            DOUBLE PRECISION,
                    ADD COLUMN IF NOT EXISTS
                        type_donnees TEXT
                            DEFAULT 'production';
                """
            )

        connexion.commit()

        print(
            "✅ Table 'prediction_logs' créée ou "
            "mise à jour avec succès."
        )

        return True

    except Exception as erreur:
        if connexion is not None:
            connexion.rollback()

        print(
            "❌ Erreur lors de la création de la table : "
            f"{erreur}"
        )

        return False

    finally:
        if connexion is not None:
            connexion.close()


# ------------------------------------------------------------------
# Enregistrement d'une prédiction
# ------------------------------------------------------------------

def log_to_postgres(
    sk_id,
    amt_credit,
    nbre_annee,
    result_dict,
    type_donnees="production",
):
    """
    Enregistre une prédiction dans NeonDB.

    type_donnees :
    - "reference" pour les données originales du fichier Parquet ;
    - "production" pour les saisies réalisées dans Gradio.
    """

    if not isinstance(result_dict, dict):
        raise TypeError(
            "result_dict doit être un dictionnaire."
        )

    requete = """
        INSERT INTO prediction_logs (
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
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        );
    """

    valeurs = (
        int(sk_id),
        float(amt_credit),
        float(nbre_annee),

        int(
            result_dict["Nombre d'enfants"]
        ),

        float(
            result_dict[
                "Ancienneté professionnelle en années"
            ]
        ),

        int(
            result_dict["Âge"]
        ),

        float(
            result_dict["Revenu annuel"]
        ),

        float(
            result_dict["Score de risque"]
        ),

        float(
            result_dict["Seuil de décision"]
        ),

        int(
            result_dict["Prédiction"]
        ),

        result_dict["Décision"],

        result_dict["Raison"],

        float(
            result_dict["Revenu mensuel"]
        ),

        float(
            result_dict[
                "Montant annuel à rembourser"
            ]
        ),

        float(
            result_dict[
                "Montant mensuel à rembourser"
            ]
        ),

        float(
            result_dict["Taux d'endettement"]
        ),

        float(
            result_dict["Seuil d'endettement"]
        ),

        float(
            result_dict[
                "Temps d'inférence en ms"
            ]
        ),

        convertir_float_optionnel(
            result_dict.get(
                "Latence application ms"
            )
        ),

        type_donnees,
    )

    connexion = None

    try:
        connexion = obtenir_connexion()

        with connexion.cursor() as curseur:
            curseur.execute(
                requete,
                valeurs,
            )

        connexion.commit()

    except Exception:
        if connexion is not None:
            connexion.rollback()

        # On transmet l'erreur à Gradio ou aux tests.
        raise

    finally:
        if connexion is not None:
            connexion.close()


# ------------------------------------------------------------------
# Fonction utilitaire
# ------------------------------------------------------------------

def convertir_float_optionnel(valeur):
    """Convertit une valeur en float si elle est renseignée."""

    if valeur is None:
        return None

    return float(valeur)


# ------------------------------------------------------------------
# Exécution directe
# ------------------------------------------------------------------

if __name__ == "__main__":
    if test_connection():
        create_predictions_logs_table()
