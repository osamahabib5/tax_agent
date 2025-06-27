from flask import Flask, render_template, request, redirect, url_for, session, make_response, jsonify
import json
from datetime import datetime, timedelta
from tax_calculator import TaxCalculator
from third_party_apis import TaxAPIIntegration
from ml_tax_optimizer import TaxOptimizationML
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
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2)
)

# Initialize components
tax_calc = TaxCalculator()
tax_api = TaxAPIIntegration()
ml_optimizer = TaxOptimizationML()

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
            'income': float(income),
            'filing_status': filing_status,
            'age': age,
            'itemized_deductions': itemized_deductions,
            'dependents': dependents,
            'withholding': withholding,
            'state': state
        }
        
        # Step 3: Enhanced tax calculation with API integration
        print("\nStep 3: Enhanced tax calculation with third-party APIs...")
        
        # Get enhanced tax brackets from API
        api_brackets = tax_api.get_current_tax_brackets(filing_status, 2023)
        print(f"  Retrieved API tax brackets: {len(api_brackets.get('brackets', []))} brackets")
        
        # Get state tax information
        state_tax_info = tax_api.get_state_tax_info(state, income)
        print(f"  State tax calculation: ${state_tax_info.get('state_tax_owed', 0):.2f}")
        
        # Get enhanced deductions
        enhanced_deductions = tax_api.get_enhanced_deductions(filing_status, income, state)
        print(f"  Enhanced deductions potential: ${enhanced_deductions.get('estimated_savings', 0):.2f}")
        
        # Perform core tax calculation
        tax_result = tax_calc.calculate_tax(processed_data)
        
        # Add API enhancements to results
        tax_result.update({
            'state_tax_owed': state_tax_info.get('state_tax_owed', 0),
            'state_tax_rate': state_tax_info.get('state_tax_rate', 0),
            'total_tax_owed': tax_result['tax_owed'] + state_tax_info.get('state_tax_owed', 0),
            'enhanced_deductions_available': enhanced_deductions.get('additional_deductions', []),
            'potential_additional_savings': enhanced_deductions.get('estimated_savings', 0)
        })
        
        # Validate calculations with API
        validation_result = tax_api.validate_tax_calculations({
            'income': income,
            'tax_owed': tax_result['tax_owed'],
            'filing_status': filing_status
        })
        
        print(f"  API validation: {validation_result.get('is_valid', 'unknown')} (confidence: {validation_result.get('confidence', 0):.2f})")
        
        # Step 4: ML-powered optimization suggestions
        print("\nStep 4: Generating ML-powered optimization suggestions...")
        
        # Get refund optimization predictions
        ml_optimization = ml_optimizer.predict_refund_optimization(processed_data)
        print(f"  ML optimization potential: {ml_optimization.get('optimization_potential', 'unknown')}")
        
        # Assess audit risk
        audit_risk = ml_optimizer.assess_audit_risk(processed_data, tax_result)
        print(f"  Audit risk assessment: {audit_risk.get('risk_level', 'unknown')}")
        
        # Get tax planning suggestions
        planning_suggestions = ml_optimizer.get_tax_planning_suggestions(processed_data)
        print(f"  Generated {len(planning_suggestions)} tax planning suggestions")
        
        # Combine ML insights
        ml_insights = {
            'optimization': ml_optimization,
            'audit_risk': audit_risk,
            'planning_suggestions': planning_suggestions,
            'confidence_score': ml_optimization.get('model_confidence', 0.8)
        }
        
        # Step 5: Store enhanced results in session
        print("\nStep 5: Storing enhanced results...")
        session['user_data'] = processed_data
        session['tax_result'] = tax_result
        session['ml_insights'] = ml_insights
        session['api_enhancements'] = {
            'state_tax_info': state_tax_info,
            'enhanced_deductions': enhanced_deductions,
            'validation': validation_result
        }
        session['calculation_timestamp'] = datetime.now().isoformat()
        
        print("  Enhanced tax calculation completed successfully!")
        
        return render_template('results.html', 
                             user_data=processed_data, 
                             tax_result=tax_result,
                             ml_insights=ml_insights,
                             api_enhancements=session['api_enhancements'])
        
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

@app.route('/optimization_suggestions')
def get_optimization_suggestions():
    """Get detailed optimization suggestions"""
    ml_insights = session.get('ml_insights', {})
    user_data = session.get('user_data', {})
    
    if not ml_insights or not user_data:
        return redirect(url_for('index'))
    
    return render_template('optimization_suggestions.html',
                         ml_insights=ml_insights,
                         user_data=user_data)

