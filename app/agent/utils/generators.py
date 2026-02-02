"""
Utilities for generating realistic but fake Indian details.
Used to bait scammers without providing real information.
"""
import random
import string

def generate_phone_number() -> str:
    """Generate a realistic 10-digit Indian phone number starting with 6-9."""
    first_digit = str(random.randint(6, 9))
    rest = "".join([str(random.randint(0, 9)) for _ in range(9)])
    return first_digit + rest

def generate_upi_id(name: str) -> str:
    """Generate a realistic UPI ID based on the persona name."""
    clean_name = name.lower().replace(" ", "")
    suffix = random.choice(["okaxis", "okhdfcbank", "ybl", "paytm", "icici", "sbi"])
    random_num = random.randint(10, 99)
    return f"{clean_name}{random_num}@{suffix}"

def generate_bank_account() -> str:
    """Generate a realistic 11-16 digit bank account number."""
    length = random.choice([11, 12, 14, 16])
    return "".join([str(random.randint(0, 9)) for _ in range(length)])

def generate_ifsc() -> str:
    """Generate a realistic-looking Indian IFSC code (e.g., SBIN0001234)."""
    bank_code = random.choice(["SBIN", "HDFC", "ICIC", "BARB", "UBIN"])
    branch_code = "".join([str(random.randint(0, 9)) for _ in range(7)])
    return f"{bank_code}0{branch_code}"
