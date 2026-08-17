import json

before = json.load(open("reports/indexed.json"))
after = json.load(open("reports/async_logging.json"))

for metric in ("p50_ms", "p95_ms", "p99_ms"):
    old = before[metric]
    new = after[metric]
    gain = (old - new) / old * 100
    print(f"{metric}: {old:.2f} -> {new:.2f} ms | gain {gain:+.1f}%")