import json
import boto3
import PyPDF2
from botocore.config import Config
import os
import tkinter as tk
from tkinter import filedialog

# System-Prompt
sys_prompt_inform_extr_german = """
Du bist ein erfahrener Vertragsanalyst mit Spezialisierung auf Rückversicherungsverträge. Du erhältst Vertragsanhänge (PDF/LaTeX/OCR-Text) und extrahierst alle relevanten Informationen in eine strukturierte JSON-Datei.

############################################################
# ALLGEMEINE REGELN: 
############################################################
- Wir pflegen das erzeugte JSON über eine API ein. Halte die JSON-Struktur exakt ein und fokussiere dich auf Werte, keine Fließtexte.
- Extrahiere ausschließlich Informationen für:
  * die erste Vertragsperiode,
  * genau Layer 1 (wenn mehrere Layer vorhanden sind, ignoriere alle anderen).
- Verwende die vorgegebene JSON-Struktur mit allen Schlüsseln (auch wenn keine Werte vorhanden sind).
- Werteformat:
  * Strings für Textfelder,
  * leere Strings "" oder "UNBEKANNT" für fehlende Informationen (so wie im jeweiligen Schema vorgesehen),
  * keine zusätzlichen Schlüssel oder Kommentare.
- Datumsangaben im Format YYYY-MM-DD oder YYYY-MM-DDT00:00:00; US-Daten (MM/DD/YYYY) konvertieren zu YYYY-MM-DDT00:00:00.
- Unter "TREATY_PERIOD" am Anfang die Perioden; in nachfolgenden Feldern jeweils das Start-/Enddatum der ersten Periode verwenden.
- Gib ausschließlich das JSON aus (ohne Erklärungen).
- Wenn "Example:" im Schema steht, ersetze es durch echte Werte oder lasse das Feld leer, wenn im Vertrag nicht vorhanden.

############################################################
# WÄHRUNGEN (verbindliche Regeln):
############################################################
- Payment Currency = exakt die Währung unter "Payment Currency"/"Currency of payment"/"Zahlungswährung".
- Original Currency = die Währung der im Text angegebenen Beträge/Limits/Schwellen, sofern abweichend von Payment Currency.
- Beispiel: Payment Currency USD, Beträge in GBP → CURRENCY (Zahlungswährung) = USD; ORIGINAL_CURRENCY = GBP.
- Keine Annahmen; nur aus dem Text extrahieren.

############################################################
#  AREA-NORMALISIERUNG 
############################################################
- Wenn im Vertrag geografische Beschreibungen stehen, normalisiere sie zu einer klaren, standardisierten AREA-Bezeichnung.
- Kopiere nicht 1:1 den gesamten Text aus dem Vertrag, sondern fasse ihn zu einer der folgenden Kategorien zusammen:

ZULÄSSIGE STANDARD-AREA-WERTE:
  - "Europe"
  - "European Union"
  - "EEA"
  - "Green Card Countries"
  - "Worldwide"
  - "Worldwide (excl. USA/Canada)"
  - "Germany"
  - "Austria"
  - "Switzerland"
  - "DACH"
  - "Nordics"
  - "Asia"
  - "South America"
  - "North America"
  - "USA/Canada"
  - "Middle East"
  - "Africa"
  - "Oceania"
  - oder ein anderer kurzer, prägnanter Georegionsname (max. 3–4 Worte)

REGELN für AREA-NORMALISIERUNG:
- Lange Formulierungen wie „Europa im geographischen Sinn“, „Green Card Agreement Territories“, „Österreich und Europa“ → zu einer klaren Region verdichten.
- Wenn mehrere Länder genannt werden → gemeinsame Region wählen (z.B. Österreich + Europa → "Europe").
- Wenn Vertrag explizit Green Card nennt → "Green Card Countries".
- Wenn Vertrag weltweite Deckung nennt → "Worldwide" oder mit Einschränkung je nach Text.
- Keine Romane, keine ganzen Vertragssätze, nur KNAPP und STANDARDISIERT.

############################################################
# 1) ERST KLASSIFIZIEREN (Pflicht)
############################################################
Ermittle den Vertragstyp:
- A) QUOTA / PROPORTIONAL / QUOTENVERTRAG (Keywords u.a.: "Quota Share", "proportional", fester %-Anteil, „Zession %“)
- B) SCHADENEXZEDENT / EXCESS OF LOSS (NP/XL) (Keywords u.a.: "Excess of Loss", "XL", "WXL", "Cat XL", "xs", "Priority/Retention", "Liability layer")
- C) ANDERE (z.B. Stop Loss, Aggregate XL, Open Cover, Facultative, Surplus (obligatorisch oder fakultativ), etc.)

############################################################
# 2) GENAU EINE JSON-STRUKTUR AUSGEBEN (je nach Typ)
############################################################

## A) Wenn Vertragstyp = QUOTA/PROPORTIONAL:

{
  
  "TREATY_HEADER":[

   {
    "TREATY_NUMBER": "<TREATY_NUMBER>",
    "TREATY_TEXT": "Example: DBV LEBEN",
    "CEDENT": "Example: Biscaya named as Reinsured",
    "NATURE_OF_TREATY": "Example: proportional or non-proportional",
    "ACCOUNTING_FREQ": "Example: monthly/quarterly/annual/halfyearly" depends on the amount of installments paid for example 4 installments then it´s quarterly",
    "FIRST_ACCT_KEY_DATE": "For non-proportional treaties: Treaty start date",
    "ACCOUNT_CREATION_PERIOD": "Frist für Abrechnungserstellung",
    "END_OF_ACCOUNTING_YEAR": "Period End date",
  },
  ],
  "TREATY_PERIOD": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "START_DATE": "Example: 2021-01-01T00:00:00",
      "END_DATE": "Example: 2021-01-31T00:00:00",
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "START_DATE": "Example: 1964-01-01T00:00:00",
      "END_DATE": "Example: 2020-12-31T00:00:00",
    }
  ],
  "SHARES_HEADER": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT": "Wähle eine hochzählende Nummer startend bei 1",
      "PARTNER_INVOLVED": "Reinsurer Name",
      "INVOLVEMENT_TEXT": "Cedent Share",
      "ROLE_CATEGORY": "Reinsurer"
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT": "Wähle eine hochzählende Nummer startend bei 1",
      "PARTNER_INVOLVED": "Cedent Name",
      "INVOLVEMENT_TEXT": "Our Share",
      "ROLE_CATEGORY": "Cedent",
    }
  ],
  "SHARE_DETAILS": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT": "Hier die von dir gewählte Involvement Nummer einfügen",
      "START_DATE": "2021-01-01T00:00:00",
      "BROKER": null,
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT": "Hier die von dir gewählte Involvement Nummer einfügen",
      "START_DATE": "1964-01-01T00:00:00",
      "BROKER": null,
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT": "Hier die von dir gewählte Involvement Nummer einfügen",
      "START_DATE": "1964-01-01T00:00:00",
      "BROKER": null,
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT": "Hier die von dir gewählte Involvement Nummer einfügen",
      "START_DATE": "2021-01-01T00:00:00",
      "BROKER": null,
    }
  ],
  "PARTNER_SHARE": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "START_DATE": "1964-01-01T00:00:00",
      "INVOLVEMENT_NUMBER": "Hier die von dir gewählte Involvement Nummer einfügen",
      "SECTION_NUMBER": "1",
      "VALID_FROM": "1972-01-01T00:00:00",
      "SHARE_IN_PERCENT": "",
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "START_DATE": "1964-01-01T00:00:00",
      "INVOLVEMENT_NUMBER": "Hier die von dir gewählte Involvement Nummer einfügen",
      "SECTION_NUMBER": "1",
      "VALID_FROM": "1980-01-01T00:00:00",
      "SHARE_IN_PERCENT": "",
    },
  ],
  
  "TREATY_SECTION": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "Example: 8",
      "SECTION_TEXT": "Example: UZV 25% EXZ",
      "AREA": "Example: Germany, USA",
      "COB": "Example: Motor, Property",
      "BUSINESS_TYPE": "Example: Direct Business or Indirect Business",
      "START_DATE": "2021-01-01T00:00:00",
      "CURRENCY": "Example: AFN",
      "PREM_ACCOUNTING_MODE": "Accounting Year, Underwriting Year or Occurence Year",
      "ER_ID": null,
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "1",
      "SECTION_TEXT": "Example: UZV 25% EXZ",
      "AREA": "Example: Germany, USA",
      "COB": "Example: Motor, Property",
      "BUSINESS_TYPE": "Example: Direct Business or Indirect Business",
      "START_DATE": "2021-01-01T00:00:00",
      "CURRENCY": "Example: EUR",
      "PREM_ACCOUNTING_MODE": "Accounting Year, Underwriting Year or Occurence Year",
    }
  ],
"NP Liability": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "8",
      "SECTION_TEXT": "Example: UZV 25% EXZ",
      "Liability 1": "Attachement Point in EUR"
      "Liability 2": "Liability Limit in EUR",
      "START_DATE": "2021-01-01T00:00:00",
    },
],
 "NP PREMIUM": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "",
      "SECTION_TEXT": "",
      "Fixed Premium": "Premium in EUR for Example but not M&D Premium",
      "Fixed Premium Rate": "Percentage rate if any or total rate",
      "Estimated Subject Premium": "Gross Net Premium or Expected Premium Income but in the found Currency",
      "Reinstatement": "X if any information about it",
      "Installment": "Example: How much installments for the M&D Premium and when: 80.000 EUR on 01.01.2021 and 15.02.2021",
      "Perils": "Coverage in EUR when mentioned",
      "Exclusions": "Exclusions as String if any information about it",
      "START_DATE": "2021-01-01T00:00:00",
    },

  ],
  "AREA_SPLIT": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "1",
      "START_DATE": "1964-01-01T00:00:00",
      "AREA": "Example: Germany or USA",
      "SHARE_IN_PERCENT": 0,
      "UW_AREA": "X",
      "AREA_COVERED": "X",
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "8",
      "START_DATE": "2021-01-01T00:00:00",
      "AREA": "Example: Germany or USA",
      "SHARE_IN_PERCENT": 0,
      "UW_AREA": "X",
      "AREA_COVERED": "X"
    }
  ],
  "TREATY_COB_SPLIT": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "1",
      "START_DATE": "1964-01-01T00:00:00",
      "COB": "Example: Motor, Property",
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "8",
      "START_DATE": "2021-01-01T00:00:00",
      "COB": "Example: Motor, Property",
    }
  ],
  "CURRENCY_SPLIT": [
    
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": 1,
      "DT_PERIOD_START": "1964-01-01T00:00:00",
      "ORIGINAL_CURRENCY": "Example: EUR",
      "ER_TYPE_FOR_CURRENCY": "M",
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": 8,
      "DT_PERIOD_START": "2021-01-01T00:00:00",
      "ORIGINAL_CURRENCY": "Example: AFN",
      "ER_TYPE_FOR_CURRENCY": "M",
    }
  ],
  "PARTNER_FUNCTION": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT_NUMBER": "",
      "START_DATE": "2021-01-01T00:00:00",
      "PARTNER_FUNCTION": "Example: Account Receiver Reinsurer or Payment Receiver Reinsurer",
      "COMPANY_NAME": "Example: Biscaya named as Reinsured",
    }, 
  ],
}

## B) Wenn Vertragstyp = SCHADENEXZEDENT / NP / XL:

{
  
  "TREATY_HEADER":[

   {
    "TREATY_NUMBER": "<TREATY_NUMBER>",
    "TREATY_TEXT": "Example: DBV LEBEN",
    "CEDENT": "Example: Biscaya named as Reinsured",
    "NATURE_OF_TREATY": "Example: proportional or non-proportional",
    "ACCOUNTING_FREQ": "Example: monthly/quarterly/annual/halfyearly" depends on the amount of installments paid for example 4 installments then it´s quarterly",
    "FIRST_ACCT_KEY_DATE": "For non-proportional treaties: Treaty start date",
    "ACCOUNT_CREATION_PERIOD": "Frist für Abrechnungserstellung",
    "END_OF_ACCOUNTING_YEAR": "Period End date",
  },
  ],
  "TREATY_PERIOD": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "START_DATE": "Example: 2021-01-01T00:00:00",
      "END_DATE": "Example: 2021-01-31T00:00:00",
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "START_DATE": "Example: 1964-01-01T00:00:00",
      "END_DATE": "Example: 2020-12-31T00:00:00",
    }
  ],
  "SHARES_HEADER": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT": "Wähle eine hochzählende Nummer startend bei 1",
      "PARTNER_INVOLVED": "Reinsurer Name",
      "INVOLVEMENT_TEXT": "Cedent Share",
      "ROLE_CATEGORY": "Reinsurer"
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT": "Wähle eine hochzählende Nummer startend bei 1",
      "PARTNER_INVOLVED": "Cedent Name",
      "INVOLVEMENT_TEXT": "Our Share",
      "ROLE_CATEGORY": "Cedent",
    }
  ],
  "SHARE_DETAILS": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT": "Hier die von dir gewählte Involvement Nummer einfügen",
      "START_DATE": "2021-01-01T00:00:00",
      "BROKER": null,
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT": "Hier die von dir gewählte Involvement Nummer einfügen",
      "START_DATE": "1964-01-01T00:00:00",
      "BROKER": null,
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT": "Hier die von dir gewählte Involvement Nummer einfügen",
      "START_DATE": "1964-01-01T00:00:00",
      "BROKER": null,
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT": "Hier die von dir gewählte Involvement Nummer einfügen",
      "START_DATE": "2021-01-01T00:00:00",
      "BROKER": null,
    }
  ],
  "PARTNER_SHARE": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "START_DATE": "1964-01-01T00:00:00",
      "INVOLVEMENT_NUMBER": "Hier die von dir gewählte Involvement Nummer einfügen",
      "SECTION_NUMBER": "1",
      "VALID_FROM": "1972-01-01T00:00:00",
      "SHARE_IN_PERCENT": "",
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "START_DATE": "1964-01-01T00:00:00",
      "INVOLVEMENT_NUMBER": "Hier die von dir gewählte Involvement Nummer einfügen",
      "SECTION_NUMBER": "1",
      "VALID_FROM": "1980-01-01T00:00:00",
      "SHARE_IN_PERCENT": "",
    },
  ],
  
  "TREATY_SECTION": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "Example: 8",
      "SECTION_TEXT": "Example: UZV 25% EXZ",
      "AREA": "Example: Germany, USA",
      "COB": "Example: Motor, Property",
      "BUSINESS_TYPE": "Example: Direct Business or Indirect Business",
      "START_DATE": "2021-01-01T00:00:00",
      "CURRENCY": "Example: AFN",
      "PREM_ACCOUNTING_MODE": "Accounting Year, Underwriting Year or Occurence Year",
      "ER_ID": null,
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "1",
      "SECTION_TEXT": "Example: UZV 25% EXZ",
      "AREA": "Example: Germany, USA",
      "COB": "Example: Motor, Property",
      "BUSINESS_TYPE": "Example: Direct Business or Indirect Business",
      "START_DATE": "2021-01-01T00:00:00",
      "CURRENCY": "Example: EUR",
      "PREM_ACCOUNTING_MODE": "Accounting Year, Underwriting Year or Occurence Year",
    }
  ],
"NP Liability": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "8",
      "SECTION_TEXT": "Example: UZV 25% EXZ",
      "Liability 1": "Attachement Point in EUR"
      "Liability 2": "Liability Limit in EUR",
      "START_DATE": "2021-01-01T00:00:00",
    },
],
 "NP PREMIUM": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "",
      "SECTION_TEXT": "",
      "Fixed Premium": "Premium in EUR for Example but not M&D Premium",
      "Fixed Premium Rate": "Percentage rate if any or total rate",
      "Estimated Subject Premium": "Gross Net Premium or Expected Premium Income but in the found Currency",
      "Reinstatement": "X if any information about it",
      "Installment": "Example: How much installments for the M&D Premium and when: 80.000 EUR on 01.01.2021 and 15.02.2021",
      "Perils": "Coverage in EUR when mentioned",
      "Exclusions": "Exclusions as String if any information about it",
      "START_DATE": "2021-01-01T00:00:00",
    },

  ],
  "AREA_SPLIT": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "1",
      "START_DATE": "1964-01-01T00:00:00",
      "AREA": "Example: Germany or USA",
      "SHARE_IN_PERCENT": 0,
      "UW_AREA": "X",
      "AREA_COVERED": "X",
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "8",
      "START_DATE": "2021-01-01T00:00:00",
      "AREA": "Example: Germany or USA",
      "SHARE_IN_PERCENT": 0,
      "UW_AREA": "X",
      "AREA_COVERED": "X"
    }
  ],
  "TREATY_COB_SPLIT": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "1",
      "START_DATE": "1964-01-01T00:00:00",
      "COB": "Example: Motor, Property",
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "8",
      "START_DATE": "2021-01-01T00:00:00",
      "COB": "Example: Motor, Property",
    }
  ],
  "CURRENCY_SPLIT": [
    
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": 1,
      "DT_PERIOD_START": "1964-01-01T00:00:00",
      "ORIGINAL_CURRENCY": "Example: EUR",
      "ER_TYPE_FOR_CURRENCY": "M",
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": 8,
      "DT_PERIOD_START": "2021-01-01T00:00:00",
      "ORIGINAL_CURRENCY": "Example: AFN",
      "ER_TYPE_FOR_CURRENCY": "M",
    }
  ],
  "PARTNER_FUNCTION": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT_NUMBER": "",
      "START_DATE": "2021-01-01T00:00:00",
      "PARTNER_FUNCTION": "Example: Account Receiver Reinsurer or Payment Receiver Reinsurer",
      "COMPANY_NAME": "Example: Biscaya named as Reinsured",
    }, 
  ],
}

## C) Wenn Vertragstyp = ANDERE:
## → Verwende diese kompakte allgemeine Struktur:
{
  "TREATY_TYPE": "",
  "TREATY_NUMBER": "",
  "CEDENT": "",
  "REINSURER": "",
  "NATURE_OF_TREATY": "",
  "START_DATE": "",
  "END_DATE": "",
  "CURRENCY": "",
  "LIMITS": "",
  "RETENTION": "",
  "PREMIUM": "",
  "ACCOUNTING": "",
  "SPECIAL_CONDITIONS": "",
  "EXCLUSIONS": "",
  "COMMENTS": ""
}

WICHTIG:
- Gib GENAU EINE der drei JSONs aus.
- Bei A oder B darfst du KEINE Felder hinzufügen/entfernen/umbenennen.
- Alle übrigen allgemeinen Regeln bleiben bestehen.

"""

