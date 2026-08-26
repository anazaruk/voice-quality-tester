#!/usr/src/NISQA/venv/bin/python

import sys
import os
import re
import subprocess
import pymysql
import phonenumbers
import geoip2.database
from phonenumbers import geocoder, timezone
from faster_whisper import WhisperModel
from jiwer import wer

NISQA_DIR = "/usr/src/NISQA"
PYTHON = "/usr/src/NISQA/venv/bin/python"
MODEL = "weights/nisqa.tar"

GEOIP_CITY_DB = "/var/lib/GeoIP/GeoLite2-City.mmdb"
GEOIP_ASN_DB = "/var/lib/GeoIP/GeoLite2-ASN.mmdb"

DB_HOST = "127.0.0.1"
DB_USER = "nisqa"
DB_PASS = "CHANGE_ME"
DB_NAME = "voice_quality"

WHISPER_MODEL = "base.en"

SILENCE_NOISE_DB = "-40dB"
SILENCE_MIN_DURATION = "1"


geo_city = geoip2.database.Reader(GEOIP_CITY_DB)
geo_asn = geoip2.database.Reader(GEOIP_ASN_DB)


def read_agi_env():
    env = {}
    while True:
        line = sys.stdin.readline().strip()
        if line == "":
            break
        if ":" in line:
            k, v = line.split(":", 1)
            env[k.strip()] = v.strip()
    return env


def agi_cmd(cmd):
    print(cmd, flush=True)
    return sys.stdin.readline()


def set_var(name, value):
    if value is None:
        value = ""
    value = str(value).replace('"', "'")
    agi_cmd(f'SET VARIABLE {name} "{value}"')


def agi_verbose(msg):
    msg = str(msg).replace('"', "'")
    agi_cmd(f'VERBOSE "{msg}" 1')


def parse_metric(text, key):
    try:
        m = re.search(rf'{re.escape(key)}=([0-9.]+)', text or "")
        return float(m.group(1)) if m else None
    except Exception:
        return None


def get_audio_duration(wav_file):
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            wav_file
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )

        return float(result.stdout.strip())
    except Exception:
        return 0.0


def detect_silence(wav_file):
    """
    Returns:
      trailing_silence_sec
      total_silence_sec
      speech_duration_sec
    """

    audio_duration = get_audio_duration(wav_file)

    out = {
        "trailing_silence_sec": 0.0,
        "total_silence_sec": 0.0,
        "speech_duration_sec": audio_duration
    }

    if audio_duration <= 0:
        return out

    try:
        cmd = [
            "ffmpeg",
            "-i", wav_file,
            "-af", f"silencedetect=noise={SILENCE_NOISE_DB}:d={SILENCE_MIN_DURATION}",
            "-f", "null",
            "-"
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )

        text = result.stderr or ""

        events = []

        for line in text.splitlines():
            start_match = re.search(r"silence_start:\s*([0-9.]+)", line)
            end_match = re.search(
                r"silence_end:\s*([0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)",
                line
            )

            if start_match:
                events.append({
                    "start": float(start_match.group(1)),
                    "end": None,
                    "duration": None
                })

            elif end_match and events:
                events[-1]["end"] = float(end_match.group(1))
                events[-1]["duration"] = float(end_match.group(2))

        total_silence = 0.0
        trailing_silence = 0.0

        for ev in events:
            start = ev["start"]
            end = ev["end"]

            if end is None:
                end = audio_duration

            duration = max(0.0, end - start)
            total_silence += duration

            if audio_duration - end <= 0.25:
                trailing_silence = duration

        speech_duration = max(0.0, audio_duration - total_silence)

        out["trailing_silence_sec"] = round(trailing_silence, 2)
        out["total_silence_sec"] = round(total_silence, 2)
        out["speech_duration_sec"] = round(speech_duration, 2)

        return out

    except Exception:
        return out


def normalize_e164(num, default_region="US"):
    n = str(num or "").strip()

    if not n:
        return ""

    n = n.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    try:
        if n.startswith("+"):
            parsed = phonenumbers.parse(n, None)
        else:
            parsed = phonenumbers.parse(n, default_region)

        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )
    except Exception:
        pass

    if n.isdigit() and len(n) == 10:
        return "+1" + n

    if n.isdigit() and len(n) == 11 and n.startswith("1"):
        return "+" + n

    return n


