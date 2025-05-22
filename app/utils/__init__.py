import os
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import requests
import json

class Office365Mailer:
    """
    Class for sending emails using Microsoft Office 365
    
    Supports two methods:
    1. SMTP with modern authentication
    2. Microsoft Graph API with OAuth (app registration)
    """
    
    def __init__(self, config=None):
        """
        Initialize with configuration
        
        Args:
            config: Dictionary containing authentication details
        """
        self.config = config or {}
        self.token = None
        self.token_expires = None
        
    def send_smtp(self, from_email, to_email, subject, body_text, body_html=None, 
                  password=None, cc=None, bcc=None):
        """
        Send email using SMTP with authentication
        
        Args:
            from_email: Sender email address
            to_email: Recipient email or list of recipients
            subject: Email subject
            body_text: Plain text email body
            body_html: HTML email body (optional)
            password: Email password (if not in config)
            cc: Carbon copy recipients (optional)
            bcc: Blind carbon copy recipients (optional)
            
        Returns:
            True if successful, False otherwise with error message
        """
        try:
            # Create message container
            msg = MIMEMultipart('alternative')
            msg['From'] = from_email
            
            # Handle multiple recipients
            if isinstance(to_email, list):
                msg['To'] = ', '.join(to_email)
            else:
                msg['To'] = to_email
                
            # Add CC if provided
            if cc:
                if isinstance(cc, list):
                    msg['Cc'] = ', '.join(cc)
                else:
                    msg['Cc'] = cc
                    
            # Add BCC (not visible in headers)
            if bcc and not isinstance(bcc, list):
                bcc = [bcc]
                
            msg['Subject'] = subject
            
            # Attach parts
            part1 = MIMEText(body_text, 'plain')
            msg.attach(part1)
            
            # Add HTML part if provided
            if body_html:
                part2 = MIMEText(body_html, 'html')
                msg.attach(part2)
            
            # Get password from config if not provided
            password = password or self.config.get('password')
            if not password:
                return False, "Password not provided"
            
            # Connect to Office 365 SMTP server
            with smtplib.SMTP('smtp.office365.com', 587) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                
                # Login with credentials
                smtp.login(from_email, password)
                
                # Determine all recipients for sending
                all_recipients = []
                if isinstance(to_email, list):
                    all_recipients.extend(to_email)
                else:
                    all_recipients.append(to_email)
                    
                if cc:
                    if isinstance(cc, list):
                        all_recipients.extend(cc)
                    else:
                        all_recipients.append(cc)
                        
                if bcc:
                    all_recipients.extend(bcc)
                
                # Send email
                smtp.sendmail(from_email, all_recipients, msg.as_string())
                
            return True, "Email sent successfully"
            
        except Exception as e:
            return False, f"Error sending email: {str(e)}"
    
    def _get_access_token(self):
        """
        Get Microsoft Graph API access token
        
        Returns:
            Access token string
        """
        # Check if we have a valid token already
        now = datetime.now()
        if self.token and self.token_expires and self.token_expires > now:
            return self.token
            
        # Get required config values
        tenant_id = self.config.get('tenant_id')
        client_id = self.config.get('client_id')
        client_secret = self.config.get('client_secret')
        
        if not all([tenant_id, client_id, client_secret]):
            raise ValueError("Missing required Azure AD credentials")
            
        # Get token from Microsoft identity platform
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'https://outlook.office365.com/.default'
        }
        
        response = requests.post(token_url, data=token_data)
        
        if response.status_code != 200:
            raise Exception(f"Failed to obtain access token: {response.text}")
            
        token_info = response.json()
        self.token = token_info.get('access_token')
        
        # Calculate token expiry time (subtract 5 minutes for safety margin)
        expires_in = token_info.get('expires_in', 3600)
        self.token_expires = now + timedelta(seconds=expires_in - 300)
        
        return self.token
    
    def send_graph_api(self, from_email, to_email, subject, body_text, body_html=None,
                      cc=None, bcc=None):
        """
        Send email using Microsoft Graph API
        
        Args:
            from_email: Sender email address
            to_email: Recipient email or list of recipients
            subject: Email subject
            body_text: Plain text email body
            body_html: HTML email body (optional)
            cc: Carbon copy recipients (optional)
            bcc: Blind carbon copy recipients (optional)
            
        Returns:
            True if successful, False otherwise with error message
        """
        try:
            # Get access token
            token = self._get_access_token()
            
            # Format recipients
            recipients = []
            if isinstance(to_email, list):
                for email in to_email:
                    recipients.append({'emailAddress': {'address': email}})
            else:
                recipients.append({'emailAddress': {'address': to_email}})
                
            # Format CC recipients
            cc_recipients = []
            if cc:
                if isinstance(cc, list):
                    for email in cc:
                        cc_recipients.append({'emailAddress': {'address': email}})
                else:
                    cc_recipients.append({'emailAddress': {'address': cc}})
                    
            # Format BCC recipients
            bcc_recipients = []
            if bcc:
                if isinstance(bcc, list):
                    for email in bcc:
                        bcc_recipients.append({'emailAddress': {'address': email}})
                else:
                    bcc_recipients.append({'emailAddress': {'address': bcc}})
            
            # Create message payload
            email_data = {
                'message': {
                    'subject': subject,
                    'body': {
                        'contentType': 'HTML' if body_html else 'Text',
                        'content': body_html if body_html else body_text
                    },
                    'toRecipients': recipients
                }
            }
            
            # Add CC and BCC if provided
            if cc_recipients:
                email_data['message']['ccRecipients'] = cc_recipients
                
            if bcc_recipients:
                email_data['message']['bccRecipients'] = bcc_recipients
                
            # Set sender if sending from shared mailbox
            if self.config.get('use_user_id'):
                email_data['saveToSentItems'] = 'true'
            else:
                email_data['message']['from'] = {'emailAddress': {'address': from_email}}
            
            # API endpoint - depends on whether sending from user or shared mailbox
            user_id = self.config.get('user_id', from_email)
            api_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/sendMail"
            
            # Send request
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(api_url, headers=headers, data=json.dumps(email_data))
            
            if response.status_code >= 400:
                return False, f"Failed to send email. Status code: {response.status_code}, Error: {response.text}"
                
            return True, "Email sent successfully"
            
        except Exception as e:
            return False, f"Error sending email: {str(e)}"


