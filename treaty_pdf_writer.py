"""
PDF Writer Module
Converts generated treaty text into formatted PDF documents.
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime
from typing import Optional
import os


class TreatyPDFWriter:
    """Writes treaty documents to PDF format."""
    
    def __init__(self, output_dir: str = "generated_treaties"):
        """
        Initialize PDF writer.
        
        Args:
            output_dir: Directory to save generated PDFs
        """
        self.output_dir = output_dir
        self._create_output_dir()
        self.styles = self._create_styles()
    
    def _create_output_dir(self):
        """Create output directory if it doesn't exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def _create_styles(self):
        """Create custom paragraph styles."""
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#003366'),
            spaceAfter=20,
            alignment=1  # Center
        ))
        
        # Heading style
        styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#003366'),
            spaceAfter=12,
            spaceBefore=12,
            borderPadding=5
        ))
        
        # Body style
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            alignment=4,  # Justify
            spaceAfter=10
        ))
        
        return styles
    
    def write_treaty_to_pdf(self, treaty_text: str, filename: str, 
                           metadata: Optional[dict] = None) -> str:
        """
        Write treaty text to a PDF file.
        
        Args:
            treaty_text: The treaty document text
            filename: Output filename (without extension)
            metadata: Optional metadata (title, author, treaty_number, etc.)
            
        Returns:
            Path to the created PDF file
        """
        # Prepare filename
        if not filename.endswith('.pdf'):
            filename = f"{filename}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch,
            title=metadata.get('title', 'Reinsurance Treaty') if metadata else 'Reinsurance Treaty'
        )
        
        # Build story (content)
        story = []
        
        # Add header with metadata
        if metadata:
            story.extend(self._build_header(metadata))
        
        # Add treaty content
        story.extend(self._parse_and_format_content(treaty_text))
        
        # Add footer
        story.append(Spacer(1, 0.5*inch))
        story.append(self._build_footer())
        
        # Build PDF
        try:
            doc.build(story)
            print(f"✓ PDF created successfully: {filepath}")
            return filepath
        except Exception as e:
            print(f"✗ Error creating PDF: {str(e)}")
            return None
    
    def _build_header(self, metadata: dict) -> list:
        """Build document header with metadata."""
        elements = []
        
        # Title
        title = metadata.get('title', 'REINSURANCE TREATY')
        elements.append(Paragraph(title, self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Metadata table
        meta_data = [
            ['Treaty Number:', metadata.get('treaty_number', 'N/A')],
            ['Cedent:', metadata.get('cedent', 'N/A')],
            ['Reinsurer:', metadata.get('reinsurer', 'N/A')],
            ['Effective Date:', metadata.get('effective_date', 'N/A')],
            ['Expiry Date:', metadata.get('expiry_date', 'N/A')],
            ['Treaty Type:', metadata.get('treaty_type', 'N/A')],
        ]
        
        meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E0E0E0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        elements.append(meta_table)
        elements.append(Spacer(1, 0.4*inch))
        
        return elements
    
    def _parse_and_format_content(self, text: str) -> list:
        """Parse and format the treaty content."""
        elements = []
        lines = text.split('\n')
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                elements.append(Spacer(1, 0.1*inch))
            elif stripped.startswith('#'):
                # Heading 1
                heading_text = stripped.lstrip('#').strip()
                elements.append(Paragraph(heading_text, self.styles['CustomTitle']))
                elements.append(Spacer(1, 0.1*inch))
            elif stripped.startswith('##'):
                # Heading 2
                heading_text = stripped.lstrip('#').strip()
                elements.append(Paragraph(heading_text, self.styles['CustomHeading']))
                elements.append(Spacer(1, 0.05*inch))
            elif stripped.startswith('###'):
                # Heading 3
                heading_text = stripped.lstrip('#').strip()
                elements.append(Paragraph(heading_text, self.styles['Heading3']))
            elif stripped.startswith('-') or stripped.startswith('•'):
                # Bullet point
                text_content = stripped.lstrip('-•').strip()
                elements.append(Paragraph(f"• {text_content}", self.styles['CustomBody']))
            else:
                # Regular paragraph
                elements.append(Paragraph(stripped, self.styles['CustomBody']))
        
        return elements
    
    def _build_footer(self) -> Paragraph:
        """Build document footer."""
        footer_text = f"<i>Document generated on {datetime.now().strftime('%d %B %Y')} - Confidential</i>"
        return Paragraph(footer_text, self.styles['Normal'])
    
    def write_multiple_treaties(self, treaties: dict) -> list:
        """
        Write multiple treaties to PDF files.
        
        Args:
            treaties: Dictionary with treaty_name: (treaty_text, metadata)
            
        Returns:
            List of created file paths
        """
        created_files = []
        
        for treaty_name, (treaty_text, metadata) in treaties.items():
            filepath = self.write_treaty_to_pdf(treaty_text, treaty_name, metadata)
            if filepath:
                created_files.append(filepath)
        
        return created_files
    
    def batch_write_with_variations(self, base_treaty: str, variations: list, 
                                   base_metadata: dict, output_prefix: str) -> list:
        """
        Write a base treaty and its variations to PDF.
        
        Args:
            base_treaty: The base treaty text
            variations: List of variation texts
            base_metadata: Base metadata dictionary
            output_prefix: Prefix for output files
            
        Returns:
            List of created file paths
        """
        created_files = []
        
        # Write base treaty
        base_filename = f"{output_prefix}_base"
        filepath = self.write_treaty_to_pdf(base_treaty, base_filename, base_metadata)
        if filepath:
            created_files.append(filepath)
        
        # Write variations
        for i, variation in enumerate(variations, 1):
            var_metadata = base_metadata.copy()
            var_metadata['title'] = f"{base_metadata.get('title', 'Treaty')} - Variation {i}"
            var_filename = f"{output_prefix}_variation_{i}"
            filepath = self.write_treaty_to_pdf(variation, var_filename, var_metadata)
            if filepath:
                created_files.append(filepath)
        
        return created_files
    
    @staticmethod
    def get_output_directory():
        """Get the output directory for generated PDFs."""
        return "generated_treaties"
