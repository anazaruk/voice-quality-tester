#!/bin/bash

ARCHIVE_DIR="/var/spool/asterisk/archive"
MONITOR_DIR="/var/spool/asterisk/monitor"
TMPFILE="/tmp/nisqa-files.txt"
LOGFILE="/var/log/nisqa_archive.log"

MAX_DISK_PERCENT=50
BATCH_HOURS=1

mkdir -p "$ARCHIVE_DIR"

DISK_USED=$(df -P "$MONITOR_DIR" | awk 'NR==2 {gsub("%","",$5); print $5}')
echo "$(date): Starting. Disk usage ${DISK_USED}%" >> "$LOGFILE"

# Exit if disk usage is below threshold
if [ "$DISK_USED" -le "$MAX_DISK_PERCENT" ]; then
    echo "$(date): Disk usage below ${MAX_DISK_PERCENT}%, nothing to archive" >> "$LOGFILE"
    exit 0
fi

# Keep archiving oldest files until disk usage drops below 50%
while [ "$DISK_USED" -gt "$MAX_DISK_PERCENT" ]; do

    # Find the oldest WAV file timestamp
    OLDEST_FILE=$(find "$MONITOR_DIR" -type f -name "nisqa*.wav" -printf '%T+ %p\n' | sort | head -n1 | awk '{print $2}')

    if [ -z "$OLDEST_FILE" ]; then
        echo "$(date): No WAV files left to archive" >> "$LOGFILE"
        break
    fi

    # Get oldest file epoch time
    OLDEST_EPOCH=$(stat -c %Y "$OLDEST_FILE")
    END_EPOCH=$((OLDEST_EPOCH + BATCH_HOURS * 3600))

    # Create list of files from oldest hour window
    find "$MONITOR_DIR" -type f -name "nisqa*.wav" -printf '%T@ %p\n' \
        | awk -v start="$OLDEST_EPOCH" -v end="$END_EPOCH" '$1 >= start && $1 < end {print $2}' \
        > "$TMPFILE"

    if [ ! -s "$TMPFILE" ]; then
        echo "$(date): No files found for oldest batch" >> "$LOGFILE"
        break
    fi

    TARFILE="$ARCHIVE_DIR/nisqa-oldest-$(date +%F-%H%M%S).tar.gz"

    echo "$(date): Archiving oldest batch to $TARFILE" >> "$LOGFILE"

    tar -czf "$TARFILE" --files-from="$TMPFILE"

    if [ $? -eq 0 ]; then
        xargs rm -f < "$TMPFILE"
        echo "$(date): Archived and removed $(wc -l < "$TMPFILE") WAV files" >> "$LOGFILE"
    else
        echo "$(date): ERROR creating $TARFILE" >> "$LOGFILE"
        break
    fi

    DISK_USED=$(df -P "$MONITOR_DIR" | awk 'NR==2 {gsub("%","",$5); print $5}')
    echo "$(date): Disk usage now ${DISK_USED}%" >> "$LOGFILE"
done
