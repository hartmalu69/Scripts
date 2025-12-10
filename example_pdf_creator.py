"""
Example PDF Creator
Main script that analyzes existing PDFs, searches for examples, 
and generates new treaty PDFs.
"""

import os
import json
import argparse
from datetime import datetime
from treaty_analyzer import TreatyAnalyzer
from treaty_searcher import InternetSearcher
from treaty_generator import TreatyGenerator
from treaty_pdf_writer import TreatyPDFWriter


class ExamplePDFCreator:
    """Main orchestrator for treaty PDF creation."""
    
    def __init__(self, aws_region: str = 'eu-central-1'):
        """Initialize the creator with all modules."""
        self.analyzer = TreatyAnalyzer()
        self.searcher = InternetSearcher()
        self.generator = TreatyGenerator(region=aws_region)
        self.pdf_writer = TreatyPDFWriter()
        self.log = []
    
    def create_from_existing_pdf(self, source_pdf: str, cedent_name: str, 
                                reinsurer_name: str, treaty_number: str,
                                num_variations: int = 2) -> dict:
        """
        Analyze an existing PDF and create similar treaty examples.
        
        Args:
            source_pdf: Path to source PDF treaty
            cedent_name: Name of ceding company for new treaty
            reinsurer_name: Name of reinsurer for new treaty
            treaty_number: Treaty number for new treaty
            num_variations: Number of variations to generate
            
        Returns:
            Dictionary with creation results
        """
        results = {
            'status': 'success',
            'source_pdf': source_pdf,
            'analysis': {},
            'generated_treaties': [],
            'generated_pdfs': [],
            'log': []
        }
        
        try:
            # Step 1: Analyze existing PDF
            self._log(f"Step 1: Analyzing existing PDF: {source_pdf}")
            if not os.path.exists(source_pdf):
                raise FileNotFoundError(f"Source PDF not found: {source_pdf}")
            
            analysis = self.analyzer.analyze_pdf(source_pdf)
            results['analysis'] = analysis
            self._log(f"✓ Analysis complete. Treaty type: {analysis.get('metadata', {}).get('nature_of_treaty', 'Unknown')}")
            
            # Step 2: Search for similar examples
            self._log(f"Step 2: Searching for similar treaty examples...")
            similar_examples = self.searcher.search_similar_treaties(analysis, max_results=2)
            self._log(f"✓ Found {len(similar_examples)} similar examples")
            
            # Step 3: Generate main treaty
            self._log(f"Step 3: Generating main treaty...")
            treaty_type = analysis.get('metadata', {}).get('nature_of_treaty', 'proportional_quota_share').lower().replace(' ', '_')
            
            main_treaty = self.generator.generate_treaty(
                treaty_type=treaty_type,
                cedent_name=cedent_name,
                reinsurer_name=reinsurer_name,
                treaty_number=treaty_number,
                analysis=analysis,
                examples=similar_examples
            )
            results['generated_treaties'].append({
                'type': 'main',
                'text': main_treaty[:500] + '...' if len(main_treaty) > 500 else main_treaty
            })
            self._log(f"✓ Main treaty generated ({len(main_treaty)} characters)")
            
            # Step 4: Generate variations
            if num_variations > 0:
                self._log(f"Step 4: Generating {num_variations} treaty variations...")
                variations = self.generator.generate_variations(main_treaty, num_variations)
                results['generated_treaties'].extend([
                    {'type': f'variation_{i+1}', 'text': v[:500] + '...' if len(v) > 500 else v}
                    for i, v in enumerate(variations)
                ])
                self._log(f"✓ Generated {len(variations)} variations")
            
            # Step 5: Write PDFs
            self._log(f"Step 5: Writing treaties to PDF...")
            
            metadata = {
                'title': f'Reinsurance Treaty - {treaty_number}',
                'treaty_number': treaty_number,
                'cedent': cedent_name,
                'reinsurer': reinsurer_name,
                'effective_date': '01 January 2025',
                'expiry_date': '31 December 2025',
                'treaty_type': analysis.get('metadata', {}).get('nature_of_treaty', 'Unknown')
            }
            
            # Write main treaty
            main_filename = f"Treaty_{treaty_number}_Main"
            pdf_path = self.pdf_writer.write_treaty_to_pdf(main_treaty, main_filename, metadata)
            if pdf_path:
                results['generated_pdfs'].append({'type': 'main', 'path': pdf_path})
            
            # Write variations
            for i, variation in enumerate(variations, 1):
                var_metadata = metadata.copy()
                var_metadata['title'] = f"{metadata['title']} - Variation {i}"
                var_filename = f"Treaty_{treaty_number}_Variation_{i}"
                pdf_path = self.pdf_writer.write_treaty_to_pdf(variation, var_filename, var_metadata)
                if pdf_path:
                    results['generated_pdfs'].append({
                        'type': f'variation_{i}',
                        'path': pdf_path
                    })
            
            self._log(f"✓ Created {len(results['generated_pdfs'])} PDF files")
            
            # Save results log
            self._save_results_log(results)
            
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            self._log(f"✗ Error: {str(e)}")
        
        results['log'] = self.log
        return results
    
    def create_from_scratch(self, treaty_type: str, cedent_name: str, 
                           reinsurer_name: str, treaty_number: str,
                           num_variations: int = 2) -> dict:
        """
        Create new treaty examples from scratch without an existing PDF.
        
        Args:
            treaty_type: Type of treaty ('proportional_quota_share', etc.)
            cedent_name: Name of ceding company
            reinsurer_name: Name of reinsurer
            treaty_number: Treaty number
            num_variations: Number of variations to generate
            
        Returns:
            Dictionary with creation results
        """
        results = {
            'status': 'success',
            'treaty_type': treaty_type,
            'generated_treaties': [],
            'generated_pdfs': [],
            'log': []
        }
        
        try:
            # Step 1: Search for examples of this treaty type
            self._log(f"Step 1: Searching for {treaty_type} examples...")
            example = self.searcher.get_template_structure(treaty_type)
            if not example:
                raise ValueError(f"Unknown treaty type: {treaty_type}")
            self._log(f"✓ Found template for {treaty_type}")
            
            # Step 2: Generate main treaty
            self._log(f"Step 2: Generating main treaty...")
            main_treaty = self.generator.generate_treaty(
                treaty_type=treaty_type,
                cedent_name=cedent_name,
                reinsurer_name=reinsurer_name,
                treaty_number=treaty_number,
                examples=[example]
            )
            results['generated_treaties'].append({'type': 'main', 'text': main_treaty[:500] + '...'})
            self._log(f"✓ Main treaty generated")
            
            # Step 3: Generate variations
            if num_variations > 0:
                self._log(f"Step 3: Generating {num_variations} variations...")
                variations = self.generator.generate_variations(main_treaty, num_variations)
                results['generated_treaties'].extend([
                    {'type': f'variation_{i+1}', 'text': v[:500] + '...'}
                    for i, v in enumerate(variations)
                ])
                self._log(f"✓ Generated {len(variations)} variations")
            
            # Step 4: Write PDFs
            self._log(f"Step 4: Writing treaties to PDF...")
            
            metadata = {
                'title': f'Reinsurance Treaty - {treaty_number}',
                'treaty_number': treaty_number,
                'cedent': cedent_name,
                'reinsurer': reinsurer_name,
                'effective_date': '01 January 2025',
                'expiry_date': '31 December 2025',
                'treaty_type': treaty_type.replace('_', ' ').title()
            }
            
            # Write main treaty
            main_filename = f"Treaty_{treaty_number}_Main"
            pdf_path = self.pdf_writer.write_treaty_to_pdf(main_treaty, main_filename, metadata)
            if pdf_path:
                results['generated_pdfs'].append({'type': 'main', 'path': pdf_path})
            
            # Write variations
            for i, variation in enumerate(variations, 1):
                var_metadata = metadata.copy()
                var_metadata['title'] = f"{metadata['title']} - Variation {i}"
                var_filename = f"Treaty_{treaty_number}_Variation_{i}"
                pdf_path = self.pdf_writer.write_treaty_to_pdf(variation, var_filename, var_metadata)
                if pdf_path:
                    results['generated_pdfs'].append({'type': f'variation_{i}', 'path': pdf_path})
            
            self._log(f"✓ Created {len(results['generated_pdfs'])} PDF files")
            self._save_results_log(results)
            
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            self._log(f"✗ Error: {str(e)}")
        
        results['log'] = self.log
        return results
    
    def _log(self, message: str):
        """Log a message."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.log.append(log_entry)
        print(log_entry)
    
    def _save_results_log(self, results: dict):
        """Save results to a JSON file."""
        log_filename = f"creation_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Prepare log data
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'status': results.get('status'),
            'generated_pdfs': results.get('generated_pdfs', []),
            'log_messages': results.get('log', [])
        }
        
        with open(log_filename, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        self._log(f"✓ Results saved to {log_filename}")
    
    def print_summary(self, results: dict):
        """Print a summary of the creation results."""
        print("\n" + "="*60)
        print("TREATY GENERATION SUMMARY")
        print("="*60)
        print(f"Status: {results['status'].upper()}")
        print(f"PDFs Generated: {len(results.get('generated_pdfs', []))}")
        
        if results.get('generated_pdfs'):
            print("\nGenerated Files:")
            for pdf_info in results['generated_pdfs']:
                print(f"  - {pdf_info['type']}: {pdf_info['path']}")
        
        if results.get('error'):
            print(f"\nError: {results['error']}")
        
        print("="*60 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate example reinsurance treaty PDFs'
    )
    
    parser.add_argument('--mode', choices=['from-existing', 'from-scratch'], 
                       default='from-existing',
                       help='Creation mode')
    parser.add_argument('--source-pdf', type=str, 
                       help='Path to source PDF (for from-existing mode)')
    parser.add_argument('--treaty-type', type=str, 
                       default='proportional_quota_share',
                       help='Treaty type for from-scratch mode')
    parser.add_argument('--cedent', type=str, 
                       default='Example Cedent Inc.',
                       help='Ceding company name')
    parser.add_argument('--reinsurer', type=str, 
                       default='Example Reinsurer Corp.',
                       help='Reinsurer name')
    parser.add_argument('--treaty-number', type=str, 
                       default='EX2025001',
                       help='Treaty reference number')
    parser.add_argument('--variations', type=int, default=2,
                       help='Number of variations to generate')
    parser.add_argument('--region', type=str, default='eu-central-1',
                       help='AWS region')
    
    args = parser.parse_args()
    
    # Initialize creator
    creator = ExamplePDFCreator(aws_region=args.region)
    
    # Execute based on mode
    if args.mode == 'from-existing':
        if not args.source_pdf:
            print("Error: --source-pdf required for from-existing mode")
            return
        results = creator.create_from_existing_pdf(
            source_pdf=args.source_pdf,
            cedent_name=args.cedent,
            reinsurer_name=args.reinsurer,
            treaty_number=args.treaty_number,
            num_variations=args.variations
        )
    else:
        results = creator.create_from_scratch(
            treaty_type=args.treaty_type,
            cedent_name=args.cedent,
            reinsurer_name=args.reinsurer,
            treaty_number=args.treaty_number,
            num_variations=args.variations
        )
    
    # Print summary
    creator.print_summary(results)


if __name__ == '__main__':
    main()
