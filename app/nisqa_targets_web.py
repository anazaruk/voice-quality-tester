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
.admin-grid { display:grid; grid-template-columns:1fr 2fr 2fr 120px 110px; gap:14px; align-items:end; }
.detail-grid {
    display:grid;
    grid-template-columns:1.4fr 1.4fr 120px 110px 110px 1.5fr 90px 90px;
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
            FROM nisqa_carrier_routes
            ORDER BY carrier_id, id
        """)
        routes = cur.fetchall()

        cur.execute("""
            SELECT *
            FROM nisqa_carrier_ips
            ORDER BY carrier_id, id
        """)
        ips = cur.fetchall()

    conn.close()

    routes_by_carrier = {}
    for r in routes:
        routes_by_carrier.setdefault(r["carrier_id"], []).append(r)

    ips_by_carrier = {}
    for i in ips:
        ips_by_carrier.setdefault(i["carrier_id"], []).append(i)

    html_out = carrier_admin_head()

    # --------------------------------------------------------
    # Add Carrier
    # --------------------------------------------------------

    html_out += f"""
    <div class="card">
        <h2>Add Carrier</h2>

        <form method="post"
              action="{BASE_URL}/admin/carriers/add">

            <div class="admin-grid">

                <div>
                    <label>Carrier Key</label>
                    <input type="text"
                           name="carrier_key"
                           placeholder="vitelity"
                           required>
                </div>

                <div>
                    <label>Carrier Name</label>
                    <input type="text"
                           name="carrier_name"
                           placeholder="Vitelity"
                           required>
                </div>

                <div>
                    <label>Notes</label>
                    <input type="text"
                           name="notes"
                           placeholder="Optional notes">
                </div>

                <div>
                    <label>Enabled</label>
                    <div class="checkbox-wrap">
                        <input type="checkbox"
                               name="enabled"
                               checked>
                        <span>Active</span>
                    </div>
                </div>

                <div>
                    <label>&nbsp;</label>
                    <button class="btn-add"
                            type="submit">
                        Add
                    </button>
                </div>

            </div>
        </form>
    </div>
    """

    if not carriers:
        html_out += """
        <div class="card">
            No carriers configured.
        </div>
        """

    # --------------------------------------------------------
    # Carrier cards
    # --------------------------------------------------------

    for c in carriers:

        cid = c["id"]
        checked = "checked" if c["enabled"] else ""

        html_out += f"""
        <div class="card">

            <h2>{esc(c["carrier_name"])}</h2>

            <form method="post"
                  action="{BASE_URL}/admin/carriers/update/{cid}">

                <div class="admin-grid">

                    <div>
                        <label>Carrier Key</label>
                        <input type="text"
                               name="carrier_key"
                               value="{esc(c["carrier_key"])}"
                               required>
                    </div>

                    <div>
                        <label>Carrier Name</label>
                        <input type="text"
                               name="carrier_name"
                               value="{esc(c["carrier_name"])}"
                               required>
                    </div>

                    <div>
                        <label>Notes</label>
                        <input type="text"
                               name="notes"
                               value="{esc(c["notes"])}">
                    </div>

                    <div>
                        <label>Enabled</label>
                        <div class="checkbox-wrap">
                            <input type="checkbox"
                                   name="enabled"
                                   {checked}>
                            <span>Active</span>
                        </div>
                    </div>

                    <div>
                        <label>&nbsp;</label>

                        <div class="actions">

                            <button class="btn-save"
                                    type="submit">
                                Save
                            </button>

                            <button class="btn-delete"
                                    type="submit"
                                    formaction="{BASE_URL}/admin/carriers/delete/{cid}"
                                    formmethod="post"
                                    onclick="return confirm('Delete carrier ID {cid} and all routes/IPs?')">
                                Delete
                            </button>

                        </div>
                    </div>

                </div>

            </form>
        """

        # ----------------------------------------------------
        # Routes
        # ----------------------------------------------------

        html_out += f"""
        <div class="section-title">SIP Routes / Trunks</div>

        <form method="post"
              action="{BASE_URL}/admin/carriers/{cid}/routes/add">

            <div class="detail-grid">

                <div>
                    <label>Trunk Name</label>
                    <input type="text"
                           name="trunk_name"
                           placeholder="outbound.vitelity.net">
                </div>

                <div>
                    <label>SIP Domain</label>
                    <input type="text"
                           name="sip_domain"
                           placeholder="sip.example.net">
                </div>

                <div>
                    <label>Direction</label>
                    <select name="direction">
                        <option value="outbound" selected>Outbound</option>
                        <option value="inbound">Inbound</option>
                        <option value="both">Both</option>
                    </select>
                </div>

                <div>
                    <label>Environment</label>
                    <input type="text"
                           name="environment"
                           placeholder="prod">
                </div>

                <div>
                    <label>Region</label>
                    <input type="text"
                           name="region"
                           placeholder="us-east">
                </div>

                <div>
                    <label>Notes</label>
                    <input type="text"
                           name="notes">
                </div>

                <div>
                    <label>Enabled</label>
                    <div class="checkbox-wrap">
                        <input type="checkbox"
                               name="enabled"
                               checked>
                    </div>
                </div>

                <div>
                    <label>&nbsp;</label>
                    <button class="btn-add"
                            type="submit">
                        Add
                    </button>
                </div>

            </div>

        </form>
        """

        carrier_routes = routes_by_carrier.get(cid, [])

        if carrier_routes:

            html_out += """
            <div class="table-wrap">
            <table>
                <tr>
                    <th>ID</th>
                    <th>Trunk</th>
                    <th>SIP Domain</th>
                    <th>Direction</th>
                    <th>Environment</th>
                    <th>Region</th>
                    <th>Notes</th>
                    <th>Enabled</th>
                    <th>Action</th>
                </tr>
            """

            for r in carrier_routes:

                rid = r["id"]
                form_id = f"route-{rid}"
                rchecked = "checked" if r["enabled"] else ""

                html_out += f"""
                <tr>

                    <td>{rid}</td>

                    <td>
                        <input form="{form_id}"
                               type="text"
                               name="trunk_name"
                               value="{esc(r["trunk_name"])}">
                    </td>

                    <td>
                        <input form="{form_id}"
                               type="text"
                               name="sip_domain"
                               value="{esc(r["sip_domain"])}">
                    </td>

                    <td>
                        <select form="{form_id}"
                                name="direction">

                            <option value="outbound"
                                {"selected" if r["direction"] == "outbound" else ""}>
                                Outbound
                            </option>

                            <option value="inbound"
                                {"selected" if r["direction"] == "inbound" else ""}>
                                Inbound
                            </option>

                            <option value="both"
                                {"selected" if r["direction"] == "both" else ""}>
                                Both
                            </option>

                        </select>
                    </td>

                    <td>
                        <input form="{form_id}"
                               type="text"
                               name="environment"
                               value="{esc(r["environment"])}">
                    </td>

                    <td>
                        <input form="{form_id}"
                               type="text"
                               name="region"
                               value="{esc(r["region"])}">
                    </td>

                    <td>
                        <input form="{form_id}"
                               type="text"
                               name="notes"
                               value="{esc(r["notes"])}">
                    </td>

                    <td>
                        <input form="{form_id}"
                               type="checkbox"
                               name="enabled"
                               {rchecked}>
                    </td>

                    <td>

                        <form id="{form_id}"
                              method="post"
                              action="{BASE_URL}/admin/carriers/{cid}/routes/update/{rid}">

                            <div class="actions">

                                <button class="btn-save"
                                        type="submit">
                                    Save
                                </button>

                                <button class="btn-delete"
                                        type="submit"
                                        formaction="{BASE_URL}/admin/carriers/{cid}/routes/delete/{rid}"
                                        formmethod="post"
                                        onclick="return confirm('Delete route ID {rid}?')">
                                    Delete
                                </button>

                            </div>

                        </form>

                    </td>

                </tr>
                """

            html_out += """
            </table>
            </div>
            """

        # ----------------------------------------------------
        # Carrier IPs
        # ----------------------------------------------------

        html_out += f"""
        <div class="section-title">SIP / Media IPs</div>

        <form method="post"
              action="{BASE_URL}/admin/carriers/{cid}/ips/add">

            <div class="detail-grid">

                <div>
                    <label>IP Address</label>
                    <input type="text"
                           name="ip_address"
                           placeholder="203.0.113.10"
                           required>
                </div>

                <div>
                    <label>Type</label>
                    <select name="ip_type">
                        <option value="sip" selected>SIP</option>
                        <option value="media">Media</option>
                        <option value="both">Both</option>
                    </select>
                </div>

                <div>
                    <label>Direction</label>
                    <select name="direction">
                        <option value="both" selected>Both</option>
                        <option value="inbound">Inbound</option>
                        <option value="outbound">Outbound</option>
                    </select>
                </div>

                <div>
                    <label>Environment</label>
                    <input type="text"
                           name="environment"
                           placeholder="prod">
                </div>

                <div>
                    <label>Region</label>
                    <input type="text"
                           name="region"
                           placeholder="us-east">
                </div>

                <div>
                    <label>Notes</label>
                    <input type="text"
                           name="notes">
                </div>

                <div>
                    <label>Enabled</label>
                    <div class="checkbox-wrap">
                        <input type="checkbox"
                               name="enabled"
                               checked>
                    </div>
                </div>

                <div>
                    <label>&nbsp;</label>
                    <button class="btn-add"
                            type="submit">
                        Add
                    </button>
                </div>

            </div>

        </form>
        """

        carrier_ips = ips_by_carrier.get(cid, [])

        if carrier_ips:

            html_out += """
            <div class="table-wrap">
            <table>
                <tr>
                    <th>ID</th>
                    <th>IP Address</th>
                    <th>Type</th>
                    <th>Direction</th>
                    <th>Environment</th>
                    <th>Region</th>
                    <th>Notes</th>
                    <th>Enabled</th>
                    <th>Action</th>
                </tr>
            """

            for i in carrier_ips:

                iid = i["id"]
                form_id = f"ip-{iid}"
                ichecked = "checked" if i["enabled"] else ""

                html_out += f"""
                <tr>

                    <td>{iid}</td>

                    <td>
                        <input form="{form_id}"
                               type="text"
                               name="ip_address"
                               value="{esc(i["ip_address"])}"
                               required>
                    </td>

                    <td>
                        <select form="{form_id}"
                                name="ip_type">

                            <option value="sip"
                                {"selected" if i["ip_type"] == "sip" else ""}>
                                SIP
                            </option>

                            <option value="media"
                                {"selected" if i["ip_type"] == "media" else ""}>
                                Media
                            </option>

                            <option value="both"
                                {"selected" if i["ip_type"] == "both" else ""}>
                                Both
                            </option>

                        </select>
                    </td>

                    <td>
                        <select form="{form_id}"
                                name="direction">

                            <option value="inbound"
                                {"selected" if i["direction"] == "inbound" else ""}>
                                Inbound
                            </option>

                            <option value="outbound"
                                {"selected" if i["direction"] == "outbound" else ""}>
                                Outbound
                            </option>

                            <option value="both"
                                {"selected" if i["direction"] == "both" else ""}>
                                Both
                            </option>

                        </select>
                    </td>

                    <td>
                        <input form="{form_id}"
                               type="text"
                               name="environment"
                               value="{esc(i["environment"])}">
                    </td>

                    <td>
                        <input form="{form_id}"
                               type="text"
                               name="region"
                               value="{esc(i["region"])}">
                    </td>

                    <td>
                        <input form="{form_id}"
                               type="text"
                               name="notes"
                               value="{esc(i["notes"])}">
                    </td>

                    <td>
                        <input form="{form_id}"
                               type="checkbox"
                               name="enabled"
                               {ichecked}>
                    </td>

                    <td>

                        <form id="{form_id}"
                              method="post"
                              action="{BASE_URL}/admin/carriers/{cid}/ips/update/{iid}">

                            <div class="actions">

                                <button class="btn-save"
                                        type="submit">
                                    Save
                                </button>

                                <button class="btn-delete"
                                        type="submit"
                                        formaction="{BASE_URL}/admin/carriers/{cid}/ips/delete/{iid}"
                                        formmethod="post"
                                        onclick="return confirm('Delete IP ID {iid}?')">
                                    Delete
                                </button>

                            </div>

                        </form>

                    </td>

                </tr>
                """

            html_out += """
            </table>
            </div>
            """

        html_out += """
        </div>
        """

    html_out += PAGE_FOOT
    return html_out


@app.route("/admin/carriers/add", methods=["POST"])
def carrier_add():

    carrier_key = request.form.get("carrier_key", "").strip()
    carrier_name = request.form.get("carrier_name", "").strip()
    notes = request.form.get("notes", "").strip()
    enabled = 1 if request.form.get("enabled") else 0

    if not carrier_key or not carrier_name:
        return redirect(f"{BASE_URL}/admin/carriers")

    conn = db()

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO nisqa_carriers
                (carrier_key, carrier_name, enabled, notes)
            VALUES (%s,%s,%s,%s)
        """, (
            carrier_key,
            carrier_name,
            enabled,
            notes or None
        ))

    conn.commit()
    conn.close()

    return redirect(f"{BASE_URL}/admin/carriers")


