#!/usr/bin/env bash
set -euo pipefail

FORCE=0
[[ "${1:-}" == "--force" ]] && FORCE=1

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: run as root."
  exit 1
fi

BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "$BASE/config/defaults.env" ]]; then
  echo "ERROR: missing $BASE/config/defaults.env"
  exit 1
fi

# shellcheck disable=SC1091
source "$BASE/config/defaults.env"

# Safety guard: this installer is intended for a NEW VM.
EXISTING=0
[[ -d /usr/src/NISQA/venv ]] && EXISTING=1
[[ -f /etc/systemd/system/nisqa-web.service ]] && EXISTING=1
if command -v mysql >/dev/null 2>&1; then
  mysql -N -B -e "SHOW DATABASES LIKE 'voice_quality'" 2>/dev/null | grep -q voice_quality && EXISTING=1 || true
fi

if [[ "$EXISTING" -eq 1 && "$FORCE" -ne 1 ]]; then
  echo
  echo "REFUSING TO INSTALL:"
  echo "An existing NISQA/voice_quality deployment appears to be present."
  echo
  echo "Use this installer on a fresh Ubuntu VM."
  echo "If you intentionally want to overwrite an existing host, rerun:"
  echo "  sudo ./install.sh --force"
  echo
  exit 2
fi

if [[ -r /etc/os-release ]]; then
  . /etc/os-release
  if [[ "${ID:-}" != "ubuntu" ]]; then
    echo "ERROR: this installer currently targets Ubuntu 24.04."
    exit 3
  fi
fi

export DEBIAN_FRONTEND=noninteractive

echo "== Installing OS packages =="
apt-get update
apt-get install -y \
  asterisk \
  mysql-server \
  nginx \
  python3 \
  python3-venv \
  python3-pip \
  python3-dev \
  build-essential \
  git \
  curl \
  wget \
  rsync \
  ffmpeg \
  sox \
  libsndfile1 \
  libsndfile1-dev \
  libssl-dev \
  libffi-dev \
  pkg-config \
  ca-certificates \
  gnupg \
  sqlite3 \
  tcpdump

echo "== Installing Grafana =="
if ! command -v grafana-server >/dev/null 2>&1; then
  mkdir -p /etc/apt/keyrings
  rm -f /etc/apt/keyrings/grafana.gpg
  curl -fsSL https://apt.grafana.com/gpg.key \
    | gpg --dearmor -o /etc/apt/keyrings/grafana.gpg

  echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" \
    > /etc/apt/sources.list.d/grafana.list

  apt-get update
  apt-get install -y grafana
fi

echo "== Detecting target network addresses =="
if [[ -z "${PRIVATE_IP:-}" ]]; then
  PRIVATE_IP="$(hostname -I | awk '{print $1}')"
fi
if [[ -z "${PUBLIC_IP:-}" ]]; then
  PUBLIC_IP="$(curl -4 -fsS --max-time 5 https://api.ipify.org 2>/dev/null || true)"
fi
[[ -n "$PUBLIC_IP" ]] || PUBLIC_IP="$PRIVATE_IP"

echo "Private IP: $PRIVATE_IP"
echo "Public IP:  $PUBLIC_IP"

SOURCE_PRIVATE_IP=""
SOURCE_PUBLIC_IP=""
if [[ -f "$BASE/config/source-network.env" ]]; then
  # shellcheck disable=SC1091
  source "$BASE/config/source-network.env"
fi

echo "== Backing up existing target configuration =="
BACKUP="/root/nisqa-preinstall-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP"
[[ -d /etc/asterisk ]] && cp -a /etc/asterisk "$BACKUP/" || true
[[ -d /etc/nginx ]] && cp -a /etc/nginx "$BACKUP/" || true
[[ -d /etc/grafana ]] && cp -a /etc/grafana "$BACKUP/" || true

echo "== Installing NISQA source =="
rm -rf /usr/src/NISQA.new
mkdir -p /usr/src/NISQA.new
rsync -a "$BASE/nisqa/" /usr/src/NISQA.new/

if [[ -d /usr/src/NISQA && "$FORCE" -eq 1 ]]; then
  mv /usr/src/NISQA "/usr/src/NISQA.old.$(date +%s)"
fi
mv /usr/src/NISQA.new /usr/src/NISQA

python3 -m venv /usr/src/NISQA/venv
/usr/src/NISQA/venv/bin/pip install --upgrade pip setuptools wheel

if [[ -f "$BASE/nisqa/requirements-current.txt" ]]; then
  /usr/src/NISQA/venv/bin/pip install -r "$BASE/nisqa/requirements-current.txt"
elif [[ -f "$BASE/nisqa/requirements.txt" ]]; then
  /usr/src/NISQA/venv/bin/pip install -r "$BASE/nisqa/requirements.txt"
else
  echo "WARN: no requirements file found"
fi

echo "== Installing application scripts =="
install -m 0755 "$BASE/app/nisqa_dialer.py" /usr/local/bin/nisqa_dialer.py
[[ -f "$BASE/app/nisqa_dialer1.py" ]] && \
  install -m 0755 "$BASE/app/nisqa_dialer1.py" /usr/local/bin/nisqa_dialer1.py
