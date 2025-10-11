import sys
import json
import fitz
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import time

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate_google_drive():
    """Authenticate and create the Drive API service"""
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('drive', 'v3', credentials=creds)

def pdf_to_google_docs(pdf_path):
    """Convert PDF to Google Docs format"""
    try:
        service = authenticate_google_drive()
        
        # Upload PDF to Google Drive
        file_metadata = {
            'name': os.path.basename(pdf_path) + ' - Converted',
            'mimeType': 'application/vnd.google-apps.document'
        }
        
        media = MediaFileUpload(pdf_path, mimetype='application/pdf')
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        # Wait for conversion
        time.sleep(5)
        
        # Download as PDF (clean version)
        exported_pdf = service.files().export(
            fileId=file.get('id'),
            mimeType='application/pdf'
        ).execute()
        
        # Save the cleaned PDF
        output_path = pdf_path.replace('.pdf', '_cleaned_from_docs.pdf')
        with open(output_path, 'wb') as f:
            f.write(exported_pdf)
        
        # Clean up - delete the Google Doc
        service.files().delete(fileId=file.get('id')).execute()
        
        return {
            "success": True,
            "output_path": output_path,
            "message": "PDF converted and cleaned via Google Docs"
        }
        
    except Exception as e:
        return {"error": f"Google Docs conversion failed: {str(e)}"}

def simple_pdf_cleaner(pdf_path):
    """Alternative: Simple PDF cleaning without Google Docs"""
    try:
        doc = fitz.open(pdf_path)
        output_path = pdf_path.replace('.pdf', '_simple_clean.pdf')
        
        # Basic cleaning - remove annotations and metadata
        for page in doc:
            # Remove all annotations (often used for watermarks)
            annots = page.annots()
            if annots:
                for annot in annots:
                    page.delete_annot(annot)
        
        # Clean metadata
        doc.set_metadata({})
        
        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        
        return {
            "success": True,
            "output_path": output_path,
            "message": "PDF cleaned (annotations and metadata removed)"
        }
        
    except Exception as e:
        return {"error": f"Simple cleaning failed: {str(e)}"}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python google_docs_converter.py input.pdf"}))
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    try:
        # Try Google Docs conversion first, fall back to simple cleaning
        result = pdf_to_google_docs(pdf_path)
        if "error" in result:
            result = simple_pdf_cleaner(pdf_path)
        
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)