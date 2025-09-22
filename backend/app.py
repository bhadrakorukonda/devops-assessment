from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY
import os
import psycopg2
from flask import Flask, jsonify, request
from flask_cors import CORS

# ------------------------------------------------------------------------------
# Flask app (single instance)
# ------------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

# ------------------------------------------------------------------------------
# Prometheus: exporter + manual endpoint
# ------------------------------------------------------------------------------
# Auto-exposes useful flask_* metrics; does NOT override the manual endpoint
metrics = PrometheusMetrics(app)

@app.get("/app-metrics")  # <- Prometheus should scrape this path
def app_metrics():
    return generate_latest(REGISTRY), 200, {"Content-Type": CONTENT_TYPE_LATEST}

# Optional custom counter example (kept, but not required)
# from prometheus_client import Counter
# REQUESTS = Counter("app_requests_total", "Total app requests", ["endpoint", "method"])
# @app.before_request
# def _count():
#     REQUESTS.labels(endpoint=request.path, method=request.method).inc()

# ------------------------------------------------------------------------------
# Environment / DB config (your current defaults)
# ------------------------------------------------------------------------------
DB_HOST = os.environ.get("DB_HOST", "postgres")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "appdb_dev")
DB_USER = os.environ.get("DB_USER", "appuser_dev")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "S3cureDev!P@ssw0rd_2025")

# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------
@app.route('/api/hello')
def hello():
    return jsonify({"message": "Hello from backend!"})

@app.route("/ping", methods=["GET"])
def ping():
    # K8s probes hit this on container port 5000
    return {"status": "ok"}, 200

@app.route('/api/dbcheck')
@app.route('/dbcheck')
def dbcheck():
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD
        )
        cur = conn.cursor()
        # Ensure table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hello(
                id SERIAL PRIMARY KEY,
                msg TEXT NOT NULL
            );
        """)
        # Insert demo row & count
        cur.execute("INSERT INTO hello(msg) VALUES (%s) RETURNING id;", ("ping from /api/dbcheck",))
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM hello;")
        (count,) = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({
            "status": "ok",
            "inserted_id": new_id,
            "rows_in_hello": count,
            "db": DB_NAME,
            "user": DB_USER,
            "host": DB_HOST,
            "port": DB_PORT
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# ------------------------------------------------------------------------------
# Entrypoint (keep this at the bottom; nothing AFTER this)
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # Matches Dockerfile EXPOSE and K8s targetPort
    app.run(host="0.0.0.0", port=5000)