install -m 0755 "$BASE/app/nisqa_targets_web.py" /usr/local/bin/nisqa_targets_web.py

install -d -o asterisk -g asterisk /var/lib/asterisk/agi-bin
install -m 0755 -o asterisk -g asterisk "$BASE/app/nisqa.py" \
  /var/lib/asterisk/agi-bin/nisqa.py

[[ -f "$BASE/scripts/archive_nisqa.sh" ]] && \
  install -m 0755 "$BASE/scripts/archive_nisqa.sh" /usr/local/bin/archive_nisqa.sh
[[ -f "$BASE/scripts/rotate_voip_pcaps.sh" ]] && \
  install -m 0755 "$BASE/scripts/rotate_voip_pcaps.sh" /usr/local/sbin/rotate_voip_pcaps.sh

echo "== Installing Asterisk configuration =="
if [[ -d "$BASE/asterisk/etc" ]]; then
  rsync -a "$BASE/asterisk/etc/" /etc/asterisk/
fi

# Replace source server addresses with the target cloud addresses where possible.
if [[ -n "${SOURCE_PUBLIC_IP:-}" && "$SOURCE_PUBLIC_IP" != "$PUBLIC_IP" ]]; then
  grep -RIl -- "$SOURCE_PUBLIC_IP" /etc/asterisk 2>/dev/null \
    | xargs -r sed -i "s/${SOURCE_PUBLIC_IP//./\\.}/${PUBLIC_IP}/g"
fi
if [[ -n "${SOURCE_PRIVATE_IP:-}" && "$SOURCE_PRIVATE_IP" != "$PRIVATE_IP" ]]; then
  grep -RIl -- "$SOURCE_PRIVATE_IP" /etc/asterisk 2>/dev/null \
    | xargs -r sed -i "s/${SOURCE_PRIVATE_IP//./\\.}/${PRIVATE_IP}/g"
fi

chown -R asterisk:asterisk /etc/asterisk

install -d -o asterisk -g asterisk /var/spool/asterisk/monitor

if [[ -d "$BASE/asterisk/sounds-custom/custom" ]]; then
  install -d -o asterisk -g asterisk /var/lib/asterisk/sounds/custom
  rsync -a "$BASE/asterisk/sounds-custom/custom/" /var/lib/asterisk/sounds/custom/
fi
if [[ -d "$BASE/asterisk/sounds-custom/en-custom" ]]; then
  install -d -o asterisk -g asterisk /var/lib/asterisk/sounds/en/custom
  rsync -a "$BASE/asterisk/sounds-custom/en-custom/" /var/lib/asterisk/sounds/en/custom/
fi

echo "== Configuring MySQL =="
systemctl enable --now mysql

