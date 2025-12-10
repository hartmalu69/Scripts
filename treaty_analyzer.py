"""
Treaty Analyzer Module
Analyzes existing PDF treaties to extract patterns, structure, and metadata.
"""

import pdfplumber
import json
import re
from typing import Dict, List, Any, Optional


class TreatyAnalyzer:
    """Analyzes PDF treaties and extracts structural patterns."""
    
    def __init__(self):
        self.patterns = {
            'date_pattern': r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            'currency_pattern': r'(EUR|USD|GBP|JPY|CHF|AUD|CAD)\s*[\d,\.]+',
            'percentage_pattern': r'\d+(?:\.\d+)?%',
            'treaty_number_pattern': r'[A-Z]{2,4}\d{2,6}',
        }
        self.sections = []
        self.metadata = {}
        self.key_terms = []
    
    def analyze_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a PDF treaty and extract structure and patterns.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing analysis results
        """
        analysis = {
            'file_path': file_path,
            'page_count': 0,
            'sections': [],
            'metadata': {},
            'patterns_found': {},
            'key_terms': [],
            'structure_summary': {}
        }
        
        try:
            with pdfplumber.open(file_path) as pdf:
                analysis['page_count'] = len(pdf.pages)
                
                # Extract text and analyze
                full_text = ""
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    full_text += text + "\n"
                    
                    # Extract tables if present
                    tables = page.extract_tables()
                    if tables:
                        analysis['sections'].append({
                            'page': page_num,
                            'type': 'table',
                            'table_count': len(tables)
                        })
                
                # Analyze patterns in full text
                analysis['patterns_found'] = self._extract_patterns(full_text)
                analysis['metadata'] = self._extract_metadata(full_text)
                analysis['key_terms'] = self._extract_key_terms(full_text)
                analysis['structure_summary'] = self._analyze_structure(full_text)
                
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def _extract_patterns(self, text: str) -> Dict[str, List[str]]:
        """Extract all pattern matches from text."""
        patterns_found = {}
        
        for pattern_name, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                patterns_found[pattern_name] = list(set(matches))[:10]  # Top 10 unique
        
        return patterns_found
    
    def _extract_metadata(self, text: str) -> Dict[str, str]:
        """Extract metadata like treaty number, cedent, etc."""
        metadata = {}
        
        # Extract treaty number
        treaty_match = re.search(r'Treaty\s+(?:Number|No\.?):\s*([A-Z0-9\-]+)', text, re.I)
        if treaty_match:
            metadata['treaty_number'] = treaty_match.group(1)
        else:
            # Try alternative patterns
            treaty_match = re.search(r'(?:Treaty|Contract)\s+(?:Ref|Reference|ID):\s*([A-Z0-9\-]+)', text, re.I)
            if treaty_match:
                metadata['treaty_number'] = treaty_match.group(1)
        
        # Extract cedent - try multiple patterns
        cedent_patterns = [
            r'(?:Cedent|Ceding Company|Ceding Insurer):\s*([A-Za-z\s&,\.]+?)(?:\n|$)',
            r'(?:Cedent|Ceding Company):\s*([A-Za-z\s&,\.]+?)(?:Reinsurer|$)',
            r'Ceded\s+by:\s*([A-Za-z\s&,\.]+?)(?:\n|$)',
            r'(?:Insurance Company|Insured|Client):\s*([A-Za-z\s&,\.]+?)(?:\n|$)',
        ]
        
        for pattern in cedent_patterns:
            cedent_match = re.search(pattern, text, re.I)
            if cedent_match:
                cedent = cedent_match.group(1).strip()
                if len(cedent) > 3 and len(cedent) < 200:  # Reasonable company name length
                    metadata['cedent'] = cedent
                    break
        
        # Extract reinsurer - try multiple patterns
        reinsurer_patterns = [
            r'(?:Reinsurer|Reinsuring Company|Reinsurance Company):\s*([A-Za-z\s&,\.]+?)(?:\n|$)',
            r'(?:Reinsurer|Assuming Company):\s*([A-Za-z\s&,\.]+?)(?:Cedent|Commission|$)',
            r'Assumed\s+by:\s*([A-Za-z\s&,\.]+?)(?:\n|$)',
            r'(?:To be reinsured with|Reinsured with):\s*([A-Za-z\s&,\.]+?)(?:\n|$)',
        ]
        
        for pattern in reinsurer_patterns:
            reinsurer_match = re.search(pattern, text, re.I)
            if reinsurer_match:
                reinsurer = reinsurer_match.group(1).strip()
                if len(reinsurer) > 3 and len(reinsurer) < 200:  # Reasonable company name length
                    metadata['reinsurer'] = reinsurer
                    break
        
        # Extract period
        period_match = re.search(r'(?:Period|Effective|Term).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(?:to|through|-)\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text, re.I)
        if period_match:
            metadata['start_date'] = period_match.group(1)
            metadata['end_date'] = period_match.group(2)
        
        # Extract nature of treaty
        nature_patterns = ['proportional', 'non-proportional', 'excess of loss', 'quota share', 'facultative', 'excess', 'surplus']
        for pattern in nature_patterns:
            if re.search(rf'\b{pattern}\b', text, re.I):
                metadata['nature_of_treaty'] = pattern.title()
                break
        
        return metadata
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key insurance/treaty terms."""
        key_terms = []
        insurance_terms = [
            'reinsurance', 'cedent', 'ceding company', 'reinsurer',
            'premium', 'loss', 'claim', 'deductible', 'retention',
            'limit', 'coverage', 'exclusion', 'clause', 'condition',
            'party', 'broker', 'intermediary', 'settlement', 'payment'
        ]
        
        for term in insurance_terms:
            if re.search(rf'\b{term}\b', text, re.I):
                key_terms.append(term)
        
        return key_terms
    
    def _analyze_structure(self, text: str) -> Dict[str, Any]:
        """Analyze document structure."""
        lines = text.split('\n')
        headings = [line.strip() for line in lines if len(line.strip()) > 0 and line.strip().isupper() and len(line.strip()) < 100]
        
        return {
            'estimated_headings': len(headings),
            'total_lines': len(lines),
            'avg_line_length': sum(len(line) for line in lines) / max(1, len(lines)),
            'has_tables': '|' in text,
            'language': 'German' if any(word in text.lower() for word in ['der', 'die', 'das', 'und']) else 'English'
        }
    
    def generate_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the analysis."""
        summary = f"""
TREATY ANALYSIS SUMMARY
=======================
File: {analysis['file_path']}
Pages: {analysis['page_count']}

METADATA:
{json.dumps(analysis['metadata'], indent=2, ensure_ascii=False)}

PATTERNS FOUND:
{json.dumps(analysis['patterns_found'], indent=2, ensure_ascii=False)}

KEY TERMS: {', '.join(analysis['key_terms'])}

STRUCTURE:
{json.dumps(analysis['structure_summary'], indent=2, ensure_ascii=False)}
"""
        return summary
