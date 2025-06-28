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

def generate_ai_insights(user_data, tax_result):
    """Generate simplified AI insights based on tax data"""
    
    # Calculate optimization potential based on income and deductions
    income = user_data.get('income', 0)
    deductions = tax_result.get('total_deductions', 0)
    dependents = user_data.get('dependents', 0)
    age = user_data.get('age', 30)
    
    # Optimization potential logic
    optimization_score = 0
    if income > 50000 and deductions < income * 0.15:
        optimization_score += 0.3
    if dependents == 0 and income > 30000:
        optimization_score += 0.2
    if age < 65 and income > 40000:
        optimization_score += 0.2
    if user_data.get('itemized_deductions', 0) == 0:
        optimization_score += 0.3
    
    if optimization_score >= 0.8:
        optimization_potential = "high"
        confidence = 0.85
    elif optimization_score >= 0.5:
        optimization_potential = "medium"
        confidence = 0.75
    else:
        optimization_potential = "low"
        confidence = 0.65
    
    # Audit risk assessment
    risk_factors = []
    risk_score = 0
    
    if income > 200000:
        risk_score += 0.3
        risk_factors.append("High income level")
    
    if user_data.get('itemized_deductions', 0) > income * 0.3:
        risk_score += 0.4
        risk_factors.append("High deduction ratio")
    
    if dependents > 3:
        risk_score += 0.2
        risk_factors.append("Multiple dependents")
    
    if age < 25 and income > 100000:
        risk_score += 0.3
        risk_factors.append("Young high earner")
    
    if risk_score >= 0.7:
        risk_level = "high"
        risk_probability = 0.25
    elif risk_score >= 0.4:
        risk_level = "medium"
        risk_probability = 0.15
    else:
        risk_level = "low"
        risk_probability = 0.05
    
    # Generate planning suggestions
    planning_suggestions = []
    
    if user_data.get('itemized_deductions', 0) == 0:
        planning_suggestions.append({
            'category': 'Deductions',
            'suggestion': 'Consider itemizing deductions if you have significant medical expenses, mortgage interest, or charitable contributions',
            'potential_savings': min(income * 0.05, 5000),
            'priority': 'high',
            'effort': 'medium',
            'implementation': 'Gather receipts and documentation for potential deductions'
        })
    
    if dependents == 0 and income > 30000:
        planning_suggestions.append({
            'category': 'Credits',
            'suggestion': 'Consider contributing to a retirement account to reduce taxable income',
            'potential_savings': min(income * 0.03, 3000),
            'priority': 'medium',
            'effort': 'low',
            'implementation': 'Open an IRA or increase 401(k) contributions'
        })
    
    if age < 65 and income > 40000:
        planning_suggestions.append({
            'category': 'Planning',
            'suggestion': 'Consider health savings account (HSA) contributions if eligible',
            'potential_savings': min(income * 0.02, 2000),
            'priority': 'medium',
            'effort': 'medium',
            'implementation': 'Check HSA eligibility and contribution limits'
        })
    
    if income > 50000:
        planning_suggestions.append({
            'category': 'Investment',
            'suggestion': 'Consider tax-loss harvesting to offset capital gains',
            'potential_savings': min(income * 0.01, 1000),
            'priority': 'low',
            'effort': 'high',
            'implementation': 'Review investment portfolio for loss opportunities'
        })
    
    if dependents > 0:
        planning_suggestions.append({
            'category': 'Family',
            'suggestion': 'Maximize child tax credit and dependent care benefits',
            'potential_savings': min(dependents * 1500, 4500),
            'priority': 'high',
            'effort': 'low',
            'implementation': 'Ensure proper documentation of dependent expenses'
        })
    
    if income > 75000:
        planning_suggestions.append({
            'category': 'Advanced',
            'suggestion': 'Consider tax-advantaged investment strategies',
            'potential_savings': min(income * 0.02, 2000),
            'priority': 'low',
            'effort': 'high',
            'implementation': 'Consult with a financial advisor for tax-efficient investing'
        })
    
    # Generate optimization recommendations
    recommendations = []
    if optimization_potential == "high":
        recommendations.append({
            'type': 'deduction_optimization',
            'description': 'High potential for additional deductions through itemization',
            'estimated_savings': min(income * 0.08, 8000),
            'effort': 'medium'
        })
    
    if dependents > 0:
        recommendations.append({
            'type': 'credit_optimization',
            'description': 'Optimize child and dependent care credits',
            'estimated_savings': min(dependents * 1000, 3000),
            'effort': 'low'
        })
    
    if income > 50000 and user_data.get('itemized_deductions', 0) == 0:
        recommendations.append({
            'type': 'retirement_planning',
            'description': 'Consider retirement account contributions to reduce taxable income',
            'estimated_savings': min(income * 0.03, 3000),
            'effort': 'low'
        })
    
    if age < 65 and income > 40000:
        recommendations.append({
            'type': 'health_savings',
            'description': 'Health savings account (HSA) contributions if eligible',
            'estimated_savings': min(income * 0.02, 2000),
            'effort': 'medium'
        })
    
    return {
        'optimization': {
            'optimization_potential': optimization_potential,
            'optimization_confidence': confidence,
            'predicted_refund': max(0, tax_result.get('refund_or_owe', 0) + min(income * 0.05, 5000)),
            'recommendations': recommendations
        },
        'audit_risk': {
            'risk_level': risk_level,
            'risk_probability': risk_probability,
            'risk_factors': risk_factors,
            'mitigation_suggestions': [
                'Ensure all deductions are properly documented',
                'Keep detailed records of income sources',
                'Consider consulting a tax professional'
            ] if risk_level != "low" else []
        },
        'planning_suggestions': planning_suggestions,
        'confidence_score': confidence
    }

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
            'standard_deduction': standard_deductions.get(filing_status, 13850),
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
        
        # Generate AI insights
        print("Step 3: Generating AI insights...")
        ml_insights = generate_ai_insights(processed_data, tax_result)
        print(f"  AI insights generated: optimization={ml_insights['optimization']['optimization_potential']}, risk={ml_insights['audit_risk']['risk_level']}")
        
        # Generate sample enhanced deductions data
        enhanced_deductions = []
        total_estimated_savings = 0
        
        # Add sample deductions based on user data
        if processed_data.get('itemized_deductions', 0) == 0:
            enhanced_deductions.append({
                'type': 'Medical Expenses',
                'description': 'Medical and dental expenses that exceed 7.5% of adjusted gross income',
                'potential_deduction': min(income * 0.03, 3000),
                'tax_savings': min(income * 0.03 * 0.22, 660)  # Assuming 22% tax bracket
            })
            total_estimated_savings += min(income * 0.03 * 0.22, 660)
        
        if processed_data.get('dependents', 0) > 0:
            enhanced_deductions.append({
                'type': 'Child Care Credit',
                'description': 'Child and dependent care credit for work-related expenses',
                'potential_deduction': min(processed_data.get('dependents', 0) * 3000, 6000),
                'tax_savings': min(processed_data.get('dependents', 0) * 600, 1200)
            })
            total_estimated_savings += min(processed_data.get('dependents', 0) * 600, 1200)
        
        if income > 50000:
            enhanced_deductions.append({
                'type': 'Retirement Contributions',
                'description': 'Traditional IRA or 401(k) contributions to reduce taxable income',
                'potential_deduction': min(income * 0.05, 6000),
                'tax_savings': min(income * 0.05 * 0.22, 1320)
            })
            total_estimated_savings += min(income * 0.05 * 0.22, 1320)
        
        if income > 40000:
            enhanced_deductions.append({
                'type': 'Student Loan Interest',
                'description': 'Student loan interest deduction (up to $2,500)',
                'potential_deduction': min(2500, income * 0.02),
                'tax_savings': min(2500 * 0.22, 550)
            })
            total_estimated_savings += min(2500 * 0.22, 550)
        
        api_enhancements = {
            'enhanced_deductions': {
                'additional_deductions': enhanced_deductions,
                'estimated_savings': total_estimated_savings
            }
        }
        
        # Store enhanced results in session
        session['tax_result'] = tax_result
        session['ml_insights'] = ml_insights
        session['api_enhancements'] = api_enhancements
        
        print(f"  Calculation complete: refund/owe = ${refund_or_owe:,.2f}")
        
        return render_template('results.html', 
                             user_data=processed_data, 
                             tax_result=tax_result,
                             ml_insights=ml_insights,
                             api_enhancements=api_enhancements)
        
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
    
    ml_insights = session.get('ml_insights', {})
    
    return render_template('optimization_suggestions.html',
                         user_data=session['user_data'],
                         tax_result=session['tax_result'],
                         ml_insights=ml_insights)

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
    
    user_data = session.get('user_data')
    tax_result = session.get('tax_result')
    ml_insights = session.get('ml_insights', {})
    api_enhancements = session.get('api_enhancements', {})
    
    current_date = dt.datetime.now().strftime('%B %d, %Y')
    
    return render_template('tax_form.html',
                         user_data=user_data,
                         tax_result=tax_result,
                         ml_insights=ml_insights,
                         api_enhancements=api_enhancements,
                         current_year=dt.datetime.now().year,
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
        response.headers['Content-Disposition'] = f'attachment; filename=enhanced_tax_return_{dt.datetime.now().strftime("%Y%m%d")}.pdf'
        return response
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        return download_form_text()

def generate_pdf_form(user_data, tax_result, ml_insights=None, api_enhancements=None):
    """Generate simplified PDF form content"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from io import BytesIO
        
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
        story.append(Paragraph(f"Tax Year {dt.datetime.now().year - 1}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Personal Information Section
        story.append(Paragraph("Personal Information", heading_style))
        personal_data = [
            ['Filing Status:', user_data.get('filing_status', 'N/A').replace('_', ' ').title()],
            ['Age:', str(user_data.get('age', 'N/A'))],
            ['Number of Dependents:', str(user_data.get('dependents', 'N/A'))],
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
            ['Line 1 - Total Income:', f"${user_data.get('income', 0):,.2f}"]
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
            ['Line 2a - Standard Deduction:', f"${tax_result.get('standard_deduction', 0):,.2f}"],
            ['Line 2b - Itemized Deductions:', f"${user_data.get('itemized_deductions', 0):,.2f}"],
            ['Line 3 - Total Deductions:', f"${tax_result.get('total_deductions', 0):,.2f}"],
            ['Line 4 - Taxable Income:', f"${tax_result.get('taxable_income', 0):,.2f}"]
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
            ['Line 5 - Tax on Taxable Income:', f"${tax_result.get('federal_tax_before_credits', 0):,.2f}"]
        ]
        
        if tax_result.get('child_tax_credit', 0) > 0:
            tax_calc_data.append(['Line 6 - Child Tax Credit:', f"${tax_result.get('child_tax_credit', 0):,.2f}"])
            tax_calc_data.append(['Line 7 - Total Tax After Credits:', f"${tax_result.get('tax_owed', 0):,.2f}"])
        else:
            tax_calc_data.append(['Line 7 - Total Tax After Credits:', f"${tax_result.get('tax_owed', 0):,.2f}"])
        
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
            ['Line 8 - Federal Income Tax Withheld:', f"${user_data.get('withholding', 0):,.2f}"]
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
        
        if tax_result.get('refund_or_owe', 0) > 0:
            result_text = f"REFUND: ${tax_result.get('refund_or_owe', 0):,.2f}"
            result_color = colors.green
        else:
            result_text = f"AMOUNT OWED: ${abs(tax_result.get('refund_or_owe', 0)):,.2f}"
            result_color = colors.red
        
        result_para = Paragraph(f"<b>{result_text}</b>", ParagraphStyle(
            'Result',
            parent=styles['Normal'],
            fontSize=16,
            textColor=result_color,
            alignment=1,
            backColor=colors.lightgrey,
            borderWidth=2,
            borderColor=result_color,
            borderPadding=10
        ))
        story.append(result_para)
        story.append(Spacer(1, 20))
        
        # AI Insights Section (if available)
        if ml_insights:
            story.append(PageBreak())
            story.append(Paragraph("AI-Powered Tax Insights", heading_style))
            
            # Optimization insights
            optimization = ml_insights.get('optimization', {})
            if optimization:
                story.append(Paragraph("Optimization Analysis", subheading_style))
                opt_data = [
                    ['Optimization Potential:', optimization.get('optimization_potential', 'Unknown').title()],
                    ['Confidence Level:', f"{optimization.get('optimization_confidence', 0)*100:.0f}%"]
                ]
                opt_table = Table(opt_data, colWidths=[2*inch, 3*inch])
                opt_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightsteelblue),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('BACKGROUND', (1, 0), (1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(opt_table)
                story.append(Spacer(1, 15))
            
            # Audit risk insights
            audit_risk = ml_insights.get('audit_risk', {})
            if audit_risk:
                story.append(Paragraph("Audit Risk Assessment", subheading_style))
                risk_data = [
                    ['Risk Level:', audit_risk.get('risk_level', 'Unknown').title()],
                    ['Risk Probability:', f"{audit_risk.get('risk_probability', 0)*100:.1f}%"]
                ]
                risk_table = Table(risk_data, colWidths=[2*inch, 3*inch])
                risk_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightcoral),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('BACKGROUND', (1, 0), (1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(risk_table)
                story.append(Spacer(1, 15))
            
            # Planning suggestions
            planning_suggestions = ml_insights.get('planning_suggestions', [])
            if planning_suggestions:
                story.append(Paragraph("Tax Planning Suggestions", subheading_style))
                for i, suggestion in enumerate(planning_suggestions[:3], 1):
                    sugg_data = [
                        ['Category:', suggestion.get('category', 'General')],
                        ['Suggestion:', suggestion.get('suggestion', 'No suggestion available')],
                        ['Potential Savings:', f"${suggestion.get('potential_savings', 0):,.0f}"],
                        ['Priority:', suggestion.get('priority', 'Medium').title()],
                        ['Effort:', suggestion.get('effort', 'Medium').title()]
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
                    story.append(Spacer(1, 10))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1
        )
        
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"Generated by AI Tax Return Agent on {dt.datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph("ENHANCED PROTOTYPE VERSION - FOR EDUCATIONAL PURPOSES ONLY", footer_style))
        story.append(Paragraph("This AI-enhanced form includes predictive analytics and third-party integrations.", footer_style))
        story.append(Paragraph("Not suitable for actual tax filing. Consult a qualified tax professional.", footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
        
    except ImportError:
        # If reportlab is not available, raise an exception to trigger fallback
        raise Exception("PDF generation requires reportlab library")

def download_form_text():
    """Enhanced fallback function for text download"""
    user_data = session.get('user_data')
    tax_result = session.get('tax_result')
    ml_insights = session.get('ml_insights', {})
    api_enhancements = session.get('api_enhancements', {})
    
    # Check if required data exists
    if not user_data or not tax_result:
        return redirect(url_for('index'))
    
    # Generate enhanced form content
    form_content = f"""
    ENHANCED AI TAX RETURN FORM - {dt.datetime.now().year}
    =============================================
    
    TAXPAYER INFORMATION:
    Filing Status: {user_data.get('filing_status', 'N/A').replace('_', ' ').title()}
    Age: {user_data.get('age', 'N/A')}
    Number of Dependents: {user_data.get('dependents', 'N/A')}
    State: {user_data.get('state', 'N/A')}
    
    INCOME INFORMATION:
    Total Income: ${user_data.get('income', 0):,.2f}
    
    DEDUCTIONS:
    Total Deductions: ${tax_result.get('total_deductions', 0):,.2f}
    
    TAX CALCULATION:
    Taxable Income: ${tax_result.get('taxable_income', 0):,.2f}
    Federal Tax Before Credits: ${tax_result.get('federal_tax_before_credits', 0):,.2f}
    Child Tax Credit: ${tax_result.get('child_tax_credit', 0):,.2f}
    Federal Tax Owed: ${tax_result.get('tax_owed', 0):,.2f}
    Tax Withheld: ${user_data.get('withholding', 0):,.2f}
    
    TAX RATE INFORMATION:
    Effective Tax Rate: {tax_result.get('effective_tax_rate', 0)}%
    Marginal Tax Rate: {tax_result.get('marginal_tax_rate', 0)}%
    
    FINAL RESULT:
    {"Refund Due: $" + str(abs(tax_result.get('refund_or_owe', 0))) if tax_result.get('refund_or_owe', 0) > 0 else "Amount Owed: $" + str(abs(tax_result.get('refund_or_owe', 0)))}
    
    Generated on: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    Enhanced with AI and third-party API integrations
    
    DISCLAIMER: This is a prototype for educational purposes only.
    """
    
    response = make_response(form_content)
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = 'attachment; filename=enhanced_tax_return.txt'
    
    return response

@app.errorhandler(404)
def not_found_error(error):
    return render_template('index.html', errors=["Page not found. Please start with the tax form."]), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('index.html', errors=["An internal server error occurred. Please try again."]), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) 