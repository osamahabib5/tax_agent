from flask import Flask, render_template, request, redirect, url_for, session, make_response, jsonify
import json
from datetime import datetime, timedelta
from tax_calculator import TaxCalculator
import logging
from config import DevelopmentConfig
import os
import secrets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

# App configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY') or secrets.token_hex(32),
    SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2)
)

# Initialize tax calculator
tax_calc = TaxCalculator()

def clean_numeric_input(value, default='0'):
    """Clean and convert numeric input to float"""
    if not value:
        return float(default)
    
    # Convert to string and strip whitespace
    cleaned = str(value).strip()
    
    # Remove common formatting characters
    cleaned = cleaned.replace(',', '').replace('$', '').replace(' ', '')
    
    # Handle empty string after cleaning
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
        
        # Cross-validate withholding against income
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

@app.route('/calculate', methods=['POST'])
def calculate_tax():
    """Process tax calculation - FIXED INCOME PROCESSING"""
    print("\n" + "="*60)
    print("DEBUG - Starting tax calculation")
    print("="*60)
    
    try:
        # Clear any existing session data
        session.pop('user_data', None)
        session.pop('tax_result', None)
        
        # Step 1: Get raw form data with detailed logging
        print("Step 1: Getting raw form data...")
        raw_income = request.form.get('income', '').strip()
        raw_filing_status = request.form.get('filing_status', '').strip()
        raw_age = request.form.get('age', '').strip()
        raw_dependents = request.form.get('dependents', '').strip()
        raw_itemized_deductions = request.form.get('itemized_deductions', '').strip()
        raw_withholding = request.form.get('withholding', '').strip()
        
        print(f"  Raw form values:")
        print(f"    income: '{raw_income}'")
        print(f"    filing_status: '{raw_filing_status}'")
        print(f"    age: '{raw_age}'")
        print(f"    dependents: '{raw_dependents}'")
        print(f"    itemized_deductions: '{raw_itemized_deductions}'")
        print(f"    withholding: '{raw_withholding}'")
        
        # Step 2: Clean and convert data with explicit tracking
        print("\nStep 2: Cleaning and converting data...")
        
        # Clean income with detailed tracking
        print(f"  Processing income:")
        print(f"    Raw income: '{raw_income}'")
        income = clean_numeric_input(raw_income)
        print(f"    Cleaned income: {income}")
        print(f"    Income type: {type(income)}")
        
        # Clean other fields
        filing_status = raw_filing_status
        age = int(float(raw_age)) if raw_age else 18
        dependents = int(float(raw_dependents)) if raw_dependents else 0
        itemized_deductions = clean_numeric_input(raw_itemized_deductions)
        withholding = clean_numeric_input(raw_withholding)
        
        print(f"  All converted values:")
        print(f"    income: {income}")
        print(f"    filing_status: '{filing_status}'")
        print(f"    age: {age}")
        print(f"    dependents: {dependents}")
        print(f"    itemized_deductions: {itemized_deductions}")
        print(f"    withholding: {withholding}")
        
        # Step 3: Validation
        print("\nStep 3: Validation...")
        errors = []
        
        if income <= 0:
            errors.append("Please enter a valid income amount")
        if income > 10000000:
            errors.append("Income seems unusually high")
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
        
        # Step 4: Create processed data dictionary - ENSURE INCOME IS PRESERVED
        print("\nStep 4: Creating processed data dictionary...")
        processed_data = {
            'income': float(income),  # Explicit conversion to ensure it's preserved as entered
            'filing_status': filing_status,
            'age': age,
            'itemized_deductions': itemized_deductions,
            'dependents': dependents,
            'withholding': withholding
        }
        
        print(f"  Created processed_data:")
        for key, value in processed_data.items():
            print(f"    {key}: {value} (type: {type(value)})")
        
        # CRITICAL: Verify income is correct before tax calculation
        print(f"\nCRITICAL CHECK - Income verification:")
        print(f"  Original input: '{raw_income}'")
        print(f"  Processed income: {processed_data['income']}")
        print(f"  Are they equal? {float(raw_income.replace(',', '')) == processed_data['income'] if raw_income else False}")
        
        # Step 5: Tax calculation
        print("\nStep 5: Calling tax calculator...")
        tax_result = tax_calc.calculate_tax(processed_data)
        
        print(f"  Tax calculation completed!")
        print(f"  Input income to calculator: {processed_data['income']}")
        print(f"  Returned gross_income: {tax_result.get('gross_income')}")
        
        # Step 6: Store in session - PRESERVE EXACT VALUES
        print("\nStep 6: Storing in session...")
        session['user_data'] = processed_data.copy()  # Use copy to ensure no reference issues
        session['tax_result'] = tax_result.copy()
        session['calculation_timestamp'] = datetime.now().isoformat()
        
        # Verify session storage
        print(f"  Session verification:")
        print(f"    Stored user_data income: {session['user_data']['income']}")
        print(f"    Stored tax_result gross_income: {session['tax_result']['gross_income']}")
        
        print("\nStep 7: Rendering results...")
        return render_template('results.html', 
                             user_data=processed_data, 
                             tax_result=tax_result)
        
    except ValueError as e:
        print(f"\nVALUE ERROR: {e}")
        session.clear()
        return render_template('index.html', errors=[f"Please check your input values: {str(e)}"])
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        session.clear()
        return render_template('index.html', 
                             errors=[f"An unexpected error occurred. Please try again."])

