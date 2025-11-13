# Category Mapping Documentation

## 📋 Przegląd

System mapowania kategorii pozwala na grupowanie podkategorii w nadrzędne kategorie biznesowe, co umożliwia dokładniejsze liczenie produktów w głównych kategoriach bez konieczności scrapowania stron kategorii.

## 🎯 Cel

Na Framer Marketplace produkty są często tagowane bardziej szczegółowymi podkategoriami (np. "Education", "Wedding") zamiast bezpośrednio głównymi kategoriami (np. "Community"). System mapowania automatycznie rozszerza listę kategorii produktu o nadrzędne kategorie, zapewniając dokładne liczenie.

## 📊 Zmapowane Kategorie

### 1. Community (12 podkategorii)
- Education
- Social & Recreational
- Social
- Wedding
- Conference
- Environmental
- Non-profit
- Membership
- Political
- Church & Religious
- Religious
- Entertainment

**Przykład:** Produkt z kategorią "Education" jest automatycznie liczony również w kategorii "Community".

### 2. Business (11 podkategorii)
- Agency
- Consulting
- SaaS
- Startup
- Enterprise
- Ecommerce
- Finance
- Coaching
- Business Blog
- Professional Services
- Marketing

**Przykład:** Produkt z kategorią "Agency" jest automatycznie liczony również w kategorii "Business".

### 3. Portfolio (7 podkategorii)
- Personal
- Creative
- Artist
- Photography
- Fashion
- Personal Blog
- Arts & Crafts

**Przykład:** Produkt z kategorią "Photography" jest automatycznie liczony również w kategorii "Portfolio".

### 4. Real Estate (5 podkategorii)
- Realtor
- Property Management
- Construction
- Architecture
- Interior Design

### 5. Health (3 podkategorie)
- Fitness
- Medical
- Wellness

### 6. Food (4 podkategorie)
- Restaurant
- Bar & Club
- Catering
- Food & Restaurant

### 7. Technology (6 podkategorii)
- AI
- SaaS
- App
- Web3
- Digital Products
- Documentation

**Uwaga:** "SaaS" jest mapowane zarówno do "Business" jak i "Technology", ponieważ może należeć do obu kategorii.

### 8. Travel (1 podkategoria)
- Travel Blog

### 9. Blog (3 podkategorie)
- Business Blog
- Personal Blog
- Travel Blog

**Uwaga:** Blogi są mapowane zarówno do "Blog" jak i do odpowiednich kategorii biznesowych (Business, Portfolio, Travel).

### 10. Services (3 podkategorie)
- Professional Services
- Coaching
- Consulting

**Uwaga:** "Professional Services", "Coaching" i "Consulting" są mapowane zarówno do "Services" jak i "Business".

## 🔧 Implementacja

### Plik: `src/utils/category_mapping.py`

```python
from src.utils.category_mapping import expand_categories

# Przykład użycia
categories = ["Education", "Modern"]
expanded = expand_categories(categories)
# Zwraca: ["Education", "Modern", "Community"]
```

### Funkcje

- `expand_categories(categories: List[str]) -> List[str]` - Rozszerza listę kategorii o nadrzędne kategorie
- `get_parent_categories(category: str) -> List[str]` - Zwraca nadrzędne kategorie dla danej kategorii
- `get_subcategories(parent_category: str) -> List[str]` - Zwraca podkategorie dla danej nadrzędnej kategorii
- `has_category_mapping(category: str) -> bool` - Sprawdza czy kategoria ma mapowanie

## 📈 Statystyki

### Pokrycie kategorii
- **Wszystkich kategorii:** 106
- **Zmapowane:** 50 (47.2%)
- **Nie zmapowane:** 56 (52.8%)

### Pokrycie produktów
- **Produkty w zmapowanych kategoriach:** ~42.6%
- **Produkty w nie zmapowanych kategoriach:** ~57.4%

**Uwaga:** Nie zmapowane kategorie to głównie style/design (Modern, Minimal, Professional, Animated, Light, Dark, Colorful, Grid, etc.), które są atrybutami wizualnymi produktów, nie kategoriami biznesowymi. Te kategorie nie powinny być mapowane do głównych kategorii.

## 🔄 Użycie w API

Mapowanie jest automatycznie używane w następujących endpointach:

1. **`GET /api/products/categories/top-by-views`**
   - Zwraca top kategorie według views
   - Używa mapowania do dokładnego liczenia produktów

2. **`GET /api/products/categories/all-by-count`**
   - Zwraca wszystkie kategorie posortowane według liczby produktów
   - Używa mapowania do dokładnego liczenia produktów

### Przykład

Produkt z kategoriami: `["Education", "Modern"]`

Po mapowaniu: `["Education", "Modern", "Community"]`

W API:
- Produkt jest liczony w kategorii "Education" (1 produkt)
- Produkt jest liczony w kategorii "Modern" (1 produkt)
- Produkt jest liczony w kategorii "Community" (1 produkt dzięki mapowaniu)

## 📝 Dodawanie Nowych Mapowań

Aby dodać nowe mapowanie:

1. Otwórz `src/utils/category_mapping.py`
2. Dodaj nową kategorię nadrzędną do `CATEGORY_MAPPING`:

```python
CATEGORY_MAPPING: Dict[str, List[str]] = {
    # ... istniejące mapowania ...
    "New Parent Category": [
        "Subcategory 1",
        "Subcategory 2",
        "Subcategory 3",
    ],
}
```

3. System automatycznie zbuduje odwrotne mapowanie przy imporcie modułu
4. Zmiany będą automatycznie używane w API endpointach

## ⚠️ Uwagi

1. **Kategorie mogą mieć wiele nadrzędnych kategorii:** Na przykład "SaaS" jest mapowane zarówno do "Business" jak i "Technology".

2. **Style/Design nie są mapowane:** Kategorie takie jak "Modern", "Minimal", "Professional", "Animated", "Light", "Dark", "Colorful", "Grid" są atrybutami wizualnymi, nie kategoriami biznesowymi, więc nie są mapowane.

3. **Mapowanie jest jednokierunkowe:** Podkategorie są mapowane do nadrzędnych kategorii, ale nadrzędne kategorie nie są mapowane do podkategorii.

4. **Cache API:** Endpointy API mają cache 5 minut (TTL). Po dodaniu nowych mapowań może być konieczne odczekanie wygaśnięcia cache lub użycie parametru `_nocache`.

## 🧪 Testowanie

```bash
# Test lokalny
python3 -c "
from src.utils.category_mapping import expand_categories
print(expand_categories(['Education', 'Modern']))
# Oczekiwany wynik: ['Education', 'Modern', 'Community']
"

# Test na produkcji
curl "https://framer-marketplace-scraper-py-production.up.railway.app/api/products/categories/all-by-count?limit=50&product_type=template&_nocache=$(date +%s)"
```

## 📚 Powiązana Dokumentacja

- [API_ENDPOINTS_LIST.md](./API_ENDPOINTS_LIST.md) - Lista wszystkich endpointów API
- [API_CATEGORIES_VIEWS_EXAMPLES.md](./API_CATEGORIES_VIEWS_EXAMPLES.md) - Przykłady użycia endpointów kategorii

---

*Ostatnia aktualizacja: 2024-12-19*

