import os.path, logging, os

from datetime import datetime

from email.mime.text import MIMEText

from email.mime.multipart import MIMEMultipart



class EmailSender:

    def __init__ (self, logger=None):

        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)

    def _format_templates(self, link, date,
                          html_template,
                          plain_text_template):
        with open(html_template, 'r') as f:
            template_html = f.read()

        with open(plain_text_template, 'r') as f:
            template_text = f.read()


        html = template_html.format(link=link,
                                    date=str(date))
        text = template_text.format(link=link,
                                    date=str(date))

        return text, html

    def create_fancy_email(self, to, subject, text, html):
        msg = MIMEMultipart("alternative")
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = to

        # Turn these into plain/html MIMEText objects
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        msg.attach(part1)
        msg.attach(part2)

        return msg
