import time, json, argparse, statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from gradio_client import Client

def run(url, samples, n=300, workers=8):
    client = Client(url)
    lat = []
    def one(s):
        t0 = time.perf_counter()
        client.predict(*s, api_name="/gradio_predict")
        return (time.perf_counter()-t0)*1000

    with ThreadPoolExecutor(max_workers=workers) as ex:
        fut = [ex.submit(one, samples[i % len(samples)]) for i in range(n)]
        for f in as_completed(fut):
            lat.append(f.result())

    lat.sort()
    return {
        "p50_ms": round(statistics.median(lat), 2),
        "p95_ms": round(lat[int(0.95*len(lat))], 2),
        "p99_ms": round(lat[int(0.99*len(lat))], 2),
        "count": len(lat)
    }

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:7860")
    ap.add_argument("--out", default="reports/base.json")
    args = ap.parse_args()

    samples = [
        (100001, 10000, 2, 2, 5, 35, 25000),
        (100002, 5000, 1, 0, 3, 42, 18000),
    ]

    res = run(args.url, samples, n=300, workers=16)
    with open(args.out, "w") as f:
        json.dump(res, f, indent=2)
    print(res)