@app.route('/api/predict_refund', methods=['POST'])
def api_predict_refund():
    """API endpoint for refund prediction"""
    try:
        data = request.get_json()
        prediction = ml_optimizer.predict_refund_optimization(data)
        return jsonify(prediction)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/assess_risk', methods=['POST'])
def api_assess_risk():
    """API endpoint for audit risk assessment"""
    try:
        data = request.get_json()
        user_data = data.get('user_data', {})
        tax_result = data.get('tax_result', {})
        
        risk_assessment = ml_optimizer.assess_audit_risk(user_data, tax_result)
        return jsonify(risk_assessment)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

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
        session.pop('ml_insights', None)
        session.pop('api_enhancements', None)
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
        session.pop('ml_insights', None)
        session.pop('api_enhancements', None)
        return jsonify({'status': 'success', 'message': 'Form reset successfully'})
    except Exception as e:
        logger.error(f"Error resetting form: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/tax_form')
def generate_tax_form():
    """Generate printable tax form"""
    user_data = session.get('user_data')
    tax_result = session.get('tax_result')
    ml_insights = session.get('ml_insights', {})
    api_enhancements = session.get('api_enhancements', {})
    
    if not user_data or not tax_result:
        return redirect(url_for('index'))
    
    current_date = datetime.now().strftime('%B %d, %Y')
    
    return render_template('tax_form.html', 
                         user_data=user_data, 
                         tax_result=tax_result,
                         ml_insights=ml_insights,
                         api_enhancements=api_enhancements,
                         current_year=datetime.now().year,
                         current_date=current_date)

@app.route('/download_form')
def download_form():
    """Download tax form as PDF file"""
    user_data = session.get('user_data')
    tax_result = session.get('tax_result')
    ml_insights = session.get('ml_insights', {})
    api_enhancements = session.get('api_enhancements', {})
    
    if not user_data or not tax_result:
        return redirect(url_for('index'))
    
    try:
        pdf_buffer = generate_pdf_form(user_data, tax_result, ml_insights, api_enhancements)
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=enhanced_tax_return_{datetime.now().strftime("%Y%m%d")}.pdf'
        return response
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        return download_form_text()

def generate_pdf_form(user_data, tax_result, ml_insights=None, api_enhancements=None):
    """Generate complete PDF form content with ALL fields from view form"""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from io import BytesIO
    
    print(f"\nDEBUG - Enhanced PDF Generation:")
    print(f"  User data income: {user_data.get('income')}")
    print(f"  Tax result gross_income: {tax_result.get('gross_income')}")
    print(f"  ML insights available: {ml_insights is not None}")
    print(f"  API enhancements available: {api_enhancements is not None}")
    
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
    
    subheading_style = ParagraphStyle(
        'SubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=8,
        textColor=colors.black,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # Title
    story.append(Paragraph(f"U.S. Individual Income Tax Return (AI Enhanced)", title_style))
    story.append(Paragraph(f"Tax Year {datetime.now().year - 1}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Personal Information Section
    story.append(Paragraph("Personal Information", heading_style))
    personal_data = [
        ['Filing Status:', user_data['filing_status'].replace('_', ' ').title()],
        ['Age:', str(user_data['age'])],
        ['Number of Dependents:', str(user_data['dependents'])],
        ['State:', user_data.get('state', 'N/A')]
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
    
    # Tax Rate Information Section (from view form)
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
    story.append(Spacer(1, 20))
    
    # Tax Summary Section (from view form)
    story.append(Paragraph("Tax Summary", subheading_style))
    summary_data = [
        ['Total Income:', f"${user_data['income']:,.2f}"],
        ['Total Deductions:', f"${tax_result['total_deductions']:,.2f}"],
        ['Taxable Income:', f"${tax_result['taxable_income']:,.2f}"],
        ['Federal Tax:', f"${tax_result['tax_owed']:,.2f}"]
    ]
    
    if tax_result.get('child_tax_credit', 0) > 0:
        summary_data.append(['Tax Credits:', f"${tax_result['child_tax_credit']:,.2f}"])
    
    # Add final result with highlighting
    if tax_result['refund_or_owe'] > 0:
        summary_data.append(['Refund Amount:', f"${tax_result['refund_or_owe']:,.2f}"])
    else:
        summary_data.append(['Amount Owed:', f"${abs(tax_result['refund_or_owe']):,.2f}"])
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        # Highlight final result
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightyellow),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 30))
    
    # State Tax Information (if available)
    if api_enhancements and api_enhancements.get('state_tax_info', {}).get('state_tax_owed', 0) > 0:
        story.append(Paragraph("State Tax Information", heading_style))
        state_info = api_enhancements['state_tax_info']
        state_data = [
            ['State:', state_info.get('state', 'N/A')],
            ['State Tax Rate:', f"{state_info.get('state_tax_rate', 0)*100:.2f}%"],
            ['State Tax Owed:', f"${state_info.get('state_tax_owed', 0):,.2f}"],
            ['Combined Federal + State Tax:', f"${tax_result['tax_owed'] + state_info.get('state_tax_owed', 0):,.2f}"]
        ]
        state_table = Table(state_data, colWidths=[3*inch, 2*inch])
        state_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightyellow),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.orange),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
        ]))
        story.append(state_table)
        story.append(Spacer(1, 20))
    
    # Start new page for AI insights
    if ml_insights:
        story.append(PageBreak())
        
        # AI Optimization Insights
        story.append(Paragraph("AI-Powered Tax Optimization Insights", heading_style))
        
        # Optimization Potential
        optimization = ml_insights.get('optimization', {})
        if optimization:
            story.append(Paragraph("Optimization Assessment", subheading_style))
            opt_data = [
                ['Optimization Potential:', optimization.get('optimization_potential', 'Unknown').title()],
                ['Model Confidence:', f"{optimization.get('optimization_confidence', 0)*100:.0f}%"],
                ['Predicted Refund:', f"${optimization.get('predicted_refund', 0):,.2f}"]
            ]
            
            opt_table = Table(opt_data, colWidths=[3*inch, 2*inch])
            opt_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(opt_table)
            story.append(Spacer(1, 20))
        
        # Audit Risk Assessment
        audit_risk = ml_insights.get('audit_risk', {})
        if audit_risk:
            story.append(Paragraph("Audit Risk Assessment", subheading_style))
            risk_data = [
                ['Risk Level:', audit_risk.get('risk_level', 'Unknown').title()],
                ['Risk Probability:', f"{audit_risk.get('risk_probability', 0)*100:.1f}%"]
            ]
            
            # Add risk factors if available
            risk_factors = audit_risk.get('risk_factors', [])
            if risk_factors:
                story.append(Paragraph("Identified Risk Factors:", styles['Normal']))
                for i, factor in enumerate(risk_factors[:3], 1):  # Limit to top 3
                    story.append(Paragraph(f"• {factor}", styles['Normal']))
                story.append(Spacer(1, 10))
            
            risk_table = Table(risk_data, colWidths=[3*inch, 2*inch])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightcoral),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(risk_table)
            story.append(Spacer(1, 20))
        
        # Tax Planning Suggestions
        planning_suggestions = ml_insights.get('planning_suggestions', [])
        if planning_suggestions:
            story.append(Paragraph("AI Tax Planning Recommendations", subheading_style))
            
            for i, suggestion in enumerate(planning_suggestions[:5], 1):  # Limit to top 5
                sugg_data = [
                    ['Category:', suggestion.get('category', 'General')],
                    ['Suggestion:', suggestion.get('suggestion', 'No suggestion available')],
                    ['Potential Savings:', f"${suggestion.get('potential_savings', 0):,.0f}"],
                    ['Priority:', suggestion.get('priority', 'Medium').title()],
                    ['Implementation:', suggestion.get('implementation', 'Consult a tax professional')]
                ]
                
                sugg_table = Table(sugg_data, colWidths=[1.5*inch, 3.5*inch])
                sugg_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightsteelblue),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (1, 0), (1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(sugg_table)
                story.append(Spacer(1, 15))
    
    # Enhanced Deductions (if available)
    if api_enhancements and api_enhancements.get('enhanced_deductions', {}).get('additional_deductions'):
        story.append(Paragraph("Additional Deduction Opportunities", heading_style))
        
        enhanced_deductions = api_enhancements['enhanced_deductions']
        for deduction in enhanced_deductions['additional_deductions']:
            ded_data = [
                ['Deduction Type:', deduction.get('type', 'Unknown')],
                ['Description:', deduction.get('description', 'No description')],
                ['Potential Deduction:', f"${deduction.get('potential_deduction', 0):,.0f}"],
                ['Tax Savings:', f"${deduction.get('tax_savings', 0):,.0f}"]
            ]
            
            ded_table = Table(ded_data, colWidths=[1.5*inch, 3.5*inch])
            ded_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(ded_table)
            story.append(Spacer(1, 10))
        
        # Total potential savings
        total_savings = enhanced_deductions.get('estimated_savings', 0)
        if total_savings > 0:
            savings_para = Paragraph(f"<b>Total Potential Additional Savings: ${total_savings:,.0f}</b>", 
                                   styles['Normal'])
            story.append(savings_para)
            story.append(Spacer(1, 20))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=1
    )
    
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"Generated by AI Tax Return Agent on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("ENHANCED PROTOTYPE VERSION - FOR EDUCATIONAL PURPOSES ONLY", footer_style))
    story.append(Paragraph("This AI-enhanced form includes predictive analytics and third-party integrations.", footer_style))
    story.append(Paragraph("Not suitable for actual tax filing. Consult a qualified tax professional.", footer_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def download_form_text():
    """Enhanced fallback function for text download"""
    user_data = session.get('user_data')
    tax_result = session.get('tax_result')
    ml_insights = session.get('ml_insights', {})
    api_enhancements = session.get('api_enhancements', {})
    
    # Generate enhanced form content
    form_content = f"""
    ENHANCED AI TAX RETURN FORM - {datetime.now().year}
    =============================================
    
    TAXPAYER INFORMATION:
    Filing Status: {user_data['filing_status'].replace('_', ' ').title()}
    Age: {user_data['age']}
    Number of Dependents: {user_data['dependents']}
    State: {user_data.get('state', 'N/A')}
    
    INCOME INFORMATION:
    Total Income: ${user_data['income']:,.2f}
    
    DEDUCTIONS:
    Standard Deduction: ${tax_result['standard_deduction']:,.2f}
    Itemized Deductions: ${user_data['itemized_deductions']:,.2f}
    Total Deductions: ${tax_result['total_deductions']:,.2f}
    
    TAX CALCULATION:
    Taxable Income: ${tax_result['taxable_income']:,.2f}
    Federal Tax Before Credits: ${tax_result['federal_tax_before_credits']:,.2f}
    Child Tax Credit: ${tax_result.get('child_tax_credit', 0):,.2f}
    Federal Tax Owed: ${tax_result['tax_owed']:,.2f}
    Tax Withheld: ${user_data['withholding']:,.2f}
    
    TAX RATE INFORMATION:
    Effective Tax Rate: {tax_result['effective_tax_rate']}%
    Marginal Tax Rate: {tax_result['marginal_tax_rate']}%
    """
    
    # Add state tax information if available
    if api_enhancements and api_enhancements.get('state_tax_info', {}).get('state_tax_owed', 0) > 0:
        state_info = api_enhancements['state_tax_info']
        form_content += f"""
    
    STATE TAX INFORMATION:
    State: {state_info.get('state', 'N/A')}
    State Tax Rate: {state_info.get('state_tax_rate', 0)*100:.2f}%
    State Tax Owed: ${state_info.get('state_tax_owed', 0):,.2f}
    Combined Tax Liability: ${tax_result['tax_owed'] + state_info.get('state_tax_owed', 0):,.2f}
        """
    
    # Add AI insights if available
    if ml_insights:
        optimization = ml_insights.get('optimization', {})
        audit_risk = ml_insights.get('audit_risk', {})
        
        form_content += f"""
    
    AI OPTIMIZATION INSIGHTS:
    Optimization Potential: {optimization.get('optimization_potential', 'Unknown').title()}
    Model Confidence: {optimization.get('optimization_confidence', 0)*100:.0f}%
    Audit Risk Level: {audit_risk.get('risk_level', 'Unknown').title()}
    Risk Probability: {audit_risk.get('risk_probability', 0)*100:.1f}%
        """
        
        planning_suggestions = ml_insights.get('planning_suggestions', [])
        if planning_suggestions:
            form_content += "\n    \n    TAX PLANNING SUGGESTIONS:"
            for i, suggestion in enumerate(planning_suggestions[:3], 1):
                form_content += f"""
    {i}. {suggestion.get('category', 'General')}: {suggestion.get('suggestion', 'N/A')}
       Potential Savings: ${suggestion.get('potential_savings', 0):,.0f}
       Priority: {suggestion.get('priority', 'Medium').title()}"""
    
    form_content += f"""
    
    FINAL RESULT:
    {"Refund Due: $" + str(abs(tax_result['refund_or_owe'])) if tax_result['refund_or_owe'] > 0 else "Amount Owed: $" + str(abs(tax_result['refund_or_owe']))}
    
    Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    Enhanced with AI and third-party API integrations
    
    DISCLAIMER: This is a prototype for educational purposes only.
    """
    
    response = make_response(form_content)
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = 'attachment; filename=enhanced_tax_return.txt'
    
    return response

if __name__ == '__main__':
    app.run(debug=True)