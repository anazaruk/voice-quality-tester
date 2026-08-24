#!/usr/src/NISQA/venv/bin/python3

from flask import Flask, request, redirect
import pymysql
import html
import os

DB_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
DB_USER = os.getenv("MYSQL_USER", "nisqa")
DB_PASS = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DATABASE", "voice_quality")

BASE_URL = "/dialer"

app = Flask(__name__)


def db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )


def esc(v):
    return html.escape("" if v is None else str(v), quote=True)


PAGE_HEAD = """
<!DOCTYPE html>
<html>
<head>
<title>NISQA Dialer Targets</title>
<style>
body { margin:0; font-family:Arial,Helvetica,sans-serif; background:#0b1120; color:#e5e7eb; }
.container { max-width:1400px; margin:30px auto; padding:0 25px; }
h1 { margin-bottom:5px; font-size:28px; }
.subtitle { color:#9ca3af; margin-bottom:25px; }
.card { background:#111827; border:1px solid #1f2937; border-radius:12px; padding:20px; margin-bottom:24px; box-shadow:0 8px 20px rgba(0,0,0,.25); }
.form-grid { display:grid; grid-template-columns:1fr 1fr 1.3fr 2fr 110px 100px; gap:14px; align-items:end; }
label { display:block; font-size:12px; color:#9ca3af; margin-bottom:6px; text-transform:uppercase; letter-spacing:.04em; }
input[type=text] { width:100%; box-sizing:border-box; background:#020617; color:#e5e7eb; border:1px solid #374151; border-radius:8px; padding:10px 12px; font-size:14px; }
input[type=text]:focus { outline:none; border-color:#3b82f6; box-shadow:0 0 0 2px rgba(59,130,246,.25); }
.checkbox-wrap { display:flex; align-items:center; gap:8px; height:40px; }
button, .btn { border:none; border-radius:8px; padding:10px 14px; cursor:pointer; font-weight:600; text-decoration:none; display:inline-block; }
.btn-add { background:#2563eb; color:white; }
.btn-save { background:#16a34a; color:white; }
.btn-delete { background:#dc2626; color:white; }
.btn-add:hover { background:#1d4ed8; }
.btn-save:hover { background:#15803d; }
.btn-delete:hover { background:#b91c1c; }
table { width:100%; border-collapse:collapse; overflow:hidden; border-radius:12px; }
th { text-align:left; background:#1f2937; color:#d1d5db; font-size:12px; text-transform:uppercase; letter-spacing:.04em; padding:12px; }
td { padding:10px 12px; border-bottom:1px solid #1f2937; vertical-align:middle; }
tr:hover { background:#111f35; }
td input[type=text] { padding:8px 10px; }
.badge { padding:5px 9px; border-radius:999px; font-size:12px; font-weight:700; }
.badge-on { background:rgba(34,197,94,.15); color:#22c55e; }
.badge-off { background:rgba(239,68,68,.15); color:#ef4444; }
.actions { display:flex; gap:8px; }
.small { color:#9ca3af; font-size:12px; margin-top:6px; }
@media (max-width:1100px) { .form-grid { grid-template-columns:1fr 1fr; } }
</style>
</head>
<body>
<div class="container">
<h1>NISQA Dialer Targets</h1>
<div class="subtitle">Add, edit, enable, disable, or remove dialer targets.</div>
"""

PAGE_FOOT = """
</div>
</body>
</html>
"""


