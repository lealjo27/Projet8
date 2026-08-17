import os
from gradio_app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    max_queue = int(os.environ.get("GRADIO_MAX_QUEUE", 64))
    max_threads = int(os.environ.get("GRADIO_MAX_THREADS", 4))

    # Compatible avec ton erreur actuelle
    app = app.queue(max_size=max_queue)

    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        max_threads=max_threads,
        debug=False,
        show_error=False,
        ssr_mode=False,
    )