def enrich_number(num):
    out = {"region": "", "state": "", "timezone": ""}

    try:
        n = normalize_e164(num)

        if not n:
            return out

        parsed = phonenumbers.parse(n, None)

        out["region"] = phonenumbers.region_code_for_number(parsed) or ""
        out["state"] = geocoder.description_for_number(parsed, "en") or ""

        tzs = timezone.time_zones_for_number(parsed)
        out["timezone"] = ",".join(tzs) if tzs else ""

    except Exception:
        pass

    return out


def enrich_ip(ip):
    out = {"country": "", "asn": "", "carrier": ""}

    try:
        r = geo_city.city(ip)
        out["country"] = r.country.name or ""
    except Exception:
        pass

    try:
        r = geo_asn.asn(ip)
        out["asn"] = str(r.autonomous_system_number)
        out["carrier"] = r.autonomous_system_organization or ""
    except Exception:
        pass

    return out


agi_env = read_agi_env()

wav_file = sys.argv[1] if len(sys.argv) > 1 else ""
source_ip = sys.argv[2] if len(sys.argv) > 2 else ""
source_number = sys.argv[3] if len(sys.argv) > 3 else ""
destination_number = sys.argv[4] if len(sys.argv) > 4 else ""

uniqueid = sys.argv[5] if len(sys.argv) > 5 else ""

duration = int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6].isdigit() else 0
codec = sys.argv[7] if len(sys.argv) > 7 else ""
reference_text = sys.argv[8] if len(sys.argv) > 8 else ""

rtp_loss = sys.argv[9] if len(sys.argv) > 9 else ""
rtp_jitter = sys.argv[10] if len(sys.argv) > 10 else ""
rtp_rtt = sys.argv[11] if len(sys.argv) > 11 else ""

rtp_avg_rx_loss = parse_metric(rtp_loss, "avgrxlost")
rtp_avg_tx_loss = parse_metric(rtp_loss, "avgtxlost")
rtp_avg_rx_jitter = parse_metric(rtp_jitter, "avgrxjitter")
rtp_avg_tx_jitter = parse_metric(rtp_jitter, "avgtxjitter")
rtp_avg_rtt = parse_metric(rtp_rtt, "avgrtt")

source_number = normalize_e164(source_number)
destination_number = normalize_e164(destination_number)

recording_file = os.path.basename(wav_file)

status = "ERROR"

mos = None
noi = None
dis = None
col = None
loud = None

transcript = ""
word_error_rate = None

trailing_silence_sec = 0.0
total_silence_sec = 0.0
speech_duration_sec = 0.0

src_meta = enrich_number(source_number)
dst_meta = enrich_number(destination_number)
ip_meta = enrich_ip(source_ip)

try:
    if not wav_file or not os.path.exists(wav_file) or os.path.getsize(wav_file) <= 44:
        status = "EMPTY_WAV"

    else:
        silence_meta = detect_silence(wav_file)

        trailing_silence_sec = silence_meta["trailing_silence_sec"]
        total_silence_sec = silence_meta["total_silence_sec"]
        speech_duration_sec = silence_meta["speech_duration_sec"]

        agi_verbose(
            f"Silence detected: trailing={trailing_silence_sec}s total={total_silence_sec}s speech={speech_duration_sec}s"
        )

        agi_verbose(f"Running NISQA for {wav_file}")

        cmd = [
            PYTHON,
            "run_predict.py",
            "--mode", "predict_file",
            "--pretrained_model", MODEL,
            "--deg", wav_file
        ]

        result = subprocess.run(
            cmd,
            cwd=NISQA_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=180
        )

        output = result.stdout

        match = re.search(
            r'(\S+\.wav)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)',
            output
        )

        if match:
            mos = float(match.group(2))
            noi = float(match.group(3))
            dis = float(match.group(4))
            col = float(match.group(5))
            loud = float(match.group(6))
            status = "OK"
        else:
            status = "NISQA_PARSE_ERROR"

        agi_verbose("Running Whisper")

        try:
            whisper = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
            segments, info = whisper.transcribe(wav_file, language="en")

            transcript = " ".join(
                [seg.text.strip() for seg in segments]
            ).strip()

            if reference_text and transcript:
                word_error_rate = float(
                    wer(reference_text.lower(), transcript.lower())
                )

        except Exception as e:
            if status == "OK":
                status = "WHISPER_ERROR"

            transcript = f"WHISPER_ERROR: {str(e)[:200]}"

