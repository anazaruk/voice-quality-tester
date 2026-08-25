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

: "${MYSQL_DATABASE:=voice_quality}"
: "${MYSQL_USER:=nisqa}"
: "${MYSQL_PASSWORD:=CHANGE_ME}"
: "${GRAFANA_ADMIN_USER:=admin}"
: "${GRAFANA_ADMIN_PASSWORD:=admin}"
: "${MAXMIND_ACCOUNT_ID:=}"
: "${MAXMIND_LICENSE_KEY:=}"
: "${PUBLIC_IP:=}"
: "${PRIVATE_IP:=}"
: "${ASTERISK_LOCALNET:=10.0.0.0/8}"

if [[ -z "$MYSQL_PASSWORD" ]]; then
  echo "ERROR: MYSQL_PASSWORD must not be empty."
  exit 1
fi

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
    echo "ERROR: this installer targets Ubuntu."
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
  jq \
  tcpdump \
  prometheus \
  prometheus-node-exporter \
  geoipupdate

echo "== Installing Grafana =="
if ! command -v grafana-server >/dev/null 2>&1 && ! command -v grafana >/dev/null 2>&1; then
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
if [[ -z "$PRIVATE_IP" ]]; then
  PRIVATE_IP="$(hostname -I | awk '{print $1}')"
fi
if [[ -z "$PUBLIC_IP" ]]; then
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
  echo "ERROR: no NISQA requirements file found"
  exit 1
fi

echo "== Installing GeoIP databases =="
install -d -m 0755 /var/lib/GeoIP

if [[ -s "$BASE/geoip/GeoLite2-City.mmdb" && -s "$BASE/geoip/GeoLite2-ASN.mmdb" ]]; then
  install -m 0644 "$BASE/geoip/GeoLite2-City.mmdb" /var/lib/GeoIP/GeoLite2-City.mmdb
  install -m 0644 "$BASE/geoip/GeoLite2-ASN.mmdb" /var/lib/GeoIP/GeoLite2-ASN.mmdb
  [[ -s "$BASE/geoip/GeoLite2-Country.mmdb" ]] && \
    install -m 0644 "$BASE/geoip/GeoLite2-Country.mmdb" /var/lib/GeoIP/GeoLite2-Country.mmdb
elif [[ -n "$MAXMIND_ACCOUNT_ID" && -n "$MAXMIND_LICENSE_KEY" ]]; then
  cat > /etc/GeoIP.conf <<GEOEOF
AccountID $MAXMIND_ACCOUNT_ID
LicenseKey $MAXMIND_LICENSE_KEY
EditionIDs GeoLite2-City GeoLite2-ASN GeoLite2-Country
DatabaseDirectory /var/lib/GeoIP
GEOEOF
  chmod 0600 /etc/GeoIP.conf
  geoipupdate
fi

if [[ ! -s /var/lib/GeoIP/GeoLite2-City.mmdb || ! -s /var/lib/GeoIP/GeoLite2-ASN.mmdb ]]; then
  echo "ERROR: GeoLite2-City.mmdb and GeoLite2-ASN.mmdb are required by app/nisqa.py."
  echo "Place them in $BASE/geoip/ or configure MAXMIND_ACCOUNT_ID/MAXMIND_LICENSE_KEY."
  exit 1
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

# Ubuntu's sample asterisk.conf marks [directories] as a template with (!).
# Activate the section so astagidir=/var/lib/asterisk/agi-bin is actually used.
if [[ -f /etc/asterisk/asterisk.conf ]]; then
  sed -i 's/^\[directories\](!)$/[directories]/' /etc/asterisk/asterisk.conf
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
  IDENTIFIED BY '${MYSQL_PASSWORD}';
ALTER USER '${MYSQL_USER}'@'localhost'
  IDENTIFIED BY '${MYSQL_PASSWORD}';

CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'127.0.0.1'
  IDENTIFIED BY '${MYSQL_PASSWORD}';
ALTER USER '${MYSQL_USER}'@'127.0.0.1'
  IDENTIFIED BY '${MYSQL_PASSWORD}';

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

