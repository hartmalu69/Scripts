"""
Internet Searcher Module
Searches for treaty examples and similar patterns online.
"""

import json
from typing import List, Dict, Any, Optional


class InternetSearcher:
    """Searches for treaty examples and similar patterns."""
    
    def __init__(self):
        # Pre-built examples database (can be extended with real web search)
        self.treaty_examples = self._initialize_examples()
    
    def _initialize_examples(self) -> Dict[str, Any]:
        """Initialize a database of treaty examples."""
        return {
            'proportional_quota_share': {
                'description': 'Proportional Quota Share Treaty',
                'structure': {
                    'cedent_share': '25%',
                    'reinsurer_share': '75%',
                    'premium_basis': 'Gross written premium',
                    'loss_sharing': 'Pro-rata basis',
                    'commission': '8-12%',
                    'profit_commission': '5-10%'
                },
                'typical_clauses': [
                    'Premium payment terms (monthly/quarterly)',
                    'Loss notification and settlement',
                    'Reinsurance to closeout',
                    'Arbitration clause',
                    'Currency and exchange rate',
                    'Force majeure',
                    'Confidentiality'
                ]
            },
            'non_proportional_excess_of_loss': {
                'description': 'Non-Proportional Excess of Loss Treaty',
                'structure': {
                    'retention': '500,000 EUR',
                    'limit': '5,000,000 EUR',
                    'premium_rate': '15-25%',
                    'loss_adjustment': 'Inside limit',
                    'reinstatement': 'Unlimited'
                },
                'typical_clauses': [
                    'Attachment point definition',
                    'Limit of liability',
                    'Loss adjustment expenses',
                    'Reinstatement premium',
                    'Notification procedures',
                    'Recovery procedures',
                    'Exclusions and conditions'
                ]
            },
            'facultative_reinsurance': {
                'description': 'Facultative Reinsurance',
                'structure': {
                    'placement_basis': 'Case-by-case',
                    'underwriting_autonomy': 'Automatic acceptance option',
                    'slip_system': 'Market-standard slip',
                    'brokers_role': 'Primary intermediary',
                    'premium_share': '90-100% of cedent premium'
                },
                'typical_clauses': [
                    'Placement procedures',
                    'Underwriting information requirements',
                    'Slip and signature procedures',
                    'Premium and loss settlement',
                    'Underwriting year accounting',
                    'Broker commission',
                    'Market standards and practices'
                ]
            },
            'umbrella_facility': {
                'description': 'Umbrella Facility / Master Facility',
                'structure': {
                    'facility_limit': '50,000,000 EUR',
                    'underlying_risks': 'Multiple lines of business',
                    'attachment': 'Aggregate by LOB',
                    'renewal_terms': 'Annual with negotiation',
                    'syndicate_structure': '8-15 syndicates typical'
                },
                'typical_clauses': [
                    'Facility overview and scope',
                    'Underlying policies and coverage',
                    'Premium collection and settlement',
                    'Claims handling procedures',
                    'Underwriting guidelines',
                    'Risk management requirements',
                    'Annual renewal procedures'
                ]
            }
        }
    
    def search_similar_treaties(self, analysis: Dict[str, Any], max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for similar treaty examples based on analysis.
        
        Args:
            analysis: Treaty analysis from TreatyAnalyzer
            max_results: Maximum number of results to return
            
        Returns:
            List of similar treaty examples
        """
        results = []
        metadata = analysis.get('metadata', {})
        nature = metadata.get('nature_of_treaty', '').lower()
        
        # Match based on nature of treaty
        if 'quota' in nature or 'proportional' in nature:
            results.append(self.treaty_examples['proportional_quota_share'])
        elif 'excess' in nature or 'non-proportional' in nature:
            results.append(self.treaty_examples['non_proportional_excess_of_loss'])
        elif 'facultative' in nature:
            results.append(self.treaty_examples['facultative_reinsurance'])
        else:
            results.append(self.treaty_examples['umbrella_facility'])
        
        # Add additional related examples
        if len(results) < max_results:
            for key, example in self.treaty_examples.items():
                if example not in results and len(results) < max_results:
                    results.append(example)
        
        return results[:max_results]
    
    def get_template_structure(self, treaty_type: str) -> Optional[Dict[str, Any]]:
        """
        Get a template structure for a specific treaty type.
        
        Args:
            treaty_type: Type of treaty ('proportional_quota_share', 'non_proportional_excess_of_loss', etc.)
            
        Returns:
            Template structure or None if not found
        """
        return self.treaty_examples.get(treaty_type)
    
    def get_clause_templates(self, treaty_type: str) -> List[str]:
        """Get typical clauses for a treaty type."""
        example = self.treaty_examples.get(treaty_type)
        if example:
            return example.get('typical_clauses', [])
        return []
    
    def search_web_simulation(self, query: str) -> Dict[str, Any]:
        """
        Simulate web search (can be extended with real web scraping).
        Returns simulated search results based on query.
        """
        # This simulates web search results
        return {
            'query': query,
            'results_count': 1000,
            'top_results': [
                {
                    'title': f'{query} - Standards and Best Practices',
                    'url': 'https://example.com/treaty-standards',
                    'snippet': f'Information about {query} and industry standards.'
                }
            ],
            'related_searches': [
                f'{query} template',
                f'{query} sample',
                f'{query} clauses',
                f'{query} best practices'
            ]
        }
    
    def extract_reference_data(self, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract useful reference data from search results."""
        return {
            'query': search_results.get('query'),
            'results_found': search_results.get('results_count', 0),
            'top_sources': [r.get('url') for r in search_results.get('top_results', [])]
        }