except subprocess.TimeoutExpired:
    status = "NISQA_TIMEOUT"

except Exception as e:
    status = "EXCEPTION"
    transcript = str(e)[:200]


try:
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset="utf8mb4"
    )

    with conn.cursor() as cur:

        # Match incoming SIP source IP against our carrier reference table.
        cur.execute("""
            SELECT c.carrier_name
            FROM nisqa_carrier_ips ci
            JOIN nisqa_carriers c
              ON c.id = ci.carrier_id
            WHERE ci.ip_address = %s
              AND ci.enabled = 1
              AND c.enabled = 1
            LIMIT 1
        """, (source_ip,))

        carrier_row = cur.fetchone()

        if carrier_row:
            matched_carrier = carrier_row[0]
        else:
            matched_carrier = "Unknown"

        cur.execute("""
            INSERT INTO nisqa_cdr
            (
                uniqueid,
                source_ip,
                source_ip_country,
                source_ip_asn,
                source_ip_carrier,
                source_number,
                source_state,
                source_region,
                source_timezone,
                destination_number,
                destination_state,
                destination_region,
                duration,
                recording_file,
                codec,
                mos_pred,
                noi_pred,
                dis_pred,
                col_pred,
                loud_pred,
                transcript,
                reference_text,
                word_error_rate,
                trailing_silence_sec,
                total_silence_sec,
                speech_duration_sec,
                rtp_avg_rx_loss,
                rtp_avg_tx_loss,
                rtp_avg_rx_jitter,
                rtp_avg_tx_jitter,
                rtp_avg_rtt,
                status
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            uniqueid,
            source_ip,
            ip_meta["country"],
            ip_meta["asn"],
            matched_carrier,
            source_number,
            src_meta["state"],
            src_meta["region"],
            src_meta["timezone"],
            destination_number,
            dst_meta["state"],
            dst_meta["region"],
            duration,
            recording_file,
            codec,
            mos,
            noi,
            dis,
            col,
            loud,
            transcript,
            reference_text,
            word_error_rate,
            trailing_silence_sec,
            total_silence_sec,
            speech_duration_sec,
            rtp_avg_rx_loss,
            rtp_avg_tx_loss,
            rtp_avg_rx_jitter,
            rtp_avg_tx_jitter,
            rtp_avg_rtt,
            status
        ))

    conn.commit()
    conn.close()

except Exception as e:
    status = "MYSQL_ERROR"
    transcript = f"{transcript} MYSQL_ERROR: {str(e)[:200]}"


set_var("NISQA_STATUS", status)
set_var("NISQA_MOS", mos)
set_var("NISQA_NOISE", noi)
set_var("NISQA_DIS", dis)
set_var("NISQA_COL", col)
set_var("NISQA_LOUD", loud)

set_var("WHISPER_TEXT", transcript[:500])
set_var("WHISPER_WER", word_error_rate)

set_var("TRAILING_SILENCE_SEC", trailing_silence_sec)
set_var("TOTAL_SILENCE_SEC", total_silence_sec)
set_var("SPEECH_DURATION_SEC", speech_duration_sec)

set_var("RTP_AVG_RX_LOSS", rtp_avg_rx_loss)
set_var("RTP_AVG_TX_LOSS", rtp_avg_tx_loss)
set_var("RTP_AVG_RX_JITTER", rtp_avg_rx_jitter)
set_var("RTP_AVG_TX_JITTER", rtp_avg_tx_jitter)
set_var("RTP_AVG_RTT", rtp_avg_rtt)

sys.exit(0)
