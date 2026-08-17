import os
import sys
import cProfile, pstats, io

# Ajouter la racine du projet au PYTHONPATH
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from gradio_app import gradio_predict


samples = [
    (100001, 10000, 2, 2, 5, 35, 25000),
] * 100

def run():
    for s in samples:
        gradio_predict(*s)

pr = cProfile.Profile()
pr.enable()
run()
pr.disable()

s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats("cumtime")
ps.print_stats(30)
ps.dump_stats("reports/profile.prof")
print(s.getvalue())
