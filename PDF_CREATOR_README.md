# Example PDF Creator - User Guide

A comprehensive system for analyzing reinsurance treaty PDFs and generating similar example treaties in PDF format.

## Features

- **Analyze Existing Treaties**: Extract patterns, structure, and metadata from PDF treaties
- **Search Examples**: Find similar treaty templates and industry standards
- **Generate New Treaties**: Create realistic treaty documents using AI (Claude)
- **Create Variations**: Generate multiple variations with different commercial terms
- **Export to PDF**: Professional PDF formatting with proper structure and styling

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install System Dependencies

#### For Windows (Tesseract OCR):
```bash
# Using Chocolatey
choco install tesseract

# Or download and install from: https://github.com/UB-Mannheim/tesseract/wiki
```

#### For macOS:
```bash
brew install tesseract
```

#### For Linux:
```bash
sudo apt-get install tesseract-ocr
```

### 3. Configure AWS Credentials

Ensure you have AWS credentials configured for Bedrock access:

```bash
# Via environment variables
set AWS_ACCESS_KEY_ID=your_key
set AWS_SECRET_ACCESS_KEY=your_secret

# Or via AWS CLI
aws configure
```

## Usage

### Mode 1: Generate from Existing PDF

Analyze an existing treaty and create similar examples:

```bash
python example_pdf_creator.py \
  --mode from-existing \
  --source-pdf "path/to/your/treaty.pdf" \
  --cedent "Your Company Name" \
  --reinsurer "Reinsurer Name" \
  --treaty-number "TREATY2025001" \
  --variations 3
```

### Mode 2: Generate from Scratch

Create treaties from scratch using a specific template:

```bash
python example_pdf_creator.py \
  --mode from-scratch \
  --treaty-type proportional_quota_share \
  --cedent "Your Company Name" \
  --reinsurer "Reinsurer Name" \
  --treaty-number "TREATY2025001" \
  --variations 2
```

### Supported Treaty Types

- `proportional_quota_share` - Proportional Quota Share treaties
- `non_proportional_excess_of_loss` - Non-Proportional Excess of Loss treaties
- `facultative_reinsurance` - Facultative Reinsurance
- `umbrella_facility` - Umbrella/Master Facility treaties

### Command-Line Options

- `--mode` - `from-existing` or `from-scratch` (default: `from-existing`)
- `--source-pdf` - Path to source PDF (required for `from-existing`)
- `--treaty-type` - Treaty type (for `from-scratch`)
- `--cedent` - Ceding company name
- `--reinsurer` - Reinsurer name
- `--treaty-number` - Treaty reference number
- `--variations` - Number of variations to generate (default: 2)
- `--region` - AWS region (default: `eu-central-1`)

## Output

Generated PDFs are saved in the `generated_treaties/` directory with the following naming convention:

- `Treaty_{NUMBER}_Main.pdf` - Main generated treaty
- `Treaty_{NUMBER}_Variation_1.pdf` - First variation
- `Treaty_{NUMBER}_Variation_2.pdf` - Second variation
- etc.

A creation log is also saved as `creation_log_YYYYMMDD_HHMMSS.json` with detailed information about the generation process.

## Architecture

### Module Structure

```
example_pdf_creator.py (main orchestrator)
├── treaty_analyzer.py (analyzes existing PDFs)
├── treaty_searcher.py (searches for similar examples)
├── treaty_generator.py (generates new treaties with Claude)
└── treaty_pdf_writer.py (converts text to PDF)
```

### Workflow

1. **Analyze**: Parse existing PDF to extract patterns and metadata
2. **Search**: Find similar treaty templates and examples
3. **Generate**: Use Claude API to create new treaties based on analysis
4. **Variations**: Create multiple variations with different terms
5. **Export**: Write treaties to professional PDF documents

## Module Details

### TreatyAnalyzer

Extracts:
- Treaty metadata (number, cedent, dates, nature)
- Patterns (dates, currencies, percentages, treaty numbers)
- Key insurance terms
- Document structure and layout

### InternetSearcher

Provides:
- Pre-built template library for different treaty types
- Typical clause examples
- Commercial term suggestions
- Industry standards

### TreatyGenerator

Uses Claude API to:
- Generate complete treaty documents
- Incorporate analysis and examples
- Create realistic commercial terms
- Generate variations with different structures

