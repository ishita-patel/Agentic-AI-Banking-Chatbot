from data_loader import BankDataLoader
import re
import math

data_loader = BankDataLoader()

class LoanAgent:
    def __init__(self):
        self.loan_products = {
            "personal": {
                "min_amount": 25000,
                "max_amount": 1500000,
                "base_interest_rate": 10.5,
                "min_tenure_months": 6,
                "max_tenure_months": 60,
                "processing_fee_percent": 1.0
            },
            "wedding": {
                "min_amount": 50000,
                "max_amount": 2500000,
                "base_interest_rate": 11.0,
                "min_tenure_months": 12,
                "max_tenure_months": 84,
                "processing_fee_percent": 1.0
            },
            "home_renovation": {
                "min_amount": 50000,
                "max_amount": 5000000,
                "base_interest_rate": 9.5,
                "min_tenure_months": 12,
                "max_tenure_months": 120,
                "processing_fee_percent": 0.5
            }
        }
    
    def calculate_emi(self, principal, annual_interest_rate, tenure_months):
        monthly_interest_rate = annual_interest_rate / (12 * 100)
        
        if monthly_interest_rate == 0:
            emi = principal / tenure_months
        else:
            emi = principal * monthly_interest_rate * ((1 + monthly_interest_rate) ** tenure_months) / (((1 + monthly_interest_rate) ** tenure_months) - 1)
        
        total_payment = emi * tenure_months
        total_interest = total_payment - principal
        
        return {
            "emi": round(emi, 2),
            "total_interest": round(total_interest, 2),
            "total_payment": round(total_payment, 2)
        }
    
    def check_eligibility(self, user, loan_type="personal", requested_amount=None):
        if user is None:
            return {
                "eligible": False,
                "reason": "User not found"
            }
        
        reasons = []
        score = 0
        
        account_age_years = user.get("account_age_years", 0)
        if account_age_years < 0.5:
            reasons.append("Account age less than 6 months")
        elif account_age_years >= 3:
            score += 30
        elif account_age_years >= 1:
            score += 15
        
        savings_balance = user["accounts"]["savings"]["balance"]
        if savings_balance < 10000:
            reasons.append("Minimum savings balance of 10,000 required")
        elif savings_balance >= 50000:
            score += 30
        elif savings_balance >= 25000:
            score += 15
        
        credit_score = user.get("credit_score", 0)
        if credit_score < 650:
            reasons.append("Credit score below 650")
        elif credit_score >= 750:
            score += 40
        elif credit_score >= 700:
            score += 20
        
        monthly_income = user["employment"]["monthly_income"]
        if monthly_income < 25000:
            reasons.append("Monthly income below 25,000")
        elif monthly_income >= 75000:
            score += 30
        elif monthly_income >= 50000:
            score += 15
        
        if requested_amount:
            max_eligible = monthly_income * 15
            if requested_amount > max_eligible:
                reasons.append(f"Requested amount exceeds maximum eligible (approx {max_eligible:,.0f})")
        
        eligible = len(reasons) == 0
        max_eligible_amount = int(monthly_income * 15) if eligible else 0
        
        return {
            "eligible": eligible,
            "score": score,
            "reasons": reasons,
            "max_eligible_amount": max_eligible_amount,
            "account_age_years": account_age_years,
            "credit_score": credit_score,
            "savings_balance": savings_balance,
            "monthly_income": monthly_income
        }
    
    def get_loan_offer(self, user, loan_type="personal", amount=None, tenure_months=None):
        eligibility = self.check_eligibility(user, loan_type, amount)
        
        if not eligibility["eligible"]:
            return {
                "success": False,
                "eligibility": eligibility,
                "message": "Not eligible for loan. " + " ".join(eligibility["reasons"])
            }
        
        loan_config = self.loan_products.get(loan_type, self.loan_products["personal"])
        
        if amount is None:
            amount = min(eligibility["max_eligible_amount"], loan_config["max_amount"])
        
        if amount < loan_config["min_amount"]:
            return {
                "success": False,
                "message": f"Minimum loan amount is {loan_config['min_amount']:,.0f}"
            }
        
        if amount > loan_config["max_amount"]:
            return {
                "success": False,
                "message": f"Maximum loan amount is {loan_config['max_amount']:,.0f}"
            }
        
        if amount > eligibility["max_eligible_amount"]:
            return {
                "success": False,
                "message": f"Maximum eligible amount based on income is {eligibility['max_eligible_amount']:,.0f}"
            }
        
        if tenure_months is None:
            tenure_months = 12
        
        if tenure_months < loan_config["min_tenure_months"]:
            tenure_months = loan_config["min_tenure_months"]
        elif tenure_months > loan_config["max_tenure_months"]:
            tenure_months = loan_config["max_tenure_months"]
        
        interest_rate = loan_config["base_interest_rate"]
        if user.get("credit_score", 0) >= 750:
            interest_rate -= 0.5
        elif user.get("credit_score", 0) < 650:
            interest_rate += 1.0
        
        emi_details = self.calculate_emi(amount, interest_rate, tenure_months)
        processing_fee = amount * (loan_config["processing_fee_percent"] / 100)
        
        return {
            "success": True,
            "eligibility": eligibility,
            "loan_details": {
                "type": loan_type,
                "amount": amount,
                "tenure_months": tenure_months,
                "interest_rate": interest_rate,
                "emi": emi_details["emi"],
                "total_interest": emi_details["total_interest"],
                "total_payment": emi_details["total_payment"],
                "processing_fee": processing_fee
            }
        }
    
    async def process(self, user_id, message):
        user = data_loader.get_user(user_id)
        
        if user is None:
            return {
                "response": f"User {user_id} not found",
                "data": None
            }
        
        message_lower = message.lower()
        
        if "emi for" in message_lower or "emi of" in message_lower:
            numbers = re.findall(r'\b\d{4,}\b', message_lower)
            
            if numbers:
                amount = int(numbers[0])
                
                if amount < 25000:
                    return {
                        "response": f"Minimum loan amount is 25,000. Please request a higher amount.",
                        "data": None
                    }
                if amount > 1500000:
                    return {
                        "response": f"Maximum loan amount is 1,500,000. Please request a lower amount.",
                        "data": None
                    }
                
                offer = self.get_loan_offer(user, "personal", amount)
                
                if offer["success"]:
                    details = offer["loan_details"]
                    response = f"Loan Amount: {details['amount']:,.0f}\n"
                    response += f"Tenure: {details['tenure_months']} months\n"
                    response += f"Interest Rate: {details['interest_rate']}%\n"
                    response += f"Monthly EMI: {details['emi']:,.2f}\n"
                    response += f"Processing Fee: {details['processing_fee']:,.2f}\n"
                    response += f"Total Interest: {details['total_interest']:,.2f}\n"
                    response += f"Total Payment: {details['total_payment']:,.2f}"
                else:
                    response = offer["message"]
                
                return {"response": response, "data": offer if 'offer' in locals() else None}
            else:
                return {
                    "response": "Please specify the loan amount. Example: emi for 50000",
                    "data": None
                }
        
        if "eligible" in message_lower or "check" in message_lower:
            eligibility = self.check_eligibility(user)
            
            if eligibility["eligible"]:
                response = f"You are eligible for a loan up to {eligibility['max_eligible_amount']:,.0f}. "
                response += f"Credit Score: {eligibility['credit_score']}. "
                response += f"Monthly Income: {eligibility['monthly_income']:,.0f}"
            else:
                response = "You are not eligible for a loan. Reasons:\n"
                for reason in eligibility["reasons"]:
                    response += f"- {reason}\n"
            
            return {"response": response, "data": eligibility}
        
        offer = self.get_loan_offer(user, "personal")
        
        if offer["success"]:
            details = offer["loan_details"]
            response = f"Based on your profile, you qualify for a personal loan up to {offer['eligibility']['max_eligible_amount']:,.0f}. "
            response += f"For a 12-month loan of {details['amount']:,.0f}, "
            response += f"your EMI would be {details['emi']:,.2f} at {details['interest_rate']}% interest. "
            response += "Reply 'check eligibility' for details or 'emi for 100000' for specific calculation."
        else:
            response = "You are currently not eligible for a loan. " + offer["message"]
        
        return {"response": response, "data": offer}