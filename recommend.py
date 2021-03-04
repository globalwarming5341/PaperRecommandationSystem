# -*- coding: utf-8 -*-
'''
@Description: To recommend paper.
@Author: Zhuang
@Date: 2019-10-05 14:22:34
@LastEditTime: 2019-12-18 16:28:52
@LastEditors: Zhuang
'''

from similarity_calculate import SimilarityCalculator
from email_sender import EmailTemplate, EmailSender
from utils import (load_data, 
    load_data_from_eml, 
    store_data,
    get_data,
    get_user_id_by_email, 
    get_email_id,
    update_user_preference,
    get_index_and_num,
    delete_data)
import datetime
import random
import os
import re
import pandas as pd
import numpy as np
import time
import logging
import sys

class PaperRecommender(object):

    def __init__(self):
        # self._feedback_pattern = re.compile(r'^[Ee][Mm](\d+?)-([01]+?)(?:\n|$)')
        # self._feedback_pattern = re.compile(r'=\n+?::Feedback::\n+?(\d.*\n)=', re.S)
        self._arxiv_prefer_pattern = re.compile(r'\narXiv:\s(\d+\.\d+)-(.*?)\n')
        self._smtp_server = 'smtp.163.com'
        self._user = 'globalwarming5341@163.com'
        self._passwd = 'hellopython123'

    def _send_email(self, to, content):
        t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        e = EmailSender()
        e.login(self._smtp_server, 25, self._user, self._passwd)
        e.setContent('arXiv Paper Recommendation({})'.format(t), content)
        e.sendEmail(self._user, [to], 'Automatic Paper Recommendation')
        e.logout()

    def process_feedback(self, addr, content):
        try:
            feedback = self.get_feedback(content)
            if feedback:
                self.set_user_preference(addr, feedback)
        except Exception as e:
            print('Feedback Exception: ' + str(e))
            with open('temp/{}.txt'.format(int(time.time() * 1000)), 'w', encoding='utf-8') as f:
                f.write(content)


    def get_feedback(self, text):
        fb = self._arxiv_prefer_pattern.findall(text)
        if fb:
            return fb
        else:
            return None

    def set_user_preference(self, user_addr, feedback_data):
        user_id = get_user_id_by_email(user_addr)
        feedback_content = 'Your feedback:\n'
        affected_row = 0
        for i, fb in enumerate(feedback_data):
            arxiv = fb[0]
            islike = fb[1].strip()
            if islike:
                islike = 1 # if islike[0] != '0' else 0
            else:
                islike = 0
            affected_row += update_user_preference(user_id, arxiv, islike)
            feedback_content += str(i + 1) + '.  ' + arxiv + ' -> '
            feedback_content += 'like' if islike == 1 else 'dislike'
            feedback_content += '\n'
        self._send_email(user_addr, 'Thank you! Your feedback has been received.\n\n\n' + feedback_content)

    def recommendTo(self, to, model_path, topK):
        user_id = get_user_id_by_email(to)
        keywords_data = get_data('rec_user_keywords', 'keywords', user_id, 'user_id = %s')
        if not keywords_data:
            return

        sc = SimilarityCalculator(model_path)
        
        index, num = get_index_and_num(user_id)
        data = get_data('rec_arxiv_paper', ['id', 'arxiv', 'title', 'abstract'],
            [index, user_id],
            "rec_arxiv_paper.id >= %s AND \
                (SELECT COUNT(1) FROM rec_user_arxiv_preference WHERE \
                user_id = %s AND \
                rec_arxiv_paper.id = rec_user_arxiv_preference.paper_id) = 0", 
            limit=num + 100)
   
        paper_data = pd.DataFrame(data, columns=['id', 'arxiv', 'title', 'abstract'])
        # paper_data['contain_keywords'] = ''
        
        
        # idx_contain_kw = set()
        
        
        keywords = [' ' + kw[0] for kw in keywords_data]
        # for kw in keywords:
        #     title_cont = paper_data['title'].str.lower().str.contains(kw)
        #     abstract_cont = paper_data['abstract'].str.lower().str.contains(kw)
        #     cont = title_cont | abstract_cont
        #     paper_data.loc[cont, 'contain_keywords'] = paper_data.loc[cont, 'contain_keywords'] + kw + ';'
        #     idx_contain_kw = idx_contain_kw | set(title_cont[title_cont == True].index.tolist())
        #     idx_contain_kw = idx_contain_kw | set(abstract_cont[abstract_cont == True].index.tolist())
        # idx_not_contain_kw = set(paper_data.index.tolist()) - idx_contain_kw
        
        # paper_data_kw = paper_data.loc[list(idx_contain_kw)].reset_index(drop=True) # Don't insert index column to the df.
        # paper_data_no_kw = paper_data.loc[list(idx_not_contain_kw)].reset_index(drop=True)

        try:
            template = EmailTemplate()
            data = get_data(['rec_user_field_paper', 'rec_field_paper'], 
                ['title', 'abstract'],
                user_id, 
                'rec_user_field_paper.user_id = %s AND \
                    rec_user_field_paper.field_paper_id = rec_field_paper.id',
                option='all')
            if data:
                field_data = pd.DataFrame(data, columns=['title', 'abstract'])
                # kw_result = sc.get_top_k(paper_data_kw, field_data, int(topK * 0.5), None)
                # no_kw_result = sc.get_top_k(paper_data_no_kw, field_data, int(topK * 0.5), None)
                no_kw_result = sc.get_top_k(paper_data, field_data, 20, None)
                # results = pd.concat([kw_result, no_kw_result], axis=0)
                results = no_kw_result
                template.fill_paper(user_id, results, keywords)
            else:
                return
        except ValueError as e:
            print(e)
            template = 'Unknown Message.'
        
        error_times = 0
        while error_times < 5:
            try:
                self._send_email(to, template)
                break
            except:
                error_times += 1
                time.sleep(10)

        results = results[['id']]
        results['user_id'] = user_id
        results['islike'] = -1
        store_data('rec_user_arxiv_preference', 
            ['paper_id', 'user_id', 'islike'], 
            results.values.tolist())
        

if __name__ == '__main__':
    root_path = os.path.dirname(__file__)
    emails = get_data('rec_user', 'email')
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(filename)s[line:%(lineno)d] - %(levelname)s - %(message)s')
    logging.info('-Begin-')
    for email in emails:
        pr = PaperRecommender()
        pr.recommendTo(email[0], 
            os.path.join(root_path, 'physics.joblib'),
            20)
        logging.info('The system has recommended to {} successfully.'.format(email[0]))
    logging.info('-End-')
    
