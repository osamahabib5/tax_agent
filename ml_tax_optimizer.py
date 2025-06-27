import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, classification_report
import joblib
import logging
from typing import Dict, List, Tuple, Optional
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class TaxOptimizationML:
    """Machine Learning models for tax optimization and predictive suggestions"""
    
    def __init__(self):
        self.refund_predictor = None
        self.deduction_optimizer = None
        self.risk_classifier = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.is_trained = False
        
        # Model file paths
        self.model_dir = "models"
        self.refund_model_path = os.path.join(self.model_dir, "refund_predictor.pkl")
        self.deduction_model_path = os.path.join(self.model_dir, "deduction_optimizer.pkl")
        self.risk_model_path = os.path.join(self.model_dir, "risk_classifier.pkl")
        self.scaler_path = os.path.join(self.model_dir, "scaler.pkl")
        
        # Create models directory if it doesn't exist
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Initialize or load models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models"""
        try:
            self._load_models()
            logger.info("ML models loaded successfully")
        except FileNotFoundError:
            logger.info("No existing models found, creating new ones")
            self._create_and_train_models()
    
    def _create_and_train_models(self):
        """Create and train ML models with synthetic data"""
        # Generate synthetic training data
        training_data = self._generate_synthetic_data(5000)
        
        # Train models
        self._train_refund_predictor(training_data)
        self._train_deduction_optimizer(training_data)
        self._train_risk_classifier(training_data)
        
        # Save models
        self._save_models()
        self.is_trained = True
        
        logger.info("ML models trained and saved successfully")
    
    def _generate_synthetic_data(self, n_samples: int) -> pd.DataFrame:
        """Generate synthetic tax data for training"""
        np.random.seed(42)
        
        data = []
        filing_statuses = ['single', 'married_joint', 'married_separate', 'head_of_household']
        
        for _ in range(n_samples):
            # Basic demographics
            age = np.random.randint(18, 80)
            filing_status = np.random.choice(filing_statuses)
            
            # Income generation based on realistic distributions
            if age < 25:
                income = np.random.lognormal(10.5, 0.8)  # Lower income for young adults
            elif age < 40:
                income = np.random.lognormal(11.2, 0.6)  # Peak earning years
            elif age < 65:
                income = np.random.lognormal(11.0, 0.7)  # Stable income
            else:
                income = np.random.lognormal(10.8, 0.9)  # Retirement income
            
            income = max(15000, min(500000, income))  # Reasonable bounds
            
            # Dependents based on filing status and age
            if filing_status == 'single':
                dependents = np.random.choice([0, 1], p=[0.8, 0.2])
            elif filing_status == 'head_of_household':
                dependents = np.random.randint(1, 4)
            else:  # Married
                dependents = np.random.poisson(1.5)
                dependents = min(dependents, 5)
            
            # Deductions
            standard_deduction = self._get_standard_deduction(filing_status)
            itemized_deductions = 0
            
            # Higher income tends to have more itemized deductions
            if income > 75000:
                if np.random.random() < 0.4:  # 40% chance of itemizing
                    itemized_deductions = np.random.uniform(standard_deduction * 1.1, 
                                                          standard_deduction * 2.5)
            
            # Withholding (typically 85-110% of actual tax owed)
            estimated_tax = self._estimate_tax(income, filing_status, dependents, 
                                             max(standard_deduction, itemized_deductions))
            withholding = estimated_tax * np.random.uniform(0.85, 1.10)
            
            # Calculate actual refund/owe
            actual_refund = withholding - estimated_tax
            
            # Optimization potential (how much could be saved with optimization)
            optimization_potential = income * np.random.uniform(0.01, 0.08)
            
            # Audit risk factors
            audit_risk = self._calculate_audit_risk(income, filing_status, itemized_deductions, 
                                                  dependents, actual_refund)
            
            data.append({
                'age': age,
                'filing_status': filing_status,
                'income': income,
                'dependents': dependents,
                'itemized_deductions': itemized_deductions,
                'withholding': withholding,
                'estimated_tax': estimated_tax,
                'actual_refund': actual_refund,
                'optimization_potential': optimization_potential,
                'audit_risk': audit_risk
            })
        
        return pd.DataFrame(data)
    
    def _train_refund_predictor(self, data: pd.DataFrame):
        """Train model to predict refund amounts"""
        # Prepare features
        features = ['age', 'income', 'dependents', 'itemized_deductions', 'withholding']
        categorical_features = ['filing_status']
        
        X = data[features].copy()
        
        # Encode categorical variables
        for cat_feature in categorical_features:
            if cat_feature not in self.label_encoders:
                self.label_encoders[cat_feature] = LabelEncoder()
            X[cat_feature] = self.label_encoders[cat_feature].fit_transform(data[cat_feature])
        
        X = X.join(pd.DataFrame(X.pop('filing_status')))
        y = data['actual_refund']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.refund_predictor = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.refund_predictor.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.refund_predictor.predict(X_test_scaled)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        logger.info(f"Refund predictor RMSE: ${rmse:.2f}")
    
    def _train_deduction_optimizer(self, data: pd.DataFrame):
        """Train model to predict optimization potential"""
        features = ['age', 'income', 'dependents', 'itemized_deductions']
        X = data[features]
        y = data['optimization_potential']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.deduction_optimizer = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        
        # Convert to classification problem (high/medium/low optimization potential)
        y_train_class = pd.cut(y_train, bins=3, labels=['low', 'medium', 'high'])
        y_test_class = pd.cut(y_test, bins=3, labels=['low', 'medium', 'high'])
        
        self.deduction_optimizer.fit(X_train, y_train_class)
        
        # Evaluate
        y_pred = self.deduction_optimizer.predict(X_test)
        logger.info("Deduction optimizer trained successfully")
    
    def _train_risk_classifier(self, data: pd.DataFrame):
        """Train model to classify audit risk"""
        features = ['income', 'itemized_deductions', 'dependents', 'actual_refund']
        X = data[features]
        y = data['audit_risk']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.risk_classifier = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            random_state=42
        )
        
        self.risk_classifier.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.risk_classifier.predict(X_test)
        logger.info("Risk classifier trained successfully")
    
    def predict_refund_optimization(self, user_data: Dict) -> Dict:
        """Predict potential refund optimization"""
        if not self.is_trained:
            return {'error': 'Models not trained'}
        
        try:
            # Prepare input data
            input_features = self._prepare_input_features(user_data)
            
            # Predict refund
            predicted_refund = self.refund_predictor.predict([input_features])[0]
            
            # Predict optimization potential
            optimization_features = [
                user_data['age'],
                user_data['income'],
                user_data['dependents'],
                user_data.get('itemized_deductions', 0)
            ]
            
            optimization_class = self.deduction_optimizer.predict([optimization_features])[0]
            optimization_proba = self.deduction_optimizer.predict_proba([optimization_features])[0]
            
            # Generate specific recommendations
            recommendations = self._generate_recommendations(user_data, optimization_class)
            
            return {
                'predicted_refund': round(predicted_refund, 2),
                'optimization_potential': optimization_class,
                'optimization_confidence': max(optimization_proba),
                'recommendations': recommendations,
                'model_confidence': 0.85
            }
            
        except Exception as e:
            logger.error(f"Error in refund optimization prediction: {e}")
            return {'error': str(e)}
    
    def assess_audit_risk(self, user_data: Dict, tax_result: Dict) -> Dict:
        """Assess audit risk based on tax data"""
        if not self.is_trained:
            return {'risk_level': 'unknown', 'confidence': 0}
        
        try:
            risk_features = [
                user_data['income'],
                user_data.get('itemized_deductions', 0),
                user_data['dependents'],
                tax_result.get('refund_or_owe', 0)
            ]
            
            risk_prediction = self.risk_classifier.predict([risk_features])[0]
            risk_proba = self.risk_classifier.predict_proba([risk_features])[0]
            
            # Generate risk mitigation suggestions
            risk_factors = self._identify_risk_factors(user_data, tax_result)
            
            return {
                'risk_level': risk_prediction,
                'risk_probability': max(risk_proba),
                'risk_factors': risk_factors,
                'mitigation_suggestions': self._get_risk_mitigation_suggestions(risk_factors)
            }
            
        except Exception as e:
            logger.error(f"Error in audit risk assessment: {e}")
            return {'risk_level': 'unknown', 'confidence': 0}
    
    def get_tax_planning_suggestions(self, user_data: Dict) -> List[Dict]:
        """Generate tax planning suggestions using ML insights"""
        suggestions = []
        
        income = user_data['income']
        age = user_data['age']
        filing_status = user_data['filing_status']
        dependents = user_data['dependents']
        
        # Income-based suggestions
        if income > 50000:
            suggestions.append({
                'category': 'Retirement Planning',
                'suggestion': 'Consider maximizing 401(k) contributions',
                'potential_savings': min(22500, income * 0.15) * 0.22,
                'priority': 'high',
                'implementation': 'Increase payroll deduction for retirement account'
            })
        
        if income > 100000:
            suggestions.append({
                'category': 'Tax-Advantaged Accounts',
                'suggestion': 'Maximize HSA contributions if available',
                'potential_savings': 3650 * 0.24 if filing_status == 'single' else 7300 * 0.24,
                'priority': 'high',
                'implementation': 'Enroll in high-deductible health plan with HSA'
            })
        
        # Age-based suggestions
        if age >= 50:
            suggestions.append({
                'category': 'Catch-up Contributions',
                'suggestion': 'Take advantage of catch-up retirement contributions',
                'potential_savings': 7500 * 0.24,  # Additional 401(k) catch-up
                'priority': 'medium',
                'implementation': 'Increase 401(k) contribution by $7,500'
            })
        
        # Family-based suggestions
        if dependents > 0:
            suggestions.append({
                'category': 'Education Planning',
                'suggestion': 'Consider 529 education savings plan',
                'potential_savings': 2000 * dependents,  # State tax deduction
                'priority': 'medium',
                'implementation': 'Open 529 account and set up automatic contributions'
            })
        
        # Business opportunity suggestions
        if income > 30000:
            suggestions.append({
                'category': 'Business Deductions',
                'suggestion': 'Track home office and business expenses',
                'potential_savings': 1500,
                'priority': 'low',
                'implementation': 'Maintain detailed records of business-related expenses'
            })
        
        return suggestions
    
    def _prepare_input_features(self, user_data: Dict) -> List:
        """Prepare input features for ML models"""
        features = [
            user_data['age'],
            user_data['income'],
            user_data['dependents'],
            user_data.get('itemized_deductions', 0),
            user_data.get('withholding', 0)
        ]
        
        # Add encoded filing status
        filing_status_encoded = self.label_encoders['filing_status'].transform([user_data['filing_status']])[0]
        features.append(filing_status_encoded)
        
        return features
    
    def _generate_recommendations(self, user_data: Dict, optimization_class: str) -> List[Dict]:
        """Generate specific tax optimization recommendations"""
        recommendations = []
        
        if optimization_class == 'high':
            recommendations.extend([
                {
                    'type': 'Retirement Contribution',
                    'description': 'Maximize retirement account contributions',
                    'estimated_savings': 3000,
                    'effort': 'low'
                },
                {
                    'type': 'Tax-Loss Harvesting',
                    'description': 'Consider selling losing investments to offset gains',
                    'estimated_savings': 1500,
                    'effort': 'medium'
                }
            ])
        
        elif optimization_class == 'medium':
            recommendations.extend([
                {
                    'type': 'Itemized Deductions',
                    'description': 'Review and maximize itemized deductions',
                    'estimated_savings': 800,
                    'effort': 'low'
                },
                {
                    'type': 'Charitable Giving',
                    'description': 'Consider bunching charitable contributions',
                    'estimated_savings': 600,
                    'effort': 'medium'
                }
            ])
        
        return recommendations
    
    def _identify_risk_factors(self, user_data: Dict, tax_result: Dict) -> List[str]:
        """Identify potential audit risk factors"""
        risk_factors = []
        
        income = user_data['income']
        itemized = user_data.get('itemized_deductions', 0)
        refund = tax_result.get('refund_or_owe', 0)
        
        if income > 200000:
            risk_factors.append('High income level')
        
        if itemized > income * 0.3:
            risk_factors.append('High itemized deductions relative to income')
        
        if refund > income * 0.15:
            risk_factors.append('Large refund amount')
        
        if user_data.get('business_income', 0) > 0:
            risk_factors.append('Self-employment income')
        
        return risk_factors
    
    def _get_risk_mitigation_suggestions(self, risk_factors: List[str]) -> List[str]:
        """Get suggestions to mitigate audit risk"""
        suggestions = []
        
        if 'High itemized deductions relative to income' in risk_factors:
            suggestions.append('Maintain detailed records and receipts for all deductions')
        
        if 'Large refund amount' in risk_factors:
            suggestions.append('Consider adjusting withholding to reduce refund amount')
        
        if 'Self-employment income' in risk_factors:
            suggestions.append('Keep meticulous business expense records')
        
        suggestions.append('Consider professional tax preparation for complex returns')
        
        return suggestions
    
    def _estimate_tax(self, income: float, filing_status: str, 
                     dependents: int, deductions: float) -> float:
        """Estimate tax for synthetic data generation"""
        taxable_income = max(0, income - deductions)
        
        # Simplified progressive tax calculation
        tax = 0
        brackets = [(11000, 0.10), (44725, 0.12), (95375, 0.22), (182050, 0.24)]
        
        for bracket_max, rate in brackets:
            if taxable_income <= 0:
                break
            
            bracket_income = min(taxable_income, bracket_max)
            tax += bracket_income * rate
            taxable_income -= bracket_income
        
        # Child tax credit
        tax = max(0, tax - (dependents * 2000))
        
        return tax
    
    def _get_standard_deduction(self, filing_status: str) -> int:
        """Get standard deduction amount"""
        deductions = {
            'single': 13850,
            'married_joint': 27700,
            'married_separate': 13850,
            'head_of_household': 20800
        }
        return deductions.get(filing_status, 13850)
    
    def _calculate_audit_risk(self, income: float, filing_status: str, 
                            itemized_deductions: float, dependents: int, 
                            refund: float) -> str:
        """Calculate audit risk category for synthetic data"""
        risk_score = 0
        
        # Income factor
        if income > 200000:
            risk_score += 2
        elif income > 100000:
            risk_score += 1
        
        # Deduction factor
        if itemized_deductions > income * 0.25:
            risk_score += 2
        elif itemized_deductions > income * 0.15:
            risk_score += 1
        
        # Refund factor
        if abs(refund) > income * 0.2:
            risk_score += 1
        
        # Random factor
        risk_score += np.random.randint(0, 2)
        
        if risk_score >= 4:
            return 'high'
        elif risk_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _save_models(self):
        """Save trained models to disk"""
        joblib.dump(self.refund_predictor, self.refund_model_path)
        joblib.dump(self.deduction_optimizer, self.deduction_model_path)
        joblib.dump(self.risk_classifier, self.risk_model_path)
        joblib.dump(self.scaler, self.scaler_path)
        
        # Save label encoders
        for name, encoder in self.label_encoders.items():
            encoder_path = os.path.join(self.model_dir, f"{name}_encoder.pkl")
            joblib.dump(encoder, encoder_path)
    
    def _load_models(self):
        """Load trained models from disk"""
        self.refund_predictor = joblib.load(self.refund_model_path)
        self.deduction_optimizer = joblib.load(self.deduction_model_path)
        self.risk_classifier = joblib.load(self.risk_model_path)
        self.scaler = joblib.load(self.scaler_path)
        
        # Load label encoders
        encoder_files = [f for f in os.listdir(self.model_dir) if f.endswith('_encoder.pkl')]
        for encoder_file in encoder_files:
            name = encoder_file.replace('_encoder.pkl', '')
            encoder_path = os.path.join(self.model_dir, encoder_file)
            self.label_encoders[name] = joblib.load(encoder_path)
        
        self.is_trained = True