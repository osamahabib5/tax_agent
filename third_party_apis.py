import requests
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class TaxAPIIntegration:
    """Integration with third-party tax APIs for enhanced calculations"""
    
    def __init__(self):
        # API endpoints (using mock endpoints for demo)
        self.tax_brackets_api = "https://api.taxee.io/v2/federal"
        self.state_tax_api = "https://api.taxee.io/v2/state"
        self.deduction_api = "https://api.smartystreets.com/tax-deductions/v1"
        self.inflation_api = "https://api.bls.gov/publicAPI/v2/timeseries/data"
        
        # API keys (should be in environment variables)
        self.api_keys = {
            'taxee': 'demo_key_12345',
            'smartystreets': 'demo_key_67890',
            'bls': 'demo_key_abcde'
        }
        
        # Cache for API responses
        self.cache = {}
        self.cache_timeout = 3600  # 1 hour
    
    def get_current_tax_brackets(self, filing_status: str, tax_year: int = 2023) -> Dict:
        """Fetch current tax brackets from third-party API"""
        cache_key = f"brackets_{filing_status}_{tax_year}"
        
        # Check cache first
        if self._is_cached(cache_key):
            logger.info(f"Using cached tax brackets for {filing_status}")
            return self.cache[cache_key]['data']
        
        try:
            # Mock API call (in production, replace with actual API)
            brackets_data = self._mock_tax_brackets_api(filing_status, tax_year)
            
            # Cache the response
            self._cache_response(cache_key, brackets_data)
            
            logger.info(f"Retrieved tax brackets from API for {filing_status}")
            return brackets_data
            
        except Exception as e:
            logger.error(f"Error fetching tax brackets: {e}")
            # Fall back to default brackets
            return self._get_fallback_brackets(filing_status)
    
    def get_state_tax_info(self, state: str, income: float) -> Dict:
        """Fetch state tax information"""
        cache_key = f"state_{state}_{int(income/1000)}"
        
        if self._is_cached(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            state_data = self._mock_state_tax_api(state, income)
            self._cache_response(cache_key, state_data)
            
            logger.info(f"Retrieved state tax info for {state}")
            return state_data
            
        except Exception as e:
            logger.error(f"Error fetching state tax info: {e}")
            return {'state_tax': 0, 'state_rate': 0, 'deductions': 0}
    
    def get_enhanced_deductions(self, filing_status: str, income: float, 
                              location: str = None) -> Dict:
        """Get enhanced deduction recommendations from API"""
        try:
            deductions_data = self._mock_deductions_api(filing_status, income, location)
            logger.info("Retrieved enhanced deductions from API")
            return deductions_data
            
        except Exception as e:
            logger.error(f"Error fetching deductions: {e}")
            return {'additional_deductions': [], 'estimated_savings': 0}
    
    def get_inflation_adjustments(self, base_year: int = 2022, 
                                current_year: int = 2023) -> float:
        """Get inflation adjustment factor"""
        try:
            adjustment = self._mock_inflation_api(base_year, current_year)
            logger.info(f"Retrieved inflation adjustment: {adjustment}")
            return adjustment
            
        except Exception as e:
            logger.error(f"Error fetching inflation data: {e}")
            return 1.0  # No adjustment
    
    def validate_tax_calculations(self, calculation_data: Dict) -> Dict:
        """Validate calculations against third-party service"""
        try:
            validation_result = self._mock_validation_api(calculation_data)
            logger.info("Tax calculation validation completed")
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating calculations: {e}")
            return {'is_valid': True, 'confidence': 0.85, 'suggestions': []}
    
    # Mock API methods (replace with actual API calls in production)
    def _mock_tax_brackets_api(self, filing_status: str, tax_year: int) -> Dict:
        """Mock tax brackets API response"""
        brackets = {
            'single': [
                {'min': 0, 'max': 11000, 'rate': 0.10},
                {'min': 11000, 'max': 44725, 'rate': 0.12},
                {'min': 44725, 'max': 95375, 'rate': 0.22},
                {'min': 95375, 'max': 182050, 'rate': 0.24},
                {'min': 182050, 'max': 231250, 'rate': 0.32},
                {'min': 231250, 'max': 578125, 'rate': 0.35},
                {'min': 578125, 'max': float('inf'), 'rate': 0.37}
            ],
            'married_joint': [
                {'min': 0, 'max': 22000, 'rate': 0.10},
                {'min': 22000, 'max': 89450, 'rate': 0.12},
                {'min': 89450, 'max': 190750, 'rate': 0.22},
                {'min': 190750, 'max': 364200, 'rate': 0.24},
                {'min': 364200, 'max': 462500, 'rate': 0.32},
                {'min': 462500, 'max': 693750, 'rate': 0.35},
                {'min': 693750, 'max': float('inf'), 'rate': 0.37}
            ]
        }
        
        return {
            'tax_year': tax_year,
            'filing_status': filing_status,
            'brackets': brackets.get(filing_status, brackets['single']),
            'standard_deduction': self._get_standard_deduction(filing_status),
            'last_updated': datetime.now().isoformat()
        }
    
    def _mock_state_tax_api(self, state: str, income: float) -> Dict:
        """Mock state tax API response"""
        state_rates = {
            'CA': 0.133, 'NY': 0.1090, 'TX': 0.0, 'FL': 0.0,
            'WA': 0.0, 'NV': 0.0, 'TN': 0.0, 'IL': 0.0495,
            'PA': 0.0307, 'OH': 0.0399
        }
        
        rate = state_rates.get(state.upper(), 0.05)  # Default 5% if state not found
        state_tax = income * rate if rate > 0 else 0
        
        return {
            'state': state,
            'state_tax_rate': rate,
            'state_tax_owed': state_tax,
            'state_deductions': 5000 if rate > 0 else 0,
            'local_taxes': income * 0.01 if state.upper() in ['NY', 'CA'] else 0
        }
    
    def _mock_deductions_api(self, filing_status: str, income: float, 
                           location: str = None) -> Dict:
        """Mock enhanced deductions API response"""
        additional_deductions = []
        estimated_savings = 0
        
        # Income-based deduction recommendations
        if income > 50000:
            additional_deductions.append({
                'type': 'Retirement Contribution',
                'description': 'Consider maximizing 401(k) contribution',
                'potential_deduction': min(22500, income * 0.15),
                'tax_savings': min(22500, income * 0.15) * 0.22
            })
        
        if income > 75000:
            additional_deductions.append({
                'type': 'HSA Contribution',
                'description': 'Health Savings Account contribution',
                'potential_deduction': 3650 if filing_status == 'single' else 7300,
                'tax_savings': (3650 if filing_status == 'single' else 7300) * 0.22
            })
        
        estimated_savings = sum(d['tax_savings'] for d in additional_deductions)
        
        return {
            'additional_deductions': additional_deductions,
            'estimated_savings': estimated_savings,
            'confidence': 0.85,
            'last_updated': datetime.now().isoformat()
        }
    
    def _mock_inflation_api(self, base_year: int, current_year: int) -> float:
        """Mock inflation adjustment API response"""
        # Simplified inflation calculation
        inflation_rate = 0.035  # 3.5% annual inflation
        years_diff = current_year - base_year
        return (1 + inflation_rate) ** years_diff
    
    def _mock_validation_api(self, calculation_data: Dict) -> Dict:
        """Mock tax calculation validation API"""
        # Simple validation logic
        income = calculation_data.get('income', 0)
        tax_owed = calculation_data.get('tax_owed', 0)
        
        # Basic sanity checks
        effective_rate = (tax_owed / income) if income > 0 else 0
        is_valid = 0 <= effective_rate <= 0.4  # Reasonable effective rate range
        
        suggestions = []
        if effective_rate > 0.3:
            suggestions.append("Consider additional deductions to reduce tax burden")
        if effective_rate < 0.05 and income > 30000:
            suggestions.append("Verify all income sources are included")
        
        return {
            'is_valid': is_valid,
            'confidence': 0.9 if is_valid else 0.6,
            'effective_rate': effective_rate,
            'suggestions': suggestions,
            'validation_timestamp': datetime.now().isoformat()
        }
    
    def _get_standard_deduction(self, filing_status: str) -> int:
        """Get standard deduction amounts"""
        deductions = {
            'single': 13850,
            'married_joint': 27700,
            'married_separate': 13850,
            'head_of_household': 20800
        }
        return deductions.get(filing_status, 13850)
    
    def _get_fallback_brackets(self, filing_status: str) -> Dict:
        """Fallback tax brackets if API fails"""
        return self._mock_tax_brackets_api(filing_status, 2023)
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if data is in cache and not expired"""
        if cache_key not in self.cache:
            return False
        
        cache_time = self.cache[cache_key]['timestamp']
        current_time = datetime.now().timestamp()
        
        return (current_time - cache_time) < self.cache_timeout
    
    def _cache_response(self, cache_key: str, data: Dict) -> None:
        """Cache API response"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }