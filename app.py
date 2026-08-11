import os

from gradio_app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        ssr_mode=False,
    )
