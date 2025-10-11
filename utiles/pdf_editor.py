# pdf_edit.py
import sys, json, fitz  # pip install pymupdf
from PIL import Image
import io
# optional: pip install pytesseract imagehash opencv-python

def redact_by_bboxes(doc, page_num, bboxes):
    page = doc[page_num]
    for bbox in bboxes:
        # bbox = (x0, y0, x1, y1) in PDF coordinate space
        rect = fitz.Rect(bbox)
        page.add_redact_annot(rect, fill=(1,1,1))  # white fill
    page.apply_redactions()

def redact_by_text(doc, text):
    for page in doc:
        text_instances = page.search_for(text, hit_max=1000)
        for r in text_instances:
            page.add_redact_annot(r, fill=(1,1,1))
        if text_instances:
            page.apply_redactions()

def main():
    payload = json.loads(sys.argv[1])
    filePath = payload['filePath']
    actions = payload['actions']
    outFile = payload.get('outFile', 'edited_output.pdf')

    doc = fitz.open(filePath)

    for act in actions:
        kind = act.get('type')
        scope = act.get('scope','currentPage') # 'allPages' or 'currentPage'
        page = int(act.get('page', 1)) - 1
        bbox = act.get('bbox')  # [x0,y0,x1,y1]
        content = act.get('content','')

        if kind in ('image','watermark','text') and bbox:
            if scope == 'currentPage':
                redact_by_bboxes(doc, page, [bbox])
            else:
                # remove same content across all pages: simple heuristic:
                # 1) If text is present and content string provided, use text search across pages
                if kind == 'text' or (kind == 'watermark' and content):
                    redact_by_text(doc, content)
                else:
                    # if image/logo or watermark with bbox: try to redact same bbox on each page
                    for pnum in range(len(doc)):
                        try:
                            redact_by_bboxes(doc, pnum, [bbox])
                        except Exception as e:
                            print('err', e)

    doc.save(outFile, deflate=True)
    doc.close()
    print('OK')

if __name__ == '__main__':
    main()
