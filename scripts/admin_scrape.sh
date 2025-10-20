#!/usr/bin/env bash
# Interactive helper to trigger backend scraping/admin tasks via curl.

set -euo pipefail

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required but not found in PATH." >&2
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  pretty_print() {
    python3 -m json.tool
  }

else
  pretty_print() {
    cat
  }
fi

DEFAULT_BACKEND_URL="https://encheres-backend.onrender.com"
BACKEND_URL="${BACKEND_URL:-$DEFAULT_BACKEND_URL}"

read -rp "Backend URL [${BACKEND_URL}]: " input_backend
if [[ -n "${input_backend}" ]]; then
  BACKEND_URL="${input_backend}"
fi

read -rp "Admin email: " ADMIN_EMAIL
if [[ -z "${ADMIN_EMAIL}" ]]; then
  echo "Email is required." >&2
  exit 1
fi

read -srp "Admin password: " ADMIN_PASSWORD
echo
if [[ -z "${ADMIN_PASSWORD}" ]]; then
  echo "Password is required." >&2
  exit 1
fi

COOKIE_JAR="$(mktemp)"

cleanup() {
  rm -f "${COOKIE_JAR}"
}
trap cleanup EXIT

echo
echo "Authenticating against ${BACKEND_URL}..."
LOGIN_STATUS="$(curl -sS -o /tmp/login_response.json -w "%{http_code}" \
  -c "${COOKIE_JAR}" \
  --data-urlencode "username=${ADMIN_EMAIL}" \
  --data-urlencode "password=${ADMIN_PASSWORD}" \
  "${BACKEND_URL}/api/v1/auth/login")"

if [[ "${LOGIN_STATUS}" != "200" ]]; then
  echo "Login failed (HTTP ${LOGIN_STATUS}). Response:"
  cat /tmp/login_response.json
  exit 1
fi

echo "Login successful."

ME_STATUS="$(curl -sS -o /tmp/me_response.json -w "%{http_code}" \
  -b "${COOKIE_JAR}" \
  "${BACKEND_URL}/api/v1/auth/me")"

if [[ "${ME_STATUS}" != "200" ]]; then
  echo "Unable to fetch user profile (HTTP ${ME_STATUS}). Response:"
  cat /tmp/me_response.json
  exit 1
fi

if ! grep -q '"is_admin":true' /tmp/me_response.json; then
  echo "The account ${ADMIN_EMAIL} is not marked as admin. Grant admin rights before retrying." >&2
  exit 1
fi

echo "Admin privileges confirmed."
echo

menu() {
  cat <<'EOF'
Select an action:
  1) Discover sales (admin/discover-sales)
  2) Scrape all sales (admin/scrape-all)
  3) Scrape a specific sale (admin/scrape)
  4) View scraper logs (admin/scraper-logs)
  5) Quit
EOF
}

while true; do
  menu
  read -rp "Choice [1-5]: " choice
  echo
  case "${choice}" in
    1)
      read -rp "Max pages to explore (press Enter for default): " max_pages
      url="${BACKEND_URL}/api/v1/admin/discover-sales"
      if [[ -n "${max_pages}" ]]; then
        url="${url}?max_pages=${max_pages}"
      fi
      echo "Calling ${url}"
      curl -sS -b "${COOKIE_JAR}" -X POST "${url}" | pretty_print || true
      echo
      ;;
    2)
      read -rp "Limit number of sales to scrape (Enter for all): " limit
      read -rp "Staleness in hours (Enter to use backend default): " staleness
      payload="{\"limit\": ${limit:-null}, \"staleness_hours\": ${staleness:-null}}"
      echo "Calling ${BACKEND_URL}/api/v1/admin/scrape-all"
      curl -sS -b "${COOKIE_JAR}" \
        -H 'Content-Type: application/json' \
        -X POST \
        -d "${payload}" \
        "${BACKEND_URL}/api/v1/admin/scrape-all" | pretty_print || true
      echo
      ;;
    3)
      read -rp "Sale number to scrape: " sale_number
      if [[ -z "${sale_number}" ]]; then
        echo "Sale number is required." >&2
        continue
      fi
      payload="{\"sale_number\": ${sale_number}}"
      echo "Calling ${BACKEND_URL}/api/v1/admin/scrape"
      curl -sS -b "${COOKIE_JAR}" \
        -H 'Content-Type: application/json' \
        -X POST \
        -d "${payload}" \
        "${BACKEND_URL}/api/v1/admin/scrape" | pretty_print || true
      echo
      ;;
    4)
      read -rp "Page (default 1): " page
      read -rp "Size (default 10): " size
      page="${page:-1}"
      size="${size:-10}"
      url="${BACKEND_URL}/api/v1/admin/scraper-logs?page=${page}&size=${size}"
      echo "Calling ${url}"
      curl -sS -b "${COOKIE_JAR}" "${url}" | pretty_print || true
      echo
      ;;
    5)
      echo "Goodbye!"
      break
      ;;
    *)
      echo "Invalid choice."
      ;;
  esac
done
