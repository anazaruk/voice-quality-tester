#!/bin/bash

CAPTURE_DIR="/var/log/voip"
LOG_FILE="/var/log/voip_pcap_rotate.log"

MAX_DISK_PERCENT=50
MAX_AGE_DAYS=5
MIN_FREE_PERCENT=50

echo "$(date '+%F %T') Starting PCAP rotation" >> "$LOG_FILE"

# 1. Delete pcaps older than 5 days
find "$CAPTURE_DIR" -type f -name "capture_*.pcap" -mtime +$MAX_AGE_DAYS -print -delete >> "$LOG_FILE" 2>&1

# 2. Check disk usage for the filesystem containing CAPTURE_DIR
DISK_USED=$(df -P "$CAPTURE_DIR" | awk 'NR==2 {gsub("%","",$5); print $5}')

echo "$(date '+%F %T') Disk used: ${DISK_USED}%" >> "$LOG_FILE"

# 3. If disk usage is above 50%, delete oldest pcaps until under 50%
while [ "$DISK_USED" -gt "$MAX_DISK_PERCENT" ]; do
    OLDEST_FILE=$(find "$CAPTURE_DIR" -type f -name "capture_*.pcap" -printf '%T+ %p\n' | sort | head -n 1 | awk '{print $2}')

    if [ -z "$OLDEST_FILE" ]; then
        echo "$(date '+%F %T') No more PCAP files to delete" >> "$LOG_FILE"
        break
    fi

    echo "$(date '+%F %T') Deleting oldest PCAP: $OLDEST_FILE" >> "$LOG_FILE"
    rm -f "$OLDEST_FILE"

    DISK_USED=$(df -P "$CAPTURE_DIR" | awk 'NR==2 {gsub("%","",$5); print $5}')
done

echo "$(date '+%F %T') Rotation complete. Disk used: ${DISK_USED}%" >> "$LOG_FILE"
