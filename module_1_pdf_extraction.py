"""
Module 1: PDF Text Extraction

This module extracts text from MCG guideline PDFs while preserving formatting,
extracting metadata, and identifying major sections.
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

import pdfplumber
from PyPDF2 import PdfReader


logger = logging.getLogger(__name__)


class PDFExtractor:
    """
    Extracts structured content from MCG guideline PDFs.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize PDF extractor with configuration.
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.preserve_formatting = config.get('pdf_extraction', {}).get('preserve_formatting', True)
        self.page_range = config.get('pdf_extraction', {}).get('page_range', None)
        
    def extract_pdf_content(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract complete content from PDF including metadata and sections.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing metadata, sections, and raw content
        """
        logger.info(f"Starting PDF extraction from: {pdf_path}")
        
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            # Extract text using pdfplumber for better formatting preservation
            raw_text = self._extract_text_with_formatting(pdf_path)
            
            # Extract metadata
            metadata = self.extract_metadata(pdf_path, raw_text)
            
            # Identify sections
            sections = self.identify_sections(raw_text)
            
            result = {
                "metadata": metadata,
                "sections": sections,
                "full_text": raw_text,
                "extraction_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Successfully extracted {len(sections)} sections from PDF")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting PDF content: {str(e)}")
            raise
    
    def _extract_text_with_formatting(self, pdf_path: str) -> str:
        """
        Extract text from PDF preserving formatting markers.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Text content with formatting preserved
        """
        text_content = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages_to_process = self._get_page_range(len(pdf.pages))
                
                for page_num in pages_to_process:
                    page = pdf.pages[page_num]
                    page_text = page.extract_text()
                    
                    if page_text:
                        # Add page marker
                        text_content.append(f"\n--- PAGE {page_num + 1} ---\n")
                        text_content.append(page_text)
                        
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}, trying PyPDF2")
            # Fallback to PyPDF2
            reader = PdfReader(pdf_path)
            pages_to_process = self._get_page_range(len(reader.pages))
            
            for page_num in pages_to_process:
                page = reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text_content.append(f"\n--- PAGE {page_num + 1} ---\n")
                    text_content.append(page_text)
        
        return "\n".join(text_content)
    
    def _get_page_range(self, total_pages: int) -> range:
        """
        Get range of pages to process based on configuration.
        
        Args:
            total_pages: Total number of pages in PDF
            
        Returns:
            Range object for pages to process
        """
        if self.page_range is None:
            return range(total_pages)
        else:
            start, end = self.page_range
            return range(start - 1, min(end, total_pages))
    
    def extract_metadata(self, pdf_path: str, text: str) -> Dict[str, Any]:
        """
        Extract metadata from PDF and text content.
        
        Args:
            pdf_path: Path to PDF file
            text: Extracted text content
            
        Returns:
            Dictionary containing metadata fields
        """
        metadata = {
            "pdf_filename": Path(pdf_path).name,
            "pdf_path": pdf_path,
            "extracted_date": datetime.now().isoformat()
        }
        
        # Extract guideline name (usually in first few lines)
        guideline_match = re.search(r'MCG[:\s]+(.+?)(?:\n|\r|$)', text[:1000], re.IGNORECASE)
        if guideline_match:
            metadata["guideline_name"] = guideline_match.group(1).strip()
        else:
            # Try alternative pattern
            title_match = re.search(r'^([A-Z][^.!?\n]{20,100})', text, re.MULTILINE)
            if title_match:
                metadata["guideline_name"] = title_match.group(1).strip()
        
        # Extract ORG code
        org_match = re.search(r'ORG[:\s]+(\d+)', text[:2000], re.IGNORECASE)
        if org_match:
            metadata["org_code"] = org_match.group(1)
        
        # Extract edition/version
        edition_patterns = [
            r'Edition[:\s]+(\d+(?:st|nd|rd|th)?\s*\d*)',
            r'Version[:\s]+([\d.]+)',
            r'(\d+)(?:st|nd|rd|th)\s+Edition'
        ]
        for pattern in edition_patterns:
            edition_match = re.search(pattern, text[:2000], re.IGNORECASE)
            if edition_match:
                metadata["edition"] = edition_match.group(1)
                break
        
        # Extract effective date
        date_patterns = [
            r'Effective[:\s]+(\w+\s+\d+,\s+\d{4})',
            r'(\w+\s+\d{1,2},\s+\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})'
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, text[:2000])
            if date_match:
                metadata["effective_date"] = date_match.group(1)
                break
        
        # Extract specialty
        specialty_match = re.search(r'Specialty[:\s]+(.+?)(?:\n|\r|$)', text[:2000], re.IGNORECASE)
        if specialty_match:
            metadata["specialty"] = specialty_match.group(1).strip()
        
        logger.info(f"Extracted metadata: {metadata.get('guideline_name', 'Unknown')}")
        return metadata
    
    def identify_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Identify major sections in the document by headers.
        
        Args:
            text: Full text content
            
        Returns:
            List of section dictionaries with content and metadata
        """
        section_headers = self.config.get('parser', {}).get('section_headers', [
            "Clinical Indications for Admission to Inpatient Care",
            "Alternatives to Admission",
            "Optimal Recovery Course",
            "Extended Stay",
            "Discharge Planning"
        ])
        
        sections = []
        lines = text.split('\n')
        current_section = None
        current_content = []
        current_page = 1
        
        for line in lines:
            # Track page numbers
            page_match = re.match(r'--- PAGE (\d+) ---', line)
            if page_match:
                current_page = int(page_match.group(1))
                continue
            
            # Check if line is a section header
            is_header = False
            for header in section_headers:
                if header.lower() in line.lower() and len(line) < len(header) + 50:
                    # Save previous section
                    if current_section:
                        sections.append({
                            "section_name": current_section,
                            "page_number": sections[-1]["page_number"] if sections else current_page,
                            "raw_text": "\n".join(current_content).strip(),
                            "formatting_markers": self._extract_formatting_markers("\n".join(current_content))
                        })
                    
                    # Start new section
                    current_section = header
                    current_content = []
                    is_header = True
                    
                    sections.append({
                        "section_name": current_section,
                        "page_number": current_page,
                        "raw_text": "",
                        "formatting_markers": []
                    })
                    break
            
            # Add content to current section
            if not is_header and current_section:
                current_content.append(line)
        
        # Add final section
        if current_section and current_content:
            sections[-1]["raw_text"] = "\n".join(current_content).strip()
            sections[-1]["formatting_markers"] = self._extract_formatting_markers("\n".join(current_content))
        
        logger.info(f"Identified {len(sections)} sections")
        return sections
    
    def _extract_formatting_markers(self, text: str) -> List[str]:
        """
        Extract formatting markers from text (bullets, numbers, indentation).
        
        Args:
            text: Text content
            
        Returns:
            List of formatting marker types found
        """
        markers = set()
        
        # Check for bullet points
        if re.search(r'^\s*[•●○■□▪▫◦‣⁃]', text, re.MULTILINE):
            markers.add('bullet_points')
        
        # Check for numbered lists
        if re.search(r'^\s*\d+[\.)]\s', text, re.MULTILINE):
            markers.add('numbered_list')
        
        # Check for lettered lists
        if re.search(r'^\s*[a-z][\.)]\s', text, re.MULTILINE | re.IGNORECASE):
            markers.add('lettered_list')
        
        # Check for indentation
        if re.search(r'^\s{4,}', text, re.MULTILINE):
            markers.add('indentation')
        
        # Check for tables
        if re.search(r'\|.+\|.+\|', text):
            markers.add('table')
        
        return list(markers)


def extract_pdf_content(pdf_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to extract PDF content.
    
    Args:
        pdf_path: Path to PDF file
        config: Configuration dictionary
        
    Returns:
        Extracted content dictionary
    """
    extractor = PDFExtractor(config)
    return extractor.extract_pdf_content(pdf_path)


if __name__ == "__main__":
    # Test the module independently
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Test with sample PDF
    pdf_path = r"uploads\mcg-guidelines\MCG Sepsis and Other Febrile Illness, without Focal Infection (1).pdf"
    
    try:
        result = extract_pdf_content(pdf_path, config)
        print(f"\nExtracted {len(result['sections'])} sections")
        print(f"Metadata: {result['metadata']}")
    except Exception as e:
        print(f"Error: {e}")
