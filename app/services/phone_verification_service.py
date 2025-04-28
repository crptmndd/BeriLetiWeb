from app.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
from twilio.rest import Client
import random


class PhoneVerificationService: 
    
    def __init__(self):
        self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        
    @staticmethod
    def generate_verification_code() -> str:
        """Генерирует 6-значный код подтверждения."""
        # return str(random.randint(1000, 9999))
        return "1234"
        
    async def send_sms_code(self, phone_number: str, code: str):
        return True