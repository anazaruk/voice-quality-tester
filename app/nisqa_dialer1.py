#!/usr/src/NISQA/venv/bin/python


import os
import time
import pymysql
import tempfile
from pathlib import Path

DB_HOST = "127.0.0.1"
DB_USER = "nisqa"
DB_PASS = "CHANGE_ME"
DB_NAME = "voice_quality"

SPOOL_DIR = "/var/spool/asterisk/outgoing"

def playback_name(path):
    # Asterisk Playback wants filename without .wav
    if path.endswith(".wav"):
        return path[:-4]
    return path

conn = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME,
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor
)

with conn.cursor() as cur:
    cur.execute("""
        SELECT *
        FROM nisqa_dialer_targets
        WHERE enabled = 1
        ORDER BY RAND()
        LIMIT 1
    """)
    row = cur.fetchone()

    if not row:
        print("No enabled targets")
        exit(0)

    target_id = row["id"]
    caller_id = row["caller_id"]
    dst_number = row["dst_number"]
    trunk_name = row["trunk_name"]
    audio_file = row["audio_file"]

    if not os.path.exists(audio_file):
        print(f"Audio file missing: {audio_file}")
        exit(1)

    audio_playback = playback_name(audio_file)

    call_content = f"""Channel: SIP/{trunk_name}/{dst_number}
CallerID: "{caller_id}" <{caller_id}>
MaxRetries: 0
RetryTime: 60
WaitTime: 60
Application: Playback
Data: {audio_playback}
Setvar: NISQA_DIALER_ID={target_id}
Setvar: NISQA_TEST_CALL=1
"""

    tmp_fd, tmp_path = tempfile.mkstemp(prefix="nisqa-", suffix=".call", dir="/tmp")
    with os.fdopen(tmp_fd, "w") as f:
        f.write(call_content)

    os.chown(tmp_path, 0, 0)
    os.chmod(tmp_path, 0o644)

    final_path = os.path.join(SPOOL_DIR, f"nisqa-{target_id}-{int(time.time())}.call")
    os.rename(tmp_path, final_path)

    cur.execute("""
        UPDATE nisqa_dialer_targets
        SET last_called_at = NOW()
        WHERE id = %s
    """, (target_id,))

conn.commit()
conn.close()

print(f"Dialed {dst_number} via {trunk_name} from {caller_id}")
