# apps/documents/utils.py
# Utility functions for document processing and AI integration.

import google.generativeai as genai
from django.conf import settings
import os
import mimetypes
from django.core.files.storage import default_storage

# Configure Gemini AI with the API key from settings
# Ensure settings.GEMINI_API_KEY is set in your .env and settings.py
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not found in settings. Gemini AI features will not be available.")
    genai = None  # Set genai to None if API key is missing

def get_document_content(document_path):
    """
    Reads the content of a document file.
    Handles basic text files, PDFs, and DOCX.
    Returns content as a string or None if unsupported/error.
    """
    if not default_storage.exists(document_path):
        print(f"Error: Document file not found at {document_path}")
        return None

    try:
        mime_type, _ = mimetypes.guess_type(document_path)
        if mime_type is None:
            print(f"Warning: Could not determine MIME type for {document_path}")
            try:
                with default_storage.open(document_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                print(f"Could not read {document_path} as text.")
                return None

        if mime_type == 'application/pdf':
            from pdfminer.high_level import extract_text
            try:
                return extract_text(default_storage.path(document_path))
            except Exception as e:
                print(f"Error extracting text from PDF {document_path}: {e}")
                return None
        elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            from docx import Document as DocxDocument
            try:
                doc = DocxDocument(default_storage.path(document_path))
                text = []
                for paragraph in doc.paragraphs:
                    text.append(paragraph.text)
                return '\n'.join(text)
            except Exception as e:
                print(f"Error extracting text from DOCX {document_path}: {e}")
                return None
        elif mime_type.startswith('text/'):
            try:
                with default_storage.open(document_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading text file {document_path}: {e}")
                return None
        else:
            print(f"Warning: Unsupported file type for text extraction: {mime_type}")
            return None

    except Exception as e:
        print(f"An unexpected error occurred while reading document {document_path}: {e}")
        return None

def summarize_document_content(document_content, prompt="Summarize the key points of this document:"):
    """
    Summarizes document content using Gemini AI.
    Takes document content as a string.
    """
    if not genai:
        print("Gemini AI is not configured. Cannot summarize.")
        return None
    if not document_content:
        print("No document content provided for summarization.")
        return None

    try:
        model = genai.GenerativeModel('gemini-pro')
        full_prompt = f"{prompt}\n\nDocument Content:\n{document_content[:10000]}"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        print(f"Error summarizing document content with Gemini AI: {e}")
        return None

def summarize_document(document_path, prompt="Summarize the key points of this document:"):
    """
    Reads document content and then summarizes it using Gemini AI.
    """
    document_content = get_document_content(document_path)
    if document_content:
        return summarize_document_content(document_content, prompt)
    return None

def segment_document_content(document_content, sections=["Executive Summary", "Introduction", "Body", "Conclusion"]):
    """
    Attempts to segment document content based on predefined sections using Gemini AI.
    Takes document content as a string.
    """
    if not genai:
        print("Gemini AI is not configured. Cannot segment.")
        return None
    if not document_content:
        print("No document content provided for segmentation.")
        return None

    try:
        prompt = f"Segment the following document content into these sections: {', '.join(sections)}. Clearly label each section. If a section is not present, indicate that.\n\nDocument Content:\n{document_content[:10000]}"
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error segmenting document content with Gemini AI: {e}")
        return None

def segment_document(document_path, sections=["Executive Summary", "Introduction", "Body", "Conclusion"]):
    """
    Reads document content and then attempts to segment it using Gemini AI.
    """
    document_content = get_document_content(document_path)
    if document_content:
        return segment_document_content(document_content, sections)
    return None

def convert_to_pdf(document_path, output_path):
    """Converts a document to PDF format."""
    pass  # Implementation depends on the file type and libraries used

def apply_qes(document_path, signature_data):
    """Applies a Qualified Electronic Signature to a document."""
    pass  # Implementation requires integration with a QES provider API

def merge_pdfs(pdf_paths, output_path):
    """Merges multiple PDF files into one."""
    pass  # Use a library like PyPDF2

def split_pdf(pdf_path, output_dir):
    """Splits a PDF file into multiple files."""
    pass  # Use a library like PyPDF2

def annotate_pdf(pdf_path, annotations):
    """Adds annotations to a PDF file."""
    pass  # Use a library or commercial SDK
