# -*- coding: utf-8 -*-
'''
@Description: Module for sending email automatically.
@Author: Zhuang
@Date: 2019-10-03 16:51:36
@LastEditTime: 2019-11-02 13:27:44
@LastEditors: Zhuang
'''

import os
import smtplib
import time
import re
from pandas import DataFrame
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import parseaddr, formataddr
from smtplib import SMTPServerDisconnected
from utils import store_data, get_arxiv_paper_id_by_arxiv



class NotLoggedIn(Exception):
    pass

class NotSettingContent(Exception):
    pass


class EmailTemplate(object):

    def __init__(self, base_content=None):
        if base_content:
            self._content = base_content
        else:
            self._content = '<h1>Automatic arXiv Paper Recommendation</h1><br />'
        self._feedback_content = '<h2>::Feedback::</h2>'

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        if not isinstance(value, str):
            raise TypeError('You must give a string as a value.')
        self._content = value
    
    # def attach_feedback(self):
    #     self._content += '<p>======================================================</p>'
    #     self._content += self._feedback_content
    #     self._content += '<p>======================================================</p>'

    # def fill_paper(self, user_id, data, field_name, repeat_set=None):
    def fill_paper(self, user_id, data, keywords):
        """Fill up email content with field name and arXiv paper.
        
        Arguments:
            data {DataFrame} -- A dataframe with title, abstract, arXiv number.
            field_name {str} -- Research field name.
        
        Keyword Arguments:
            repeat_set {set} -- To remove repeated data (default: {None})
        
        Raises:
            TypeError: Raise the exception if the parameter 'data' is not a pd.Dataframe.
        """
        if not isinstance(data, DataFrame):
            raise TypeError('The parameter \'data\' expects a pd.DataFrame object but got a {}'.format(type(data)))
        i = 1
        for item in data.itertuples(index=False):
            # arxiv_paper_id = getattr(item, 'id')
            arXiv_content = getattr(item, 'arxiv')
            title_content = getattr(item, 'title')
            abstract_content = getattr(item, 'abstract')
            self._content += '<p>------------------------------------------------------------------------------------------------</p>'
            self._content += '<p><b>Top:</b> {}</p>'.format(i)
            self._content += '<p><b>arXiv:</b> {}-</p>'.format(arXiv_content)
            self._content += '<p>(Tips: Type any character after "-", representing you like this paper.)</p>'
            self._content += '<p><b>Title:</b> {}</p>'.format(title_content)
            self._content += '<p><b>Abstract:</b> {}</p>'.format(abstract_content)
            self._content += '<p><b>Link:</b><a href="https://arxiv.org/abs/{}">https://arxiv.org/abs/{}</a></p>'.format(arXiv_content, arXiv_content)
            self._content += '<p>------------------------------------------------------------------------------------------------</p>'
            
            for kw in keywords:
                kw_pattern = re.compile(r'({})'.format(kw), re.I)
                self._content = kw_pattern.sub(r'<b style="color: rgb(255, 0, 0);">\1</b>',self._content)

            i += 1

class EmailSender(object):
    def __init__(self):
        self._smtp = smtplib.SMTP()
        self._multipart = None
        self._isConnected = False

    def login(self,host, port, username, passwd):
        self._smtp.connect(host=host, port=port)
        self._smtp.login(user=username, password=passwd)
        self._isConnected = True

    def setContent(self, title, content, app_files=None):
        if self._isConnected:
            self._multipart = MIMEMultipart()
            self._multipart['Subject'] = title
            if isinstance(content, EmailTemplate):
                content = MIMEText(content.content, 'html', 'utf-8')
            elif isinstance(content, str):
                content = MIMEText(content, 'plain', 'utf-8')
            else:
                raise TypeError('The parameter \'content\' must be a str or EmailTemplate.')
            self._multipart.attach(content)
            if app_files:
                if isinstance(app_files, list):
                    for file_path in app_files:
                        file = open(file_path, 'rb')
                        file_name = os.path.basename(file_path)
                        app = MIMEApplication(file.read())
                        app.add_header('Content-Disposition', 'attachment', filename=file_name)
                        self._multipart.attach(app)
                else:
                    raise ValueError('The parameter 3 must be a list.')

    def sendEmail(self, from_addr, to_addr, from_name=None):
        if self._multipart:
            if from_name:
                self._multipart['From'] = formataddr((Header(from_name, 'utf-8').encode(), from_addr))
            else:
                self._multipart['From'] = from_addr
            self._multipart['To'] = ';'.join(to_addr)
            self._smtp.sendmail(from_addr, to_addr, self._multipart.as_string())
        else:
            raise NotSettingContent()

    def logout(self):
        self._smtp.quit()




if __name__ == '__main__':
    template = '''<p>This is a simple template</p>
    <p><b>Bold</b></p>
    <p><a href="https://www.baidu.com">Baidu</a></p>
    '''
    e = EmailSender()
    e.login('smtp.163.com', 25, 'globalwarming5341@163.com', 'hellopython123')
    e.setContent('paperpaper', template)
    e.sendEmail('globalwarming5341@163.com', ['shiquying@163.com'], 'paper html')
    e.logout()
