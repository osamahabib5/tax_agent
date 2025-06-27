import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
# from datetime import datetime
import datetime as dt

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# ESSENTIAL: Root route - this must exist!
@app.route('/')
def index():
    logger.info("Root route (/) accessed")
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Tax Return Agent</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 40px; 
                background-color: #f5f5f5; 
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
                background: white; 
                padding: 30px; 
                border-radius: 10px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .btn { 
                background: #007bff; 
                color: white; 
                padding: 12px 24px; 
                text-decoration: none; 
                border-radius: 5px; 
                display: inline-block;
                margin: 10px 5px;
            }
            .btn:hover { background: #0056b3; }
            h1 { color: #333; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 AI Tax Return Agent</h1>
            <p>Welcome to your intelligent tax preparation assistant!</p>
            <p>This prototype helps you calculate federal taxes with AI-powered recommendations.</p>
            
            <a href="/form" class="btn">📋 Start Tax Calculation</a>
            <a href="/health" class="btn">🔍 Health Check</a>
            
            <hr style="margin: 30px 0;">
            <h3>Features:</h3>
            <ul>
                <li>✅ Progressive tax bracket calculations</li>
                <li>🧮 Standard and itemized deductions</li>
                <li>👶 Child tax credit support</li>
                <li>🤖 AI-powered recommendations</li>
                <li>📄 Printable tax forms</li>
            </ul>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health_check():
    logger.info("Health check accessed")
    return jsonify({
        'status': 'healthy',
        # 'timestamp': str(dt.datetime.now()),
        'service': 'AI Tax Return Agent',
        'version': '1.0.0'
    }), 200

@app.route('/form')
def tax_form():
    logger.info("Tax form accessed")
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tax Form - AI Tax Agent</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 40px; 
                background-color: #f5f5f5; 
            }
            .container { 
                max-width: 600px; 
                margin: 0 auto; 
                background: white; 
                padding: 30px; 
                border-radius: 10px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .form-group { 
                margin-bottom: 20px; 
            }
            label { 
                display: block; 
                margin-bottom: 8px; 
                font-weight: bold; 
                color: #333;
            }
            input, select { 
                width: 100%; 
                padding: 12px; 
                border: 2px solid #ddd; 
                border-radius: 5px; 
                font-size: 16px;
                box-sizing: border-box;
            }
            input:focus, select:focus {
                border-color: #007bff;
                outline: none;
            }
            .btn { 
                background: #28a745; 
                color: white; 
                padding: 15px 30px; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                font-size: 16px;
                width: 100%;
            }
            .btn:hover { background: #218838; }
            .back-link { 
                color: #007bff; 
                text-decoration: none; 
                margin-top: 20px; 
                display: inline-block;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📋 Tax Information Form</h1>
            <form method="POST" action="/calculate">
                <div class="form-group">
                    <label for="name">Full Name:</label>
                    <input type="text" id="name" name="name" required placeholder="Enter your full name">
                </div>
                
                <div class="form-group">
                    <label for="annual_income">Annual Income ($):</label>
                    <input type="number" id="annual_income" name="annual_income" step="0.01" required placeholder="e.g., 50000">
                </div>
                
                <div class="form-group">
                    <label for="filing_status">Filing Status:</label>
                    <select id="filing_status" name="filing_status" required>
                        <option value="">Select Filing Status</option>
                        <option value="single">Single</option>
                        <option value="married_jointly">Married Filing Jointly</option>
                        <option value="married_separately">Married Filing Separately</option>
                        <option value="head_of_household">Head of Household</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="age">Age:</label>
                    <input type="number" id="age" name="age" min="0" max="120" value="30" required>
                </div>
                
                <div class="form-group">
                    <label for="dependents">Number of Dependents:</label>
                    <input type="number" id="dependents" name="dependents" min="0" value="0">
                </div>
                
                <div class="form-group">
                    <label for="withholdings">Tax Withholdings ($):</label>
                    <input type="number" id="withholdings" name="withholdings" step="0.01" value="0" placeholder="Amount withheld from paychecks">
                </div>
                
                <button type="submit" class="btn">🧮 Calculate Taxes</button>
            </form>
            
            <a href="/" class="back-link">← Back to Home</a>
        </div>
    </body>
    </html>
    """

@app.route('/calculate', methods=['POST'])
def calculate():
    logger.info("Calculate route accessed")
    try:
        # Get form data
        name = request.form.get('name', 'Unknown')
        annual_income = float(request.form.get('annual_income', 0))
        filing_status = request.form.get('filing_status', 'single')
        age = int(request.form.get('age', 30))
        dependents = int(request.form.get('dependents', 0))
        withholdings = float(request.form.get('withholdings', 0))
        
        # Simple tax calculation (replace with your complex logic)
        # Standard deduction amounts for 2023
        standard_deductions = {
            'single': 13850,
            'married_jointly': 27700,
            'married_separately': 13850,
            'head_of_household': 20800
        }
        
        # Add senior deduction if applicable
        standard_deduction = standard_deductions.get(filing_status, 13850)
        if age >= 65:
            senior_addition = 1850 if filing_status in ['single', 'head_of_household'] else 1500
            standard_deduction += senior_addition
        
        # Calculate taxable income
        taxable_income = max(0, annual_income - standard_deduction)
        
        # Simple progressive tax calculation (2023 brackets for single filers)
        tax_brackets = [
            (11000, 0.10),
            (44725, 0.12),
            (95375, 0.22),
            (182050, 0.24),
            (231250, 0.32),
            (578125, 0.35),
            (float('inf'), 0.37)
        ]
        
        federal_tax = 0
        previous_bracket = 0
        
        for bracket_limit, rate in tax_brackets:
            if taxable_income <= previous_bracket:
                break
            
            taxable_in_bracket = min(taxable_income, bracket_limit) - previous_bracket
            federal_tax += taxable_in_bracket * rate
            previous_bracket = bracket_limit
            
            if taxable_income <= bracket_limit:
                break
        
        # Child tax credit
        child_tax_credit = min(dependents * 2000, federal_tax) if annual_income < 200000 else 0
        
        # Final calculations
        tax_after_credits = max(0, federal_tax - child_tax_credit)
        refund_or_owed = withholdings - tax_after_credits
        effective_rate = (tax_after_credits / annual_income * 100) if annual_income > 0 else 0
        
        # Determine marginal rate
        marginal_rate = 10.0
        previous_bracket = 0
        for bracket_limit, rate in tax_brackets:
            if taxable_income > previous_bracket:
                marginal_rate = rate * 100
            if taxable_income <= bracket_limit:
                break
            previous_bracket = bracket_limit
        
        result_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tax Results - AI Tax Agent</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 40px; 
                    background-color: #f5f5f5; 
                }}
                .container {{ 
                    max-width: 800px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 30px; 
                    border-radius: 10px; 
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .result-card {{ 
                    background: #f8f9fa; 
                    padding: 20px; 
                    border-radius: 8px; 
                    margin: 15px 0; 
                    border-left: 5px solid #007bff;
                }}
                .highlight {{ 
                    color: #28a745; 
                    font-size: 1.3em; 
                    font-weight: bold; 
                }}
                .refund {{ color: #28a745; }}
                .owed {{ color: #dc3545; }}
                .btn {{ 
                    background: #007bff; 
                    color: white; 
                    padding: 12px 24px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 10px 5px; 
                    display: inline-block;
                }}
                .btn:hover {{ background: #0056b3; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f8f9fa; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Tax Calculation Results</h1>
                
                <div class="result-card">
                    <h2>Hello, {name}!</h2>
                    <p><strong>Filing Status:</strong> {filing_status.replace('_', ' ').title()}</p>
                    <p><strong>Annual Income:</strong> ${annual_income:,.2f}</p>
                    <p><strong>Standard Deduction:</strong> ${standard_deduction:,.2f}</p>
                    <p><strong>Taxable Income:</strong> ${taxable_income:,.2f}</p>
                </div>
                
                <div class="result-card">
                    <h3>💰 Tax Summary</h3>
                    <table>
                        <tr><th>Item</th><th>Amount</th></tr>
                        <tr><td>Federal Tax Before Credits</td><td>${federal_tax:.2f}</td></tr>
                        <tr><td>Child Tax Credit</td><td>${child_tax_credit:.2f}</td></tr>
                        <tr><td><strong>Total Tax After Credits</strong></td><td><strong>${tax_after_credits:.2f}</strong></td></tr>
                        <tr><td>Tax Withholdings</td><td>${withholdings:.2f}</td></tr>
                        <tr><td><strong>{'Refund' if refund_or_owed >= 0 else 'Amount Owed'}</strong></td>
                            <td class="{'refund' if refund_or_owed >= 0 else 'owed'}"><strong>${abs(refund_or_owed):.2f}</strong></td></tr>
                    </table>
                </div>
                
                <div class="result-card">
                    <h3>📈 Tax Rates</h3>
                    <p><strong>Effective Tax Rate:</strong> {effective_rate:.2f}%</p>
                    <p><strong>Marginal Tax Rate:</strong> {marginal_rate:.1f}%</p>
                </div>
                
                <div class="result-card">
                    <h3>ℹ️ Important Notes</h3>
                    <ul>
                        <li>This is a simplified federal tax calculation for demonstration purposes</li>
                        <li>Actual tax preparation may involve additional forms, schedules, and considerations</li>
                        <li>State taxes are not included in this calculation</li>
                        <li>Please consult a qualified tax professional for official tax advice</li>
                    </ul>
                </div>
                
                <a href="/form" class="btn">🔄 Calculate Again</a>
                <a href="/" class="btn">🏠 Home</a>
            </div>
        </body>
        </html>
        """
        
        return result_html
        
    except Exception as e:
        logger.error(f"Error in calculate route: {str(e)}")
        return f"""
        <h1>Calculation Error</h1>
        <p>There was an error processing your tax calculation:</p>
        <p><strong>{str(e)}</strong></p>
        <p><a href="/form">Try Again</a> | <a href="/">Home</a></p>
        """, 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"404 error: {request.url}")
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Page Not Found</title></head>
    <body style="font-family: Arial, sans-serif; margin: 40px;">
        <h1>🔍 Page Not Found</h1>
        <p>The page you're looking for doesn't exist.</p>
        <p><strong>Available pages:</strong></p>
        <ul>
            <li><a href="/">🏠 Home</a></li>
            <li><a href="/form">📋 Tax Form</a></li>
            <li><a href="/health">🔍 Health Check</a></li>
        </ul>
    </body>
    </html>
    """, 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}")
    return jsonify({'error': 'Internal server error', 'details': str(error)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting AI Tax Return Agent on port {port}")
    logger.info("Available routes:")
    logger.info("- / (Home)")
    logger.info("- /form (Tax Form)")
    logger.info("- /health (Health Check)")
    logger.info("- /calculate (POST - Tax Calculation)")
    
    app.run(host='0.0.0.0', port=port, debug=False)