@app.route("/")
def index():
    conn = db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM nisqa_dialer_targets ORDER BY id DESC")
        rows = cur.fetchall()
    conn.close()

    html_out = PAGE_HEAD

    html_out += f"""
    <div class="card">
        <form method="post" action="{BASE_URL}/add">
            <div class="form-grid">
                <div>
                    <label>Caller ID</label>
                    <input type="text" name="caller_id" value="+16465686440">
                </div>
                <div>
                    <label>Destination</label>
                    <input type="text" name="dst_number" value="+14694217792">
                </div>
                <div>
                    <label>Trunk</label>
                    <input type="text" name="trunk_name" value="outbound.vitelity.net">
                </div>
                <div>
                    <label>Audio File</label>
                    <input type="text" name="audio_file" value="/var/spool/asterisk/monitor/alex-test.wav">
                </div>
                <div>
                    <label>Enabled</label>
                    <div class="checkbox-wrap">
                        <input type="checkbox" name="enabled" checked>
                        <span>Active</span>
                    </div>
                </div>
                <div>
                    <label>&nbsp;</label>
                    <button class="btn-add" type="submit">Add</button>
                </div>
            </div>
        </form>
    </div>
    """

    html_out += """
    <div class="card">
    <table>
        <tr>
            <th>ID</th>
            <th>Caller ID</th>
            <th>Destination</th>
            <th>Trunk</th>
            <th>Audio File</th>
            <th>Status</th>
            <th>Last Called</th>
            <th>Created</th>
            <th>Action</th>
        </tr>
    """

    for r in rows:
        checked = "checked" if r["enabled"] else ""
        badge = '<span class="badge badge-on">Enabled</span>' if r["enabled"] else '<span class="badge badge-off">Disabled</span>'

        html_out += f"""
        <tr>
        <form method="post" action="{BASE_URL}/update/{r['id']}">
            <td>{esc(r['id'])}</td>
            <td><input type="text" name="caller_id" value="{esc(r['caller_id'])}"></td>
            <td><input type="text" name="dst_number" value="{esc(r['dst_number'])}"></td>
            <td><input type="text" name="trunk_name" value="{esc(r['trunk_name'])}"></td>
            <td><input type="text" name="audio_file" value="{esc(r['audio_file'])}"></td>
            <td>
                {badge}
                <div class="small">
                    <input type="checkbox" name="enabled" {checked}> active
                </div>
            </td>
            <td>{esc(r['last_called_at'])}</td>
            <td>{esc(r['created_at'])}</td>
            <td>
                <div class="actions">
                    <button class="btn-save" type="submit">Save</button>
                    <a class="btn btn-delete" href="{BASE_URL}/delete/{r['id']}" onclick="return confirm('Delete target ID {r['id']}?')">Delete</a>
                </div>
            </td>
        </form>
        </tr>
        """

    html_out += """
    </table>
    </div>
    """

    html_out += PAGE_FOOT
    return html_out


@app.route("/add", methods=["POST"])
def add():
    enabled = 1 if request.form.get("enabled") else 0
    conn = db()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO nisqa_dialer_targets
            (caller_id, dst_number, trunk_name, audio_file, enabled)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            request.form.get("caller_id", "").strip(),
            request.form.get("dst_number", "").strip(),
            request.form.get("trunk_name", "").strip(),
            request.form.get("audio_file", "").strip(),
            enabled
        ))
    conn.commit()
    conn.close()
    return redirect(f"{BASE_URL}/")


@app.route("/update/<int:target_id>", methods=["POST"])
def update(target_id):
    enabled = 1 if request.form.get("enabled") else 0
    conn = db()
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE nisqa_dialer_targets
            SET caller_id=%s,
                dst_number=%s,
                trunk_name=%s,
                audio_file=%s,
                enabled=%s
            WHERE id=%s
        """, (
            request.form.get("caller_id", "").strip(),
            request.form.get("dst_number", "").strip(),
            request.form.get("trunk_name", "").strip(),
            request.form.get("audio_file", "").strip(),
            enabled,
            target_id
        ))
    conn.commit()
    conn.close()
    return redirect(f"{BASE_URL}/")


@app.route("/delete/<int:target_id>")
def delete(target_id):
    conn = db()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM nisqa_dialer_targets WHERE id=%s", (target_id,))
    conn.commit()
    conn.close()
    return redirect(f"{BASE_URL}/")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8088)
