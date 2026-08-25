#!/usr/bin/env bash
set -u

PASS=0
FAIL=0

check_service() {
  local s="$1"
  printf "%-28s " "$s"
  if systemctl is-active --quiet "$s"; then
    echo "OK"
    PASS=$((PASS+1))
  else
    echo "FAILED"
    FAIL=$((FAIL+1))
  fi
}

check_url() {
  local name="$1" url="$2"
  printf "%-28s " "$name"
  if curl -fsS --max-time 5 "$url" >/dev/null; then
    echo "OK"
    PASS=$((PASS+1))
  else
    echo "FAILED"
    FAIL=$((FAIL+1))
  fi
}

echo "=== Services ==="
for s in asterisk mysql grafana-server nginx nisqa-web prometheus prometheus-node-exporter; do
  check_service "$s"
done

echo
echo "=== Asterisk ==="
asterisk -V 2>/dev/null || true
asterisk -rx "core show settings" 2>/dev/null | grep -E 'Configuration file|AGI Scripts directory' || true
if asterisk -rx "core show settings" 2>/dev/null | grep -q 'AGI Scripts directory:.*\/var\/lib\/asterisk\/agi-bin'; then
  echo "AGI directory                 OK"
  PASS=$((PASS+1))
else
  echo "AGI directory                 FAILED"
  FAIL=$((FAIL+1))
fi

if [[ -x /var/lib/asterisk/agi-bin/nisqa.py ]]; then
  echo "nisqa.py                      OK"
  PASS=$((PASS+1))
else
  echo "nisqa.py                      FAILED"
  FAIL=$((FAIL+1))
fi

echo
echo "=== Database ==="
mysql -N -B -e "SHOW DATABASES LIKE 'voice_quality'" 2>/dev/null || true
mysql -N -B voice_quality -e "SHOW TABLES" 2>/dev/null || true

echo
echo "=== GeoIP ==="
for f in /var/lib/GeoIP/GeoLite2-City.mmdb /var/lib/GeoIP/GeoLite2-ASN.mmdb; do
  if [[ -s "$f" ]]; then
    echo "$f OK"
    PASS=$((PASS+1))
  else
    echo "$f FAILED"
    FAIL=$((FAIL+1))
  fi
done

echo
echo "=== HTTP endpoints ==="
check_url "NISQA web" "http://127.0.0.1:8088/"
check_url "nginx /dialer/" "http://127.0.0.1/dialer/"
check_url "Grafana health" "http://127.0.0.1:3000/api/health"
check_url "Prometheus ready" "http://127.0.0.1:9090/-/ready"
check_url "Node exporter" "http://127.0.0.1:9100/metrics"

echo
echo "=== Prometheus targets ==="
curl -fsS http://127.0.0.1:9090/api/v1/targets 2>/dev/null \
  | jq -r '.data.activeTargets[] | [.labels.job,.health,.scrapeUrl,.lastError] | @tsv' 2>/dev/null || true

echo
echo "=== Grafana datasources ==="
if [[ -f /var/lib/grafana/grafana.db ]]; then
  sqlite3 -header -column /var/lib/grafana/grafana.db \
    'SELECT uid,name,type,url,user,is_default FROM data_source;' || true

  for uid in voice-quality-mysql voice-quality-prometheus; do
    if sqlite3 /var/lib/grafana/grafana.db "SELECT uid FROM data_source WHERE uid='$uid';" | grep -qx "$uid"; then
      echo "$uid OK"
      PASS=$((PASS+1))
    else
      echo "$uid FAILED"
      FAIL=$((FAIL+1))
    fi
  done
fi

echo
echo "=== Grafana dashboard ==="
find /var/lib/grafana/dashboards/nisqa -maxdepth 1 -type f -name '*.json' -print 2>/dev/null || true

echo
echo "=== Listening ports ==="
ss -lntup 2>/dev/null | egrep ':80 |:3000 |:3306 |:5060 |:5061 |:9090 |:9100 ' || true

echo
echo "Checks passed: $PASS"
echo "Checks failed: $FAIL"
[[ "$FAIL" -eq 0 ]]
