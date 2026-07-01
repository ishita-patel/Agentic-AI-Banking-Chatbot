# backend/auth/totp_service.py

import pyotp
import qrcode


class TOTPService:

    @staticmethod
    def generate_secret():
        return pyotp.random_base32()

    @staticmethod
    def generate_qr(secret, username):
        uri = pyotp.TOTP(secret).provisioning_uri(
            name=username,
            issuer_name="Aiko Bank"
        )

        img = qrcode.make(uri)

        path = f"qr_codes/{username}.png"
        img.save(path)

        return path

    @staticmethod
    def verify(secret, otp):
        return pyotp.TOTP(secret).verify(otp)