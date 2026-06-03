"""
Download ICD-10-VN from HL7 Vietnam official FHIR server.
Source: https://fhir.hl7.org.vn/core (QD 4469/QD-BYT, BYT official)
15,026 codes: 2,043 type codes + 12,983 disease codes
"""

import urllib.request
import json
import os
import ssl

DATA_DIR = r'D:\MediVoice_VN\data\reference'
URL = 'https://downloads.fhir.hl7.org.vn/core/0.5.3/terminology/clinical/CodeSystem-vn-icd10-cs.full.json'
RAW_FILE = os.path.join(DATA_DIR, 'icd10vn_raw.json')
OUT_FILE = os.path.join(DATA_DIR, 'icd10vn.json')

os.makedirs(DATA_DIR, exist_ok=True)

# --- Download ---
print(f"Downloading ICD-10-VN from HL7 Vietnam...")
print(f"URL: {URL}")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    req = urllib.request.Request(URL, headers={'User-Agent': 'MediVoice-VN/0.2.0'})
    with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
        raw_data = response.read()

    with open(RAW_FILE, 'wb') as f:
        f.write(raw_data)
    print(f"Downloaded: {len(raw_data)/1024:.0f} KB -> {RAW_FILE}")
except Exception as e:
    print(f"Download failed: {e}")
    print("Trying alternative approach...")
    exit(1)

# --- Parse FHIR CodeSystem format ---
with open(RAW_FILE, 'r', encoding='utf-8') as f:
    fhir_data = json.load(f)

print(f"\nFHIR resource type: {fhir_data.get('resourceType')}")
print(f"Title: {fhir_data.get('title') or fhir_data.get('name')}")
print(f"Status: {fhir_data.get('status')}")

# Count concepts
concepts = fhir_data.get('concept', [])
print(f"Top-level concepts: {len(concepts)}")

# Flatten all codes (including nested)
def flatten_concepts(concepts_list, parent_code=None, depth=0):
    result = []
    for concept in concepts_list:
        code = concept.get('code', '')
        display = concept.get('display', '')

        # Get Vietnamese display if available in designations
        vn_display = display
        for designation in concept.get('designation', []):
            lang = designation.get('language', '')
            if lang in ('vi', 'vi-VN'):
                vn_display = designation.get('value', display)
                break

        # Get definition/description
        definition = concept.get('definition', '')

        # Keywords: split code by dot to get parent codes
        parts = code.split('.')
        keywords = [code.lower()]
        if len(parts) > 1:
            keywords.append(parts[0].lower())  # chapter code
        # Add words from display name
        words = vn_display.lower().replace(',', ' ').replace('(', ' ').replace(')', ' ').split()
        keywords.extend([w for w in words if len(w) >= 3])

        entry = {
            "code": code,
            "display": vn_display,
            "definition": definition,
            "depth": depth,
            "parent": parent_code,
            "keywords": list(set(keywords))
        }
        result.append(entry)

        # Recurse into children
        children = concept.get('concept', [])
        if children:
            result.extend(flatten_concepts(children, code, depth + 1))

    return result

all_codes = flatten_concepts(concepts)
print(f"Total codes (flattened): {len(all_codes)}")

# Build output database
db = {
    "_meta": {
        "source": "HL7 Vietnam FHIR CodeSystem vn-icd10-cs v0.5.3",
        "authority": "Bo Y te VN - QD4469/QD-BYT, QD4400/QD-BYT, QD98/QD-BYT, TT01/2025",
        "total_codes": len(all_codes),
        "license": "Vietnamese Ministry of Health - Official"
    },
    "by_code": {},
    "keyword_index": {}
}

for entry in all_codes:
    code = entry["code"]
    db["by_code"][code] = entry

    for kw in entry["keywords"]:
        if kw not in db["keyword_index"]:
            db["keyword_index"][kw] = []
        if code not in db["keyword_index"][kw]:
            db["keyword_index"][kw].append(code)

# Save
with open(OUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(db, f, ensure_ascii=False, indent=2)

size_kb = os.path.getsize(OUT_FILE) / 1024
print(f"\nSaved: {OUT_FILE}")
print(f"Size: {size_kb:.0f} KB")
print(f"Total codes: {len(db['by_code'])}")
print(f"Keywords indexed: {len(db['keyword_index'])}")

# Sample lookup
print("\n--- SAMPLE CODES ---")
samples = ['J02.9', 'K58.9', 'M17.1', 'I10', 'J18.9', 'E11']
for code in samples:
    if code in db["by_code"]:
        e = db["by_code"][code]
        print(f"  {e['code']:10} | {e['display'][:60]}")
    else:
        print(f"  {code:10} | not found")

# Verify common medical terms
print("\n--- KEYWORD LOOKUP TEST ---")
test_kw = ['viêm họng', 'cao huyết áp', 'tiểu đường', 'cúm', 'đau lưng']
for kw in test_kw:
    matches = db["keyword_index"].get(kw, [])
    if matches:
        first = db["by_code"][matches[0]]
        print(f"  '{kw}' -> [{first['code']}] {first['display'][:50]}")
    else:
        print(f"  '{kw}' -> no exact match")

print("\nDone!")
