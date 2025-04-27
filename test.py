# import secrets
# secret_key = secrets.token_hex(32)
# print(secret_key)


import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
client = Client(account_sid, auth_token)

service = client.verify.v2.services.create(
    friendly_name="BeriLeti", custom_code_enabled=True
)

print(service.sid)


verification = client.verify.v2.services(
    service.sid
).verifications.create(to="+79934205484", channel="sms", custom_code=1010)

print(verification.status)