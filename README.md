# AI Call Agent - Asterisk ARI Outbound Campaign System

Ein intelligenter AI-Agent für automatisierte Outbound-Anrufe mit Asterisk ARI, OpenAI, Faster Whisper und Coqui TTS für Lead-Generierung und Terminvereinbarung im Fund Recovery Service.

## Features

- **Asterisk ARI Integration**: Vollständige Integration mit Asterisk 20.15.2 über ARI
- **AI-gesteuerte Gespräche**: Natürliche Konversationen mit OpenAI GPT-4
- **Speech-to-Text**: Echtzeit-Spracherkennung mit Faster Whisper
- **Text-to-Speech**: Hochwertige deutsche Sprachsynthese mit Coqui TTS
- **Kampagnenmanagement**: Verwaltung von Outbound-Kampagnen mit mehreren gleichzeitigen Anrufen
- **Lead-Tracking**: Vollständige Datenbank für Leads, Anrufe und Termine
- **Terminvereinbarung**: Automatische Terminplanung während des Gesprächs

## Systemanforderungen

- Ubuntu 22.04 LTS (oder ähnlich)
- Python 3.8 oder höher
- Asterisk 20.15.2 mit ARI aktiviert
- MySQL/MariaDB
- Mindestens 4GB RAM (8GB empfohlen für TTS/STT Modelle)

## Installation

### 1. Repository klonen

```bash
git clone https://github.com/berndmarcel860-byte/Agcai.git
cd Agcai
```

### 2. Setup ausführen

```bash
chmod +x setup.sh
./setup.sh
```

### 3. Konfiguration

Bearbeiten Sie die `.env` Datei mit Ihren Daten:

```bash
nano .env
```

Wichtige Einstellungen:
- `DB_*`: MySQL Datenbankzugangsdaten
- `ARI_*`: Asterisk ARI Verbindungsdaten
- `OPENAI_API_KEY`: Ihr OpenAI API Schlüssel
- `OUTBOUND_CALLER_ID`: Ihre Rufnummer für ausgehende Anrufe

### 4. Asterisk Konfiguration

Stellen Sie sicher, dass ARI in Asterisk aktiviert ist:

**ari.conf:**
```ini
[general]
enabled = yes
pretty = yes

[ai_agent]
type = user
read_only = no
password = ai_agent_secure_password_123
```

**http.conf:**
```ini
[general]
enabled = yes
bindaddr = 127.0.0.1
bindport = 8088
```

**pjsip.conf** - Fügen Sie Ihre SIP-Trunk-Konfiguration hinzu für ausgehende Anrufe.

### 5. Datenbank initialisieren

```bash
source venv/bin/activate
python main.py --init-db
```

## Verwendung

### Kampagne starten

```bash
# Mit Leads aus CSV-Datei
python main.py --campaign "Fund Recovery Campaign" --leads example_leads.csv

# Nur mit vorhandenen Leads in der Datenbank
python main.py --campaign "Fund Recovery Campaign"
```

### Leads-CSV Format

```csv
phone_number,first_name,last_name,email,company
+491234567890,Max,Mustermann,max@example.com,Example GmbH
```

## Architektur

```
┌─────────────────┐
│   Main App      │
│   (main.py)     │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┬──────────┐
    │         │          │          │          │
┌───▼───┐ ┌──▼──┐   ┌──▼──┐   ┌───▼───┐  ┌──▼──┐
│  ARI  │ │ AI  │   │ TTS │   │  STT  │  │ DB  │
│Client │ │Conv.│   │Coqui│   │Whisper│  │MySQL│
└───────┘ └─────┘   └─────┘   └───────┘  └─────┘
```

### Komponenten

- **ARI Client** (`src/ari/`): Asterisk REST Interface Verbindung
- **AI Conversation** (`src/ai/`): OpenAI GPT-4 Integration
- **TTS** (`src/tts/`): Coqui Text-to-Speech
- **STT** (`src/stt/`): Faster Whisper Speech-to-Text
- **Database** (`src/database/`): SQLAlchemy ORM mit MySQL
- **Campaign Manager** (`src/campaign/`): Kampagnen- und Anrufverwaltung

## Datenbankschema

- **leads**: Kontaktinformationen und Status
- **campaigns**: Kampagnenverwaltung
- **call_records**: Anrufprotokolle
- **conversation_logs**: Gesprächsverlauf
- **appointments**: Vereinbarte Termine

## Gesprächsablauf

1. System ruft Lead an
2. Bei Annahme: AI-Agent begrüßt Angerufenen
3. Agent qualifiziert Lead (Betrugsopfer?)
4. Agent erklärt Fund Recovery Service
5. Agent vereinbart Beratungstermin
6. System speichert alle Informationen in DB

## Konfigurationsoptionen

### Kampagneneinstellungen

- `MAX_CONCURRENT_CALLS`: Maximale gleichzeitige Anrufe (Standard: 5)
- `CALL_TIMEOUT`: Timeout für Anrufe in Sekunden (Standard: 300)

### AI-Einstellungen

- `OPENAI_MODEL`: GPT Modell (Standard: gpt-4-turbo-preview)
- `WHISPER_MODEL`: Whisper Modellgröße (tiny/base/small/medium/large)
- `TTS_MODEL`: Coqui TTS Modell

## Monitoring und Logs

Logs werden gespeichert in:
- `logs/aiagent.log`: Hauptanwendungslog
- Console: Farbige Echtzeitausgabe

## Troubleshooting

### ARI Verbindungsfehler

```bash
# Prüfen Sie ob Asterisk läuft
systemctl status asterisk

# ARI Konfiguration testen
curl -u ai_agent:password http://127.0.0.1:8088/ari/asterisk/info
```

### Datenbankfehler

```bash
# MySQL Status prüfen
systemctl status mysql

# Datenbankverbindung testen
mysql -h 127.0.0.1 -u aiagent -p ai_calls
```

### TTS/STT Modelle

Beim ersten Start werden die Modelle automatisch heruntergeladen. Dies kann einige Minuten dauern.

## Sicherheit

- ⚠️ Verwenden Sie **niemals** die Beispielpasswörter in Produktion
- Ändern Sie alle Passwörter in `.env`
- Begrenzen Sie ARI Zugriff auf localhost
- Verwenden Sie SSL/TLS für Produktionsumgebungen
- Speichern Sie niemals Kreditkartendaten oder ähnliche sensible Daten

## Lizenz

MIT License

## Support

Bei Fragen oder Problemen erstellen Sie bitte ein Issue im GitHub Repository.

## Entwicklung

### Tests ausführen

```bash
# Unit Tests
pytest tests/

# Mit Coverage
pytest --cov=src tests/
```

### Code-Stil

```bash
# Linting
pylint src/

# Formatierung
black src/
```

## Roadmap

- [ ] Web-Dashboard für Kampagnenüberwachung
- [ ] Multi-Sprachen Support
- [ ] SMS-Integration für Terminerinnerungen
- [ ] CRM-Integration (Salesforce, HubSpot)
- [ ] A/B Testing für Gesprächsskripte
- [ ] Echtzeit-Analytics Dashboard

## Mitwirken

Pull Requests sind willkommen! Für größere Änderungen öffnen Sie bitte zuerst ein Issue.

## Autoren

- Bernd Marcel

## Danksagungen

- Asterisk Project
- OpenAI
- Coqui AI
- Faster Whisper