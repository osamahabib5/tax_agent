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
        income = float(data.get('income', 0))
        if income < 0:
            errors.append("Income cannot be negative")
        elif income > 10000000:  # Reasonable upper limit
            errors.append("Income amount seems unusually high")
    except ValueError:
        errors.append("Invalid income amount")
    
    # Validate filing status
    valid_statuses = ['single', 'married_joint', 'married_separate', 'head_of_household']
    filing_status = data.get('filing_status')
    if filing_status not in valid_statuses:
        errors.append("Invalid filing status")
    
    # Validate age
    try:
        age = int(data.get('age', 0))
        if age < 18 or age > 120:
            errors.append("Invalid age")
    except ValueError:
        errors.append("Invalid age")
    
    # Validate dependents
    try:
        dependents = int(data.get('dependents', 0))
        if dependents < 0:
            errors.append("Number of dependents cannot be negative")
        elif dependents > 20:  # Reasonable upper limit
            errors.append("Number of dependents seems unusually high")
        
        # Special validation for filing status and dependents
        if filing_status == 'single' and dependents > 1:
            errors.append("Single filers can have a maximum of 1 dependent")
        
    except ValueError:
        errors.append("Invalid number of dependents")
    
    # Validate deductions
    try:
        deductions = float(data.get('itemized_deductions', 0))
        if deductions < 0:
            errors.append("Deductions cannot be negative")
    except ValueError:
        errors.append("Invalid deduction amount")
    
    # Validate withholding
    try:
        withholding = float(data.get('withholding', 0))
        if withholding < 0:
            errors.append("Tax withholding cannot be negative")
    except ValueError:
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
    
    # Format current date
    current_date = datetime.now().strftime('%B %d, %Y')
    
    return render_template('tax_form.html', 
                         user_data=user_data, 
                         tax_result=tax_result,
                         current_year=datetime.now().year)

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
    
    # Income Section
    story.append(Paragraph("Income", heading_style))
    income_data = [
        ['Line 1 - Total Income:', f"${user_data['income']:,.2f}"]
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
        # Highlight total deductions and taxable income
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
    
    # Add child tax credit if applicable
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
        # Highlight final tax amount
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
        alignment=1  # Center alignment
    )
    
    story.append(Paragraph(f"Generated by AI Tax Return Agent on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("PROTOTYPE VERSION - FOR EDUCATIONAL PURPOSES ONLY", footer_style))
    story.append(Paragraph("This form is not suitable for actual tax filing. Consult a qualified tax professional.", footer_style))
    
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