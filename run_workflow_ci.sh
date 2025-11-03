#!/bin/bash

# Skrypt do uruchomienia CI workflow
# Wymaga: GitHub Personal Access Token z uprawnieniami do workflow

REPO="michalporada/framer-marketplace-scraper-py"
WORKFLOW_FILE=".github/workflows/ci.yml"

# Sprawdź czy token jest ustawiony
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Błąd: GITHUB_TOKEN nie jest ustawiony"
    echo ""
    echo "Aby uruchomić workflow, potrzebujesz GitHub Personal Access Token:"
    echo "1. Przejdź do: https://github.com/settings/tokens"
    echo "2. Kliknij 'Generate new token (classic)'"
    echo "3. Nadaj uprawnienia 'repo' i 'workflow'"
    echo "4. Skopiuj token"
    echo "5. Uruchom: export GITHUB_TOKEN='twoj_token'"
    echo "6. Następnie uruchom ponownie: ./run_workflow_ci.sh"
    echo ""
    echo "Lub użyj:"
    echo "  GITHUB_TOKEN=twoj_token ./run_workflow_ci.sh"
    exit 1
fi

# Pobierz workflow ID
echo "🔍 Pobieranie listy workflow..."
WORKFLOW_ID=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/${REPO}/actions/workflows" | \
    python3 -c "import sys, json; data = json.load(sys.stdin); workflows = [w for w in data['workflows'] if w['path'] == '${WORKFLOW_FILE}']; print(workflows[0]['id'] if workflows else '')" 2>/dev/null)

if [ -z "$WORKFLOW_ID" ]; then
    echo "❌ Nie znaleziono workflow. Sprawdzam dostępne workflow..."
    curl -s -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/repos/${REPO}/actions/workflows" | \
        python3 -m json.tool | grep -A 5 "name\|path" || echo "Brak workflow"
    exit 1
fi

echo "🚀 Uruchamianie CI workflow (ID: ${WORKFLOW_ID})..."

# Uruchom workflow
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW_ID}/dispatches" \
    -d '{"ref":"main"}')

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" == "204" ]; then
    echo "✅ CI workflow uruchomiony pomyślnie!"
    echo ""
    echo "🔗 Sprawdź status:"
    echo "   https://github.com/${REPO}/actions"
    echo ""
    echo "⏳ Workflow jest teraz w kolejce. Może potrwać kilka sekund zanim się uruchomi."
else
    echo "❌ Błąd podczas uruchamiania workflow (HTTP $HTTP_CODE)"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    exit 1
fi