# Example usage:
if __name__ == "__main__":
    # Configuration for Graph API
    graph_config = {
        'tenant_id': 'your_tenant_id',
        'client_id': 'your_client_id',
        'client_secret': 'your_client_secret',
        'user_id': 'shared_mailbox@yourdomain.com'  # Optional for shared mailbox
    }
    
    # Configuration for SMTP
    smtp_config = {
        'password': 'your_email_password'
    }
    
    # Create mailer instances
    graph_mailer = Office365Mailer(graph_config)
    smtp_mailer = Office365Mailer(smtp_config)
    
    # Send using Graph API
    success, message = graph_mailer.send_graph_api(
        from_email='sender@yourdomain.com',
        to_email='recipient@example.com',
        subject='Test Email via Graph API',
        body_text='This is a test email sent via Microsoft Graph API.',
        body_html='<p>This is a <strong>test email</strong> sent via Microsoft Graph API.</p>'
    )
    print(f"Graph API: {success} - {message}")
    
    # Send using SMTP
    success, message = smtp_mailer.send_smtp(
        from_email='sender@yourdomain.com',
        to_email='recipient@example.com',
        subject='Test Email via SMTP',
        body_text='This is a test email sent via SMTP.',
        body_html='<p>This is a <strong>test email</strong> sent via SMTP.</p>'
    )
    print(f"SMTP: {success} - {message}")