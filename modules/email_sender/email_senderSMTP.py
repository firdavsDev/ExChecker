import os.path, logging, os, sys
import smtplib, ssl
from email.message import EmailMessage
from datetime import datetime

#inheritance class
from modules.email_sender.email_sender import EmailSender

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)


class EmailSenderSMTP(EmailSender):
    def __init__(self, sender_email, password, port=465,
                 smtp_server="smtp.gmail.com", logger=None):
        '''
        Create a email sender class for send emails with SMTP

        Args:
            sender_email: User's email address.
            password: password from sender user.
            port: port to smtp_server.
            smtp_server: smtp server to send emails.
            frec: set the sending frequency (nº email/hour)

        Take a look:
            https://myaccount.google.com/lesssecureapps: Activate insecure access
            in account is nedded.
            https://realpython.com/python-send-email/
        '''
        
        self.sender_email = sender_email
        self.password = password
        self.port = port
        self.smtp_server = smtp_server
        
        super().__init__(logger)

    def _send(self, message, to):
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.port, context=context) as server:
                server.login(self.sender_email, self.password)
                self.logger.info('Sendind message to ' + to)
                server.sendmail(self.sender_email, to, message.as_string())
                self.logger.info('Message to ' + to + ' sended successfully')
        except Exception as e:
            self.logger.error('An error occurred: ' + str(e))
            raise e
            
    def send_restore_pass_msg(self, to, reset_pass_link,
                          html_template=os.path.join(BASE_DIR, "forgot_pass_template.html"),
                          plain_text_template=os.path.join(BASE_DIR, "plainText_forgot_pass_template.txt")):
        
        date = datetime.now()
        text, html = self._format_templates(reset_pass_link,
                                            date,
                                            html_template,
                                            plain_text_template)
        subject = "Exchecker Recuperación de Contraseña"
        msg = self.create_fancy_email(to, subject, text, html)
        self._send(msg, to)
        
    def send_register_msg(self, to, register_link,
                          html_template=os.path.join(BASE_DIR, "register_mail_template.html"),
                          plain_text_template=os.path.join(BASE_DIR, "plainText_register_mail_template.txt")):
        
        date = datetime.now()
        text, html = self._format_templates(register_link,
                                            date,
                                            html_template,
                                            plain_text_template)
        subject = "Exchecker Verificación de Cuenta"
        msg = self.create_fancy_email(to, subject, text, html)
        self._send(msg, to)

    def send_message(self, to, subject, message_text):
        """Send an email message.

        Args:
            to: Email address of the receiver.
            subject: The subject of the email message.
            message_text: Message to be sent.
        """
        msg = EmailMessage()
        msg.set_content(message_text)

        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = to

        self._send(msg, to)

if __name__ == '__main__':
    #logging.basicConfig(level=logging.DEBUG)

    email_sender_smtp = EmailSenderSMTP('exchecker_noreply@gmail.com', 'contraseña1234')
    email_sender_smtp.send_restore_pass_msg('test_email@gmail.com',
                                    'www.excheker.com/?1234')
