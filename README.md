# 📬 Zulip Reader

Zulip Reader je nástroj pro stahování zpráv ze serveru [Zulip](https://zulip.com) a jejich uložení do čitelných souborů (TXT nebo CSV). Využívá oficiální Zulip Python klient a umožňuje snadné filtrování zpráv podle tématu nebo stavu přečtení.

---

## 🚀 Funkce

- Připojení k libovolnému Zulip serveru pomocí API klíče
- Načtení nepřečtených zpráv nebo zpráv podle tématu a streamu
- Uložení výstupu do souboru:
  - CSV (pro tabulkový formát)
  - TXT (přehledný lidsky čitelný formát)
- Odstranění HTML tagů z obsahu
- CLI rozhraní pomocí `click` (volitelné)

---

## 🧰 Instalace

```bash
git clone https://github.com/uzivatel/zulip-reader.git
cd zulip-reader
poetry install
````

> 📝 Pokud Poetry vypíše chybu kvůli `README.md`, ujisti se, že tento soubor existuje.

---

## 🛠 Použití

### Pomocí CLI (`cli.py`):

```bash
python cli.py --email "tvůj@email.cz" --api-key "tvůj_api_klíč" --site "https://zulip.example.com" --stream "Název kanálu" --topic "Název tématu" --output vystup.txt --format txt
```

### Přepínače:

| Argument   | Popis                      |
| ---------- | -------------------------- |
| `--unread` | Stáhne nepřečtené zprávy   |
| `--stream` | Název streamu (kanálu)     |
| `--topic`  | Název tématu (vlákna)      |
| `--output` | Cesta k výstupnímu souboru |
| `--format` | `txt` nebo `csv`           |

---

## ✅ Příklad

```bash
python cli.py --email "user@example.com" \
              --api-key "abcd1234" \
              --site "https://zulip.example.com" \
              --stream "General" \
              --topic "Development" \
              --output messages.csv \
              --format csv
```

---

## 📦 Závislosti

* Python ≥ 3.12
* [zulip](https://pypi.org/project/zulip/)
* [arrow](https://pypi.org/project/arrow/)
* [click](https://pypi.org/project/click/) (pokud používáš CLI)

Instalují se automaticky pomocí:

```bash
poetry install
```

---

## 📄 Licence

MIT License – používej svobodně.