rm -f /etc/nginx/sites-enabled/*
if [[ -f /etc/nginx/sites-available/nisqa-web ]]; then
  ln -sfn /etc/nginx/sites-available/nisqa-web /etc/nginx/sites-enabled/nisqa-web
fi
nginx -t

echo "== Configuring Prometheus =="
cat > /etc/prometheus/prometheus.yml <<'PROMEOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: prometheus
    scrape_interval: 5s
    scrape_timeout: 5s
    static_configs:
      - targets: ['localhost:9090']

  - job_name: node
    static_configs:
      - targets: ['localhost:9100']
PROMEOF

systemctl enable --now prometheus-node-exporter
systemctl enable --now prometheus

echo "== Installing Grafana dashboards and datasources =="
install -d -m 0755 /etc/grafana/provisioning/dashboards
install -d -m 0755 /etc/grafana/provisioning/datasources
install -d -o grafana -g grafana -m 0755 /var/lib/grafana/dashboards/nisqa

install -m 0644 \
  "$BASE/grafana/provisioning/dashboards/nisqa.yaml" \
  /etc/grafana/provisioning/dashboards/nisqa.yaml

if compgen -G "$BASE/grafana/dashboards/*.json" >/dev/null; then
  cp "$BASE"/grafana/dashboards/*.json /var/lib/grafana/dashboards/nisqa/
  chown grafana:grafana /var/lib/grafana/dashboards/nisqa/*.json
  chmod 0644 /var/lib/grafana/dashboards/nisqa/*.json
else
  echo "ERROR: No Grafana dashboards found in $BASE/grafana/dashboards"
  exit 1
fi

# These UIDs are intentionally stable and match the version-controlled dashboard.
cat > /etc/grafana/provisioning/datasources/nisqa-mysql.yaml <<DSLEOF
apiVersion: 1

datasources:
  - name: mysql
    uid: voice-quality-mysql
    type: mysql
    access: proxy
    url: 127.0.0.1:3306
    user: ${MYSQL_USER}
    secureJsonData:
      password: "${MYSQL_PASSWORD}"
    jsonData:
      database: ${MYSQL_DATABASE}
      maxOpenConns: 25
      maxIdleConns: 25
      connMaxLifetime: 14400
    isDefault: true
    editable: true

  - name: prometheus
    uid: voice-quality-prometheus
    type: prometheus
    access: proxy
    url: http://127.0.0.1:9090
    isDefault: false
    editable: true
DSLEOF
chown root:grafana /etc/grafana/provisioning/datasources/nisqa-mysql.yaml
chmod 0640 /etc/grafana/provisioning/datasources/nisqa-mysql.yaml

echo "== Setting Grafana admin credentials =="
if ! grep -q '^\[security\]' /etc/grafana/grafana.ini; then
  cat >> /etc/grafana/grafana.ini <<GFEOF

[security]
admin_user = ${GRAFANA_ADMIN_USER}
admin_password = ${GRAFANA_ADMIN_PASSWORD}
GFEOF
fi

systemctl enable grafana-server
systemctl restart grafana-server
sleep 5

if command -v grafana >/dev/null 2>&1; then
  grafana cli admin reset-admin-password "$GRAFANA_ADMIN_PASSWORD" >/dev/null 2>&1 || true
elif command -v grafana-cli >/dev/null 2>&1; then
  grafana-cli admin reset-admin-password "$GRAFANA_ADMIN_PASSWORD" >/dev/null 2>&1 || true
fi

echo "== Installing systemd / cron =="
cat > /etc/voice-quality.env <<ENVEOF
MYSQL_DATABASE=${MYSQL_DATABASE}
MYSQL_USER=${MYSQL_USER}
MYSQL_PASSWORD=${MYSQL_PASSWORD}
GRAFANA_ADMIN_USER=${GRAFANA_ADMIN_USER}
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
PUBLIC_IP=${PUBLIC_IP}
PRIVATE_IP=${PRIVATE_IP}
ASTERISK_LOCALNET=${ASTERISK_LOCALNET}
ENVEOF
chmod 0600 /etc/voice-quality.env

if [[ -f "$BASE/systemd/nisqa-web.service" ]]; then
  cp "$BASE/systemd/nisqa-web.service" /etc/systemd/system/nisqa-web.service
fi

cp "$BASE/cron/nisqa.cron" /etc/cron.d/nisqa
chmod 0644 /etc/cron.d/nisqa

echo "== Starting application services =="
systemctl daemon-reload
systemctl enable asterisk nginx
systemctl restart asterisk
systemctl restart nginx

if [[ -f /etc/systemd/system/nisqa-web.service ]]; then
  systemctl enable nisqa-web
  systemctl restart nisqa-web
fi

echo "== Verifying installed application =="

mysql \
  -h127.0.0.1 \
  -u"${MYSQL_USER}" \
  -p"${MYSQL_PASSWORD}" \
  "${MYSQL_DATABASE}" \
  -e "SELECT 1; SHOW TABLES;" >/dev/null

# Give Flask a few seconds to bind after systemd starts it.
WEB_OK=0
for _ in $(seq 1 15); do
  if curl -fsS --max-time 3 http://127.0.0.1:8088/ >/dev/null; then
    WEB_OK=1
    break
  fi
  sleep 1
done
[[ "$WEB_OK" -eq 1 ]] || { echo "ERROR: nisqa-web is not responding on 127.0.0.1:8088"; exit 1; }

curl -fsS http://127.0.0.1/dialer/ >/dev/null
curl -fsS http://127.0.0.1:3000/api/health \
  | grep -q '"database"[[:space:]]*:[[:space:]]*"ok"'
curl -fsS http://127.0.0.1:9090/-/ready >/dev/null
curl -fsS http://127.0.0.1:9100/metrics >/dev/null

ASTERISK_AGI_DIR="$(asterisk -rx 'core show settings' 2>/dev/null | awk -F: '/AGI Scripts directory/ {sub(/^[[:space:]]+/,"",$2); print $2}')"
if [[ "$ASTERISK_AGI_DIR" != "/var/lib/asterisk/agi-bin" ]]; then
  echo "ERROR: Asterisk AGI directory is '$ASTERISK_AGI_DIR', expected /var/lib/asterisk/agi-bin"
  exit 1
fi

for uid in voice-quality-mysql voice-quality-prometheus; do
  found=0
  for _ in $(seq 1 10); do
    if sqlite3 /var/lib/grafana/grafana.db "SELECT uid FROM data_source WHERE uid='$uid';" 2>/dev/null | grep -qx "$uid"; then
      found=1
      break
    fi
    sleep 1
  done
  if [[ "$found" -ne 1 ]]; then
    echo "ERROR: Grafana datasource $uid was not provisioned"
    exit 1
  fi
done

echo "Application verification: OK"
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
echo "Dialer UI:"
echo "  URL:      http://${PUBLIC_IP}/dialer/"
echo
echo "MySQL local application account:"
echo "  Database: ${MYSQL_DATABASE}"
echo "  User:     ${MYSQL_USER}"
echo "  Password: ${MYSQL_PASSWORD}"
echo
echo "SIP authentication:"
echo "  IP based; no SIP password is configured."
echo
echo "IMPORTANT:"
echo "  Allowlist this server's public IP with the SIP carrier before expecting PSTN tests to work."
echo "  Run ./verify.sh for a complete local validation."
echo "======================================================================"
