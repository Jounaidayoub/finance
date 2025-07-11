import smtplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import main
import os

main.load_dotenv()

sender_email = os.getenv("EMAIL_ADDRESS")
app_password = os.getenv("APP_PASSWORD")

receiver_email = os.getenv("RECEIVER_EMAIL") # Make recipient configurable

def send_alert_email(subject, body, recipient=None, attachment_path=None, attachment_filename=None):
    if sender_email is None or app_password is None:
        print("❌ Error: EMAIL_ADDRESS or APP_PASSWORD environment variables not set.")
        return

    if recipient is None:
        recipient = receiver_email # Use default if not provided

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    if attachment_path and attachment_filename:
        try:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {attachment_filename}",
            )
            message.attach(part)
        except Exception as e:
            print(f"❌ Error attaching file {attachment_filename}: {e}")
            return

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipient, message.as_string())
        print(f"✅ Email sent successfully to {recipient}!")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
    finally:
        if 'server' in locals() and server:
            server.quit()
