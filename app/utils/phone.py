"""Phone number normalization utilities."""


def normalize_phone_number(phone: str, default_country_code: str = "52") -> str:
    """Normalize phone number to E.164 format (+XXXXXXXXXXX).

    Handles: "+5215533997393", "5215533997393", "5512345678", etc.
    """
    phone = phone.strip().replace(" ", "").replace("-", "")

    if phone.startswith("+"):
        return phone  # Already E.164

    if phone.startswith(default_country_code) and len(phone) > 10:
        return f"+{phone}"  # Has country code, just missing "+"

    return f"+{default_country_code}{phone}"  # Add country code
