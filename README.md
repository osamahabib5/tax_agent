# 💼 AI Tax Return Agent Prototype

A comprehensive prototype of an **AI-powered tax return preparation system** built using Flask and Python, offering intelligent recommendations and personalized tax optimization strategies.

---

## 🚀 Features

* ✅ **User-Friendly Interface**: Clean, responsive web interface for easy tax data entry
* 📊 **Comprehensive Tax Calculations**: Supports multiple filing statuses and real-world tax scenarios
* 🧮 **Progressive Tax Brackets**: Accurate federal tax calculations based on 2023 IRS tax brackets
* 🧾 **Standard & Itemized Deductions**: Automatically selects the most beneficial deduction method
* 👶 **Child Tax Credit**: Handles eligibility and calculation of simplified child tax credits
* 🤖 **AI Recommendations**: Provides personalized, AI-driven suggestions for maximizing refunds and minimizing tax liabilities
* 🖨️ **Printable Tax Forms**: Generate and download a summary of completed tax return information
* 🔐 **Input Validation & Security**: Strong input validation with basic sanitization and error handling
* 💰 **AI-Powered Tax Optimization**: Shows potential savings and optimization recommendations
* 📈 **Audit Risk Assessment**: AI-driven risk analysis and mitigation suggestions

---

## 🛠️ Technology Stack

* **Backend**: Python Flask
* **Frontend**: HTML5, CSS3, JavaScript
* **Templating**: Jinja2
* **Styling**: Custom CSS with responsive design
* **AI Logic**: Python-based rules and heuristics for tax guidance
* **Data Processing**: Python standard libraries
* **PDF Generation**: ReportLab
* **Machine Learning**: Scikit-learn, NumPy, Pandas

---

## ⚙️ Installation & Setup

### Prerequisites

* Python 3.8 or higher
* pip (Python package installer)
* Git (for cloning the repository)

### Step-by-Step Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/osamahabib5/tax_agent.git
   cd tax_agent
   ```

2. **Create a virtual environment**

   **On Windows:**
   ```bash
   python -m venv venv
   ```

   **On Linux/macOS:**
   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment**

   **On Windows (Command Prompt):**
   ```cmd
   venv\Scripts\activate
   ```

   **On Windows (PowerShell):**
   ```powershell
   venv\Scripts\Activate.ps1
   ```

   **On Linux/macOS:**
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   If you don't have a requirements.txt file, install the required packages manually:
   ```bash
   pip install flask python-dotenv reportlab scikit-learn numpy pandas
   ```

5. **Set up environment variables (optional)**

   Create a `.env` file in the project root:
   ```bash
   # .env file
   FLASK_ENV=development
   FLASK_DEBUG=1
   SECRET_KEY=your-secret-key-here
   ```

6. **Run the application**

   **On Windows:**
   ```bash
   python app.py
   ```

   **On Linux/macOS:**
   ```bash
   python3 app.py
   ```

   Or using Flask directly:
   ```bash
   flask run
   ```

7. **Access the application**

   Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

---

## 📁 Project Structure

```
tax_agent_code/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── models/               # Machine learning models
│   ├── deduction_optimizer.pkl
│   ├── filing_status_encoder.pkl
│   └── refund_predictor.pkl
├── static/               # Static files (CSS, JS, images)
│   └── style.css
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── results.html
│   ├── tax_form.html
│   └── optimization_suggestions.html
├── venv/                 # Virtual environment
└── README.md
```

---

## 🔧 Configuration

### Environment Variables

You can configure the application using environment variables:

* `FLASK_ENV`: Set to 'development' or 'production'
* `FLASK_DEBUG`: Set to 1 for debug mode
* `SECRET_KEY`: Secret key for session management

### Flask Configuration

The application uses the following Flask configuration:

* Debug mode enabled for development
* Session management for user data
* Static file serving
* Template auto-reload

---

## 🚀 Running in Production

For production deployment:

1. **Set production environment**
   ```bash
   export FLASK_ENV=production
   export FLASK_DEBUG=0
   ```

2. **Use a production WSGI server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. **Set up a reverse proxy (nginx recommended)**

---

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Find and kill the process using port 5000
   lsof -ti:5000 | xargs kill -9
   ```

2. **Virtual environment not activated**
   - Make sure you see `(venv)` in your terminal prompt
   - Re-run the activation command

3. **Dependencies not installed**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Permission errors (Linux/macOS)**
   ```bash
   chmod +x venv/bin/activate
   ```

### Windows-Specific Issues

1. **PowerShell execution policy**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Path issues**
   - Use `python` instead of `python3` on Windows
   - Use backslashes in paths: `venv\Scripts\activate`

---

## 📌 Important Notes

* **Educational Purpose Only**: This prototype is designed for educational and prototyping purposes only and **does not constitute official tax advice**.
* **Not for Production Use**: Always consult a certified tax professional for real-world filings.
* **Data Privacy**: User data is stored in session memory and is not persisted to disk.
* **AI Limitations**: The AI recommendations are based on simplified models and should not be used for actual tax planning.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

This project is for educational purposes only. Please ensure compliance with local tax laws and regulations.

---

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the Flask documentation
3. Create an issue in the repository

**Remember**: This is a prototype for educational purposes. For actual tax preparation, consult a qualified tax professional.

