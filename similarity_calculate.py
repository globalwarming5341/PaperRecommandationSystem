# -*- coding: utf-8 -*-
'''
@Description: In User Settings Edit
@Author: your name
@Date: 2019-10-04 17:37:48
@LastEditTime: 2019-10-29 15:52:30
@LastEditors: Zhuang
'''
#from sklearn.externals import joblib
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from utils import preprocess_data
from operator import itemgetter
import pandas as pd
import os
import numpy as np

class SimilarityCalculator(object):
    
    def __init__(self, tfidf_model_path):
        self._model = joblib.load(tfidf_model_path)

    @property
    def model(self):
        return self._model
    
    @model.setter
    def model(self, model):
        assert isinstance(model, TfidfVectorizer), 'The parameter \'model\' must be a TfidfVectorizer object.'
        self._model = model

    def setup_model(self, tfidf_model_path):
        self._model = joblib.load(tfidf_model_path)

    def get_similarity(self, paper_matrix, field_matrix, addition_matrix=None):
        scores = np.mean(np.power(np.matmul(paper_matrix, field_matrix.T), 0.8), axis=1)
        if not addition_matrix is None:
            addition = np.mean(np.power(np.matmul(paper_matrix, addition_matrix.T), 0.8), axis=1)
            return scores * 0.8 + addition * 0.2
        return scores
    
    def get_top_k(self, arXiv_df, field_df, k, addition_df=None):
        field_matrix = self._model.transform(preprocess_data(field_df)).toarray()
        paper_matrix = self._model.transform(preprocess_data(arXiv_df[['title', 'abstract']])).toarray()
        if not addition_df is None:
            addition_matrix = self._model.transform(preprocess_data(addition_df)).toarray()

            result = np.argsort(self.get_similarity(paper_matrix, field_matrix, addition_matrix))[::-1]
        else:
            result = np.argsort(self.get_similarity(paper_matrix, field_matrix))[::-1]
        # print(result)
        return arXiv_df.loc[result[:k]]

    def get_rank(self, arXiv_df, field_df):
        field_matrix = self._model.transform(preprocess_data(field_df)).toarray()
        paper_matrix = self._model.transform(preprocess_data(arXiv_df[['title', 'abstract']])).toarray()
        score = self.get_similarity(paper_matrix, field_matrix)
        result_df = arXiv_df.copy()
        result_df['score'] = score
        result_df.sort_values(by='score', inplace=True, ascending=False)
        return result_df

    def get_top_k_with_kw(self, arXiv_df, field_df, k, addition_df=None):
        field_matrix = self._model.transform(preprocess_data(field_df)).toarray()
        paper_matrix = self._model.transform(preprocess_data(arXiv_df[['title', 'abstract']])).toarray()
        if not addition_df is None:
            addition_matrix = self._model.transform(preprocess_data(addition_df)).toarray()
            result = np.argsort(self.get_similarity(paper_matrix, field_matrix, addition_matrix))[::-1]
        else:
            score = self.get_similarity(paper_matrix, field_matrix)
            addition_score = arXiv_df['contain_keywords'].str.strip().str.split(';').apply(lambda item: 0.01 * 2 ** len(item[:-1])).values
            score += addition_score
            result = np.argsort(score)[::-1]
        return arXiv_df.loc[result[:k]]

    