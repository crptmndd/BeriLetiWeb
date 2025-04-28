from app.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
from twilio.rest import Client
import random


class PhoneVerificationService: 
    
    def __init__(self):
        self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        
    @staticmethod
    def generate_verification_code() -> str:
        """Генерирует 6-значный код подтверждения."""
        return str(random.randint(1000, 9999))
        
    async def send_sms_code(self, phone_number: str, code: str):
        service = self.client.verify.v2.services.create(
            friendly_name="BeriLeti", custom_code_enabled=True
        )   
        ph = f"+{phone_number}"
        verification = self.client.verify.v2.services(
            service.sid
        ).verifications.create(to=ph, channel="sms", custom_code=code)
        
        return (verification, verification.status)