from flask import Flask, render_template, request, redirect, url_for, session, make_response
import json
from datetime import datetime
from tax_calculator import TaxCalculator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Initialize tax calculator
tax_calc = TaxCalculator()

def validate_input(data):
    """Validate and sanitize user input"""
    errors = []
    
    # Validate income
    try:
        income = float(data.get('income', 0))
        if income < 0:
            errors.append("Income cannot be negative")
        elif income > 10000000:  # Reasonable upper limit
            errors.append("Income amount seems unusually high")
    except ValueError:
        errors.append("Invalid income amount")
    
    # Validate filing status
    valid_statuses = ['single', 'married_joint', 'married_separate', 'head_of_household']
    if data.get('filing_status') not in valid_statuses:
        errors.append("Invalid filing status")
    
    # Validate age
    try:
        age = int(data.get('age', 0))
        if age < 18 or age > 120:
            errors.append("Invalid age")
    except ValueError:
        errors.append("Invalid age")
    
    # Validate deductions
    try:
        deductions = float(data.get('itemized_deductions', 0))
        if deductions < 0:
            errors.append("Deductions cannot be negative")
    except ValueError:
        errors.append("Invalid deduction amount")
    
    return errors

@app.route('/')
def index():
    """Main page with tax input form"""
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate_tax():
    """Process tax calculation"""
    try:
        # Get form data
        user_data = {
            'income': request.form.get('income'),
            'filing_status': request.form.get('filing_status'),
            'age': request.form.get('age'),
            'itemized_deductions': request.form.get('itemized_deductions', '0'),
            'dependents': request.form.get('dependents', '0'),
            'withholding': request.form.get('withholding', '0')
        }
        
        # Validate input
        errors = validate_input(user_data)
        if errors:
            return render_template('index.html', errors=errors, form_data=user_data)
        
        # Convert to appropriate types
        processed_data = {
            'income': float(user_data['income']),
            'filing_status': user_data['filing_status'],
            'age': int(user_data['age']),
            'itemized_deductions': float(user_data['itemized_deductions']),
            'dependents': int(user_data['dependents']),
            'withholding': float(user_data['withholding'])
        }
        
        # Calculate tax
        tax_result = tax_calc.calculate_tax(processed_data)
        
        # Store in session for form generation
        session['user_data'] = processed_data
        session['tax_result'] = tax_result
        
        logger.info(f"Tax calculation completed for income: {processed_data['income']}")
        
        return render_template('results.html', 
                             user_data=processed_data, 
                             tax_result=tax_result)
    
    except Exception as e:
        logger.error(f"Error in tax calculation: {str(e)}")
        return render_template('index.html', 
                             errors=[f"An error occurred: {str(e)}"], 
                             form_data=user_data)

@app.route('/tax_form')
def generate_tax_form():
    """Generate printable tax form"""
    user_data = session.get('user_data')
    tax_result = session.get('tax_result')
    
    if not user_data or not tax_result:
        return redirect(url_for('index'))
    
    return render_template('tax_form.html', 
                         user_data=user_data, 
                         tax_result=tax_result,
                         current_year=datetime.now().year)

@app.route('/download_form')
def download_form():
    """Download tax form as text file"""
    user_data = session.get('user_data')
    tax_result = session.get('tax_result')
    
    if not user_data or not tax_result:
        return redirect(url_for('index'))
    
    # Generate form content
    form_content = f"""
    TAX RETURN FORM - {datetime.now().year}
    =====================================
    
    TAXPAYER INFORMATION:
    Filing Status: {user_data['filing_status'].replace('_', ' ').title()}
    Age: {user_data['age']}
    Number of Dependents: {user_data['dependents']}
    
    INCOME INFORMATION:
    Total Income: ${user_data['income']:,.2f}
    
    DEDUCTIONS:
    Standard Deduction: ${tax_result['standard_deduction']:,.2f}
    Itemized Deductions: ${user_data['itemized_deductions']:,.2f}
    Total Deductions: ${tax_result['total_deductions']:,.2f}
    
    TAX CALCULATION:
    Taxable Income: ${tax_result['taxable_income']:,.2f}
    Tax Owed: ${tax_result['tax_owed']:,.2f}
    Tax Withheld: ${user_data['withholding']:,.2f}
    
    RESULT:
    {"Refund Due: $" + str(abs(tax_result['refund_or_owe'])) if tax_result['refund_or_owe'] > 0 else "Amount Owed: $" + str(abs(tax_result['refund_or_owe']))}
    
    Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    response = make_response(form_content)
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = 'attachment; filename=tax_return.txt'
    
    return response

if __name__ == '__main__':
    app.run(debug=True)