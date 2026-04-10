import json
import re
from docx import Document

DOCX_FILE = "Sbornik_zakoni_Pustinyakovo.docx"
OUTPUT_JSON = "laws_data.json"

SECTOR_HEADINGS = [
    "Конституционен ред и държавно устройство",
    "Избори и политически партии",
    "Сигурност, армия и извънредни правомощия",
    "Съдебна власт и прокуратура",
    "Вътрешен ред, полиция и администрация",
    "Образование, наука и култура",
    "Икономика, индустрия и стратегическа инфраструктура",
    "Енергетика и публични ресурси",
    "Медии, информация и обществен дебат",
    "Права, свободи и вероизповедания",
    "Следвоенно възстановяване и институционална нормализация"
]

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def is_sector_heading(text):
    return text in SECTOR_HEADINGS

def looks_like_law_title(text):
    if not text:
        return False
    return text.startswith("Закон за") or text.startswith("Конституция на")

def parse_year_and_id(text):
    year_match = re.search(r"Година на приемане:\s*(\d{4})", text)
    id_match = re.search(r"Идентификационен номер:\s*(PU\d{4}/\d{3})", text)

    year = int(year_match.group(1)) if year_match else None
    law_id = id_match.group(1) if id_match else None

    return year, law_id

def parse_docx_to_json():
    doc = Document(DOCX_FILE)
    paragraphs = [clean_text(p.text) for p in doc.paragraphs if clean_text(p.text)]

    laws = []
    current_sector = None
    current_law = None

    for para in paragraphs:
        if is_sector_heading(para):
            current_sector = para
            continue

        if looks_like_law_title(para):
            if current_law:
                current_law["full_text"] = " ".join(
                    f'{a["article_number"]} {a["text"]}'.strip()
                    for a in current_law["articles"]
                )
                laws.append(current_law)

            current_law = {
                "sector": current_sector,
                "title": para,
                "year": None,
                "law_id": None,
                "subject": "",
                "articles": [],
                "full_text": ""
            }
            continue

        if current_law is None:
            continue

        if "Година на приемане:" in para and "Идентификационен номер:" in para:
            year, law_id = parse_year_and_id(para)
            current_law["year"] = year
            current_law["law_id"] = law_id
            continue

        if para.startswith("Предмет на закона:"):
            current_law["subject"] = para.replace("Предмет на закона:", "").strip()
            continue

        if para.startswith("Чл."):
            article_match = re.match(r"(Чл\.\s*\d+\.)\s*(.*)", para)
            if article_match:
                current_law["articles"].append({
                    "article_number": article_match.group(1),
                    "text": article_match.group(2).strip()
                })
            else:
                current_law["articles"].append({
                    "article_number": "",
                    "text": para
                })

    if current_law:
        current_law["full_text"] = " ".join(
            f'{a["article_number"]} {a["text"]}'.strip()
            for a in current_law["articles"]
        )
        laws.append(current_law)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(laws, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(laws)} laws to {OUTPUT_JSON}")

if __name__ == "__main__":
    parse_docx_to_json()