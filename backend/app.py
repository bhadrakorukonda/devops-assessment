import os
import psycopg2
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Read DB settings from environment (provided by docker-compose .env)
DB_HOST = os.environ.get("DB_HOST", "postgres")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "appdb_dev")
DB_USER = os.environ.get("DB_USER", "appuser_dev")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "S3cureDev!P@ssw0rd_2025")

@app.route('/api/hello')
def hello():
    return jsonify({"message": "Hello from backend!"})

@app.route("/ping", methods=["GET"])
def ping():
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
        # Insert a row (optional demo) and read count
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
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == "__main__":
    # 0.0.0.0 so it’s reachable in the container
    app.run(host="0.0.0.0", port=5000)


# app.py
from flask import Flask, request
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST, REGISTRY

app = Flask(__name__)

# Count requests by endpoint and method
REQUESTS = Counter("app_requests_total", "Total app requests", ["endpoint", "method"])

@app.before_request
def _count():
    REQUESTS.labels(endpoint=request.path, method=request.method).inc()

@app.get("/metrics")
def metrics():
    return generate_latest(REGISTRY), 200, {"Content-Type": CONTENT_TYPE_LATEST}
