# Dziennik Osobisty

Aplikacja webowa do zarządzania zdrowiem i formą fizyczną. Aplikacja pozwala na śledzenie aktywności sportowej, żywienia oraz danych osobistych z wizualizacją na wykresach.

## Funkcje

### Dziennik Sportowy
- Rejestrowanie treningów z datą i czasem trwania
- Dodawanie zdjęć z treningów
- Opis aktywności i notatki
- Przeglądanie historii treningów

### Dziennik Żywieniowy
- Zapisywanie posiłków według typu (śniadanie, obiad, kolacja, przekąska)
- Monitorowanie kalorii i spożycia wody
- Szczegółowe informacje o ilości porcji
- Notatki dotyczące posiłków

### Dane Osobiste
- Śledzenie wagi, wzrostu i BMI
- Monitorowanie tkanki tłuszczowej i masy mięśniowej
- Interaktywne wykresy zmian w czasie
- Automatyczne obliczanie BMI z kategoryzacją

### Kalendarz
- Miesięczny widok aktywności
- Wizualizacja dni z treningami
- Szybki dostęp do dodawania wpisów
- Podsumowania miesięczne

<img width="1470" height="834" alt="Zrzut ekranu 2025-08-7 o 16 34 50" src="https://github.com/user-attachments/assets/36dd0e12-60fc-42e6-926e-185a5ddfcd11" />
<img width="1470" height="956" alt="Zrzut ekranu 2025-08-7 o 16 35 02" src="https://github.com/user-attachments/assets/bc983b14-1ad4-45e2-b70b-461be09dc031" />
<img width="1470" height="956" alt="Zrzut ekranu 2025-08-7 o 16 35 16" src="https://github.com/user-attachments/assets/b6f98023-27e2-45ec-bf71-f5b1f350fc30" />
<img width="1470" height="956" alt="Zrzut ekranu 2025-08-7 o 16 35 23" src="https://github.com/user-attachments/assets/05202ddc-d6d0-4d16-ace9-d<img width="1470" height="956" alt="Zrzut ekranu 2025-08-7 o 16 35 29" src="https://github.com/user-attachments/assets/f5538817-8eed-4969-8669-56db7da8a946" />
93ccb685edf" />
<img width="1470" height="956" alt="Zrzut ekranu 2025-08-7 o 16 35 35" src="https://github.com/user-attachments/assets/307984ad-aadf-4cb8-bc7b-eb949da8d79c" />
<img width="1470" height="956" alt="Zrzut ekranu 2025-08-7 o 16 35 42" src="https://github.com/user-attachments/assets/ff580cd6-1762-4ce9-87e8-4a1b5f38b1dd" />


## Technologie

- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Wykresy**: Plotly.js
- **Upload zdjęć**: Werkzeug
- **Icons**: Font Awesome

## Instalacja

### Wymagania
- Python 3.7+
- pip

### Kroki instalacji

1. **Sklonuj lub pobierz projekt**
```bash
cd dziennikkal
```

2. **Zainstaluj wymagane pakiety**
```bash
pip install -r requirements.txt
```

3. **Uruchom aplikację**
```bash
python app.py
```

4. **Otwórz przeglądarkę**
```
http://127.0.0.1:5000
```

## Użytkowanie

### Pierwszy start
1. Aplikacja automatycznie utworzy bazę danych SQLite
2. Przejdź na stronę główną aby zapoznać się z funkcjami
3. Rozpocznij od dodania swojego pierwszego treningu lub pomiaru

### Dodawanie treningów
1. Kliknij "Sport" w menu
2. Wybierz "Dodaj Trening"
3. Wypełnij formularz (data, aktywność, czas)
4. Opcjonalnie dodaj zdjęcie i notatki
5. Zapisz

### Monitorowanie żywienia
1. Kliknij "Żywienie" w menu
2. Wybierz "Dodaj Posiłek"
3. Wybierz typ posiłku i opisz co jadłeś
4. Podaj kalorie i ilość wody
5. Zapisz

### Śledzenie danych osobistych
1. Kliknij "Dane Osobiste" w menu
2. Wybierz "Dodaj Pomiar"
3. Wprowadź wagę, wzrost i inne parametry
4. Kalkulator BMI policzy automatycznie
5. Zapisz aby zobaczyć na wykresach

### Przeglądanie kalendarza
1. Kliknij "Kalendarz" w menu
2. Zobacz swoje aktywności w widoku miesięcznym
3. Kliknij na dzień aby zobaczyć szczegóły

## Struktura plików

```
dziennikkal/
├── app.py                 # Główna aplikacja Flask
├── requirements.txt       # Zależności Python
├── dziennik.db           # Baza danych SQLite (tworzona automatycznie)
├── static/
│   ├── css/
│   │   └── style.css     # Style CSS
│   ├── js/               # JavaScript (jeśli potrzebny)
│   └── uploads/          # Folder na zdjęcia
├── templates/
│   ├── base.html         # Szablon bazowy
│   ├── index.html        # Strona główna
│   ├── sport.html        # Lista treningów
│   ├── add_sport.html    # Formularz dodawania treningu
│   ├── nutrition.html    # Lista posiłków
│   ├── add_nutrition.html # Formularz dodawania posiłku
│   ├── personal.html     # Dane osobiste z wykresami
│   ├── add_personal.html # Formularz danych osobistych
│   └── calendar.html     # Widok kalendarza
└── README.md             # Ten plik
```

## Funkcje szczegółowe

### Upload zdjęć
- Obsługiwane formaty: JPG, PNG, GIF
- Maksymalny rozmiar: 16MB
- Automatyczne zabezpieczanie nazw plików
- Podgląd w galerii treningów

### Wykresy i statystyki
- Wykres zmian wagi w czasie
- Wykres BMI z liniami referencyjnymi
- Kategoryzacja BMI (niedowaga, norma, nadwaga, otyłość)
- Automatyczne obliczenia

### Responsywność
- Aplikacja działa na telefonach, tabletach i komputerach
- Bootstrap 5 zapewnia nowoczesny wygląd
- Intuicyjna nawigacja

## Bezpieczeństwo

- Walidacja wszystkich danych wejściowych
- Zabezpieczenie nazw plików przy upload
- Ograniczenie rozmiaru uploadowanych plików
- Filtrowanie typów plików


## Autor

Projekt utworzony dla użytku osobistego. Możesz modyfikować i dostosowywać według potrzeb. Franciszek Łasiński projekt wykonany z pomocą github copilot
