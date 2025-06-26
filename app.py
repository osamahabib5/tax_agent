from flask import Flask, render_template, request, redirect, url_for, session, make_response
import json
from datetime import datetime
from tax_calculator import TaxCalculator
import logging
from config import DevelopmentConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

# Initialize tax calculator
tax_calc = TaxCalculator()

def validate_input(data):
    """Validate and sanitize user input"""
    errors = []
    
    # Validate income
    try:
        income_str = str(data.get('income', '0')).strip()
        if income_str == '':
            income_str = '0'
        income = float(income_str)
        if income < 0:
            errors.append("Income cannot be negative")
        elif income > 10000000:  # Reasonable upper limit
            errors.append("Income amount seems unusually high")
    except (ValueError, TypeError):
        errors.append("Invalid income amount")
    
    # Validate filing status
    valid_statuses = ['single', 'married_joint', 'married_separate', 'head_of_household']
    filing_status = data.get('filing_status')
    if filing_status not in valid_statuses:
        errors.append("Invalid filing status")
    
    # Validate age - Fixed validation
    try:
        age_str = str(data.get('age', '')).strip()
        if age_str == '':
            errors.append("Age is required")
        else:
            age = int(float(age_str))  # Convert to float first, then int to handle decimal inputs
            if age < 18 or age > 120:
                errors.append("Age must be between 18 and 120")
    except (ValueError, TypeError):
        errors.append("Invalid age - please enter a whole number")
    
    # Validate dependents - Fixed validation
    try:
        dependents_str = str(data.get('dependents', '0')).strip()
        if dependents_str == '':
            dependents_str = '0'
        dependents = int(float(dependents_str))  # Convert to float first, then int
        if dependents < 0:
            errors.append("Number of dependents cannot be negative")
        elif dependents > 20:  # Reasonable upper limit
            errors.append("Number of dependents seems unusually high")
        
        # Filing status specific dependent rules
        if filing_status == 'single' and dependents > 1:
            errors.append("Single filers can have a maximum of 1 dependent")
        elif filing_status == 'head_of_household' and dependents == 0:
            errors.append("Head of Household filing status requires at least 1 dependent")
            
    except (ValueError, TypeError):
        errors.append("Invalid number of dependents - please enter a whole number")
    
    # Validate deductions
    try:
        deductions_str = str(data.get('itemized_deductions', '0')).strip()
        if deductions_str == '':
            deductions_str = '0'
        deductions = float(deductions_str)
        if deductions < 0:
            errors.append("Deductions cannot be negative")
    except (ValueError, TypeError):
        errors.append("Invalid deduction amount")
    
    # Validate withholding
    try:
        withholding_str = str(data.get('withholding', '0')).strip()
        if withholding_str == '':
            withholding_str = '0'
        withholding = float(withholding_str)
        if withholding < 0:
            errors.append("Tax withholding cannot be negative")
        # Cross-validate withholding against income
        try:
            income_val = float(str(data.get('income', '0')).strip() or '0')
            if withholding > income_val:
                errors.append("Tax withholding cannot exceed total income")
        except (ValueError, TypeError):
            pass  # Income validation will catch this
    except (ValueError, TypeError):
        errors.append("Invalid withholding amount")
    
    return errors

@app.route('/')
def index():
    """Main page with tax input form"""
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate_tax():
    """Process tax calculation"""
    try:
        # Get form data with better handling
        user_data = {
            'income': request.form.get('income', '').strip(),
            'filing_status': request.form.get('filing_status', '').strip(),
            'age': request.form.get('age', '').strip(),
            'itemized_deductions': request.form.get('itemized_deductions', '0').strip(),
            'dependents': request.form.get('dependents', '0').strip(),
            'withholding': request.form.get('withholding', '0').strip()
        }
        
        # Log the received data for debugging
        logger.info(f"Received form data: {user_data}")
        
        # Validate input
        errors = validate_input(user_data)
        if errors:
            logger.warning(f"Validation errors: {errors}")
            return render_template('index.html', errors=errors, form_data=user_data)
        
        # Convert to appropriate types with better error handling
        try:
            processed_data = {
                'income': float(user_data['income'] or '0'),
                'filing_status': user_data['filing_status'],
                'age': int(float(user_data['age'])),  # Handle potential decimal values
                'itemized_deductions': float(user_data['itemized_deductions'] or '0'),
                'dependents': int(float(user_data['dependents'] or '0')),  # Handle potential decimal values
                'withholding': float(user_data['withholding'] or '0')
            }
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting data types: {str(e)}")
            return render_template('index.html', 
                                 errors=[f"Data conversion error: {str(e)}"], 
                                 form_data=user_data)
        
        # Log processed data
        logger.info(f"Processed data: {processed_data}")
        
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
                             errors=[f"An unexpected error occurred. Please try again."], 
                             form_data=user_data if 'user_data' in locals() else {})

# ... rest of your routes remain the same ...

@app.route('/tax_form')
def generate_tax_form():
    """Generate printable tax form"""
    user_data = session.get('user_data')
    tax_result = session.get('tax_result')
    
    if not user_data or not tax_result:
        return redirect(url_for('index'))
    
    # Format current date
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
        # Create PDF content
        pdf_buffer = generate_pdf_form(user_data, tax_result)
        
        # Create response with PDF content
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=tax_return_{datetime.now().strftime("%Y%m%d")}.pdf'
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        # Fallback to text format if PDF generation fails
        return download_form_text()

def generate_pdf_form(user_data, tax_result):
    """Generate PDF form content"""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from io import BytesIO
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center alignment
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
    
    # Build PDF content
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
    
    # Continue with rest of PDF generation...
    # (Include the rest of the PDF generation code from previous response)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def download_form_text():
    """Fallback function for text download if PDF generation fails"""
    user_data = session.get('user_data')
    tax_result = session.get('tax_result')
    
    # Generate form content (original text version)
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