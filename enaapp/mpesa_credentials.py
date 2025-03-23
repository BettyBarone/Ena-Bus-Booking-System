import requests
import base64
import datetime
from django.conf import settings

# Replace these with your actual credentials from Safaricom
CONSUMER_KEY = "5aXeXUXQyvwTpGW20xve4Q4TZTG5PjHXYdcGdk96ssRNvd4Z"
CONSUMER_SECRET = "UdUB14bpKN72wGA6WYVUMJb9zzBtrRJHeh5NTLSDIoo1Io2wtyHeVX7it40eJDom"
BUSINESS_SHORTCODE = "174379"
PASSKEY = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"

class MpesaAccessToken:
    """ Class to generate an access token for MPESA API """
    
    @staticmethod
    def get_access_token():
        api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(api_url, auth=(CONSUMER_KEY, CONSUMER_SECRET))
        access_token = response.json().get("access_token")
        return access_token

class LipanaMpesaPpassword:
    """ Class to generate Lipa Na MPESA password """

    BusinessShortCode = BUSINESS_SHORTCODE

    @staticmethod
    def get_timestamp():
        return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    @staticmethod
    def encode_password():
        """ Generate Base64-encoded password for Lipa Na MPESA request """
        timestamp = LipanaMpesaPpassword.get_timestamp()
        data_to_encode = f"{LipanaMpesaPpassword.BusinessShortCode}{PASSKEY}{timestamp}"
        encoded_password = base64.b64encode(data_to_encode.encode()).decode()
        return encoded_password
