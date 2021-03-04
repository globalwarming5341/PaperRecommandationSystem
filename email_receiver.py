'''
@Description: Module for receive email
@Author: Zhuang
@Date: 2019-10-05 20:07:29
@LastEditTime: 2019-11-01 21:42:50
@LastEditors: Zhuang
'''
import poplib
import re
from email.parser import Parser
from email.utils import parseaddr



class EmailReceiver(object):

    def __init__(self):
        self._newline_pattern = re.compile(r'<br>')
        self._rn_pattern = re.compile(r'\r\n')
        self._div_pattern = re.compile(r'<div>(.*?)</div>', re.S)
        self._clean_pattern = re.compile(r'<.*?>|&.*?;')
        self._is_login = False

    def login(self, username, password):
        self._pop3 = poplib.POP3('pop.163.com')
        self._pop3.set_debuglevel(0)
        self._pop3.user(username)
        self._pop3.pass_(password)
        self._is_login = True

    def get_addr_content(self, delete=False):
        try:
            content = []
            _, message_list, __ = self._pop3.list()
            total_num = len(message_list)
            for i in range(1, total_num + 1):
                _, lines, __ = self._pop3.retr(i)
                message_content = b'\r\n'.join(lines).decode('utf-8')
                message = Parser().parsestr(text=message_content)
                addr = ''
                text_plain = ''
                text_html = ''
                for part in message.walk():
                    content_type = part.get_content_type()
                    if content_type == 'multipart/alternative':
                        _, msg_from = parseaddr(part['From'])
                        addr = msg_from
                    elif content_type == 'text/plain':
                        text = part.get_payload(decode='utf-8')
                        text_plain = self._rn_pattern.sub('\n', text.decode('utf-8', errors='ignore'))
                    elif content_type == 'text/html':
                        text = text.decode('utf-8', errors='ignore')
                        text = self._div_pattern.sub(r'\1\n', text)
                        text = self._newline_pattern.sub('\n', text)
                        text = self._clean_pattern.sub('', text).strip()
                        text_html = text
                if addr and text_plain:
                    content.append((addr, text_plain))
                elif addr and text_html:
                    content.append((addr, text_html))
                else:
                    continue
        except Exception:
            raise
        finally:
            if delete:
                self._pop3.dele(i)

        return content
    
    def logout(self):
        self._pop3.quit()
    

if __name__ == '__main__':
    
    er = EmailReceiver()
    er.login('globalwarming5341@163.com', 'hellopython123')
    
    print(er.get_addr_content(False))

    er.logout()