mysql <<SQL
CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE}\`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'localhost'
  IDENTIFIED BY '';

ALTER USER '${MYSQL_USER}'@'localhost'
  IDENTIFIED BY '';

CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'127.0.0.1'
  IDENTIFIED BY '';

ALTER USER '${MYSQL_USER}'@'127.0.0.1'
  IDENTIFIED BY '';

GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}\`.* TO '${MYSQL_USER}'@'localhost';
GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}\`.* TO '${MYSQL_USER}'@'127.0.0.1';
FLUSH PRIVILEGES;
SQL

if [[ -s "$BASE/database/schema.sql" ]]; then
  mysql "$MYSQL_DATABASE" < "$BASE/database/schema.sql"
fi
if [[ -s "$BASE/database/config-data.sql" ]]; then
  mysql "$MYSQL_DATABASE" < "$BASE/database/config-data.sql"
fi

echo "== Installing nginx configuration =="
if [[ -d "$BASE/nginx/sites-available" ]]; then
  rsync -a "$BASE/nginx/sites-available/" /etc/nginx/sites-available/
fi

# Re-create source enabled-site symlinks by basename.
if [[ -d "$BASE/nginx/sites-enabled" ]]; then
  rm -f /etc/nginx/sites-enabled/*
  for item in "$BASE"/nginx/sites-enabled/*; do
    [[ -e "$item" || -L "$item" ]] || continue
    name="$(basename "$item")"
    if [[ -f "/etc/nginx/sites-available/$name" ]]; then
      ln -s "/etc/nginx/sites-available/$name" "/etc/nginx/sites-enabled/$name"
    elif [[ -f "$item" ]]; then
      cp "$item" "/etc/nginx/sites-enabled/$name"
    fi
  done
fi

nginx -t

echo "== Installing Grafana dashboards and datasource =="
install -d -o grafana -g grafana /var/lib/grafana/dashboards/nisqa
if compgen -G "$BASE/grafana/dashboards/*.json" >/dev/null; then
  cp "$BASE"/grafana/dashboards/*.json /var/lib/grafana/dashboards/nisqa/
fi
chown -R grafana:grafana /var/lib/grafana/dashboards

install -d /etc/grafana/provisioning/dashboards
install -d /etc/grafana/provisioning/datasources

cp "$BASE/grafana/provisioning/dashboards/nisqa.yaml" \
  /etc/grafana/provisioning/dashboards/nisqa.yaml

# Rebuild datasource file with actual install-time DB credentials.
python3 - "$BASE" "$MYSQL_USER" "$MYSQL_PASSWORD" "$MYSQL_DATABASE" <<'PY'
import json, os, sys
base, user, password, database = sys.argv[1:5]
meta = os.path.join(base, "grafana", "datasource-meta.json")
out = "/etc/grafana/provisioning/datasources/nisqa-mysql.yaml"

records=[]
try:
    with open(meta) as f:
        records=json.load(f)
except Exception:
    pass

ds=next((r for r in records if str(r.get("type","")).lower()=="mysql"), {})
name=ds.get("name") or "Voice Quality MySQL"
uid=ds.get("uid") or "voice-quality-mysql"

password_block = ""
if password:
    password_block = f"""    secureJsonData:
      password: {password}
"""

with open(out,"w") as f:
    f.write(f"""apiVersion: 1
datasources:
  - name: {name}
    uid: {uid}
    type: mysql
    access: proxy
    url: 127.0.0.1:3306
    user: {user}
{password_block}    jsonData:
      database: {database}
      maxOpenConns: 25
      maxIdleConns: 25
      connMaxLifetime: 14400
    isDefault: true
    editable: true
""")
PY

echo "== Setting Grafana default admin credentials =="
# Set defaults for first-start path.
if ! grep -q '^\[security\]' /etc/grafana/grafana.ini; then
  cat >> /etc/grafana/grafana.ini <<EOF

[security]
admin_user = ${GRAFANA_ADMIN_USER}
admin_password = ${GRAFANA_ADMIN_PASSWORD}
EOF
fi

systemctl enable grafana-server
systemctl restart grafana-server
sleep 3

# Also reset password on installations where Grafana initialized before config edit.
if command -v grafana >/dev/null 2>&1; then
  grafana cli admin reset-admin-password "$GRAFANA_ADMIN_PASSWORD" >/dev/null 2>&1 || true
elif command -v grafana-cli >/dev/null 2>&1; then
  grafana-cli admin reset-admin-password "$GRAFANA_ADMIN_PASSWORD" >/dev/null 2>&1 || true
fi

echo "== Installing systemd / cron =="
if [[ -f "$BASE/systemd/nisqa-web.service" ]]; then
  cp "$BASE/systemd/nisqa-web.service" /etc/systemd/system/nisqa-web.service
fi

cp "$BASE/cron/nisqa.cron" /etc/cron.d/nisqa
chmod 0644 /etc/cron.d/nisqa

cat > /etc/voice-quality.env <<EOF
MYSQL_DATABASE=${MYSQL_DATABASE}
MYSQL_USER=${MYSQL_USER}
MYSQL_PASSWORD=${MYSQL_PASSWORD}
GRAFANA_ADMIN_USER=${GRAFANA_ADMIN_USER}
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
PUBLIC_IP=${PUBLIC_IP}
PRIVATE_IP=${PRIVATE_IP}
ASTERISK_LOCALNET=${ASTERISK_LOCALNET}
EOF
chmod 0600 /etc/voice-quality.env

echo "== Starting services =="
systemctl daemon-reload
systemctl enable asterisk nginx
systemctl restart asterisk
systemctl restart nginx

if [[ -f /etc/systemd/system/nisqa-web.service ]]; then
  systemctl enable nisqa-web
  systemctl restart nisqa-web || {
    echo "WARN: nisqa-web did not start. Check:"
    echo "  systemctl status nisqa-web"
    echo "  journalctl -u nisqa-web -n 100"
  }
fi

echo "== Basic verification =="
echo
asterisk -V || true
systemctl --no-pager --full status asterisk | head -15 || true
systemctl --no-pager --full status mysql | head -15 || true
systemctl --no-pager --full status grafana-server | head -15 || true
systemctl --no-pager --full status nginx | head -15 || true
[[ -f /etc/systemd/system/nisqa-web.service ]] && \
  systemctl --no-pager --full status nisqa-web | head -15 || true

echo
echo "======================================================================"
echo " INSTALL COMPLETE"
echo "======================================================================"
echo
echo "Grafana:"
echo "  URL:      http://${PUBLIC_IP}:3000"
echo "  User:     ${GRAFANA_ADMIN_USER}"
echo "  Password: ${GRAFANA_ADMIN_PASSWORD}"
echo
echo "MySQL local application account:"
echo "  Database: ${MYSQL_DATABASE}"
echo "  User:     ${MYSQL_USER}"
echo "  Password: <none>"
echo
echo "SIP authentication:"
echo "  IP based; no SIP password is configured."
echo
echo "IMPORTANT:"
echo "  Allowlist this server's public IP with the SIP carrier before expecting PSTN tests to work."
echo
echo "Change all default passwords after validation."
echo "======================================================================"