@app.route('/clear_session')
def clear_session():
    """Clear all session data"""
    try:
        session.clear()
        logger.info("Session data cleared by user")
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        return redirect(url_for('index'))

@app.route('/new_return')
def new_return():
    """Start a new tax return by clearing session data"""
    try:
        session.pop('user_data', None)
        session.pop('tax_result', None)
        logger.info("New tax return started - session data cleared")
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error starting new return: {str(e)}")
        return redirect(url_for('index'))

@app.route('/reset_form', methods=['POST'])
def reset_form():
    """Handle form reset via AJAX"""
    try:
        session.pop('user_data', None)
        session.pop('tax_result', None)
        return jsonify({'status': 'success', 'message': 'Form reset successfully'})
    except Exception as e:
        logger.error(f"Error resetting form: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/tax_form')
def generate_tax_form():
    """Generate printable tax form"""
    user_data = session.get('user_data')
    tax_result = session.get('tax_result')
    
    print(f"\nDEBUG - Tax Form Generation:")
    print(f"  Session user_data income: {user_data.get('income') if user_data else 'None'}")
    print(f"  Session tax_result gross_income: {tax_result.get('gross_income') if tax_result else 'None'}")
    
    if not user_data or not tax_result:
        return redirect(url_for('index'))
    
    current_date = datetime.now().strftime('%B %d, %Y')
    
    return render_template('tax_form.html', 
                         user_data=user_data, 
                         tax_result=tax_result,
                         current_year=datetime.now().year,
                         current_date=current_date)

@app.route('/download_form')
def download_form():
    """Download tax form as PDF file"""
    user_data = session.get('user_data')
    tax_result = session.get('tax_result')
    
    if not user_data or not tax_result:
        return redirect(url_for('index'))
    
    try:
        pdf_buffer = generate_pdf_form(user_data, tax_result)
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=tax_return_{datetime.now().strftime("%Y%m%d")}.pdf'
        return response
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        return download_form_text()

def generate_pdf_form(user_data, tax_result):
    """Generate complete PDF form content - FIXED INCOME DISPLAY"""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from io import BytesIO
    
    print(f"\nDEBUG - PDF Generation:")
    print(f"  User data income: {user_data.get('income')}")
    print(f"  Tax result gross_income: {tax_result.get('gross_income')}")
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue,
        borderWidth=1,
        borderColor=colors.darkblue,
        borderPadding=5,
        backColor=colors.lightgrey
    )
    
    story = []
    
    # Title
    story.append(Paragraph(f"U.S. Individual Income Tax Return (Simplified)", title_style))
    story.append(Paragraph(f"Tax Year {datetime.now().year - 1}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Personal Information Section
    story.append(Paragraph("Personal Information", heading_style))
    personal_data = [
        ['Filing Status:', user_data['filing_status'].replace('_', ' ').title()],
        ['Age:', str(user_data['age'])],
        ['Number of Dependents:', str(user_data['dependents'])]
    ]
    personal_table = Table(personal_data, colWidths=[2*inch, 3*inch])
    personal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(personal_table)
    story.append(Spacer(1, 20))
    
    # Income Section - FIXED: Use user_data income directly
    story.append(Paragraph("Income", heading_style))
    
    # Get the actual income value - try multiple sources to ensure correctness
    actual_income = user_data.get('income', 0)
    print(f"  PDF Income Value Used: {actual_income}")
    
    income_data = [
        ['Line 1 - Total Income:', f"${actual_income:,.2f}"]
    ]
    income_table = Table(income_data, colWidths=[3*inch, 2*inch])
    income_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(income_table)
    story.append(Spacer(1, 20))
    
    # Deductions Section
    story.append(Paragraph("Deductions", heading_style))
    deductions_data = [
        ['Line 2a - Standard Deduction:', f"${tax_result['standard_deduction']:,.2f}"],
        ['Line 2b - Itemized Deductions:', f"${user_data['itemized_deductions']:,.2f}"],
        ['Line 3 - Total Deductions:', f"${tax_result['total_deductions']:,.2f}"],
        ['Line 4 - Taxable Income:', f"${tax_result['taxable_income']:,.2f}"]
    ]
    deductions_table = Table(deductions_data, colWidths=[3*inch, 2*inch])
    deductions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 2), (-1, 3), colors.lightyellow),
        ('FONTNAME', (0, 2), (-1, 3), 'Helvetica-Bold')
    ]))
    story.append(deductions_table)
    story.append(Spacer(1, 20))
    
    # Tax Calculation Section
    story.append(Paragraph("Tax Calculation", heading_style))
    tax_calc_data = [
        ['Line 5 - Tax on Taxable Income:', f"${tax_result['federal_tax_before_credits']:,.2f}"]
    ]
    
    if tax_result.get('child_tax_credit', 0) > 0:
        tax_calc_data.append(['Line 6 - Child Tax Credit:', f"${tax_result['child_tax_credit']:,.2f}"])
        tax_calc_data.append(['Line 7 - Total Tax After Credits:', f"${tax_result['tax_owed']:,.2f}"])
    else:
        tax_calc_data.append(['Line 7 - Total Tax After Credits:', f"${tax_result['tax_owed']:,.2f}"])
    
    tax_calc_table = Table(tax_calc_data, colWidths=[3*inch, 2*inch])
    tax_calc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightyellow),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    ]))
    story.append(tax_calc_table)
    story.append(Spacer(1, 20))
    
    # Payments Section
    story.append(Paragraph("Payments", heading_style))
    payments_data = [
        ['Line 8 - Federal Income Tax Withheld:', f"${user_data['withholding']:,.2f}"]
    ]
    payments_table = Table(payments_data, colWidths=[3*inch, 2*inch])
    payments_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(payments_table)
    story.append(Spacer(1, 20))
    
    # Final Result Section
    story.append(Paragraph("Final Result", heading_style))
    
    if tax_result['refund_or_owe'] > 0:
        result_text = f"REFUND: ${tax_result['refund_or_owe']:,.2f}"
        result_color = colors.green
    else:
        result_text = f"AMOUNT OWED: ${abs(tax_result['refund_or_owe']):,.2f}"
        result_color = colors.red
    
    result_data = [
        ['Line 9 - Final Result:', result_text]
    ]
    result_table = Table(result_data, colWidths=[3*inch, 2*inch])
    result_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.black),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('TEXTCOLOR', (1, 0), (1, -1), result_color),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('GRID', (0, 0), (-1, -1), 2, colors.black)
    ]))
    story.append(result_table)
    story.append(Spacer(1, 30))
    
    # Tax Rate Information
    story.append(Paragraph("Tax Rate Information", heading_style))
    rate_data = [
        ['Effective Tax Rate:', f"{tax_result['effective_tax_rate']}%"],
        ['Marginal Tax Rate:', f"{tax_result['marginal_tax_rate']}%"]
    ]
    rate_table = Table(rate_data, colWidths=[3*inch, 2*inch])
    rate_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(rate_table)
    story.append(Spacer(1, 30))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=1
    )
    
    story.append(Paragraph(f"Generated by AI Tax Return Agent on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("PROTOTYPE VERSION - FOR EDUCATIONAL PURPOSES ONLY", footer_style))
    story.append(Paragraph("This form is not suitable for actual tax filing. Consult a qualified tax professional.", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def download_form_text():
    """Fallback function for text download if PDF generation fails"""
    user_data = session.get('user_data')
    tax_result = session.get('tax_result')
    
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