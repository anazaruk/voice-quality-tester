#!/usr/bin/env bash
set -u

echo "=== Services ==="
for s in asterisk mysql grafana-server nginx nisqa-web; do
  printf "%-20s " "$s"
  systemctl is-active "$s" 2>/dev/null || true
done

echo
echo "=== Asterisk ==="
asterisk -V 2>/dev/null || true
asterisk -rx "module show like sip" 2>/dev/null || true

echo
echo "=== Database ==="
mysql -N -B -e "SHOW DATABASES LIKE 'voice_quality'" 2>/dev/null || true
mysql -N -B voice_quality -e "SHOW TABLES" 2>/dev/null || true

echo
echo "=== Grafana dashboards on disk ==="
find /var/lib/grafana/dashboards/nisqa -maxdepth 1 -type f -name '*.json' -print 2>/dev/null || true

echo
echo "=== Listening ports ==="
ss -lntup 2>/dev/null | egrep ':80 |:3000 |:3306 |:5060 |:5061 ' || true
