# GeoLite2 databases

The voice quality AGI uses MaxMind GeoLite2 City and ASN databases:

- `GeoLite2-City.mmdb`
- `GeoLite2-ASN.mmdb`

For a fresh installation, use one of these methods:

1. Put the licensed `.mmdb` files in this `geoip/` directory before running `install.sh`.
2. Set `MAXMIND_ACCOUNT_ID` and `MAXMIND_LICENSE_KEY` in `config/defaults.env`; the installer will run `geoipupdate`.

Do not commit MaxMind credentials to a public repository.