# Task-Prompt
task_prompt_inform_extr_german = """
Hier ist der LaTeX-Code eines Rückversicherungsvertragsanhangs. Bitte extrahiere alle relevanten Informationen und gib sie in einer strukturierten JSON-Datei aus.
"""

# Claude-Aufruf
def call_claude_for_information_extraction(bedrock_client, model_name, sys_prompt, task_prompt, ocr_text, max_tokens=130000):
    if not ocr_text.strip():
        print("Error: ocr_text is empty")
        return "ERROR ON THIS PAGE", "Empty text"

    kwargs = {
        "modelId": model_name,
        "contentType": "application/json",
        "accept": "application/json",
        "body": json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": 1.0,
            "thinking": {"type": "enabled", "budget_tokens": 1024},
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": sys_prompt + "\n" + task_prompt + "\n" + ocr_text}],
                }
            ],
        })
    }

    try:
        response = bedrock_client.invoke_model(**kwargs)
        body = json.loads(response['body'].read())
       # print("RAW RESPONSE:", body)  # Debug-Ausgabe
        return body['content'][1]['text'], None #content[0] → thinking, content[1] → text (die JSON-Ausgabe)
                                                                
    except Exception as e:
        print(f"Error calling Claude API: {str(e)}")
        return "ERROR ON THIS PAGE", e

