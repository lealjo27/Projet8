import time

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


def gradio_predict(
    identifiant_client,
    montant_credit,
    duree_credit,
    nombre_enfants,
    anciennete_professionnelle,
    age,
    revenu_annuel,
):
    """Lance une prédiction et enregistre le résultat dans NeonDB."""

    try:
        debut_traitement = time.perf_counter()

        resultat = predict_client(
            sk_id_curr=int(identifiant_client),
            amt_credit=float(montant_credit),
            nbre_annee=float(duree_credit),

            # Nouvelles informations
            nombre_enfants=int(nombre_enfants),
            anciennete_professionnelle=float(
                anciennete_professionnelle
            ),
            age=int(age),
            revenu_annuel=float(revenu_annuel),
        )

        fin_traitement = time.perf_counter()

        latence_application_ms = (
            fin_traitement - debut_traitement
        ) * 1000

        resultat["Latence application ms"] = round(
            latence_application_ms,
            2,
        )

        if isinstance(resultat, dict):
            log_to_postgres(
                sk_id=int(identifiant_client),
                amt_credit=float(montant_credit),
                nbre_annee=float(duree_credit),
                result_dict=resultat,
                type_donnees="production",
            )

        return resultat

    except Exception as erreur:
        return {
            "erreur": str(erreur)
        }


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
