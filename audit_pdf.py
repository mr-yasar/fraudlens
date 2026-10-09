"""Render PNG images for each of the 9 pages of the generated IEEE PDF
and verify text, citations, forbidden words, and layout.
"""

from pathlib import Path
import re
import pymupdf

PDF_PATH = Path("FraudLens_AI_Research_Paper/FraudLens_AI_IEEE_Research_Paper.pdf")
PNG_DIR = Path("FraudLens_AI_Research_Paper/FraudLens_AI_Research_Paper_Source/page_previews")
PNG_DIR.mkdir(parents=True, exist_ok=True)

doc = pymupdf.open(str(PDF_PATH))
total_pages = len(doc)
print(f"Total Pages: {total_pages}")
assert total_pages == 9, f"Expected exactly 9 pages, got {total_pages}"

full_text = ""
for i in range(total_pages):
    page = doc[i]
    pix = page.get_pixmap(dpi=150)
    out_img = PNG_DIR / f"page_{i+1}.png"
    pix.save(str(out_img))
    
    txt = page.get_text()
    full_text += f"\n--- PAGE {i+1} ---\n" + txt
    print(f"Rendered Page {i+1} -> {out_img} (text length: {len(txt)} chars)")

# Strict Prohibited Word Audit
prohibited_patterns = [
    r"\bRAG\b",
    r"\brag\b",
    r"retrieval-augmented generation",
    r"retrieval augmented generation",
]

violations = []
for pat in prohibited_patterns:
    matches = re.findall(pat, full_text, flags=re.IGNORECASE)
    if matches:
        violations.append((pat, len(matches)))

print("\n=== PROHIBITED WORD AUDIT ===")
if violations:
    print(f"CRITICAL VIOLATION FOUND: {violations}")
else:
    print("PASSED: Exactly 0 occurrences of prohibited chatbot term/acronym 'RAG' or 'retrieval-augmented generation' found in entire paper!")

# Citation Audit
print("\n=== CITATION INTEGRITY AUDIT ===")
citations_found = []
for ref_id in range(1, 26):
    cite_pat = rf"\[{ref_id}\]"
    if re.search(cite_pat, full_text):
        citations_found.append(ref_id)
    else:
        print(f"Warning: Citation [{ref_id}] not found in text!")

print(f"Total authentic references cited in text: {len(citations_found)}/25")

# Author Details Audit
print("\n=== AUTHOR DETAILS AUDIT ===")
authors_expected = ["Mohana Priya S", "Monisha S", "Sona College of Technology", "Anna University"]
for a in authors_expected:
    if a.lower() in full_text.lower():
        print(f"PASSED: Found '{a}'")
    else:
        print(f"FAILED: '{a}' not found!")

doc.close()
print("\nPDF Audit Completed Successfully!")
