import json
import os

class ServicingAgent:
    def __init__(self, services_config_path="config/services.json"):
        self.services_config_path = services_config_path
        self.services = self.load_services()
    
    def load_services(self):
        if os.path.exists(self.services_config_path):
            with open(self.services_config_path, "r") as f:
                return json.load(f)
        return self.get_default_services()
    
    def get_default_services(self):
        return {
            "block_card": {
                "response": "To block your card:\n1. Login to mobile banking\n2. Go to Cards section\n3. Select the card\n4. Click 'Block Card'\n\nWould you like me to block it for you?",
                "requires_action": True
            },
            "replace_card": {
                "response": "To request a card replacement:\n1. Login to net banking\n2. Go to Service Requests\n3. Select 'Card Replacement'\n4. Confirm address\n\nA new card will be delivered in 5-7 business days.",
                "requires_action": True
            },
            "pin_reset": {
                "response": "To reset your PIN:\n1. Visit nearest ATM\n2. Select 'PIN Generation'\n3. Enter your card and details\n4. Set new PIN\n\nAlternatively, use mobile banking 'Forgot PIN' option.",
                "requires_action": False
            },
            "cheque_book": {
                "response": "To request a cheque book:\n1. Login to net banking\n2. Go to Service Requests\n3. Select 'Cheque Book Request'\n4. Choose account and quantity\n\nCheque book will be delivered in 7 days.",
                "requires_action": True
            },
            "stop_cheque": {
                "response": "To stop a cheque payment:\n1. Login to net banking\n2. Go to 'Stop Cheque Payment'\n3. Enter cheque number and amount\n4. Confirm request\n\nA fee of 150 may apply.",
                "requires_action": True
            },
            "address_change": {
                "response": "To change your address:\n1. Download address change form from website\n2. Fill and sign the form\n3. Attach address proof\n4. Submit to nearest branch\n\nUpdate takes 3-5 business days.",
                "requires_action": False
            },
            "contact_update": {
                "response": "To update mobile number:\n1. Login to net banking\n2. Go to Profile Settings\n3. Select 'Update Contact'\n4. Enter new number\n5. Verify with OTP",
                "requires_action": True
            },
            "email_update": {
                "response": "To update email address:\n1. Login to net banking\n2. Go to Profile Settings\n3. Select 'Update Email'\n4. Enter new email\n5. Verify with OTP",
                "requires_action": True
            },
            "nominee": {
                "response": "To add or update nominee:\n1. Login to net banking\n2. Go to Account Settings\n3. Select 'Nominee Registration'\n4. Enter nominee details\n5. Submit form",
                "requires_action": True
            },
            "interest_rates": {
                "response": "Current Interest Rates:\n- Savings Account: 3.5% per annum\n- Fixed Deposit (1 year): 7.2% per annum\n- Fixed Deposit (5 years): 7.5% per annum\n- Recurring Deposit: 6.8% per annum\n\nVisit our website for complete rate sheet.",
                "requires_action": False
            },
            "fixed_deposit": {
                "response": "To open a Fixed Deposit:\n1. Login to net banking\n2. Go to 'Open FD'\n3. Select amount and tenure\n4. Choose payout option\n5. Confirm booking\n\nMinimum FD amount is 5,000.",
                "requires_action": True
            },
            "recurring_deposit": {
                "response": "To open a Recurring Deposit:\n1. Login to net banking\n2. Go to 'Open RD'\n3. Select monthly amount and tenure\n4. Choose account for debit\n5. Confirm booking\n\nMinimum monthly RD amount is 500.",
                "requires_action": True
            },
            "fund_transfer": {
                "response": "To transfer funds:\n1. Login to net banking\n2. Go to 'Fund Transfer'\n3. Select beneficiary\n4. Enter amount\n5. Confirm with OTP\n\nNEFT: Free, takes 2 hours\nIMPS: 5 fee, instant\nRTGS: 25 fee (for 2 lakh+)",
                "requires_action": True
            },
            "upi": {
                "response": "UPI Payment Services:\n- Create UPI ID in mobile banking\n- Link your account\n- Set UPI PIN\n- Start sending/receiving money\n\nDaily limit: 1,00,000 per transaction.",
                "requires_action": False
            },
            "bill_payment": {
                "response": "To pay bills:\n1. Login to net banking\n2. Go to 'Bill Pay'\n3. Select biller\n4. Enter amount\n5. Confirm payment\n\nSchedule recurring payments for convenience.",
                "requires_action": True
            },
            "branch_info": {
                "response": "Branch Hours: Monday to Friday, 10 AM to 4 PM\nSaturday: 10 AM to 1 PM\nSunday: Closed\n\nFind nearest branch using our mobile app location service.",
                "requires_action": False
            },
            "customer_care": {
                "response": "Customer Care:\n- Phone: 1800-123-4567 (24x7)\n- Email: care@agenticbank.com\n- WhatsApp: +91-9876543210\n- Chat: Available in mobile app\n\nFor complaints: grievance@agenticbank.com",
                "requires_action": False
            },
            "complaint": {
                "response": "To raise a complaint:\n1. Call customer care or\n2. Email grievance@agenticbank.com or\n3. Visit nearest branch\n\nReference number will be shared. Resolution within 7 days.",
                "requires_action": False
            }
        }
    
    async def process(self, user_id, message, service_type):
        service = self.services.get(service_type)
        
        if not service:
            return {
                "response": "I understand your request. Please contact customer care for assistance with this service.",
                "data": {"service_type": service_type}
            }
        
        return {
            "response": service.get("response", "Service information not available."),
            "data": {
                "service_type": service_type,
                "requires_action": service.get("requires_action", False)
            }
        }