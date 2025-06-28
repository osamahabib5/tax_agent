from flask import Flask, render_template, request, redirect, url_for, session, make_response, jsonify
import json
from datetime import datetime, timedelta
import logging
import os
import secrets
import datetime as dt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# App configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY') or secrets.token_hex(32),
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2)
)

def clean_numeric_input(value, default='0'):
    """Clean and convert numeric input to float"""
    if not value:
        return float(default)
    
    cleaned = str(value).strip()
    cleaned = cleaned.replace(',', '').replace('$', '').replace(' ', '')
    
    if not cleaned:
        return float(default)
    
    try:
        return float(cleaned)
    except ValueError:
        return float(default)

def validate_input(data):
    """Validate and sanitize user input"""
    errors = []
    
    # Validate income
    try:
        income = clean_numeric_input(data.get('income', '0'))
        if income < 0:
            errors.append("Income cannot be negative")
        elif income > 10000000:
            errors.append("Income amount seems unusually high")
    except (ValueError, TypeError):
        errors.append("Invalid income amount")
    
    # Validate filing status
    valid_statuses = ['single', 'married_joint', 'married_separate', 'head_of_household']
    filing_status = data.get('filing_status')
    if filing_status not in valid_statuses:
        errors.append("Invalid filing status")
    
    # Validate age
    try:
        age_str = str(data.get('age', '')).strip()
        if age_str == '':
            errors.append("Age is required")
        else:
            age = int(float(age_str))
            if age < 18 or age > 120:
                errors.append("Age must be between 18 and 120")
    except (ValueError, TypeError):
        errors.append("Invalid age - please enter a valid number")
    
    # Validate dependents
    try:
        dependents_str = str(data.get('dependents', '0')).strip()
        if dependents_str == '':
            dependents_str = '0'
        dependents = int(float(dependents_str))
        if dependents < 0:
            errors.append("Number of dependents cannot be negative")
        elif dependents > 20:
            errors.append("Number of dependents seems unusually high")
        
        # Filing status specific dependent rules
        if filing_status == 'single' and dependents > 1:
            errors.append("Single filers can have a maximum of 1 dependent")
        elif filing_status == 'head_of_household' and dependents == 0:
            errors.append("Head of Household filing status requires at least 1 dependent")
            
    except (ValueError, TypeError):
        errors.append("Invalid number of dependents - please enter a valid number")
    
    # Validate deductions
    try:
        deductions = clean_numeric_input(data.get('itemized_deductions', '0'))
        if deductions < 0:
            errors.append("Deductions cannot be negative")
    except (ValueError, TypeError):
        errors.append("Invalid deduction amount")
    
    # Validate withholding
    try:
        withholding = clean_numeric_input(data.get('withholding', '0'))
        if withholding < 0:
            errors.append("Tax withholding cannot be negative")
        
        income_val = clean_numeric_input(data.get('income', '0'))
        if withholding > income_val:
            errors.append("Tax withholding cannot exceed total income")
    except (ValueError, TypeError):
        errors.append("Invalid withholding amount")
    
    return errors

@app.before_request
def before_request():
    """Run before each request"""
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=2)
    
    if request.endpoint not in ['static']:
        logger.debug(f"Request to {request.endpoint}, Session has user_data: {'user_data' in session}")

@app.route('/')
def index():
    """Main page with tax input form"""
    if request.args.get('clear') == 'true':
        session.clear()
    
    return render_template('index.html')

@app.route('/health')
def health_check():
    logger.info("Health check accessed")
    return jsonify({
        'status': 'healthy',
        'timestamp': str(dt.datetime.now()),
        'service': 'AI Tax Return Agent',
        'version': '1.0.0'
    }), 200

