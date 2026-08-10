import gradio as gr

app = gr.Interface(
    fn=lambda x: x,
    inputs=gr.Textbox(label="Test"),
    outputs=gr.Textbox(label="Réponse"),
    title="Test Space"
)
