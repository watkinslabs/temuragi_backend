import os
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import requests
import json
from jinja2 import Environment, FileSystemLoader

class Office365Mailer:
    """
    Class for sending emails using Microsoft Office 365 via Microsoft Graph API
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
        
        # Set up Jinja environment
        self.jinja_env = Environment(
            loader=FileSystemLoader('templates')
        )
    
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
    
    def send_template_email(self, from_email, to_email, subject, template_path, template_data,
                           cc=None, bcc=None):
        """
        Send email using a Jinja template
        
        Args:
            from_email: Sender email address
            to_email: Recipient email or list of recipients
            subject: Email subject
            template_path: Path to Jinja template (relative to templates directory)
            template_data: Dictionary of data to render in the template
            cc: Carbon copy recipients (optional)
            bcc: Blind carbon copy recipients (optional)
            
        Returns:
            True if successful, False otherwise with error message
        """
        try:
            # Render template
            template = self.jinja_env.get_template(template_path)
            html_body = template.render(**template_data)
            
            # Create plain text version
            # This is a simple conversion - you might want a more sophisticated one
            text_body = self._html_to_text(html_body)
            
            # Send email using Graph API
            return self.send_graph_api(
                from_email=from_email,
                to_email=to_email,
                subject=subject,
                body_text=text_body,
                body_html=html_body,
                cc=cc,
                bcc=bcc
            )
            
        except Exception as e:
            return False, f"Error sending template email: {str(e)}"
    
    def _html_to_text(self, html):
        """
        Simple HTML to plain text conversion
        
        Args:
            html: HTML content
            
        Returns:
            Plain text version
        """
        # Replace some common HTML elements with plain text equivalents
        # This is a very basic implementation
        text = html.replace('<p>', '').replace('</p>', '\n\n')
        text = text.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
        text = text.replace('&nbsp;', ' ')
        
        # Remove remaining HTML tags
        in_tag = False
        plain_text = ''
        for char in text:
            if char == '<':
                in_tag = True
            elif char == '>':
                in_tag = False
            elif not in_tag:
                plain_text += char
                
        return plain_text
    
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


def send_password_reset_email(user_email, reset_token, app_name="Performance Radiator"):
    """
    Send password reset email using the Jinja template
    
    Args:
        user_email: Email address to send to
        reset_token: The reset token to include in the link
        app_name: Application name for the email
        
    Returns:
        Tuple of (success, message)
    """
    # Create mailer with your Azure AD credentials
    mailer = Office365Mailer({
        'tenant_id': 'your_tenant_id',
        'client_id': 'your_client_id',
        'client_secret': 'your_client_secret',
        'user_id': 'noreply@yourcompany.com'  # Optional for shared mailbox
    })
    
    # Construct reset URL - adjust base URL for your environment
    reset_url = f"https://yourapp.com/reset-password?token={reset_token}"
    
    # Prepare template data
    template_data = {
        'app_name': app_name,
        'reset_url': reset_url,
        'expires_in': '24 hours',
        'user_email': user_email
    }
    
    # Send email with template
    return mailer.send_template_email(
        from_email='noreply@yourcompany.com',
        to_email=user_email,
        subject=f"{app_name} - Password Reset Request",
        template_path='email/reset.html',  # This will load from templates/email/reset.html
        template_data=template_data
    )


# Integration with your AuthDB class
def handle_reset_request(email):
    """
    Process a password reset request
    
    Args:
        email: User's email address
        
    Returns:
        Tuple of (success, message)
    """
    # Get user by email
    auth_db = AuthDB()
    user = auth_db.get_user_by_email(email)
    
    if not user:
        return False, "User not found"
    
    # Create reset token
    reset_token = auth_db.create_reset_token(user['user_id'])
    
    if not reset_token:
        return False, "Failed to create reset token"
    
    # Send email
    email_success, email_message = send_password_reset_email(email, reset_token)
    
    if not email_success:
        return False, f"Failed to send email: {email_message}"
    
    return True, "Password reset instructions sent to your email"