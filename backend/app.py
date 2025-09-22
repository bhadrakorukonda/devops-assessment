from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY
import os
import psycopg2
from flask import Flask, jsonify
from flask_cors import CORS

# ------------------------------------------------------------------------------
# Flask app
# ------------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

# Attach exporter (auto-exposes useful flask_* metrics)
metrics = PrometheusMetrics(app)  # does not override /app-metrics below

# ------------------------------------------------------------------------------
# Prometheus manual metrics endpoint (scrape this path)
# ------------------------------------------------------------------------------
@app.get("/app-metrics")
def app_metrics():
    return generate_latest(REGISTRY), 200, {"Content-Type": CONTENT_TYPE_LATEST}

# ------------------------------------------------------------------------------
# Environment / DB config (with your current defaults)
# ------------------------------------------------------------------------------
DB_HOST = os.environ.get("DB_HOST", "postgres")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "appdb_dev")
DB_USER = os.environ.get("DB_USER", "appuser_dev")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "S3cureDev!P@ssw0rd_2025")

# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------
@app.route("/api/hello")
def hello():
    return jsonify({"message": "Hello from backend!"})

@app.route("/ping", methods=["GET"])
def ping():
    # K8s liveness/readiness probes hit this internally on port 5000
    return {"status": "ok"}, 200

@app.route("/api/dbcheck")
@app.route("/dbcheck")
def dbcheck():
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD
        )
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({"db": "ok"}), 200
    except Exception as e:
        return jsonify({"db": "error", "detail": str(e)}), 500

# ------------------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # Listen on 0.0.0.0:5000 (matches Dockerfile EXPOSE and K8s targetPort)
    app.run(host="0.0.0.0", port=5000)