@app.route("/admin/carriers/update/<int:carrier_id>",
           methods=["POST"])
def carrier_update(carrier_id):

    carrier_key = request.form.get("carrier_key", "").strip()
    carrier_name = request.form.get("carrier_name", "").strip()
    notes = request.form.get("notes", "").strip()
    enabled = 1 if request.form.get("enabled") else 0

    conn = db()

    with conn.cursor() as cur:
        cur.execute("""
            UPDATE nisqa_carriers
               SET carrier_key=%s,
                   carrier_name=%s,
                   enabled=%s,
                   notes=%s
             WHERE id=%s
        """, (
            carrier_key,
            carrier_name,
            enabled,
            notes or None,
            carrier_id
        ))

    conn.commit()
    conn.close()

    return redirect(f"{BASE_URL}/admin/carriers")


@app.route("/admin/carriers/delete/<int:carrier_id>",
           methods=["POST"])
def carrier_delete(carrier_id):

    conn = db()

    with conn.cursor() as cur:
        cur.execute("""
            DELETE FROM nisqa_carriers
             WHERE id=%s
        """, (carrier_id,))

    conn.commit()
    conn.close()

    return redirect(f"{BASE_URL}/admin/carriers")


@app.route("/admin/carriers/<int:carrier_id>/routes/add",
           methods=["POST"])
