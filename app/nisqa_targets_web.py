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
input[type=text], select { width:100%; box-sizing:border-box; background:#020617; color:#e5e7eb; border:1px solid #374151; border-radius:8px; padding:10px 12px; font-size:14px; }
input[type=text]:focus, select:focus { outline:none; border-color:#3b82f6; box-shadow:0 0 0 2px rgba(59,130,246,.25); }
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
td input[type=text], select { padding:8px 10px; }
.badge { padding:5px 9px; border-radius:999px; font-size:12px; font-weight:700; }
.badge-on { background:rgba(34,197,94,.15); color:#22c55e; }
.badge-off { background:rgba(239,68,68,.15); color:#ef4444; }
.actions { display:flex; gap:8px; }
.small { color:#9ca3af; font-size:12px; margin-top:6px; }
.nav { display:flex; gap:10px; margin:0 0 24px 0; }
.nav a { color:#93c5fd; text-decoration:none; padding:8px 12px; border:1px solid #374151; border-radius:8px; }
.nav a:hover { background:#1f2937; }
.admin-grid { display:grid; grid-template-columns:1fr 2fr 140px 180px; gap:14px; align-items:end; }
.detail-grid {
    display:grid;
    grid-template-columns:2fr 2fr 150px 100px 90px;
    gap:10px;
    align-items:end;
}
.section-title {
    margin-top:26px;
    margin-bottom:12px;
    font-size:18px;
}
.table-wrap {
    overflow-x:auto;
}

@media (max-width:1100px) {
    .form-grid { grid-template-columns:1fr 1fr; }
    .admin-grid { grid-template-columns:1fr 1fr; }
}
</style>
</head>
<body>
<div class="container">
<h1>NISQA Dialer Targets</h1>
<div class="subtitle">Add, edit, enable, disable, or remove dialer targets.</div>
<div class="nav">
    <a href="/dialer/">Dialer Targets</a>
    <a href="/dialer/admin/carriers">Carrier Admin</a>
</div>
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
                    <button class="btn-delete"
                            type="submit"
                            formaction="{BASE_URL}/delete/{r['id']}"
                            formmethod="post"
                            onclick="return confirm('Delete target ID {r['id']}?')">Delete</button>
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


@app.route("/delete/<int:target_id>", methods=["POST"])
def delete(target_id):
    conn = db()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM nisqa_dialer_targets WHERE id=%s", (target_id,))
    conn.commit()
    conn.close()
    return redirect(f"{BASE_URL}/")


def carrier_admin_head():
    return PAGE_HEAD.replace(
        "<title>NISQA Dialer Targets</title>",
        "<title>NISQA Carrier Admin</title>"
    ).replace(
        '<h1>NISQA Dialer Targets</h1>\n'
        '<div class="subtitle">Add, edit, enable, disable, or remove dialer targets.</div>',
        '<h1>Carrier Admin</h1>\n'
        '<div class="subtitle">Manage carriers used by the dialer and reporting.</div>'
    )


@app.route("/admin/carriers")
def carrier_admin():
    conn = db()

    with conn.cursor() as cur:
        cur.execute("""
            SELECT *
            FROM nisqa_carriers
            ORDER BY carrier_name
        """)
        carriers = cur.fetchall()

        cur.execute("""
            SELECT *
            FROM nisqa_carrier_ips
            ORDER BY carrier_id, ip_address
        """)
        ips = cur.fetchall()

    conn.close()

    ips_by_carrier = {}

    for row in ips:
        ips_by_carrier.setdefault(
            row["carrier_id"], []
        ).append(row)

    html_out = carrier_admin_head()

    # --------------------------------------------------------
    # Add Carrier
    # --------------------------------------------------------

    html_out += f"""
    <div class="card">

        <h2>Add Carrier</h2>

        <form method="post"
              action="{BASE_URL}/admin/carriers/add">

            <div style="
                display:grid;
                grid-template-columns:1fr 110px;
                gap:14px;
                align-items:end;
            ">

                <div>
                    <label>Carrier Name</label>

                    <input type="text"
                           name="carrier_name"
                           placeholder="Vitelity"
                           required>
                </div>

                <div>
                    <button class="btn-add"
                            type="submit">
                        Add
                    </button>
                </div>

            </div>

        </form>

    </div>
    """

    # --------------------------------------------------------
    # Existing carriers
    # --------------------------------------------------------

    for carrier in carriers:

        cid = carrier["id"]
        carrier_name = esc(carrier["carrier_name"])

        html_out += f"""
        <div class="card">

            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                margin-bottom:22px;
            ">

                <h2 style="margin:0;">
                    {carrier_name}
                </h2>

                <form method="post"
                      action="{BASE_URL}/admin/carriers/delete/{cid}"
                      style="margin:0;">

                    <button class="btn-delete"
                            type="submit"
                            onclick="return confirm('Delete carrier {carrier_name} and all associated IPs?')">
                        Delete Carrier
                    </button>

                </form>

            </div>

            <div class="section-title"
                 style="margin-top:0;">
                Inbound SIP IPs
            </div>
        """

        carrier_ips = ips_by_carrier.get(cid, [])

        if carrier_ips:

            html_out += """
            <div style="
                border:1px solid #1f2937;
                border-radius:10px;
                overflow:hidden;
                margin-bottom:18px;
            ">
            """

            for ip in carrier_ips:

                iid = ip["id"]
                ip_address = esc(ip["ip_address"])

                html_out += f"""
                <div style="
                    display:grid;
                    grid-template-columns:1fr 100px;
                    gap:16px;
                    align-items:center;
                    padding:11px 14px;
                    border-bottom:1px solid #1f2937;
                ">

                    <div style="
                        font-family:monospace;
                        font-size:15px;
                    ">
                        {ip_address}
                    </div>

                    <form method="post"
                          action="{BASE_URL}/admin/carriers/{cid}/ips/delete/{iid}"
                          style="margin:0;">

                        <button class="btn-delete"
                                type="submit"
                                onclick="return confirm('Delete IP {ip_address}?')">
                            Delete
                        </button>

                    </form>

                </div>
                """

            html_out += """
            </div>
            """

        else:

            html_out += """
            <div class="small"
                 style="margin-bottom:18px;">
                No inbound SIP IPs configured.
            </div>
            """

        # ----------------------------------------------------
        # Add IP
        # ----------------------------------------------------

        html_out += f"""
            <form method="post"
                  action="{BASE_URL}/admin/carriers/{cid}/ips/add">

                <div style="
                    display:grid;
                    grid-template-columns:1fr 110px;
                    gap:14px;
                    align-items:end;
                ">

                    <div>
                        <label>Add Incoming SIP Source IP</label>

                        <input type="text"
                               name="ip_address"
                               placeholder="206.146.130.2"
                               required>
                    </div>

                    <div>
                        <button class="btn-add"
                                type="submit">
                            Add IP
                        </button>
                    </div>

                </div>

            </form>

        </div>
        """

    html_out += PAGE_FOOT
    return html_out


@app.route("/admin/carriers/add", methods=["POST"])
def carrier_add():

    carrier_name = request.form.get(
        "carrier_name", ""
    ).strip()

    if not carrier_name:
        return redirect(
            f"{BASE_URL}/admin/carriers"
        )

    conn = db()

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO nisqa_carriers
            (
                carrier_name,
                enabled
            )
            VALUES (%s,1)
        """, (
            carrier_name,
        ))

    conn.commit()
    conn.close()

    return redirect(
        f"{BASE_URL}/admin/carriers"
    )


@app.route("/admin/carriers/delete/<int:carrier_id>",
           methods=["POST"])
def carrier_delete(carrier_id):

    conn = db()

    with conn.cursor() as cur:
        cur.execute("""
            DELETE FROM nisqa_carriers
             WHERE id=%s
        """, (
            carrier_id,
        ))

    conn.commit()
    conn.close()

    return redirect(
        f"{BASE_URL}/admin/carriers"
    )


@app.route("/admin/carriers/<int:carrier_id>/ips/add",
           methods=["POST"])
def carrier_ip_add(carrier_id):

    ip_address = request.form.get(
        "ip_address", ""
    ).strip()

    if not ip_address:
        return redirect(
            f"{BASE_URL}/admin/carriers"
        )

    conn = db()

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO nisqa_carrier_ips
            (
                carrier_id,
                ip_address,
                enabled
            )
            VALUES (%s,%s,1)
        """, (
            carrier_id,
            ip_address
        ))

    conn.commit()
    conn.close()

    return redirect(
        f"{BASE_URL}/admin/carriers"
    )


@app.route("/admin/carriers/<int:carrier_id>/ips/delete/<int:ip_id>",
           methods=["POST"])
def carrier_ip_delete(carrier_id, ip_id):

    conn = db()

    with conn.cursor() as cur:
        cur.execute("""
            DELETE FROM nisqa_carrier_ips
             WHERE id=%s
               AND carrier_id=%s
        """, (
            ip_id,
            carrier_id
        ))

    conn.commit()
    conn.close()

    return redirect(
        f"{BASE_URL}/admin/carriers"
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8088)
