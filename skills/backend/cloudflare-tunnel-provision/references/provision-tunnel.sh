#!/usr/bin/env bash
# provision-tunnel.sh — One-shot, idempotent: create a locally-managed Cloudflare
# tunnel + proxied DNS CNAME for a dockerized app, write creds/config, start cloudflared.
#
# Generalized from ~/bin/family-fiscal-tunnel-setup.sh. Parameterize via env vars:
#   CF_API_TOKEN   (required) token with Account:Cloudflare Tunnel:Edit + Zone:DNS:Edit
#   ZONE           apex zone on Cloudflare           (default: phyra.uk)
#   HOST           full hostname to expose           (e.g. myapp.phyra.uk)
#   TUNNEL_NAME    tunnel name                        (default: basename of HOST)
#   PROJ           project dir holding docker-compose (default: $PWD)
#   UPSTREAM       compose service:port to route to   (e.g. frontend:3010)
#   ACCOUNT_TAG    your account tag                   (default: shared phyra account)
set -euo pipefail

: "${CF_API_TOKEN:?Set CF_API_TOKEN (Account:Cloudflare Tunnel:Edit + Zone:DNS:Edit)}"
ZONE="${ZONE:-phyra.uk}"
HOST="${HOST:?Set HOST, e.g. myapp.phyra.uk}"
TUNNEL_NAME="${TUNNEL_NAME:-${HOST%%.*}}"
PROJ="${PROJ:-$PWD}"
UPSTREAM="${UPSTREAM:?Set UPSTREAM, e.g. frontend:3010 (compose service:port)}"
ACCOUNT_TAG="${ACCOUNT_TAG:-50483b2af2b0b1926e69332ce7be4717}"
CFDIR="$PROJ/cloudflared"
API="https://api.cloudflare.com/client/v4"
auth=(-H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json")
jget() { python3 -c "import sys,json;d=json.load(sys.stdin);print($1)"; }

echo "==> verifying token"
curl -s "${auth[@]}" "$API/user/tokens/verify" | grep -q '"status":"active"' \
  && echo "  token active" || { echo "  token NOT active"; exit 1; }

echo "==> resolving account + zone id"
ACCOUNT_ID=$(curl -s "${auth[@]}" "$API/accounts" | jget "d['result'][0]['id']")
ZONE_ID=$(curl -s "${auth[@]}" "$API/zones?name=$ZONE" | jget "d['result'][0]['id']")
echo "  account=$ACCOUNT_ID zone=$ZONE_ID"

echo "==> creating locally-managed tunnel '$TUNNEL_NAME'"
SECRET=$(python3 -c "import secrets,base64;print(base64.b64encode(secrets.token_bytes(32)).decode())")
RESP=$(curl -s "${auth[@]}" -X POST "$API/accounts/$ACCOUNT_ID/cfd_tunnel" \
  --data "{\"name\":\"$TUNNEL_NAME\",\"tunnel_secret\":\"$SECRET\",\"config_src\":\"local\"}")
TUNNEL_ID=$(echo "$RESP" | jget "d['result']['id']" 2>/dev/null || true)
if [ -z "${TUNNEL_ID:-}" ]; then
  echo "  create returned no id — tunnel name likely already exists."
  echo "  A locally-managed tunnel's secret CANNOT be recovered. Reuse the existing"
  echo "  cloudflared/<id>.json you kept, or delete the old tunnel and re-run."
  TUNNEL_ID=$(curl -s "${auth[@]}" "$API/accounts/$ACCOUNT_ID/cfd_tunnel?name=$TUNNEL_NAME&is_deleted=false" \
    | jget "d['result'][0]['id']")
  if [ ! -f "$CFDIR/$TUNNEL_ID.json" ]; then
    echo "  ERR: no local creds for existing tunnel $TUNNEL_ID — aborting (would write a broken secret)."
    exit 1
  fi
  echo "  reusing existing creds at $CFDIR/$TUNNEL_ID.json"
  SECRET=$(jget "d['TunnelSecret']" < "$CFDIR/$TUNNEL_ID.json")
fi
echo "  tunnel id=$TUNNEL_ID"

echo "==> writing credentials + config"
mkdir -p "$CFDIR"
cat > "$CFDIR/$TUNNEL_ID.json" <<EOF
{"AccountTag":"$ACCOUNT_TAG","TunnelID":"$TUNNEL_ID","TunnelSecret":"$SECRET"}
EOF
cat > "$CFDIR/config.yml" <<EOF
tunnel: $TUNNEL_ID
credentials-file: /etc/cloudflared/$TUNNEL_ID.json

ingress:
  - hostname: $HOST
    service: http://$UPSTREAM
  - service: http_status:404
EOF
echo "  wrote $CFDIR/config.yml + $TUNNEL_ID.json  (ensure both are gitignored)"

echo "==> creating proxied DNS CNAME $HOST -> $TUNNEL_ID.cfargotunnel.com"
TARGET="$TUNNEL_ID.cfargotunnel.com"
EXIST=$(curl -s "${auth[@]}" "$API/zones/$ZONE_ID/dns_records?name=$HOST" \
  | jget "d['result'][0]['id'] if d['result'] else ''")
DATA="{\"type\":\"CNAME\",\"name\":\"$HOST\",\"content\":\"$TARGET\",\"proxied\":true}"
if [ -n "$EXIST" ]; then
  curl -s "${auth[@]}" -X PUT "$API/zones/$ZONE_ID/dns_records/$EXIST" --data "$DATA" >/dev/null
  echo "  updated existing record"
else
  curl -s "${auth[@]}" -X POST "$API/zones/$ZONE_ID/dns_records" --data "$DATA" >/dev/null
  echo "  created DNS record"
fi

echo "==> starting cloudflared container"
cd "$PROJ"
docker compose up -d cloudflared

echo "==> done. tunnel=$TUNNEL_ID  host=https://$HOST"
echo "    verify: docker compose logs --tail=20 cloudflared   (expect 'Registered tunnel connection')"
echo "            curl -sL https://$HOST -o /dev/null -w 'HTTP %{http_code}\\n'"
