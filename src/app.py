from flask import Flask, render_template, request, send_file, redirect, url_for, session, flash
from src.utils import generate_qr_code, is_valid_url
import psycopg2
import io
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "una-chiave-segreta")

# Supabase Auth
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

DB_PARAMS = {
    "host": "db.tnupavqdngycwlruixmy.supabase.co",
    "database": "postgres",
    "user": "postgres",
    "password": "Davide0902!",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_PARAMS)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            supabase.auth.sign_up({"email": email, "password": password})
            flash("Registrazione completata! Ora puoi fare il login.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(str(e), "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            user = supabase.auth.sign_in_with_password({"email": email, "password": password}).user
            session["user_id"] = user.id
            return redirect(url_for("index"))
        except Exception as e:
            flash("Login fallito: " + str(e), "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    supabase.auth.sign_out()
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    qr_generated = False
    error = None
    user_id = session["user_id"]

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
                "INSERT INTO qrcodes (site_name, qr_code, url, user_id) VALUES (%s, %s, %s, %s)",
                (site_name, psycopg2.Binary(qr_bytes), url, user_id)
            )
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for("index", qr_generated=1))

    qr_generated = request.args.get("qr_generated") == "1"

    # Recupera solo i record dell'utente loggato
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, site_name, url FROM qrcodes WHERE user_id = %s ORDER BY id DESC", (user_id,))
    records = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("index.html", qr_generated=qr_generated, error=error, records=records)

@app.route("/qrcode_img/<int:qr_id>")
def qrcode_img(qr_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT qr_code FROM qrcodes WHERE id = %s AND user_id = %s", (qr_id, user_id))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return send_file(io.BytesIO(row[0]), mimetype="image/png")
    return "QR code non trovato", 404

if __name__ == "__main__":
    app.run(debug=True)