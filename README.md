# Voice Quality Tester - reproducible install

This package was exported from the working Asterisk/NISQA voice-quality host.

## Fresh Ubuntu installation

```bash
git clone <YOUR_REPOSITORY>
cd voice-quality-tester
sudo ./install.sh
```

The installer refuses to overwrite an existing NISQA/voice_quality deployment
unless `--force` is supplied.

## Default credentials

Grafana:

- user: `admin`
- password: `admin`

MySQL local application account:

- database: `voice_quality`
- user: `nisqa`
- password: **none / empty**

SIP:

- authentication is **IP based**
- no SIP password is created or required by this package
- the new server public IP must be allowed by the upstream SIP network

**Change the Grafana admin password after validation if this server is reachable from untrusted networks.**

## What is exported

- Full Asterisk configuration (sanitized Git copy)
- Custom Asterisk sounds
- NISQA source/model files found under `/usr/src/NISQA` except venv/runtime media
- Exact Python dependency freeze
- NISQA dialer/web/AGI scripts
- Database schema
- Non-CDR configuration table data
- nginx configuration
- cron
- nisqa-web systemd unit
- Grafana dashboards as JSON
- Grafana datasource metadata and provisioning
- Private exact Grafana/Asterisk snapshots under `private/` (ignored by Git)

## Important limitation

No generic installer can invent external carrier credentials or authorize the
new cloud public IP with your SIP carrier. The software stack can be reproduced,
but PSTN tests may require updating the carrier/trunk IP allowlist or SIP
credentials.

## Verify

```bash
sudo ./verify.sh
```

## Security check before GitHub

```bash
cat SECRET_REVIEW.txt
grep -RniE 'password|passwd|secret|token|api.?key|private.?key|BEGIN .*PRIVATE KEY' . --exclude-dir=.git --exclude-dir=private
```

The `private/` directory contains exact local snapshots and is intentionally
excluded by `.gitignore`.
