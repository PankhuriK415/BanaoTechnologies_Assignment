import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_email(event, context):
    try:
        # Check event body (serverless-offline delivers this as event.get('body'))
        body_str = event.get('body', '{}')
        if not body_str:
            body_str = '{}'
        
        # In serverless-offline/Lambda, event['body'] can sometimes be a dict if pre-parsed
        if isinstance(body_str, dict):
            body = body_str
        else:
            body = json.loads(body_str)
        
        trigger = body.get('trigger')
        email = body.get('email')
        data = body.get('data', {})
        
        if not email or not trigger:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing email or trigger'})
            }
        
        # Craft email
        subject = ""
        html_content = ""
        
        if trigger == 'SIGNUP_WELCOME':
            subject = "Welcome to Mini HMS!"
            name = data.get('name', 'User')
            role = data.get('role', 'Patient')
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <div style="background-color: #0d6efd; color: white; padding: 20px; text-align: center;">
                            <h1 style="margin: 0;">Welcome to Mini HMS!</h1>
                        </div>
                        <div style="padding: 20px;">
                            <h2>Hello {name},</h2>
                            <p>Thank you for signing up on the Mini Hospital Management System (HMS).</p>
                            <p>Your account has been registered with the role of <strong>{role.upper()}</strong>.</p>
                            <p>You can now log into your dashboard to manage appointments and calendar slots.</p>
                            <br>
                            <p>Best regards,<br>The Mini HMS Team</p>
                        </div>
                    </div>
                </body>
            </html>
            """
        elif trigger == 'BOOKING_CONFIRMATION':
            subject = "Appointment Booking Confirmed!"
            patient_name = data.get('patient_name', 'Patient')
            doctor_name = data.get('doctor_name', 'Doctor')
            date = data.get('date', '')
            start_time = data.get('start_time', '')
            end_time = data.get('end_time', '')
            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <div style="background-color: #198754; color: white; padding: 20px; text-align: center;">
                            <h1 style="margin: 0;">Appointment Confirmed!</h1>
                        </div>
                        <div style="padding: 20px;">
                            <h2>Hello {patient_name},</h2>
                            <p>Your appointment with <strong>Dr. {doctor_name}</strong> has been successfully booked.</p>
                            <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #198754; margin: 20px 0;">
                                <p style="margin: 5px 0;"><strong>Date:</strong> {date}</p>
                                <p style="margin: 5px 0;"><strong>Time:</strong> {start_time} - {end_time}</p>
                            </div>
                            <p>Google Calendar events have been automatically scheduled on both of your connected Google Calendars.</p>
                            <br>
                            <p>Best regards,<br>The Mini HMS Team</p>
                        </div>
                    </div>
                </body>
            </html>
            """
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Unsupported trigger: {trigger}'})
            }
        
        # Setup SMTP
        smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_user = os.environ.get('SMTP_USER', '')
        smtp_pass = os.environ.get('SMTP_PASS', '')
        
        print(f"[{trigger}] Attempting to send email to {email}...")
        
        if not smtp_user or not smtp_pass:
            # Fallback to local console log & file mock if SMTP config is missing (super robust for local running!)
            print("--- SMTP Credentials Missing! Logging Email to Console and File instead ---")
            print(f"To: {email}")
            print(f"Subject: {subject}")
            print("-----------------------------------------------------------------")
            
            # Write to a local file in the workspace as a verifiable mock log!
            log_dir = os.path.join(os.path.dirname(__file__), 'sent_emails_log')
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"{trigger}_{email}.html")
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"To: {email}\nSubject: {subject}\n\n{html_content}")
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'message': 'Email logged to local server console and files successfully (Mock SMTP Mode).',
                    'logged_file': log_file
                })
            }
            
        # Send actual SMTP email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = email
        
        part = MIMEText(html_content, 'html')
        msg.attach(part)
        
        # Connect & Send
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [email], msg.as_string())
        server.quit()
        
        print(f"Email sent successfully to {email}!")
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'Email sent successfully!'})
        }
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