def carrier_route_add(carrier_id):

    trunk_name = request.form.get("trunk_name", "").strip()
    sip_domain = request.form.get("sip_domain", "").strip()

    if not trunk_name and not sip_domain:
        return redirect(f"{BASE_URL}/admin/carriers")

    direction = request.form.get("direction", "outbound")

    if direction not in ("inbound", "outbound", "both"):
        direction = "outbound"

    environment = request.form.get("environment", "").strip()
    region = request.form.get("region", "").strip()
    notes = request.form.get("notes", "").strip()
    enabled = 1 if request.form.get("enabled") else 0

    conn = db()

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO nisqa_carrier_routes
            (
                carrier_id,
                trunk_name,
                sip_domain,
                direction,
                environment,
                region,
                enabled,
                notes
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            carrier_id,
            trunk_name or None,
            sip_domain or None,
            direction,
            environment or None,
            region or None,
            enabled,
            notes or None
        ))

    conn.commit()
    conn.close()

    return redirect(f"{BASE_URL}/admin/carriers")


@app.route("/admin/carriers/<int:carrier_id>/routes/update/<int:route_id>",
           methods=["POST"])
def carrier_route_update(carrier_id, route_id):

    direction = request.form.get("direction", "outbound")

    if direction not in ("inbound", "outbound", "both"):
        direction = "outbound"

    enabled = 1 if request.form.get("enabled") else 0

    conn = db()

    with conn.cursor() as cur:
        cur.execute("""
            UPDATE nisqa_carrier_routes
               SET trunk_name=%s,
                   sip_domain=%s,
                   direction=%s,
                   environment=%s,
                   region=%s,
                   enabled=%s,
                   notes=%s
             WHERE id=%s
               AND carrier_id=%s
        """, (
            request.form.get("trunk_name", "").strip() or None,
            request.form.get("sip_domain", "").strip() or None,
            direction,
            request.form.get("environment", "").strip() or None,
            request.form.get("region", "").strip() or None,
            enabled,
            request.form.get("notes", "").strip() or None,
            route_id,
            carrier_id
        ))

    conn.commit()
    conn.close()

    return redirect(f"{BASE_URL}/admin/carriers")