# JSON-Extraktion
def extract_json(s: str, parse: bool = False):
    start = s.find('{')
    if start == -1:
        raise ValueError("No opening '{' found.")
    depth = 0
    for i in range(start, len(s)):
        ch = s[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                candidate = s[start:i+1]
                if parse:
                    return json.loads(candidate)
                return candidate
    raise ValueError("No matching closing '}' found.")

# PDF-Text extrahieren
def read_pdf(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Datei nicht gefunden: {file_path}")
    text = ""
    with open(file_path, "rb") as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# Hauptteil
if __name__ == '__main__':
    config = Config(region_name='eu-central-1', retries={'max_attempts': 1, 'mode': 'adaptive'}, read_timeout=360)
    bedrock_client = boto3.client('bedrock-runtime', config=config)

    aws_model_id = "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
    
    # Open file dialog to select PDF
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(
        title="Select a PDF file",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )
    root.destroy()
    
    if not file_path:
        print("No file selected.")
        exit()

    try:
        ocr_text = read_pdf(file_path)
        print(f"PDF erfolgreich gelesen, Länge: {len(ocr_text)} Zeichen")
    except Exception as e:
        print(f"Fehler beim Lesen der PDF: {e}")
        exit()

    json_output, exception = call_claude_for_information_extraction(
        bedrock_client, aws_model_id, sys_prompt_inform_extr_german, task_prompt_inform_extr_german, ocr_text
    )

    try:
        json_output = extract_json(json_output, parse=True)
        pretty_json = json.dumps(json_output, indent=4, ensure_ascii=False)
        print(pretty_json)
        
        # Save the JSON to a file in the same directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(script_dir, "extracted_treaty_data.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(pretty_json)
        print(f"JSON saved to: {output_file}")
        
    except Exception as e:
        print("Fehler beim JSON-Parsing:", e)
        print("Roh-Output:", json_output)