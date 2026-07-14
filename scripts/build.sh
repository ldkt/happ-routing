#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST="${DIST_DIR:-$ROOT/dist}"
CACHE="${CACHE_DIR:-$ROOT/.cache}"
UPSTREAM="${GEOSITE_REPOSITORY:-https://github.com/v2fly/domain-list-community.git}"
GEOIP_BASE="${GEOIP_BASE_URL:-https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download}"

command -v curl >/dev/null
command -v git >/dev/null
command -v go >/dev/null
command -v python3 >/dev/null

mkdir -p "$DIST" "$CACHE"
rm -f "$DIST/geosite.dat" "$DIST/geoip.dat"

if [[ -d "$CACHE/domain-list-community/.git" ]]; then
  git -C "$CACHE/domain-list-community" fetch --depth=1 origin master
  git -C "$CACHE/domain-list-community" reset --hard origin/master
else
  git clone --depth=1 --branch master "$UPSTREAM" "$CACHE/domain-list-community"
fi

for source in "$ROOT"/data/*; do
  cp "$source" "$CACHE/domain-list-community/data/$(basename "$source")"
done

(
  cd "$CACHE/domain-list-community"
  go run ./ --outputdir "$DIST" --outputname "geosite.dat"
)

curl --fail --location --retry 3 --output "$DIST/geoip.dat" "$GEOIP_BASE/geoip.dat"
curl --fail --location --retry 3 --output "$DIST/geoip.dat.sha256sum.upstream" \
  "$GEOIP_BASE/geoip.dat.sha256sum"
(
  cd "$DIST"
  expected="$(awk '{print $1}' geoip.dat.sha256sum.upstream)"
  actual="$(shasum -a 256 geoip.dat | awk '{print $1}')"
  [[ "$expected" == "$actual" ]]
  rm geoip.dat.sha256sum.upstream
)

python3 "$ROOT/scripts/generate_configs.py" --output "$DIST"
python3 "$ROOT/scripts/release_metadata.py" --dist "$DIST" \
  --geosite-source "$(git -C "$CACHE/domain-list-community" rev-parse HEAD)"

(
  cd "$DIST"
  shasum -a 256 geoip.dat geosite.dat happ-routing.json \
    happ-routing-link.txt 3x-ui-routing.json release.json > SHA256SUMS
)

python3 "$ROOT/scripts/validate.py" --dist "$DIST"
