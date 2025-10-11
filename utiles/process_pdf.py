#!/usr/bin/env python3
import sys, re, hashlib, json
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

# Configure tesseract path if needed (uncomment and adjust for your system)
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Enhanced patterns to remove
TEXT_PATTERNS = [
    r"https?://\S+",
    r"www\.\S+",
    r"Join Our WhatsApp Channel",
    r"For More Info Visit Cluesbook\.Com",
    r"cluesbook\.com",
    r"join telegram",
    r"subscribe",
    r"hamza anwar",
    r"team",
    r"institute",
    r"Copyright Pearson Prentice-Hall",
    r"CluesBook",
    r"VU Help Forum",
    r"telegram",
    r"whatsapp",
    r"channel",
    r"subscribe",
    r"follow us",
    r"like us",
    r"share",
    r"click here"
]

# Watermark detection keywords
WATERMARK_WORDS = [
    "cluesbook", "hamza", "anwar", "team", "institute", 
    "copyright", "pearson", "prentice-hall", "vu help forum",
    "vuhelp", "virtual university", "vu students"
]

def should_remove_text(txt, font_size=None, flags=0, bbox_area=0, page_area=1):
    """
    Determine if text should be removed based on content and context
    """
    txt_lower = txt.lower().strip()
    
    if not txt_lower or len(txt_lower) < 2:
        return False
    
    # Check against patterns
    for pat in TEXT_PATTERNS:
        if re.search(pat, txt_lower, re.IGNORECASE):
            return True
    
    # Check for watermark keywords
    for word in WATERMARK_WORDS:
        if word in txt_lower:
            return True
    
    # Remove very common spam phrases
    spam_phrases = [
        "join our", "visit us", "click here", "download now",
        "subscribe to", "follow our", "like our", "share this"
    ]
    for phrase in spam_phrases:
        if phrase in txt_lower:
            return True
    
    # Large font text at page edges (likely headers/footers)
    if font_size and font_size > 18:
        bbox_ratio = bbox_area / page_area if page_area > 0 else 0
        if bbox_ratio < 0.005:  # Very small text area with large font
            return True
    
    return False

def extract_clean_text(pdf_path):
    """Extract just the clean text without saving PDF"""
    try:
        doc = fitz.open(pdf_path)
        clean_text = ""
        
        for page_num, page in enumerate(doc):
            page_area = page.rect.width * page.rect.height
            blocks = page.get_text("dict")["blocks"]
            
            page_text = []
            
            for b in blocks:
                if "lines" not in b:
                    continue
                    
                for line in b["lines"]:
                    line_text = []
                    for span in line["spans"]:
                        txt = span["text"].strip()
                        if not txt:
                            continue
                            
                        font_size = span.get("size", 0)
                        flags = span.get("flags", 0)
                        bbox = fitz.Rect(span["bbox"])
                        bbox_area = bbox.width * bbox.height
                        
                        # Only keep text that should NOT be removed
                        if not should_remove_text(txt, font_size, flags, bbox_area, page_area):
                            line_text.append(txt)
                    
                    if line_text:
                        page_text.append(" ".join(line_text))
            
            if page_text:
                clean_text += f"\n--- Page {page_num + 1} ---\n" + "\n".join(page_text) + "\n"
        
        doc.close()
        return clean_text.strip()
    
    except Exception as e:
        raise Exception(f"Error extracting text: {str(e)}")

def clean_pdf(input_path, output_path, enable_ocr=False):
    """Create a cleaned PDF version with watermarks removed"""
    try:
        doc = fitz.open(input_path)
        seen_images = set()
        
        for page_num, page in enumerate(doc):
            page_area = page.rect.width * page.rect.height
            
            # Get all text blocks
            blocks = page.get_text("dict")["blocks"]
            
            # Identify header/footer regions
            header_region = fitz.Rect(0, 0, page.rect.width, page.rect.height * 0.15)
            footer_region = fitz.Rect(0, page.rect.height * 0.85, page.rect.width, page.rect.height)
            
            redaction_rects = []
            
            # Process text blocks for removal
            for b in blocks:
                if "lines" not in b:
                    continue
                    
                for line in b["lines"]:
                    for span in line["spans"]:
                        txt = span["text"].strip()
                        if not txt:
                            continue
                            
                        font_size = span.get("size", 0)
                        flags = span.get("flags", 0)
                        bbox = fitz.Rect(span["bbox"])
                        bbox_area = bbox.width * bbox.height
                        
                        # Check if this text should be removed
                        if should_remove_text(txt, font_size, flags, bbox_area, page_area):
                            # Expand bbox slightly to ensure complete removal
                            expanded_bbox = bbox + (-2, -2, 2, 2)
                            redaction_rects.append(expanded_bbox)
            
            # Process images for potential removal
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                xref = img[0]
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if not pix:
                        continue
                        
                    img_width, img_height = pix.width, pix.height
                    img_area = img_width * img_height
                    
                    # Create hash for duplicate detection
                    img_data = pix.samples
                    img_hash = hashlib.md5(img_data[:min(1000, len(img_data))]).hexdigest()
                    
                    # Get image position
                    img_instances = page.get_image_bbox(xref)
                    
                    for img_rect in img_instances:
                        # Remove small images and duplicates
                        if img_area < 3000 or img_hash in seen_images:
                            redaction_rects.append(img_rect)
                            continue
                        
                        # Remove images in header/footer that are small-medium sized
                        if (img_area < 30000 and 
                            (header_region.intersects(img_rect) or footer_region.intersects(img_rect))):
                            redaction_rects.append(img_rect)
                            continue
                        
                        seen_images.add(img_hash)
                        
                except Exception as e:
                    continue
            
            # Apply all redactions
            for rect in redaction_rects:
                page.add_redact_annot(rect, fill=(1, 1, 1))
            
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE)
        
        # Save the cleaned PDF
        doc.save(output_path, deflate=True, garbage=4)
        doc.close()
        return f"Cleaned PDF saved as: {output_path}"
    
    except Exception as e:
        raise Exception(f"Error cleaning PDF: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: python process_pdf.py input.pdf output.pdf [--extract-text]"}))
        sys.exit(1)
    
    infile, outfile = sys.argv[1], sys.argv[2]
    
    try:
        if "--extract-text" in sys.argv:
            # Extract and return clean text as JSON
            text = extract_clean_text(infile)
            result = {
                "success": True,
                "text": text,
                "message": "Text extracted successfully",
                "pages": text.count('--- Page') if text else 0
            }
            print(json.dumps(result))
        else:
            # Create cleaned PDF
            message = clean_pdf(infile, outfile, enable_ocr=False)
            result = {
                "success": True,
                "message": message
            }
            print(json.dumps(result))
            
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(error_result))
        sys.exit(1)