"""
Example PDF Creator
Main script that analyzes existing PDFs and generates multiple treaty PDFs.
"""

import os
import sys
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
    
    def create_multiple_treaties(self, source_pdf: str, cedent_name: str, 
                                reinsurer_name: str, treaty_number: str,
                                num_treaties: int = 3) -> dict:
        """
        Analyze an existing PDF and create multiple treaty examples.
        
        Args:
            source_pdf: Path to source PDF treaty
            cedent_name: Name of ceding company for new treaty
            reinsurer_name: Name of reinsurer for new treaty
            treaty_number: Treaty number for new treaty
            num_treaties: Number of treaties to generate
            
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
            
            # Step 3: Generate multiple treaties (parallelized)
            self._log(f"Step 3: Generating {num_treaties} treaties (parallel)...")
            treaty_type = analysis.get('metadata', {}).get('nature_of_treaty', 'proportional_quota_share').lower().replace(' ', '_')

            # Use a ThreadPoolExecutor to parallelize network (API) calls and IO-bound tasks
            from concurrent.futures import ThreadPoolExecutor, as_completed

            max_workers = min(8, max(1, num_treaties))
            generated_treaty_texts = [None] * num_treaties

            def _generate(i: int):
                # i is zero-based index
                self._log(f"  Generating treaty {i+1}/{num_treaties}...")
                try:
                    treaty = self.generator.generate_treaty(
                        treaty_type=treaty_type,
                        cedent_name=cedent_name,
                        reinsurer_name=reinsurer_name,
                        treaty_number=f"{treaty_number}_{i+1}",
                        analysis=analysis,
                        examples=similar_examples
                    )
                    return i, treaty
                except Exception as e:
                    return i, f"ERROR: {str(e)}"

            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = [ex.submit(_generate, idx) for idx in range(num_treaties)]
                for fut in as_completed(futures):
                    idx, treaty_text = fut.result()
                    generated_treaty_texts[idx] = treaty_text
                    short = treaty_text[:500] + '...' if treaty_text and len(treaty_text) > 500 else treaty_text
                    results['generated_treaties'].append({
                        'type': f'treaty_{idx+1}',
                        'text': short
                    })
                    self._log(f"  ✓ Treaty {idx+1} ready (length: {len(treaty_text) if treaty_text else 0})")
            
            # Step 4: Write PDFs
            self._log(f"Step 4: Writing treaties to PDF...")
            
            metadata = {
                'title': f'Reinsurance Treaty - {treaty_number}',
                'treaty_number': treaty_number,
                'cedent': cedent_name,
                'reinsurer': reinsurer_name,
                'effective_date': '01 January 2025',
                'expiry_date': '31 December 2025',
                'treaty_type': analysis.get('metadata', {}).get('nature_of_treaty', 'Unknown')
            }
            
            # Write all treaties in parallel (IO-bound)
            self._log("Step 4: Writing PDFs in parallel...")
            from concurrent.futures import ThreadPoolExecutor, as_completed

            def _write(i: int, treaty_text: str):
                pdf_metadata = metadata.copy()
                if i > 1:
                    pdf_metadata['title'] = f"{metadata['title']} - {i}"
                filename = f"Treaty_{treaty_number}_{i}"
                return i, self.pdf_writer.write_treaty_to_pdf(treaty_text, filename, pdf_metadata)

            with ThreadPoolExecutor(max_workers=min(4, max(1, num_treaties))) as ex:
                futures = [ex.submit(_write, i+1, generated_treaty_texts[i]) for i in range(num_treaties)]
                for fut in as_completed(futures):
                    i, pdf_path = fut.result()
                    if pdf_path:
                        results['generated_pdfs'].append({
                            'type': f'treaty_{i}',
                            'path': pdf_path
                        })
                        self._log(f"  ✓ PDF {i} written: {pdf_path}")
            
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


def select_folder():
    """Open a folder selection dialog."""
    try:
        from tkinter import Tk, filedialog
        root = Tk()
        root.withdraw()
        folder = filedialog.askdirectory(title="Select folder containing PDF treaties")
        root.destroy()
        return folder
    except ImportError:
        print("Tkinter not available. Please provide folder path as argument.")
        return None


def interactive_mode():
    """Run in interactive mode with GUI folder selection."""
    print("\n" + "="*60)
    print("INTERACTIVE TREATY PDF CREATOR")
    print("="*60)
    
    # Select folder
    folder = select_folder()
    if not folder:
        print("No folder selected. Exiting.")
        return
    
    print(f"\nSelected folder: {folder}")
    
    # Find PDF files
    pdf_files = [f for f in os.listdir(folder) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {folder}")
        return
    
    print(f"\nFound {len(pdf_files)} PDF file(s):")
    for i, pdf in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf}")
    
    # Select PDF to analyze
    while True:
        try:
            selection = int(input(f"\nSelect PDF file (1-{len(pdf_files)}): "))
            if 1 <= selection <= len(pdf_files):
                selected_pdf = pdf_files[selection - 1]
                break
            print(f"Please enter a number between 1 and {len(pdf_files)}")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    source_pdf_path = os.path.join(folder, selected_pdf)
    
    # Analyze the PDF to extract information
    print("\n" + "-"*60)
    print("Analyzing PDF to extract treaty information...")
    
    creator = ExamplePDFCreator()
    analyzer = TreatyAnalyzer()
    analysis = analyzer.analyze_pdf(source_pdf_path)
    
    metadata = analysis.get('metadata', {})
    
    # Extract or use defaults from analysis
    cedent = metadata.get('cedent', 'Example Cedent Inc.')
    reinsurer = metadata.get('reinsurer', 'Example Reinsurer Corp.')
    treaty_number = metadata.get('treaty_number', 'EX2025001')
    
    print(f"\n✓ Information extracted from PDF:")
    print(f"  Cedent: {cedent}")
    print(f"  Reinsurer: {reinsurer}")
    print(f"  Treaty Number: {treaty_number}")
    
    # Option to override extracted values
    print("\n" + "-"*60)
    override = input("Override extracted information? (y/n, default: n): ").strip().lower()
    
    if override == 'y':
        cedent = input(f"Enter Ceding Company name (current: '{cedent}'): ").strip() or cedent
        reinsurer = input(f"Enter Reinsurer name (current: '{reinsurer}'): ").strip() or reinsurer
        treaty_number = input(f"Enter Treaty Number (current: '{treaty_number}'): ").strip() or treaty_number
    
    # Get number of treaties
    while True:
        try:
            num_treaties = int(input("Number of treaties to generate (default: 3): ") or "3")
            if num_treaties > 0:
                break
            print("Please enter a positive number.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    region = input("Enter AWS region (default: 'eu-central-1'): ").strip() or "eu-central-1"
    
    # Create treaties
    print("\n" + "="*60)
    print(f"GENERATING {num_treaties} TREATIES...")
    print("="*60)
    
    results = creator.create_multiple_treaties(
        source_pdf=source_pdf_path,
        cedent_name=cedent,
        reinsurer_name=reinsurer,
        treaty_number=treaty_number,
        num_treaties=num_treaties
    )
    
    # Print summary
    creator.print_summary(results)


def main():
    """Main entry point."""
    # Check if running with command-line arguments
    if len(sys.argv) > 1:
        # Command-line mode
        parser = argparse.ArgumentParser(
            description='Generate multiple reinsurance treaty PDFs'
        )
        
        parser.add_argument('--interactive', action='store_true',
                           help='Run in interactive mode with folder selection')
        parser.add_argument('--mode', choices=['from-existing', 'from-scratch'], 
                           default='from-existing',
                           help='Creation mode')
        parser.add_argument('--source-pdf', type=str, 
                           help='Path to source PDF (for from-existing mode)')
        parser.add_argument('--cedent', type=str, 
                           default='Example Cedent Inc.',
                           help='Ceding company name')
        parser.add_argument('--reinsurer', type=str, 
                           default='Example Reinsurer Corp.',
                           help='Reinsurer name')
        parser.add_argument('--treaty-number', type=str, 
                           default='EX2025001',
                           help='Treaty reference number')
        parser.add_argument('--num-treaties', type=int, default=3,
                           help='Number of treaties to generate')
        parser.add_argument('--region', type=str, default='eu-central-1',
                           help='AWS region')
        
        args = parser.parse_args()
        
        # Check for interactive mode
        if args.interactive:
            interactive_mode()
            return
        
        # Initialize creator
        creator = ExamplePDFCreator(aws_region=args.region)
        
        # Execute based on mode
        if args.mode == 'from-existing':
            if not args.source_pdf:
                print("Error: --source-pdf required for from-existing mode")
                return
            results = creator.create_multiple_treaties(
                source_pdf=args.source_pdf,
                cedent_name=args.cedent,
                reinsurer_name=args.reinsurer,
                treaty_number=args.treaty_number,
                num_treaties=args.num_treaties
            )
        else:
            print("Error: from-scratch mode requires implementation")
            return
        
        # Print summary
        creator.print_summary(results)
    else:
        # Interactive mode by default when no arguments
        interactive_mode()


if __name__ == '__main__':
    main()