@app.route("/admin/carriers/<int:carrier_id>/routes/delete/<int:route_id>",
           methods=["POST"])
def carrier_route_delete(carrier_id, route_id):

    conn = db()

    with conn.cursor() as cur:
        cur.execute("""
            DELETE FROM nisqa_carrier_routes
             WHERE id=%s
               AND carrier_id=%s
        """, (
            route_id,
            carrier_id
        ))

    conn.commit()
    conn.close()

    return redirect(f"{BASE_URL}/admin/carriers")


@app.route("/admin/carriers/<int:carrier_id>/ips/add",
           methods=["POST"])
def carrier_ip_add(carrier_id):

    ip_address = request.form.get("ip_address", "").strip()

    if not ip_address:
        return redirect(f"{BASE_URL}/admin/carriers")

    ip_type = request.form.get("ip_type", "sip")

    if ip_type not in ("sip", "media", "both"):
        ip_type = "sip"

    direction = request.form.get("direction", "both")

    if direction not in ("inbound", "outbound", "both"):
        direction = "both"

    enabled = 1 if request.form.get("enabled") else 0

    conn = db()

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO nisqa_carrier_ips
            (
                carrier_id,
                ip_address,
                ip_type,
                direction,
                environment,
                region,
                enabled,
                notes
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            carrier_id,
            ip_address,
            ip_type,
            direction,
            request.form.get("environment", "").strip() or None,
            request.form.get("region", "").strip() or None,
            enabled,
            request.form.get("notes", "").strip() or None
        ))

    conn.commit()
    conn.close()

    return redirect(f"{BASE_URL}/admin/carriers")


