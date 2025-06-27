class TaxCalculator:
    """
    Tax calculation engine with support for different filing statuses
    and basic tax rules (simplified for prototype)
    """
    
    def __init__(self):
        # 2023 Tax Brackets (simplified)
        self.tax_brackets = {
            'single': [
                (0, 11000, 0.10),
                (11000, 44725, 0.12),
                (44725, 95375, 0.22),
                (95375, 182050, 0.24),
                (182050, 231250, 0.32),
                (231250, 578125, 0.35),
                (578125, float('inf'), 0.37)
            ],
            'married_joint': [
                (0, 22000, 0.10),
                (22000, 89450, 0.12),
                (89450, 190750, 0.22),
                (190750, 364200, 0.24),
                (364200, 462500, 0.32),
                (462500, 693750, 0.35),
                (693750, float('inf'), 0.37)
            ],
            'married_separate': [
                (0, 11000, 0.10),
                (11000, 44725, 0.12),
                (44725, 95375, 0.22),
                (95375, 182050, 0.24),
                (182050, 231250, 0.32),
                (231250, 346875, 0.35),
                (346875, float('inf'), 0.37)
            ],
            'head_of_household': [
                (0, 15700, 0.10),
                (15700, 59850, 0.12),
                (59850, 95350, 0.22),
                (95350, 182050, 0.24),
                (182050, 231250, 0.32),
                (231250, 578100, 0.35),
                (578100, float('inf'), 0.37)
            ]
        }
        
        # Standard deductions for 2023
        self.standard_deductions = {
            'single': 13850,
            'married_joint': 27700,
            'married_separate': 13850,
            'head_of_household': 20800
        }
    
    def calculate_federal_tax(self, taxable_income, filing_status):
        """Calculate federal income tax using progressive tax brackets"""
        if taxable_income <= 0:
            return 0
        
        brackets = self.tax_brackets.get(filing_status, self.tax_brackets['single'])
        total_tax = 0
        
        for i, (min_income, max_income, rate) in enumerate(brackets):
            if taxable_income <= min_income:
                break
            
            taxable_in_bracket = min(taxable_income, max_income) - min_income
            tax_in_bracket = taxable_in_bracket * rate
            total_tax += tax_in_bracket
            
            if taxable_income <= max_income:
                break
        
        return round(total_tax, 2)
    
    def calculate_tax(self, user_data):
        """Main tax calculation method - FIXED INCOME PRESERVATION"""
        print(f"\nTAX CALCULATOR DEBUG:")
        print(f"  Received data: {user_data}")
        print(f"  Data types: {[(k, type(v)) for k, v in user_data.items()]}")
        
        try:
            # CRITICAL: Extract income with explicit preservation
            original_income = user_data.get('income')
            print(f"  Original income from user_data: {original_income} (type: {type(original_income)})")
            
            # Ensure income is correctly preserved as a float
            income = float(original_income)
            print(f"  Converted income: {income} (type: {type(income)})")
            
            # Extract other data
            filing_status = user_data['filing_status']
            itemized_deductions = float(user_data.get('itemized_deductions', 0))
            dependents = int(user_data.get('dependents', 0))
            withholding = float(user_data.get('withholding', 0))
            age = int(user_data.get('age', 0))
            
            print(f"  All extracted values:")
            print(f"    income: {income}")
            print(f"    filing_status: {filing_status}")
            print(f"    age: {age}")
            print(f"    dependents: {dependents}")
            print(f"    itemized_deductions: {itemized_deductions}")
            print(f"    withholding: {withholding}")
            
            # Get standard deduction
            standard_deduction = self.standard_deductions[filing_status]
            print(f"  Base standard deduction: {standard_deduction}")
            
            # Additional standard deduction for seniors (65+)
            if age >= 65:
                if filing_status in ['single', 'head_of_household']:
                    standard_deduction += 1850
                    print(f"  Added senior bonus (single/HOH): +1850")
                elif filing_status in ['married_joint', 'married_separate']:
                    standard_deduction += 1500
                    print(f"  Added senior bonus (married): +1500")
            
            print(f"  Final standard deduction: {standard_deduction}")
            
            # Choose higher deduction (standard vs itemized)
            total_deductions = max(standard_deduction, itemized_deductions)
            print(f"  Total deductions: {total_deductions}")
            
            # Calculate taxable income
            taxable_income = max(0, income - total_deductions)
            print(f"  Taxable income: {income} - {total_deductions} = {taxable_income}")
            
            # Calculate federal tax
            federal_tax = self.calculate_federal_tax(taxable_income, filing_status)
            print(f"  Federal tax: {federal_tax}")
            
            # Child tax credit (simplified - $2000 per dependent under certain income limits)
            child_tax_credit = 0
            if income < 200000:  # Simplified income limit
                child_tax_credit = dependents * 2000
            print(f"  Child tax credit: {child_tax_credit}")
            
            # Total tax after credits
            tax_after_credits = max(0, federal_tax - child_tax_credit)
            print(f"  Tax after credits: {tax_after_credits}")
            
            # Calculate refund or amount owed
            refund_or_owe = withholding - tax_after_credits
            print(f"  Refund or owe: {withholding} - {tax_after_credits} = {refund_or_owe}")
            
            # CRITICAL: Prepare detailed results - PRESERVE ORIGINAL INCOME EXACTLY
            result = {
                'gross_income': round(float(income), 2),  # Ensure exact preservation
                'standard_deduction': round(standard_deduction, 2),
                'itemized_deductions': round(itemized_deductions, 2),
                'total_deductions': round(total_deductions, 2),
                'taxable_income': round(taxable_income, 2),
                'federal_tax_before_credits': round(federal_tax, 2),
                'child_tax_credit': round(child_tax_credit, 2),
                'tax_owed': round(tax_after_credits, 2),
                'withholding': round(withholding, 2),
                'refund_or_owe': round(refund_or_owe, 2),
                'effective_tax_rate': round((tax_after_credits / income * 100) if income > 0 else 0, 2),
                'marginal_tax_rate': self.get_marginal_rate(taxable_income, filing_status)
            }
            
            print(f"  FINAL VERIFICATION:")
            print(f"    Input income: {income}")
            print(f"    Result gross_income: {result['gross_income']}")
            print(f"    Values match: {income == result['gross_income']}")
            
            return result
            
        except Exception as e:
            print(f"  TAX CALCULATOR ERROR: {e}")
            import traceback
            traceback.print_exc()
            raise e
    
    def get_marginal_rate(self, taxable_income, filing_status):
        """Get the marginal tax rate for the given income"""
        brackets = self.tax_brackets.get(filing_status, self.tax_brackets['single'])
        
        for min_income, max_income, rate in brackets:
            if min_income <= taxable_income <= max_income:
                return round(rate * 100, 1)
        
        return 0