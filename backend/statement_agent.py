from data_loader import BankDataLoader
from datetime import datetime, timedelta
from fpdf import FPDF
import os
import re

data_loader = BankDataLoader()

class StatementAgent:
    def __init__(self):
        self.statements_dir = "generated_statements"
        if not os.path.exists(self.statements_dir):
            os.makedirs(self.statements_dir)
    
    def parse_date_range(self, message_lower):
        today = datetime.now()
        
        if "last month" in message_lower:
            start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            end_date = today.replace(day=1) - timedelta(days=1)
        elif "last 3 months" in message_lower or "last three months" in message_lower:
            start_date = (today.replace(day=1) - timedelta(days=90))
            end_date = today
        elif "last 6 months" in message_lower or "last six months" in message_lower:
            start_date = (today.replace(day=1) - timedelta(days=180))
            end_date = today
        elif "this month" in message_lower:
            start_date = today.replace(day=1)
            end_date = today
        elif "last week" in message_lower:
            start_date = today - timedelta(days=7)
            end_date = today
        else:
            start_date = today - timedelta(days=30)
            end_date = today
        
        return start_date, end_date
    
    def generate_pdf_bytes(self, user, transactions, start_date, end_date, account_type):
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, "Agentic Bank - Account Statement", ln=True, align="C")
        pdf.ln(10)
        
        # Customer Details
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, "Customer Information", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(100, 8, f"Name: {user['name']}", ln=True)
        pdf.cell(100, 8, f"User ID: {user['user_id']}", ln=True)
        pdf.cell(100, 8, f"Account Type: {account_type.capitalize()}", ln=True)
        pdf.cell(100, 8, f"Account Number: {user['accounts'][account_type]['account_number']}", ln=True)
        pdf.ln(5)
        
        # Statement Period
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, "Statement Period", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(100, 8, f"From: {start_date.strftime('%d-%b-%Y')}", ln=True)
        pdf.cell(100, 8, f"To: {end_date.strftime('%d-%b-%Y')}", ln=True)
        pdf.ln(5)
        
        # Opening Balance
        opening_balance = user['accounts'][account_type]['balance']
        for t in reversed(transactions):
            if t['date'] < start_date.isoformat():
                opening_balance = t.get('balance_after', opening_balance)
                break
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, "Balance Summary", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(100, 8, f"Opening Balance: {opening_balance:,.2f}", ln=True)
        pdf.cell(100, 8, f"Closing Balance: {user['accounts'][account_type]['balance']:,.2f}", ln=True)
        pdf.ln(5)
        
        # Transaction Table Header
        pdf.set_font("Arial", "B", 10)
        pdf.cell(40, 10, "Date", 1)
        pdf.cell(80, 10, "Description", 1)
        pdf.cell(35, 10, "Amount", 1)
        pdf.cell(35, 10, "Balance", 1)
        pdf.ln()
        
        # Transaction Rows
        pdf.set_font("Arial", "", 9)
        filtered_count = 0
        for t in transactions:
            if t['date'] >= start_date.isoformat() and t['date'] <= end_date.isoformat():
                filtered_count += 1
                if filtered_count <= 50:
                    date_str = t['date'][:10]
                    desc = t['description'][:40]
                    amount_str = f"{t['amount']:,.2f}"
                    balance_str = f"{t.get('balance_after', 0):,.2f}"
                    
                    pdf.cell(40, 8, date_str, 1)
                    pdf.cell(80, 8, desc, 1)
                    pdf.cell(35, 8, amount_str, 1)
                    pdf.cell(35, 8, balance_str, 1)
                    pdf.ln()
        
        if filtered_count > 50:
            pdf.cell(190, 8, f"... and {filtered_count - 50} more transactions", 1, 1, "C")
        
        # Footer
        pdf.ln(10)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(200, 10, "This is a computer-generated statement. No signature required.", ln=True, align="C")
        pdf.cell(200, 10, f"Generated on: {datetime.now().strftime('%d-%b-%Y %H:%M:%S')}", ln=True, align="C")
        
        return pdf.output(dest='S').encode('latin1')
    
    async def process(self, user_id, message):
        user = data_loader.get_user(user_id)
        
        if user is None:
            return {
                "response": f"User {user_id} not found",
                "data": None
            }
        
        message_lower = message.lower()
        
        if "savings" in message_lower:
            account_type = "savings"
        elif "checking" in message_lower:
            account_type = "checking"
        else:
            account_type = "savings"
        
        start_date, end_date = self.parse_date_range(message_lower)
        transactions = data_loader.get_transactions(user_id, account_type, 365)
        
        filtered_transactions = []
        for t in transactions:
            t_date = datetime.fromisoformat(t['date'])
            if start_date <= t_date <= end_date:
                filtered_transactions.append(t)
        
        if len(filtered_transactions) == 0:
            return {
                "response": f"No transactions found for {account_type} account in the specified period.",
                "data": None
            }
        
        pdf_bytes = self.generate_pdf_bytes(user, transactions, start_date, end_date, account_type)
        
        total_credits = sum(t['amount'] for t in filtered_transactions if t['amount'] > 0)
        total_debits = sum(t['amount'] for t in filtered_transactions if t['amount'] < 0)
        
        filename = f"statement_{user['user_id']}_{account_type}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        response = f"Statement generated for {account_type} account.\n"
        response += f"Period: {start_date.strftime('%d-%b-%Y')} to {end_date.strftime('%d-%b-%Y')}\n"
        response += f"Total Credits: {total_credits:,.2f}\n"
        response += f"Total Debits: {abs(total_debits):,.2f}\n"
        response += f"Total Transactions: {len(filtered_transactions)}\n\n"
        response += "Click the Download button below to save the PDF."
        
        return {
            "response": response,
            "pdf_bytes": pdf_bytes,
            "filename": filename,
            "data": {
                "account_type": account_type,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_credits": total_credits,
                "total_debits": abs(total_debits),
                "transaction_count": len(filtered_transactions)
            }
        }