import gradio as gr
from credit_app.predictor  import df, predict_client
import os
from credit_app.bdd.logger_db import log_to_postgres


client_ids = df["SK_ID_CURR"].dropna().astype(int).unique().tolist()



def gradio_predict(sk_id_curr, amt_credit, nbre_annee):
    try:
        result =  predict_client(
            sk_id_curr=int(sk_id_curr),
            amt_credit=float(amt_credit),
            nbre_annee=float(nbre_annee),
        )

        if isinstance(result, dict):
            log_to_postgres(
                sk_id=int(sk_id_curr),
                amt_credit=float(amt_credit),
                nbre_annee=float(nbre_annee),
                result_dict=result,
            )
            # print(f"DEBUG - Résultat du modèle : {result}")

            return result

    except Exception as error:
        return {"erreur": str(error)}

app = gr.Interface(
    fn=gradio_predict,
    inputs=[
        gr.Dropdown(choices=client_ids, value=None, label="Identifiant client", filterable=True, allow_custom_value=True),
        gr.Number(label="Montant total du crédit", minimum=1),
        gr.Number(label="Durée du crédit en années", minimum=1),
    ],
    outputs=gr.JSON(label="Résultat du scoring"),
    title="Prêt à Dépenser — Scoring crédit",
    description="Saisissez l'identifiant client, le montant du crédit et la durée souhaitée.",
)
