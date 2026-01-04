"""
PDF Parser Service
Handles extraction of timetable data from PDF files (both text-based and scanned)
"""

import pdfplumber
import os
import pytesseract
from PIL import Image
import io


def detect_pdf_type(pdf_path):
    """
    Detect if PDF is text-based or scanned
    Returns: 'text-based' or 'scanned'
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Check first page for text content
            if len(pdf.pages) > 0:
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                
                # If we extracted meaningful text, it's text-based
                if text and len(text.strip()) > 50:
                    return 'text-based'
        
        return 'scanned'
    except Exception as e:
        print(f"Error detecting PDF type: {e}")
        return 'unknown'


def extract_from_text_pdf(pdf_path):
    """
    Extract table data from text-based PDF using pdfplumber
    Returns: List of dictionaries representing rows
    """
    all_rows = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract tables from the page
                tables = page.extract_tables()
                
                if tables:
                    for table in tables:
                        if not table or len(table) < 2:
                            continue
                        
                        # Assume first row is header
                        headers = table[0]
                        
                        # Process remaining rows
                        for row in table[1:]:
                            if not row or all(cell is None or str(cell).strip() == '' for cell in row):
                                continue
                            
                            # Create dictionary from row
                            row_dict = {}
                            for i, header in enumerate(headers):
                                if header and i < len(row):
                                    # Clean header and value
                                    clean_header = str(header).strip() if header else f'Column{i+1}'
                                    clean_value = str(row[i]).strip() if row[i] is not None else ''
                                    row_dict[clean_header] = clean_value
                                
                                # Inject Page Context for Frontend Separation
                                row_dict['_SHEET_NAME_'] = f"Page {page_num + 1}"
                            
                            if row_dict:
                                all_rows.append(row_dict)
                else:
                    # Try to extract text and parse as structured data
                    text = page.extract_text()
                    if text:
                        # Simple line-based parsing (fallback)
                        lines = [line.strip() for line in text.split('\n') if line.strip()]
                        if lines:
                            # This is a basic fallback - PDFs without clear tables
                            # will need manual mapping anyway
                            pass
        
        return all_rows
    
    except Exception as e:
        raise Exception(f"Failed to extract from text PDF: {str(e)}")


def extract_from_scanned_pdf(pdf_path):
    """
    Extract table data from scanned PDF using OCR (pytesseract)
    Returns: List of dictionaries representing rows
    """
    try:
        # Check if tesseract is available
        try:
            pytesseract.get_tesseract_version()
        except Exception:
            raise Exception(
                "Tesseract OCR is not installed or not found in PATH. "
                "For scanned PDF support, please install Tesseract OCR from "
                "https://github.com/UB-Mannheim/tesseract/wiki. "
                "Alternatively, please upload a text-based PDF, CSV, or Excel file."
            )
        
        all_rows = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Convert page to image
                page_image = page.to_image(resolution=300)
                pil_image = page_image.original
                
                # Perform OCR
                ocr_text = pytesseract.image_to_string(pil_image)
                
                # Parse OCR text into structured data
                lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
                
                # This is a simplified parser - real OCR data needs sophisticated processing
                # For now, we'll return lines as simple row data
                # The structure mapper will help users fix any issues
                for line in lines:
                    # Split by multiple spaces or tabs
                    parts = [p.strip() for p in line.split('  ') if p.strip()]
                    if len(parts) > 1:
                        # Create a generic row structure
                        # Create a generic row structure
                        row_dict = {f'Column{i+1}': part for i, part in enumerate(parts)}
                        # Inject Page Context
                        row_dict['_SHEET_NAME_'] = f"Page {page_num + 1}"
                        all_rows.append(row_dict)
        
        return all_rows
    
    except Exception as e:
        raise Exception(f"Failed to extract from scanned PDF: {str(e)}")


def parse_pdf_file(pdf_path):
    """
    Main entry point for PDF parsing
    Automatically detects type and uses appropriate extraction method
    
    Returns: Dictionary with extraction results
    """
    try:
        if not os.path.exists(pdf_path):
            raise Exception("PDF file not found")
        
        # Detect PDF type
        pdf_type = detect_pdf_type(pdf_path)
        
        # Get number of pages
        with pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)
        
        # Extract based on type
        if pdf_type == 'text-based':
            rows = extract_from_text_pdf(pdf_path)
            extraction_method = 'table_extraction'
        elif pdf_type == 'scanned':
            rows = extract_from_scanned_pdf(pdf_path)
            extraction_method = 'ocr'
        else:
            raise Exception("Could not determine PDF type. Please ensure the file is a valid PDF.")
        
        return {
            'success': True,
            'type': pdf_type,
            'pages': num_pages,
            'extraction_method': extraction_method,
            'rows': rows,
            'row_count': len(rows)
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'type': None,
            'pages': 0,
            'rows': []
        }


# Test function (for development only)
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        test_pdf = sys.argv[1]
        result = parse_pdf_file(test_pdf)
        print("PDF Parsing Result:")
        print(f"Success: {result['success']}")
        print(f"Type: {result.get('type')}")
        print(f"Pages: {result.get('pages')}")
        print(f"Rows extracted: {result.get('row_count')}")
        if not result['success']:
            print(f"Error: {result.get('error')}")
        else:
            print(f"First 3 rows: {result['rows'][:3]}")
