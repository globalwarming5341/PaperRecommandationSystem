'''
@Description: 
@Author: Zhuang
@Date: 2019-11-13 15:12:10
@LastEditors: Zhuang
@LastEditTime: 2019-12-13 22:54:12
'''
from database import MongoDB
import pandas as pd
from collections import Counter
import re
import jieba
if __name__ == '__main__':

    data = pd.read_excel('bz3.xls', encoding='utf-8')[['病证', '临床表现']]


    data['病证'] = data['病证'].str.strip().str.replace(r'^.*，', '')
    # data['临床表现'] = data['临床表现'].str.replace(r'等.*?(?:\s|$)|[，。,.、；;]', ' ')
    # data['临床表现'] = data['临床表现'].str.replace(r'或|常伴|伴有?|发生|[轻甚]则|甚至', '')
    # data['临床表现'] = data['临床表现'].str.replace(r'[^\s]{9,}', ' ')
    # data['临床表现'] = data['临床表现'].str.replace(r'\s+', ' ')
    data['临床表现'] = data['临床表现'].str.strip()


    data.drop_duplicates('病证', 'last', inplace=True)
    # data = data['临床表现'].str.split().tolist()
    # data = [j for i in data for j in i]
    # counter = Counter(data)
    
    # print(data['临床表现'])
    # data.to_excel('bz2.xls', index=False)
    # bz = pd.read_excel('bz.xls')[['病症', '临床表现']]
    mongo = MongoDB()
    food_info = mongo.find_all('diet_merge', projection={'name': 1, 'ingredients': 1, 'syndrome': 1})

    food_info_df = pd.DataFrame(data=[[f['name'], f['ingredients'], f['syndrome']] for f in food_info], columns=['食疗方', '食材', '主治'])
    
    food_info_df['存在关联'] = 0
    food_info_df['主治'] = food_info_df['主治'].str.replace('证', '').str.replace('型', '')
    food_info_df.loc[food_info_df['主治'] != '', '主治'] = food_info_df['主治'] + '证'
    food_bz = [item['syndrome'] for item in food_info]
    food_bz = list(filter(None, food_bz))
    print('Food(Total): {}'.format(len(food_bz)))
    food_bz = set([item.replace('证', '').replace('型', '') for item in food_bz])
    results = []
    n_valid_bz = 0
    valid_bz_set = set()
    for item in food_bz:
        item += '证'
        res = data[data['病证'].str.contains(item)]
        if len(res):
            n_valid_bz += 1
            valid_bz_set.add(item)
            # results += res['临床表现'].str.split().values.tolist()[0]
    food_info_df.loc[food_info_df['主治'].isin(valid_bz_set), '存在关联'] = 1




    food_info_df.to_excel('diet_merge.xls', index=False)

    # counter = Counter(results)
    # print('Food(Valid): {}'.format(food_info_df['存在关联'].sum()))
    # print('病证(Total) num: {}'.format(len(food_bz)))
    # print('病证(Valid) num: {}'.format(len(valid_bz_set)))
    # print('Symtom num: {}'.format(len(counter)))

    # 
    # pd.DataFrame(data=[[k, y] for k, y in counter.most_common()], columns=['症状', '频数']).to_excel('freq.xls', index=False)
    # data = data[data['病证'].isin(valid_bz_set)]
    # a = data[data['临床表现'].str.contains('舌红 ')]['临床表现']

    # a1 = a[312].split()
    # a2 = a[373].split()
    # a3 = a[408].split()
    # print(set(a1) & set(a3))



    # print(counter.most_common())
        

