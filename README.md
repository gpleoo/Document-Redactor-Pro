# AI Document Redactor Pro

Applicazione desktop professionale per l'oscuramento automatico e manuale di dati sensibili in documenti PDF e immagini. Funziona **100% offline** - nessun dato lascia mai il dispositivo.

## Funzionalità

- **Rilevamento IA**: OCR (Tesseract) + NER (spaCy/Presidio) per riconoscimento automatico di dati sensibili
- **Sanificazione reale**: Rimozione dal flusso di testo del PDF + flattening del layer (non semplice overlay)
- **Preset di oscuramento**: Codici Fiscali, IBAN, SSN, nomi, email, telefono, carte di credito, firme
- **Anteprima interattiva**: Click sulle parole per oscurare/deoscurare manualmente
- **Multilingua**: Supporto IT, EN, DE, FR, ES con pattern regex e modelli NER localizzati
- **Integrità file**: Il file originale non viene mai modificato
- **Dark Mode**: Interfaccia professionale con accenti blu cobalto

## Architettura

```
src/
├── core/
│   ├── ocr_engine.py      # Estrazione testo (Tesseract + PyMuPDF nativo)
│   ├── ner_engine.py       # Riconoscimento entità (spaCy + Presidio + Regex)
│   ├── pdf_processor.py    # Redazione reale + flattening PDF
│   └── file_manager.py     # Gestione file e copie temporanee
├── gui/
│   ├── main_window.py      # Finestra principale
│   ├── theme.py            # Dark theme con accenti blu cobalto
│   ├── sidebar.py          # Pannello laterale preset e controlli
│   ├── preview_widget.py   # Anteprima interattiva con click-to-redact
│   └── drop_zone.py        # Area drag & drop
├── utils/
│   ├── i18n.py             # Sistema internazionalizzazione
│   └── config.py           # Configurazione persistente
└── main.py                 # Entry point
```

## Installazione

```bash
pip install -r requirements.txt
python -m spacy download it_core_news_sm
python -m spacy download en_core_web_sm
```

## Avvio

```bash
cd src
python main.py
```

## Requisiti di Sistema

- Python >= 3.10
- Tesseract OCR installato sul sistema
- PyQt6 per l'interfaccia grafica

## Target

Progettato per studi legali, uffici HR e professionisti che necessitano di oscuramento documenti conforme alla normativa privacy (GDPR).
