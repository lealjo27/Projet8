import gradio as gr
from app.app import df, predict_client   # ← IMPORTANT: from app.app

client_ids = df["SK_ID_CURR"].dropna().astype(int).unique().tolist()

def gradio_predict(sk_id_curr, amt_credit, nbre_annee):
    try:
        return predict_client(int(sk_id_curr), float(amt_credit), float(nbre_annee))
    except Exception as error:
        return {"erreur": str(error)}

app = gr.Interface(
    fn=gradio_predict,
    inputs=[
        gr.Dropdown(choices=client_ids, value=None, label="Identifiant client",
                    filterable=True, allow_custom_value=True),
        gr.Number(label="Montant total du crédit", minimum=1),
        gr.Number(label="Durée du crédit en années", minimum=1),
    ],
    outputs=gr.JSON(label="Résultat du scoring"),
    title="Prêt à Dépenser — Scoring crédit",
    description="Saisissez l'identifiant client, le montant du crédit et la durée souhaitée.",
)
