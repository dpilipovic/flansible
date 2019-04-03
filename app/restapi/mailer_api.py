"""Mailer functions for API"""
import os
from string import Template

import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.conf.config import APP_PATH, MAILRELAY, MAIL_PORT, EMAIL_SENDER, APP_URL, COMPANY_INFO



def send_email_api(receiver_email, filename, api_user):
    """ Function that handles mail for API calls """
    subject = "API call Ansible runlog"
    template = os.path.join(APP_PATH, "restapi", "templates", "restapi", "api_email_template.html")
    body_file = open(template)
    body_template = body_file.read()
    # Pass variables into the HTML template
    body = Template(body_template).safe_substitute(curr_user=str(api_user), app_url=str(APP_URL), company_info=str(COMPANY_INFO))
    sender_email = EMAIL_SENDER

    # Create a multipart message and set headers
    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(body, "html"))
    body_file.close()

    # Open attachment file in binary mode
    file_path = os.path.join(APP_PATH, "logs", filename)
    with open(file_path, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    # Send email via mailrelay using SMTP
    with smtplib.SMTP(MAILRELAY, MAIL_PORT) as server:
        server.sendmail(sender_email, receiver_email, text)