@app.route("/admin/carriers/<int:carrier_id>/ips/update/<int:ip_id>",
           methods=["POST"])
def carrier_ip_update(carrier_id, ip_id):

    ip_type = request.form.get("ip_type", "sip")

    if ip_type not in ("sip", "media", "both"):
        ip_type = "sip"

    direction = request.form.get("direction", "both")

    if direction not in ("inbound", "outbound", "both"):
        direction = "both"

    enabled = 1 if request.form.get("enabled") else 0

    conn = db()

    with conn.cursor() as cur:
        cur.execute("""
            UPDATE nisqa_carrier_ips
               SET ip_address=%s,
                   ip_type=%s,
                   direction=%s,
                   environment=%s,
                   region=%s,
                   enabled=%s,
                   notes=%s
             WHERE id=%s
               AND carrier_id=%s
        """, (
            request.form.get("ip_address", "").strip(),
            ip_type,
            direction,
            request.form.get("environment", "").strip() or None,
            request.form.get("region", "").strip() or None,
            enabled,
            request.form.get("notes", "").strip() or None,
            ip_id,
            carrier_id
        ))

    conn.commit()
    conn.close()

    return redirect(f"{BASE_URL}/admin/carriers")


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

    return redirect(f"{BASE_URL}/admin/carriers")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8088)
