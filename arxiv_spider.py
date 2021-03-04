'''
@Description: 
@Author: Zhuang
@Date: 2019-10-14 12:32:21
@LastEditors: Zhuang
@LastEditTime: 2019-11-12 21:24:26
'''
import asyncio
import aiohttp
import aiofiles
import requests
import re
import pandas as pd
import time
from lxml import etree
from urllib.parse import urlsplit
from database import MySQL
class AsyncSpider(object):

    def __init__(self, urls, max_task=100):
        self._results = []
        self._urls = urls
        self._max_task = max_task
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
            'Sec-Fetch-Mode': 'no-cors',
            'Host': 'arxiv.org'
        }

    async def _get_body(self, task_id, url):
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=url, timeout=10, headers=self._headers) as response:
                        if response.status == 200:
                            content = await response.read()
                            return content
            except Exception:
                await asyncio.sleep(180)
    
    async def _parse_url(self, task_id, queue):
        while not queue.empty():
            url = queue.get_nowait()
            content = await self._get_body(task_id, url)
            # text = content.decode('utf-8')
            html = etree.HTML(content)
            title = html.xpath('//h1[@class="title mathjax"]/text()')[0].strip()
            authors = ','.join(html.xpath('//div[@class="authors"]/a/text()')).strip()
            abstract = html.xpath('//blockquote[@class="abstract mathjax"]/text()')[0].strip()
            subjects = html.xpath('string(//td[@class="tablecell subjects"])').strip()
            arxiv = url.split('/')[-1]
            self._results.append((arxiv, title, authors, abstract, subjects))
            print(arxiv)
            # filename = url.split('/')[-1]
            # async with aiofiles.open('arxiv/{}.html'.format(filename), 'w', encoding='utf-8') as f:
            #     await f.write(text)
            #     print(filename)
    
    def start_loop(self):
        queue = asyncio.Queue()
        for url in self._urls:
            queue.put_nowait(url)
        loop = asyncio.get_event_loop()
        tasks = [asyncio.ensure_future(self._parse_url(i, queue)) for i in range(self._max_task)]
        loop.run_until_complete(asyncio.wait(tasks))
        data = pd.DataFrame(self._results, columns=['arxiv', 'title', 'authors', 'abstract', 'subjects'])
        data.to_csv('data.csv', index=False)

class Spider(object):
    def __init__(self):
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
            'Sec-Fetch-Mode': 'no-cors',
            'Host': 'arxiv.org'
        }
        self._sess = requests.Session()
        self._sleep_time = 5
        self._mysql = MySQL()

    def _get_detail(self, url):
        while 1:
            try:
                content = self._sess.get(url, headers=self._headers).content
            except Exception as e:
                print(e)
                self._sess.close()
                self._sess = requests.Session()
                time.sleep(self._sleep_time)
                continue
            html = etree.HTML(content)
            title = html.xpath('//h1[@class="title mathjax"]/text()')[0].strip()
            #authors = ','.join(html.xpath('//div[@class="authors"]/a/text()')).strip()
            abstract = html.xpath('//blockquote[@class="abstract mathjax"]/text()')[0].strip()
            subjects = html.xpath('string(//td[@class="tablecell subjects"])').strip()
            arxiv = url.split('/')[-1]
            print(arxiv)
            return (arxiv, title, abstract, subjects)
    
    def crawl_arxiv_n(self, begin, stop):
        self._mysql.connect()
        # for month in ['07, 06, 05, 04, 03, 02, 01']:
        #     try:
        index_error_count = 0
        for i in range(begin, stop + 1):
            try:
                result = self._get_detail('https://arxiv.org/abs/1709.{:05d}'.format(i))
                index_error_count = 0
                self._mysql.execute('INSERT IGNORE INTO `rec_arxiv_paper` \
                    (`arxiv`, `title`, `abstract`, `subjects`) VALUES \
                    (%s, %s, %s, %s)', result)
                time.sleep(self._sleep_time // 5)
                if i % 150:
                    self._sess.close()
                    self._sess = requests.Session()
            except IndexError:
                index_error_count += 1
                if index_error_count > 5:
                    break
            # except IndexError:
            #     continue
        self._mysql.close()

if __name__ == '__main__':
    # spider = AsyncSpider(['https://arxiv.org/abs/1910.{:05d}'.format(i) for i in range(1, 5333)])
    # spider.start_loop()
    spider = Spider()
    spider.crawl_arxiv_n(1, 20000)


    

    
