#!/usr/src/NISQA/venv/bin/python

import os
import time
import pymysql
import tempfile
import pwd
import grp

DB_HOST = "127.0.0.1"
DB_USER = "nisqa"
DB_PASS = "CHANGE_ME"
DB_NAME = "voice_quality"

SPOOL_DIR = "/var/spool/asterisk/outgoing"

DIALS_PER_RUN = 60
DIAL_DELAY_SECONDS = 3
PICK_MODE = "random"

ASTERISK_UID = pwd.getpwnam("asterisk").pw_uid
ASTERISK_GID = grp.getgrnam("asterisk").gr_gid


def playback_name(path):
    if path.endswith(".wav"):
        return path[:-4]
    return path


def create_call_file(row):
    target_id = row["id"]
    caller_id = row["caller_id"]
    dst_number = row["dst_number"]
    trunk_name = row["trunk_name"]
    audio_file = row["audio_file"]

    if not os.path.exists(audio_file):
        print(f"Audio file missing for target {target_id}: {audio_file}")
        return False

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

    timestamp = int(time.time())

    tmp_fd, tmp_path = tempfile.mkstemp(
        prefix=f"nisqa-{target_id}-{timestamp}-",
        suffix=".call",
        dir="/tmp"
    )

    with os.fdopen(tmp_fd, "w") as f:
        f.write(call_content)

    os.chown(tmp_path, ASTERISK_UID, ASTERISK_GID)
    os.chmod(tmp_path, 0o644)

    final_path = os.path.join(
        SPOOL_DIR,
        f"nisqa-{target_id}-{timestamp}-{os.path.basename(tmp_path)}"
    )

    os.rename(tmp_path, final_path)

    os.chown(final_path, ASTERISK_UID, ASTERISK_GID)
    os.chmod(final_path, 0o644)

    print(f"Dialed {dst_number} via {trunk_name} from {caller_id}")
    return True


conn = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME,
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor
)

dialed_ids = []

try:
    with conn.cursor() as cur:
        if PICK_MODE == "oldest":
            order_by = "last_called_at IS NULL DESC, last_called_at ASC"
        else:
            order_by = "RAND()"

        cur.execute(f"""
            SELECT *
            FROM nisqa_dialer_targets
            WHERE enabled = 1
            ORDER BY {order_by}
            LIMIT %s
        """, (DIALS_PER_RUN,))

        rows = cur.fetchall()

        if not rows:
            print("No enabled targets")
            exit(0)

        for i, row in enumerate(rows):
            if create_call_file(row):
                dialed_ids.append(row["id"])

            if i < len(rows) - 1:
                time.sleep(DIAL_DELAY_SECONDS)

        if dialed_ids:
            placeholders = ",".join(["%s"] * len(dialed_ids))
            cur.execute(f"""
                UPDATE nisqa_dialer_targets
                SET last_called_at = NOW()
                WHERE id IN ({placeholders})
            """, dialed_ids)

    conn.commit()

finally:
    conn.close()

print(f"Created {len(dialed_ids)} call files")
