#!/usr/bin/env bash
# End-to-end smoke test for a RUNNING stack (api + worker + postgres + redis).
#
#   bash backend/scripts/smoke.sh [base_url]        # default: http://localhost:8000
#
# Needs only curl and python3.  Exit code is 0 when every check passes.
set -u

BASE="${1:-http://localhost:8000}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
FAILED=0

check() { # check <description> <actual> <expected>
  if [ "$2" = "$3" ]; then
    echo "PASS  $1"
  else
    echo "FAIL  $1  (got: '$2', expected: '$3')"
    FAILED=1
  fi
}

http_code() { curl -s -o /dev/null -w '%{http_code}' "$@"; }

json_get() { # json_get <file> <python expression over d>
  python3 -c 'import json, sys; d = json.load(open(sys.argv[1])); print(eval(sys.argv[2]))' "$1" "$2"
}

wait_processed() { # wait_processed <file id>  -> prints the final processing_status
  local status=""
  for _ in $(seq 1 30); do
    curl -s "$BASE/files/$1" -o "$WORK/poll.json"
    status="$(json_get "$WORK/poll.json" 'd["processing_status"]')"
    if [ "$status" = "processed" ] || [ "$status" = "failed" ]; then break; fi
    sleep 1
  done
  echo "$status"
}

alert_exists() { # alert_exists <file id> <level>
  curl -s "$BASE/alerts" -o "$WORK/alerts.json"
  python3 -c 'import json, sys; print(any(a["file_id"] == sys.argv[2] and a["level"] == sys.argv[3] for a in json.load(open(sys.argv[1]))))' \
    "$WORK/alerts.json" "$1" "$2"
}

upload() { # upload <title> <path> <mime> -> prints "<http code> <id or ->"
  local code
  code="$(curl -s -o "$WORK/upload.json" -w '%{http_code}' -F "title=$1" -F "file=@$2;type=$3" "$BASE/files")"
  if [ "$code" = "201" ]; then echo "$code $(json_get "$WORK/upload.json" 'd["id"]')"; else echo "$code -"; fi
}

printf 'one\ntwo\n' >"$WORK/note.txt"
printf 'MZ' >"$WORK/run.exe"
: >"$WORK/empty.txt"

echo "== upload and processing =="
read -r CODE ID <<<"$(upload 'Smoke note' "$WORK/note.txt" text/plain)"
check "POST /files returns 201" "$CODE" "201"
check "file is processed by the worker" "$(wait_processed "$ID")" "processed"

curl -s "$BASE/files/$ID" -o "$WORK/file.json"
check "scan_status is clean" "$(json_get "$WORK/file.json" 'd["scan_status"]')" "clean"
check "metadata line_count" "$(json_get "$WORK/file.json" 'd["metadata_json"]["line_count"]')" "2"
check "metadata char_count" "$(json_get "$WORK/file.json" 'd["metadata_json"]["char_count"]')" "8"
check "info alert was created" "$(alert_exists "$ID" info)" "True"

echo "== suspicious file =="
read -r CODE EXE_ID <<<"$(upload 'Smoke exe' "$WORK/run.exe" application/octet-stream)"
check "POST /files (exe) returns 201" "$CODE" "201"
check "exe is processed" "$(wait_processed "$EXE_ID")" "processed"
curl -s "$BASE/files/$EXE_ID" -o "$WORK/exe.json"
check "exe is flagged" "$(json_get "$WORK/exe.json" 'd["scan_status"]')" "suspicious"
check "warning alert was created" "$(alert_exists "$EXE_ID" warning)" "True"

echo "== download, update, validation =="
curl -s "$BASE/files/$ID/download" -o "$WORK/downloaded.txt"
cmp -s "$WORK/note.txt" "$WORK/downloaded.txt" && SAME=same || SAME=different
check "download returns the stored bytes" "$SAME" "same"
check "PATCH title" "$(http_code -X PATCH -H 'Content-Type: application/json' -d '{"title":"Renamed"}' "$BASE/files/$ID")" "200"
check "PATCH empty title is rejected" "$(http_code -X PATCH -H 'Content-Type: application/json' -d '{"title":""}' "$BASE/files/$ID")" "422"
LONG="$(python3 -c 'print("x" * 300)')"
check "PATCH 300-char title is rejected (was HTTP 500)" "$(http_code -X PATCH -H 'Content-Type: application/json' -d "{\"title\":\"$LONG\"}" "$BASE/files/$ID")" "422"
check "empty upload is rejected" "$(http_code -F 'title=Empty' -F "file=@$WORK/empty.txt;type=text/plain" "$BASE/files")" "400"
check "unknown file is 404" "$(http_code "$BASE/files/does-not-exist")" "404"

echo "== delete (by the models' foreign key the old code was expected to fail with HTTP 500 once an alert existed) =="
check "DELETE processed file" "$(http_code -X DELETE "$BASE/files/$ID")" "204"
check "deleted file is gone" "$(http_code "$BASE/files/$ID")" "404"
check "its download is gone" "$(http_code "$BASE/files/$ID/download")" "404"
check "its alerts are gone" "$(alert_exists "$ID" info)" "False"
check "DELETE the exe file" "$(http_code -X DELETE "$BASE/files/$EXE_ID")" "204"

echo
if [ "$FAILED" = "0" ]; then echo "ALL CHECKS PASSED"; else echo "SOME CHECKS FAILED"; fi
exit "$FAILED"
