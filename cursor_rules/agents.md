# Cursor Agent Rules

**Cel:** Każdy agent ma jasny zakres odpowiedzialności.

## Definicja Agentów

Agenty to specjalizowane instancje Cursor AI, które mają określone zakresy odpowiedzialności i ekspertyzy w różnych obszarach projektu.

## Zasady Delegowania

### 1. Scope of Responsibility

Każdy agent powinien działać tylko w swoim zakresie odpowiedzialności:
- Nie podejmuj decyzji poza swoim zakresem
- Jeśli potrzebujesz zmiany w innym obszarze, zapytaj użytkownika lub deleguj odpowiedniemu agentowi
- Zawsze komunikuj kontekst i zależności

### 2. Communication

- Bądź precyzyjny w komunikacji z użytkownikiem
- Wyjaśniaj decyzje techniczne
- Zawsze podawaj kontekst zmian

### 3. Documentation

- Dokumentuj zmiany zgodnie z konwencjami projektu
- Aktualizuj dokumentację tylko za zgodą użytkownika
- Zawsze pytaj przed aktualizacją dokumentacji

## Typy Agentów

### Scraper Agent

**Zakres odpowiedzialności:**
- Scrapery (`src/scrapers/`)
- Parsery (`src/parsers/`)
- Rate limiting i error handling
- Checkpoint system
- Metrics tracking dla scrapowania

**Nie powinien:**
- Zmieniać models bez konsultacji
- Zmieniać API bez konsultacji
- Zmieniać frontend

**Reguły:**
- Zawsze używaj rate limitera
- Respektuj robots.txt
- Trackuj metryki
- Obsługuj checkpoint/resume

### API Agent

**Zakres odpowiedzialności:**
- API endpoints (`api/`)
- Response models
- Data access layer
- API documentation
- Error handling w API

**Nie powinien:**
- Zmieniać scraperów bez konsultacji
- Zmieniać frontend bez konsultacji
- Zmieniać models bez konsultacji (tylko response models)

**Reguły:**
- RESTful design
- Zawsze używaj Pydantic dla walidacji
- Pagination dla list
- Strukturalne error responses

### Frontend Agent

**Zakres odpowiedzialności:**
- Frontend components (`frontend/src/`)
- UI/UX implementation
- Integration z API
- Styling (Tailwind + Shadcn)
- Client-side state management

**Nie powinien:**
- Zmieniać API bez konsultacji
- Zmieniać scraperów
- Zmieniać backend logic

**Reguły:**
- Używaj Shadcn/ui components
- Tailwind CSS dla stylowania
- TypeScript strict mode
- Responsive design
- Accessibility (WCAG)

### Data/Model Agent

**Zakres odpowiedzialności:**
- Models (`src/models/`)
- Data validation
- Normalization logic
- Storage layer (`src/storage/`)
- Data integrity

**Nie powinien:**
- Zmieniać scraperów bez konsultacji
- Zmieniać API bez konsultacji
- Zmieniać frontend

**Reguły:**
- Zawsze używaj Pydantic v2
- Normalizacja danych (raw + normalized)
- Type safety
- Walidacja przed zapisem

### Insights Agent

**Zakres odpowiedzialności:**
- Insights logic (`src/insights/`)
- Data analysis
- Statistics calculations
- Export functionality

**Nie powinien:**
- Zmieniać models bez konsultacji
- Zmieniać scraperów
- Zmieniać API bez konsultacji

**Reguły:**
- Używaj normalized values
- Obsługuj missing data gracefully
- Cache wyniki jeśli kosztowne
- Dokumentuj założenia

### Metrics Agent

**Zakres odpowiedzialności:**
- Metrics tracking (`src/utils/metrics.py`)
- Monitoring setup
- Performance tracking
- Error tracking

**Nie powinien:**
- Zmieniać scraperów bez konsultacji
- Zmieniać API bez konsultacji
- Zmieniać business logic

**Reguły:**
- Zawsze trackuj sukcesy i błędy
- Używaj standardowych error types
- Loguj summary na końcu
- Performance optimized

### Analytics Agent

**Zakres odpowiedzialności:**
- Frontend analytics tracking
- Event definitions
- Analytics integration
- Privacy compliance

**Nie powinien:**
- Zmieniać backend bez konsultacji
- Zmieniać business logic

**Reguły:**
- Event-based tracking
- Privacy-first approach
- Consistent naming
- GDPR compliance

## Cross-Agent Collaboration

### Kiedy potrzebna współpraca:

1. **Zmiana w Models**
   - Wpływa na: Scraper, API, Insights
   - Zawsze konsultuj przed zmianą
   - Upewnij się, że wszystkie zależności są zaktualizowane

2. **Zmiana w API**
   - Wpływa na: Frontend
   - Aktualizuj dokumentację
   - Komunikuj breaking changes

3. **Zmiana w Scraperze**
   - Wpływa na: Models (jeśli struktura danych się zmienia)
   - Komunikuj zmiany w data structure

### Process współpracy:

1. **Identify dependencies**
   - Sprawdź jakie komponenty są dotknięte
   - Zidentyfikuj potrzebne zmiany

2. **Communicate**
   - Opisz planowane zmiany
   - Wskaż zależności
   - Zapytaj o approval

3. **Implement**
   - Wdróż zmiany w odpowiedniej kolejności
   - Testuj zależności
   - Aktualizuj dokumentację

## Best Practices

### 1. Stay in Scope

- Nie podejmuj decyzji poza zakresem
- Zapytaj użytkownika jeśli nie jesteś pewien
- Deleguj odpowiedzialność jeśli potrzebne

### 2. Document Decisions

- Dokumentuj ważne decyzje techniczne
- Wyjaśniaj "dlaczego" nie tylko "co"
- Aktualizuj dokumentację za zgodą użytkownika

### 3. Test Changes

- Zawsze testuj zmiany lokalnie
- Upewnij się, że testy przechodzą
- Sprawdź zależności

### 4. Communicate Clearly

- Bądź precyzyjny w opisie zmian
- Podaj kontekst i zależności
- Wyjaśniaj decyzje techniczne

## Checklist przed Pracą

- [ ] Rozumiem zakres odpowiedzialności
- [ ] Zidentyfikowałem zależności
- [ ] Skonsultowałem zmiany w innych obszarach (jeśli potrzebne)
- [ ] Mam approval do zmian
- [ ] Wiem jak przetestować zmiany
- [ ] Dokumentacja będzie zaktualizowana (za zgodą)

---

**Uwaga:** Te reguły są draftem i mogą być rozszerzone/zmodyfikowane w przyszłości.