@app.route('/calculate', methods=['POST'])
def calculate_tax():
    """Process tax calculation with API integration and ML optimization"""
    print("\n" + "="*60)
    print("DEBUG - Starting enhanced tax calculation")
    print("="*60)
    
    try:
        # Clear existing session data
        session.pop('user_data', None)
        session.pop('tax_result', None)
        session.pop('ml_insights', None)
        session.pop('api_enhancements', None)
        
        # Get and clean form data
        print("Step 1: Processing form data...")
        raw_income = request.form.get('income', '').strip()
        raw_filing_status = request.form.get('filing_status', '').strip()
        raw_age = request.form.get('age', '').strip()
        raw_dependents = request.form.get('dependents', '').strip()
        raw_itemized_deductions = request.form.get('itemized_deductions', '').strip()
        raw_withholding = request.form.get('withholding', '').strip()
        state = request.form.get('state', 'CA').strip()  # Optional state field
        
        # Convert data
        income = clean_numeric_input(raw_income)
        filing_status = raw_filing_status
        age = int(float(raw_age)) if raw_age else 18
        dependents = int(float(raw_dependents)) if raw_dependents else 0
        itemized_deductions = clean_numeric_input(raw_itemized_deductions)
        withholding = clean_numeric_input(raw_withholding)
        
        print(f"  Processed values: income={income}, filing_status={filing_status}")
        
        # Validation
        print("Step 2: Validation...")
        errors = []
        
        if income <= 0:
            errors.append("Please enter a valid income amount")
        if not filing_status:
            errors.append("Please select a filing status")
        if filing_status not in ['single', 'married_joint', 'married_separate', 'head_of_household']:
            errors.append("Invalid filing status")
        if age < 18 or age > 120:
            errors.append("Age must be between 18 and 120")
        if dependents < 0:
            errors.append("Dependents cannot be negative")
        if filing_status == 'single' and dependents > 1:
            errors.append("Single filers can have maximum 1 dependent")
        if filing_status == 'head_of_household' and dependents == 0:
            errors.append("Head of Household requires at least 1 dependent")
        
        if errors:
            print(f"  Validation errors: {errors}")
            return render_template('index.html', errors=errors)
        
        print("  Validation passed!")
        
        # Create processed data
        processed_data = {
            'income': income,
            'filing_status': filing_status,
            'age': age,
            'dependents': dependents,
            'itemized_deductions': itemized_deductions,
            'withholding': withholding,
            'state': state
        }
        
        # Store in session
        session['user_data'] = processed_data
        
        # Basic tax calculation (simplified for now)
        # Standard deductions for 2023
        standard_deductions = {
            'single': 13850,
            'married_joint': 27700,
            'married_separate': 13850,
            'head_of_household': 20800
        }
        
        # Use standard deduction if itemized is less
        deduction = max(standard_deductions.get(filing_status, 13850), itemized_deductions)
        taxable_income = max(0, income - deduction)
        
        # Simplified tax calculation (2023 brackets)
        tax_brackets = {
            'single': [
                (0, 11000, 0.10),
                (11000, 44725, 0.12),
                (44725, 95375, 0.22),
                (95375, 182100, 0.24),
                (182100, 231250, 0.32),
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
                (95375, 182100, 0.24),
                (182100, 231250, 0.32),
                (231250, 346875, 0.35),
                (346875, float('inf'), 0.37)
            ],
            'head_of_household': [
                (0, 15700, 0.10),
                (15700, 59850, 0.12),
                (59850, 95350, 0.22),
                (95350, 182100, 0.24),
                (182100, 231250, 0.32),
                (231250, 578100, 0.35),
                (578100, float('inf'), 0.37)
            ]
        }
        
        brackets = tax_brackets.get(filing_status, tax_brackets['single'])
        total_tax = 0
        remaining_income = taxable_income
        
        for i, (min_income, max_income, rate) in enumerate(brackets):
            if remaining_income <= 0:
                break
            
            if i == 0:  # First bracket
                bracket_income = min(remaining_income, max_income)
            else:
                bracket_income = min(remaining_income, max_income - brackets[i-1][1])
            
            total_tax += bracket_income * rate
            remaining_income -= bracket_income
        
        # Child tax credit (simplified)
        child_credit = min(dependents * 2000, total_tax)
        final_tax = max(0, total_tax - child_credit)
        
        # Calculate refund/amount owed
        refund_or_owe = withholding - final_tax
        
        # Store results
        tax_result = {
            'total_income': income,
            'total_deductions': deduction,
            'taxable_income': taxable_income,
            'federal_tax_before_credits': total_tax,
            'child_tax_credit': child_credit,
            'tax_owed': final_tax,
            'withholding': withholding,
            'refund_or_owe': refund_or_owe,
            'is_refund': refund_or_owe > 0,
            'effective_tax_rate': round((final_tax / income) * 100, 1) if income > 0 else 0,
            'marginal_tax_rate': 0
        }
        
        # Calculate marginal tax rate based on the highest bracket used
        for min_income, max_income, rate in brackets:
            if taxable_income > min_income:
                tax_result['marginal_tax_rate'] = round(rate * 100, 1)
            if taxable_income <= max_income:
                break
        
        session['tax_result'] = tax_result
        
        print(f"  Calculation complete: refund/owe = ${refund_or_owe:,.2f}")
        
        return render_template('results.html', 
                             user_data=processed_data, 
                             tax_result=tax_result)
        
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        logger.error(f"Tax calculation error: {str(e)}")
        return render_template('index.html', 
                             errors=[f"An error occurred during calculation: {str(e)}"])

@app.route('/optimization_suggestions')
def get_optimization_suggestions():
    """Get AI-powered tax optimization suggestions"""
    if 'user_data' not in session or 'tax_result' not in session:
        return redirect(url_for('index'))
    
    return render_template('optimization_suggestions.html',
                         user_data=session['user_data'],
                         tax_result=session['tax_result'])

@app.route('/clear_session')
def clear_session():
    """Clear all session data"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/new_return')
def new_return():
    """Start a new tax return"""
    session.clear()
    return redirect(url_for('index', clear='true'))

@app.route('/reset_form', methods=['POST'])
def reset_form():
    """Reset form via AJAX"""
    session.clear()
    return jsonify({'status': 'success', 'message': 'Form reset successfully'})

@app.route('/tax_form')
def generate_tax_form():
    """Generate a printable tax form"""
    if 'user_data' not in session or 'tax_result' not in session:
        return redirect(url_for('index'))
    
    return render_template('tax_form.html',
                         user_data=session['user_data'],
                         tax_result=session['tax_result'])

@app.errorhandler(404)
def not_found_error(error):
    return render_template('index.html', errors=["Page not found. Please start with the tax form."]), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('index.html', errors=["An internal server error occurred. Please try again."]), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) 