### TreatyPDFWriter

Creates professional PDFs with:
- Metadata header with treaty information
- Structured sections and headings
- Professional formatting and styling
- Document footer with generation date

## Examples

### Example 1: Analyze and Generate from Existing Treaty

```bash
python example_pdf_creator.py \
  --mode from-existing \
  --source-pdf "anonym - select - Biscaya Marine&Aviation 2025.pdf" \
  --cedent "New Cedent Company" \
  --reinsurer "New Reinsurer Corp" \
  --treaty-number "NEW2025001" \
  --variations 3
```

Output:
- `Treaty_NEW2025001_Main.pdf`
- `Treaty_NEW2025001_Variation_1.pdf`
- `Treaty_NEW2025001_Variation_2.pdf`
- `Treaty_NEW2025001_Variation_3.pdf`
- `creation_log_20250110_143022.json`

### Example 2: Create Excess of Loss Variations

```bash
python example_pdf_creator.py \
  --mode from-scratch \
  --treaty-type non_proportional_excess_of_loss \
  --cedent "Insurance Company AG" \
  --reinsurer "Global Reinsurance Ltd" \
  --treaty-number "EOL2025001" \
  --variations 2
```

## Advanced Usage

### Python API

You can also use the modules programmatically:

```python
from example_pdf_creator import ExamplePDFCreator

# Initialize creator
creator = ExamplePDFCreator(aws_region='eu-central-1')

# Generate from existing PDF
results = creator.create_from_existing_pdf(
    source_pdf="treaty.pdf",
    cedent_name="Company A",
    reinsurer_name="Company B",
    treaty_number="TEST2025001",
    num_variations=2
)

# Print summary
creator.print_summary(results)
```

### Direct Module Access

```python
from treaty_analyzer import TreatyAnalyzer
from treaty_searcher import InternetSearcher
from treaty_generator import TreatyGenerator
from treaty_pdf_writer import TreatyPDFWriter

# Analyze a treaty
analyzer = TreatyAnalyzer()
analysis = analyzer.analyze_pdf("treaty.pdf")
print(analyzer.generate_summary(analysis))

# Search for examples
searcher = InternetSearcher()
examples = searcher.search_similar_treaties(analysis)

# Generate treaties
generator = TreatyGenerator()
treaty = generator.generate_treaty(
    treaty_type="proportional_quota_share",
    cedent_name="Cedent Inc",
    reinsurer_name="Reinsurer Corp",
    treaty_number="EX2025001"
)

# Write to PDF
writer = TreatyPDFWriter()
pdf_path = writer.write_treaty_to_pdf(treaty, "my_treaty", metadata={...})
```

## Troubleshooting

### Issue: Tesseract not found

**Solution**: Ensure Tesseract is installed and in PATH:

```bash
# Test installation
tesseract --version

# If not in PATH, set PYTESSERACT_PATH environment variable:
set PYTESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Issue: AWS credentials not found

**Solution**: Configure AWS credentials:

```bash
aws configure
# Enter your Access Key ID, Secret Access Key, and region
```

### Issue: PDF contains only images (scanned document)

**Solution**: The system will automatically use Tesseract OCR for scanned PDFs. Ensure Tesseract is properly installed (see above).

### Issue: Claude API errors

**Solution**: 
- Check AWS region is correct
- Verify Bedrock access is enabled for your AWS account
- Check Claude model ID is available in your region

## Performance Tips

1. **For large PDFs**: The system processes page-by-page, which may take time for documents with 100+ pages
2. **OCR performance**: OCR is slower than text extraction; consider using text-based PDFs when possible
3. **API costs**: Each treaty generation makes API calls to Claude; monitor usage for cost management
4. **Parallel processing**: Multiple treaty generation calls can be parallelized

## License

This tool is provided as-is for creating example reinsurance treaty documents.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the creation log file generated during execution
3. Ensure all dependencies are correctly installed
4. Verify AWS credentials and region settings

## Future Enhancements

Potential improvements:
- Web search integration for real-world treaty examples
- Custom template creation and management
- Batch processing of multiple source PDFs
- Fine-tuning based on historical treaty database
- Interactive UI for parameter selection
- Template versioning and management
- Multi-language support
