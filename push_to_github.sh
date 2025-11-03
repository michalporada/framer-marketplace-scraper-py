#!/bin/bash

# Skrypt pomocniczy do wgrania repozytorium na GitHub
# Użycie: ./push_to_github.sh YOUR_USERNAME REPO_NAME

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Użycie: ./push_to_github.sh YOUR_USERNAME REPO_NAME"
    echo ""
    echo "Przykład: ./push_to_github.sh michalporada framer-marketplace-scraper"
    exit 1
fi

USERNAME=$1
REPO_NAME=$2

echo "🚀 Przygotowanie do wgrania na GitHub..."
echo ""

# Sprawdź czy remote już istnieje
if git remote | grep -q origin; then
    echo "⚠️  Remote 'origin' już istnieje. Usuwam..."
    git remote remove origin
fi

# Dodaj remote
echo "📡 Dodawanie remote repository..."
git remote add origin "https://github.com/${USERNAME}/${REPO_NAME}.git"

# Sprawdź branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "🔄 Zmienianie nazwy brancha na 'main'..."
    git branch -M main
fi

# Push
echo "⬆️  Wgrywanie kodu na GitHub..."
echo ""
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Sukces! Repozytorium zostało wgrane na GitHub."
    echo ""
    echo "🔗 Link: https://github.com/${USERNAME}/${REPO_NAME}"
    echo ""
    echo "📋 Następne kroki:"
    echo "1. Przejdź do https://github.com/${USERNAME}/${REPO_NAME}"
    echo "2. Kliknij zakładkę 'Actions'"
    echo "3. Włącz GitHub Actions jeśli zostaniesz o to poproszony"
    echo "4. Przeczytaj GITHUB_SETUP.md dla szczegółowych instrukcji"
else
    echo ""
    echo "❌ Błąd podczas wgrywania. Sprawdź:"
    echo "   - Czy repozytorium zostało utworzone na GitHub"
    echo "   - Czy masz uprawnienia do push"
    echo "   - Czy używasz poprawnej nazwy użytkownika i repozytorium"
fi

