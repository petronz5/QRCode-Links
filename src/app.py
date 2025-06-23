from flask import Flask, render_template, request, send_file, redirect, url_for
from utils import generate_qr_code, is_valid_url
import psycopg2
import io
import os

app = Flask(__name__)

# Configura la connessione al database
DB_PARAMS = {
    "host": "localhost",
    "database": "QRCodeLinks",
    "user": "postgres",
    "password": "postgres",
    "port": "5433"
}

def get_db_connection():
    return psycopg2.connect(**DB_PARAMS)

@app.route("/", methods=["GET", "POST"])
def index():
    qr_generated = False
    error = None

    if request.method == "POST":
        url = request.form.get("url")
        site_name = request.form.get("site_name")
        if not is_valid_url(url):
            error = "URL non valido!"
        elif not site_name:
            error = "Nome sito obbligatorio!"
        else:
            filename = "qrcode.png"
            generate_qr_code(url, filename)
            with open(filename, "rb") as f:
                qr_bytes = f.read()
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO qrcodes (site_name, qr_code, url) VALUES (%s, %s, %s)",
                (site_name, psycopg2.Binary(qr_bytes), url)
            )
            conn.commit()
            cur.close()
            conn.close()
            # Redirect dopo il POST per evitare duplicati
            return redirect(url_for("index", qr_generated=1))

    qr_generated = request.args.get("qr_generated") == "1"

    # Recupera tutti i record dal db
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, site_name, url FROM qrcodes ORDER BY id DESC")
    records = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("index.html", qr_generated=qr_generated, error=error, records=records)


@app.route("/qrcode_img/<int:qr_id>")
def qrcode_img(qr_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT qr_code FROM qrcodes WHERE id = %s", (qr_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return send_file(io.BytesIO(row[0]), mimetype="image/png")
    return "QR code non trovato", 404

if __name__ == "__main__":
    app.run(debug=True)