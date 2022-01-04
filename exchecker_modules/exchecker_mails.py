import os, sys
from secrets import token_hex

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR,  '..', 'modules'))
from email_sender.email_senderSMTP import EmailSenderSMTP
from modules.timeOut.timeout import TimeOut

class ExcheckerMails(EmailSenderSMTP):
    def __init__ (self, sender_email, password, web_url,
                 restore_tout=60,
                 register_tout=60, port=465,
                 smtp_server="smtp.gmail.com", logger=None):
        
        self.web_url = web_url
        
        #In minutes
        self.restore_tout = restore_tout
        
        # This dict saves request from restore_pass requests.
        # Keys are generated tokens and values are timeout and email.
        self.restore_pass_request = {}
        
        # This dict saves request from register requests.
        # Keys are generated tokens and values are First name, last name,
        # username, email and pass.
        self.register_requests = {}

        super().__init__(sender_email, password, port,
                 smtp_server, logger)
                 
    def send_restore(self, to):
         request_tout = TimeOut(minutes=self.restore_tout)
         request_token = token_hex(16)
         self.restore_pass_request[request_token] = {'timeout': request_tout,
											 'email': to}
         reset_pass_link = self.web_url + '/accounts/restore_password/?t='+request_token
         self.send_restore_pass_msg(to, reset_pass_link)
        
    def check_restore(self, token):
        if token in self.restore_pass_request:
            request_tout = self.restore_pass_request[token]['timeout']
            email = self.restore_pass_request[token]['email']
            del self.restore_pass_request[token]
            if not request_tout.is_expired:
                return True, email
            else:
                return False, None
        else:
            return False, None
        
    def send_register(self, to, data):
         request_tout = TimeOut(minutes=self.restore_tout)
         request_token = token_hex(16)
         data['timeout'] = request_tout
         self.register_requests[request_token] = data
         verify_account_link = self.web_url + '/accounts/verify_account/?t='+request_token
         self.send_register_msg(to, verify_account_link)
        
    def check_register(self, token):
        if token in self.register_requests:
            request_tout = self.register_requests[token]['timeout']
            del self.register_requests[token]['timeout']
            data = self.register_requests[token]
            del self.register_requests[token]
            if not request_tout.is_expired:
                return True, data
            else:
                return False, None
        else:
            return False, None
