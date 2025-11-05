#!/bin/bash
# Script do monitorowania scrapera na żywo

echo "=== Monitorowanie Scrapera Framer Marketplace ==="
echo ""
echo "Wybierz opcję:"
echo "1. Wszystkie logi (na żywo)"
echo "2. Tylko scrapowanie produktów"
echo "3. Postęp i statystyki"
echo "4. Błędy i ostrzeżenia"
echo "5. Podsumowanie (ostatnie 100 linii)"
echo ""
read -p "Wybierz opcję (1-5): " choice

case $choice in
    1)
        echo "=== Wszystkie logi ==="
        tail -f logs/scraper.log
        ;;
    2)
        echo "=== Scrapowanie produktów ==="
        tail -f logs/scraper.log | grep --line-buffered 'product_scraped'
        ;;
    3)
        echo "=== Postęp i statystyki ==="
        tail -f logs/scraper.log | grep --line-buffered -E '(scraping_progress|batch_scrape_completed|product_urls_found|supplemented_with_fallback|marketplace_scraping_completed)'
        ;;
    4)
        echo "=== Błędy i ostrzeżenia ==="
        tail -f logs/scraper.log | grep --line-buffered -E '(error|failed|warning)' | grep -v 'HTTP Request'
        ;;
    5)
        echo "=== Podsumowanie (ostatnie 100 linii) ==="
        tail -100 logs/scraper.log | grep -E '(scraping_progress|batch_scrape_completed|product_urls_found|marketplace_scraping_completed|product_scraped)' | tail -20
        ;;
    *)
        echo "Nieprawidłowa opcja"
        exit 1
        ;;
esac

