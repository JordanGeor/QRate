import os
import smtplib
from email.message import EmailMessage

def send_email(subject: str, body: str, to_email: str) -> None:
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASS", "")
    from_email = os.getenv("SMTP_FROM", user)
    use_tls = os.getenv("SMTP_TLS", "1") == "1"

    # Αν δεν έχεις ρυθμίσει SMTP ακόμα, απλά δεν στέλνει (χωρίς crash)
    if not host or not to_email or not from_email:
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP(host, port, timeout=10) as s:
        if use_tls:
            s.starttls()
        if user and password:
            s.login(user, password)
        s.send_message(msg)
