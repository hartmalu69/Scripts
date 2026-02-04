import json
import boto3
import PyPDF2
from botocore.config import Config
import os
import tkinter as tk
from tkinter import filedialog

# System-Prompt
sys_prompt_inform_extr_german = """
Du bist ein erfahrener Vertragsanalyst mit Spezialisierung auf Rückversicherungsverträge. Du erhältst Vertragsanhänge im LaTeX-Format und extrahierst alle relevanten Informationen in eine strukturierte JSON-Datei.

Regeln:
- Wichtig! Wir wollen mit dem erzeugten JSON über eine API einen Vertrag in ein System einpflegen. Daher ist es essenziell, dass die JSON-Struktur exakt eingehalten wird und du nicht so viel Text schreibst sondern dich auf die Werte fokussierst.
- Extrahiere ausschließlich Informationen für:
  * die erste Vertragsperiode,
  * Pro Layer muss ein eigener Vertrag angelegt werden und in diesem Fall legst du nur einen Layer (Vertrag) an.
- Verwende die vorgegebene JSON-Struktur mit allen Schlüsseln (auch wenn keine Werte vorhanden sind).
- Werte müssen im gleichen Format wie das Beispiel sein:
  * Strings für Textfelder,
  * leere Strings "" oder "UNBEKANNT" für fehlende Informationen,
  * keine zusätzlichen Schlüssel oder Kommentare.
- Datumsangaben im Format YYYY-MM-DD oder YYYY-MM-DDT00:00:00 und für Amerikanische Datumsangaben MM/DD/YYYY in YYYY-MM-DDT00:00:00 umwandeln.
- Unter "TREATY_PERIOD" findest du am Anfang die Perioden des Vertrags und in allen folgenden Feldern nimmst du auch das Startdatum bzw. Enddatum der jeweiligen Periode.
- Wenn mehrere Layer oder Perioden vorhanden sind, ignoriere alle außer der ersten und Layer 1.
- Gib nur die JSON-Datei aus, ohne Erklärungen oder Kommentare.
- Wenn du das Wort "Example:" siehst, dann habe ich dir ein Beispiel gegeben, wie der Wert aussehen könnte. Ersetze "Example:" und den Beispielwert durch den tatsächlichen Wert aus dem Vertrag oder lasse das Feld leer, wenn der Wert nicht gefunden werden kann.

Die JSON-Datei MUSS mindestens die folgende Struktur enthalten (mit allen Schlüsseln):

{
  {
  "TREATY_HEADER": {
    "TREATY_NUMBER": "<TREATY_NUMBER>",
    "TREATY_TEXT": "Example: DBV LEBEN",
    "CEDENT": "Example: Biscaya named as Reinsured",
    "TTY_DIRECTION": "Example: Incoming when you are the Reinsurer and Outgoing when you are the Cedent",
    "NATURE_OF_TREATY": "Example: proportional or non-proportional",
    "ACCOUNTING_FREQ": "Example: monthly/quarterly/annual/halfyearly",
    "FIRST_ACCT_KEY_DATE": "For non-proportional treaties: Treaty start date",
    "ACCOUNT_CREATION_PERIOD": "Frist für Abrechnungserstellung",
    "END_OF_ACCOUNTING_YEAR": "Period End date",
  },
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
      "ROLE_CATEGORY": "Cedent"
    }
  ],
  "SHARE_DETAILS": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT": Hier die von dir gewählte Involvement Nummer einfügen,
      "START_DATE": "2021-01-01T00:00:00",
      "BROKER": null,
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT": Hier die von dir gewählte Involvement Nummer einfügen,
      "START_DATE": "1964-01-01T00:00:00",
      "BROKER": null,
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT": Hier die von dir gewählte Involvement Nummer einfügen,
      "START_DATE": "1964-01-01T00:00:00",
      "BROKER": null,
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT": Hier die von dir gewählte Involvement Nummer einfügen,
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
      "SHARE_IN_PERCENT": 25,
      "TR_PS_STATUS": "005"
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "START_DATE": "1964-01-01T00:00:00",
      "INVOLVEMENT_NUMBER": "Hier die von dir gewählte Involvement Nummer einfügen",
      "SECTION_NUMBER": "1",
      "VALID_FROM": "1980-01-01T00:00:00",
      "SHARE_IN_PERCENT": 0,
      "TR_PS_STATUS": "005"
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "START_DATE": "2021-01-01T00:00:00",
      "INVOLVEMENT_NUMBER": "Hier die von dir gewählte Involvement Nummer einfügen",
      "SECTION_NUMBER": "8",
      "VALID_FROM": "2021-01-01T00:00:00",
      "SHARE_IN_PERCENT": 15,
      "TR_PS_STATUS": "001"
    }
  ],
  
  "TREATY_SECTION": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "8",
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
      "ER_ID": null,
    }
  ],
  "Quota": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "8",
      "SECTION_TEXT": "Example: UZV 25% EXZ",
      "Share": "Quota Share in Percentage",
      "Limit": "Liability Limit in EUR",
      "EPI": "Estimated Premium Income in EUR",
    },
  ],
  "Suex": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "1",
      "SECTION_TEXT": "Example: UZV 25% EXZ",
      "Maxima": "Retention in EUR",
      "Limit": "Liability Limit in EUR",
      "Priority": "Estimated Premium Income in EUR",
    }
  ],

  
  "AREA_SPLIT": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "1",
      "START_DATE": "1964-01-01T00:00:00",
      "AREA": "Example: Germany or USA",
      "SHARE_IN_PERCENT": 0,
      "UW_AREA": "X",
      "AREA_COVERED": "X"
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
      "COB": "Example: Motor, Property"
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "8",
      "START_DATE": "2021-01-01T00:00:00",
      "COB": "Example: Motor, Property"
    }
  ],
  "CURRENCY_SPLIT": [
    
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": 1,
      "DT_PERIOD_START": "1964-01-01T00:00:00",
      "ORIGINAL_CURRENCY": "Example: EUR",
      "ER_TYPE_FOR_CURRENCY": "M"
    },
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": 8,
      "DT_PERIOD_START": "2021-01-01T00:00:00",
      "ORIGINAL_CURRENCY": "Example: AFN",
      "ER_TYPE_FOR_CURRENCY": "M"
    }
  ],
  "PARTNER_FUNCTION": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "INVOLVEMENT_NUMBER": "",
      "START_DATE": "2021-01-01T00:00:00",
      "PARTNER_FUNCTION": "Example: Account Receiver (Reinsurer) or Payment Receiver (Reinsurer)",
      "COMPANY_NAME": "Example: Biscaya named as Reinsured",
    }, 
  ],
  "COMMISSION_DETAILS": [
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "Example: 1",
      "START_DATE": "2021-01-01T00:00:00",
      "COMMISSION_TYPE": "Example: Fixed Commission or Provisional Commission",
      "COMMISSION_RATE": "Example: 5%",
      "LOSS_RATIO": "Only usable when Commission Type is Scaled Commission Example: 70%",
    }
    {
      "TREATY_NUMBER": "<TREATY_NUMBER>",
      "SECTION_NUMBER": "Example: 1",
      "START_DATE": "2021-01-01T00:00:00",
      "COMMISSION_TYPE": "Example: Fixed Commission or Provisional Commission",
      "COMMISSION_RATE": "Example: 5%",
      "LOSS_RATIO": "Only usable when Commission Type is Scaled Commission",
    }
  ],
}

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