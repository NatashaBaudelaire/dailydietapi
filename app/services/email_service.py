import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email(to_emails, subject, html_content):
    """
    Send an email using SendGrid

    :param to_emails: Recipient's email address
    :param subject: Email subject
    :param html_content: Email content in HTML format
    :return: True if email was sent, else False
    """
    message = Mail(
        from_email=os.environ.get('SENDER_EMAIL'),
        to_emails=to_emails,
        subject=subject,
        html_content=html_content
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        return response.status_code == 202
    except Exception as e:
        print(e)
        return False
