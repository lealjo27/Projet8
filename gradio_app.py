import logging
import time
from concurrent.futures import ThreadPoolExecutor
import gradio as gr

from credit_app.predictor import df, predict_client
from credit_app.bdd.logger_db import log_to_postgres


identifiants_clients = (
    df["SK_ID_CURR"]
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)

##########gradio_predict avec pg en synchrone
# def gradio_predict(
#     identifiant_client,
#     montant_credit,
#     duree_credit,
#     nombre_enfants,
#     anciennete_professionnelle,
#     age,
#     revenu_annuel,
# ):
#     """Lance une prédiction et enregistre le résultat dans NeonDB."""

#     try:
#         debut_total = time.perf_counter()

#         # 1. Prédiction
#         debut_prediction = time.perf_counter()

#         resultat = predict_client(
#             sk_id_curr=int(identifiant_client),
#             amt_credit=float(montant_credit),
#             nbre_annee=float(duree_credit),
#             nombre_enfants=int(nombre_enfants),
#             anciennete_professionnelle=float(
#                 anciennete_professionnelle
#             ),
#             age=int(age),
#             revenu_annuel=float(revenu_annuel),
#         )

#         fin_prediction = time.perf_counter()

#         # 2. Écriture dans NeonDB
#         debut_logging = time.perf_counter()

#         if isinstance(resultat, dict):
#             log_to_postgres(
#                 sk_id=int(identifiant_client),
#                 amt_credit=float(montant_credit),
#                 nbre_annee=float(duree_credit),
#                 result_dict=resultat,
#                 type_donnees="production",
#             )

#         fin_logging = time.perf_counter()
#         fin_total = time.perf_counter()

#         # 3. Ajout des métriques à la réponse
#         resultat["Temps prédiction application ms"] = round(
#             (fin_prediction - debut_prediction) * 1000,
#             2,
#         )

#         resultat["Temps logging PostgreSQL ms"] = round(
#             (fin_logging - debut_logging) * 1000,
#             2,
#         )

#         resultat["Temps traitement total ms"] = round(
#             (fin_total - debut_total) * 1000,
#             2,
#         )

#         return resultat

#     except Exception as erreur:
#         return {"erreur": str(erreur)}
##########gradio_predict avec pg en synchrone

##########gradio_predict avec pg en asynchrone
def gradio_predict(
    identifiant_client,
    montant_credit,
    duree_credit,
    nombre_enfants,
    anciennete_professionnelle,
    age,
    revenu_annuel,
):
    """Lance une prédiction et programme son enregistrement."""

    try:
        debut_total = time.perf_counter()
        debut_prediction = time.perf_counter()

        resultat = predict_client(
            sk_id_curr=int(identifiant_client),
            amt_credit=float(montant_credit),
            nbre_annee=float(duree_credit),
            nombre_enfants=int(nombre_enfants),
            anciennete_professionnelle=float(
                anciennete_professionnelle
            ),
            age=int(age),
            revenu_annuel=float(revenu_annuel),
        )

        fin_prediction = time.perf_counter()

        resultat["Temps prédiction application ms"] = round(
            (fin_prediction - debut_prediction) * 1000,
            2,
        )

        # On copie le dictionnaire pour éviter une modification
        # pendant son utilisation par le thread d'arrière-plan.
        resultat_a_enregistrer = resultat.copy()

        debut_mise_en_file = time.perf_counter()

        logging_executor.submit(
            enregistrer_prediction_async,
            sk_id=int(identifiant_client),
            amt_credit=float(montant_credit),
            nbre_annee=float(duree_credit),
            result_dict=resultat_a_enregistrer,
            type_donnees="production",
        )

        fin_mise_en_file = time.perf_counter()
        fin_total = time.perf_counter()

        resultat["Temps mise en file logging ms"] = round(
            (fin_mise_en_file - debut_mise_en_file) * 1000,
            2,
        )

        resultat["Temps traitement total ms"] = round(
            (fin_total - debut_total) * 1000,
            2,
        )

        return resultat

    except Exception as erreur:
        return {"erreur": str(erreur)}

##########fin gradio_predict avec pg en asynchrone

app = gr.Interface(
    fn=gradio_predict,

    inputs=[
        gr.Dropdown(
            choices=identifiants_clients,
            value=None,
            label="Identifiant client",
            filterable=True,
            allow_custom_value=True,
        ),

        gr.Number(
            label="Montant total du crédit",
            minimum=1,
        ),

        gr.Number(
            label="Durée du crédit en années",
            minimum=1,
        ),

        gr.Number(
            label="Nombre d'enfants",
            minimum=0,
            maximum=20,
            step=1,
            precision=0,
        ),

        gr.Number(
            label="Ancienneté professionnelle en années",
            minimum=0,
            maximum=60,
            step=1,
        ),

        gr.Number(
            label="Âge",
            minimum=18,
            maximum=100,
            step=1,
            precision=0,
        ),

        gr.Number(
            label="Revenu annuel",
            minimum=0,
            step=100,
        ),
    ],

    outputs=gr.JSON(
        label="Résultat du scoring"
    ),

    title="Prêt à Dépenser — Scoring crédit",

    description=(
        "Saisissez les informations du client, "
        "le montant du crédit et la durée souhaitée."
    ),
)

# Deux écritures PostgreSQL peuvent être exécutées en arrière-plan
logging_executor = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="postgres-logger",
)


def enregistrer_prediction_async(**donnees):
    """Enregistre une prédiction sans bloquer la réponse Gradio."""

    debut = time.perf_counter()

    try:
        log_to_postgres(**donnees)

        duree_ms = (time.perf_counter() - debut) * 1000

        logging.info(
            "Logging PostgreSQL terminé en %.2f ms",
            duree_ms,
        )

    except Exception:
        logging.exception(
            "Échec de l'enregistrement dans PostgreSQL"
        )
