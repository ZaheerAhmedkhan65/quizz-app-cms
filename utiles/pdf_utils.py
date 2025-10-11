import sys
import json
import fitz
import base64
import os
from PIL import Image
import io

def get_pdf_info(pdf_path):
    """Extract PDF information"""
    try:
        doc = fitz.open(pdf_path)
        info = {
            "pages": len(doc),
            "page_size": [],
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", "")
        }
        
        for page in doc:
            info["page_size"].append({
                "width": page.rect.width,
                "height": page.rect.height
            })
        
        doc.close()
        return info
    except Exception as e:
        return {"error": str(e)}

def generate_page_images(pdf_path, output_dir):
    """Generate images for each PDF page for the editor"""
    try:
        doc = fitz.open(pdf_path)
        images = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Render page as image with reasonable resolution
            mat = fitz.Matrix(1.5, 1.5)  # Good balance of quality and performance
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Convert to base64 for web display
            img_data = pix.tobytes("png")
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            images.append({
                "page": page_num + 1,
                "width": pix.width,
                "height": pix.height,
                "data": f"data:image/png;base64,{img_base64}",
                "original_width": page.rect.width,
                "original_height": page.rect.height
            })
        
        doc.close()
        return {"images": images}
    except Exception as e:
        return {"error": f"Failed to generate images: {str(e)}"}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: python pdf_utils.py [info|generate-images] pdf_path [output_dir]"}))
        sys.exit(1)
    
    command = sys.argv[1]
    pdf_path = sys.argv[2]
    
    # Validate PDF file exists
    if not os.path.exists(pdf_path):
        print(json.dumps({"error": f"PDF file not found: {pdf_path}"}))
        sys.exit(1)
    
    try:
        if command == "info":
            result = get_pdf_info(pdf_path)
        elif command == "generate-images":
            output_dir = sys.argv[3] if len(sys.argv) > 3 else "."
            result = generate_page_images(pdf_path, output_dir)
        else:
            result = {"error": f"Unknown command: {command}"}
        
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": f"Python script error: {str(e)}"}))
        sys.exit(1)