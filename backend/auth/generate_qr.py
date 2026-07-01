import pyotp
import qrcode

secret = "OZUEDAAZPCMPKPIK4GFKCGVFKVQFFMQG"

uri = pyotp.TOTP(secret).provisioning_uri(
    name="raj.sharma",
    issuer_name="Aiko Bank"
)

img = qrcode.make(uri)

img.save("aiko_bank_mfa.png")

print("QR generated successfully")