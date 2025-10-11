import sys
import json
import re
import pdfplumber

SECTION_PATTERNS = {
    "Lecture": r"(Lecture\s*(?:No\.?|#)?\s*\d+)",
    "Lesson": r"(Lesson\s*(?:No\.?|#)?\s*\d+)",
    "Chapter": r"(Chapter\s*\d+)",
    "Module": r"(Module\s*\d+)",
    "Topic": r"(Topic\s*\d+[:.-]?)"
}

def parse_pdf(file_path):
    results = {}
    with pdfplumber.open(file_path) as pdf:
        total_pages = len(pdf.pages)
        section_positions = []

        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            print(f"PROGRESS:{int((page_num / total_pages) * 100)}", file=sys.stderr)
            sys.stderr.flush()

            if page_num <= 5 and sum(len(re.findall(p, text, re.I)) for p in SECTION_PATTERNS.values()) > 3:
                continue

            for key, pattern in SECTION_PATTERNS.items():
                for m in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                    match = m.group().strip()
                    if m.start() > 100:
                        continue
                    clean_title = re.sub(r"\s+", " ", match)
                    section_positions.append((clean_title, page_num))

        seen = set()
        unique_sections = []
        for title, pg in section_positions:
            if title not in seen:
                seen.add(title)
                unique_sections.append((title, pg))

        for i, (title, start_page) in enumerate(unique_sections):
            if i < len(unique_sections) - 1:
                _, next_start = unique_sections[i + 1]
                end_page = next_start - 1 if next_start > start_page else start_page
            else:
                end_page = len(pdf.pages)
            results[title] = {"start_page": start_page, "end_page": end_page}

    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No PDF file provided"}))
        sys.exit(1)

    file_path = sys.argv[1]
    try:
        output = parse_pdf(file_path)
        print(json.dumps(output, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
