"""
Treaty Generator Module
Generates new treaty examples using Claude and templates.
"""

import json
import boto3
from typing import Dict, Any, Optional
from botocore.config import Config


class TreatyGenerator:
    """Generates new treaty documents using Claude API."""
    
    def __init__(self, region: str = 'eu-central-1', model_id: str = 'eu.anthropic.claude-sonnet-4-5-20250929-v1:0'):
        """
        Initialize the treaty generator.
        
        Args:
            region: AWS region for Bedrock
            model_id: Claude model ID
        """
        self.region = region
        self.model_id = model_id
        self.bedrock_client = self._init_bedrock_client()
    
    def _init_bedrock_client(self):
        """Initialize Bedrock client."""
        config = Config(
            region_name=self.region,
            retries={'max_attempts': 1, 'mode': 'adaptive'},
            read_timeout=360
        )
        return boto3.client('bedrock-runtime', config=config)
    
    def generate_treaty(self, 
                       treaty_type: str,
                       cedent_name: str,
                       reinsurer_name: str,
                       treaty_number: str,
                       analysis: Optional[Dict[str, Any]] = None,
                       examples: Optional[list] = None) -> str:
        """
        Generate a new treaty document.
        
        Args:
            treaty_type: Type of treaty to generate
            cedent_name: Name of the ceding company
            reinsurer_name: Name of the reinsurer
            treaty_number: Treaty reference number
            analysis: Optional analysis from existing treaty
            examples: Optional list of example treaties
            
        Returns:
            Generated treaty text
        """
        
        # Build context from analysis and examples
        context = self._build_context(analysis, examples)
        
        # Create system prompt
        system_prompt = self._create_system_prompt(treaty_type)
        
        # Create task prompt
        task_prompt = self._create_task_prompt(
            treaty_type, cedent_name, reinsurer_name, treaty_number, context
        )
        
        # Call Claude
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 4096,
                    'temperature': 0.7,
                    'messages': [
                        {
                            'role': 'user',
                            'content': [{'type': 'text', 'text': system_prompt + '\n\n' + task_prompt}]
                        }
                    ]
                })
            )
            
            body = json.loads(response['body'].read())
            generated_text = body['content'][0]['text']
            return generated_text
            
        except Exception as e:
            print(f"Error calling Claude API: {str(e)}")
            return f"Error generating treaty: {str(e)}"
    
    def _build_context(self, analysis: Optional[Dict[str, Any]], examples: Optional[list]) -> str:
        """Build context from analysis and examples."""
        context_parts = []
        
        if analysis:
            context_parts.append("ANALYSIS OF EXISTING TREATY:")
            context_parts.append(f"- Treaty Type: {analysis.get('metadata', {}).get('nature_of_treaty', 'Unknown')}")
            context_parts.append(f"- Key Terms: {', '.join(analysis.get('key_terms', [])[:5])}")
            context_parts.append(f"- Patterns Found: {json.dumps(analysis.get('patterns_found', {}), ensure_ascii=False)}")
        
        if examples:
            context_parts.append("\nRELATED TREATY EXAMPLES:")
            for i, example in enumerate(examples, 1):
                context_parts.append(f"\nExample {i}: {example.get('description', 'Treaty Example')}")
                structure = example.get('structure', {})
                for key, value in structure.items():
                    context_parts.append(f"  - {key}: {value}")
        
        return '\n'.join(context_parts)
    
    def _create_system_prompt(self, treaty_type: str) -> str:
        """Create system prompt for treaty generation."""
        return f"""
You are an expert reinsurance underwriter and contract specialist with 20+ years of experience.
You are tasked with generating professional, legally compliant reinsurance treaty documents.

GUIDELINES:
- Generate comprehensive, professional reinsurance treaty documents
- Use industry-standard language and structures
- Include all necessary clauses and conditions
- Ensure clarity and legal precision
- Follow market standards and practices
- Be specific with percentages, amounts, and terms
- Use professional formatting with clear sections

TREATY TYPE: {treaty_type}

Generate a complete, realistic treaty document that:
1. Follows professional reinsurance standards
2. Includes all necessary clauses
3. Uses realistic numbers and terms
4. Is formatted for readability
5. Could be used as a template for actual treaties
"""
    
    def _create_task_prompt(self, treaty_type: str, cedent_name: str, 
                          reinsurer_name: str, treaty_number: str, 
                          context: str) -> str:
        """Create task prompt for treaty generation."""
        return f"""
Generate a professional reinsurance treaty document with the following specifications:

TREATY SPECIFICATIONS:
- Treaty Type: {treaty_type}
- Ceding Company: {cedent_name}
- Reinsurer: {reinsurer_name}
- Treaty Number: {treaty_number}
- Effective Date: 01 January 2025
- Expiry Date: 31 December 2025

CONTEXT FOR GENERATION:
{context}

REQUIREMENTS:
1. Create a complete treaty document with professional header
2. Include all standard clauses for this treaty type
3. Use realistic and industry-standard terms
4. Include specific percentages, limits, and amounts
5. Add professional legal language
6. Structure with clear sections and subsections
7. Include definitions, conditions, and procedures
8. Make it suitable as a real treaty document or template

Please generate the complete treaty document:
"""
    
    def generate_variations(self, base_treaty: str, num_variations: int = 3) -> list:
        """
        Generate variations of a treaty with different terms.
        
        Args:
            base_treaty: The base treaty text
            num_variations: Number of variations to create
            
        Returns:
            List of treaty variations
        """
        variations = []
        
        variation_prompt = f"""
Based on this treaty:
{base_treaty[:500]}...

Generate {num_variations} professional variations with:
1. Different premium rates (vary by ±20%)
2. Different retention/limit levels
3. Different commission structures
4. Different renewal terms

Provide each variation as a concise treaty summary with key commercial terms.
"""
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 2048,
                    'temperature': 0.8,
                    'messages': [
                        {
                            'role': 'user',
                            'content': [{'type': 'text', 'text': variation_prompt}]
                        }
                    ]
                })
            )
            
            body = json.loads(response['body'].read())
            variations_text = body['content'][0]['text']
            
            # Parse variations
            variations = [v.strip() for v in variations_text.split('\n\n') if v.strip()]
            
        except Exception as e:
            print(f"Error generating variations: {str(e)}")
        
        return variations
