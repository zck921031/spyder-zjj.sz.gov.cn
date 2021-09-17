#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 12 19:07:39 2021

@author: zck921031
"""

import argparse
import urllib3
import logging
import os
from bs4 import BeautifulSoup
from urllib.parse import unquote
from tqdm import tqdm
from collections import defaultdict
import pandas as pd
import pickle
from urllib.parse import urlparse, parse_qs
from multiprocessing import Pool


if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    parser = argparse.ArgumentParser()
    parser.add_argument('--url',
                        '-i',
                        default='http://zjj.sz.gov.cn/ris/bol/szfdc/projectdetail.aspx?id=57458')
    parser.add_argument('--output',
                        '-o',
                        default='output')
    args = parser.parse_args()
    url = args.url
    output = args.output
    project_id = parse_qs(urlparse(url).query)["id"][0]
    
    # set static vars
    building_http_prefix = 'http://zjj.sz.gov.cn/ris/bol/szfdc/'
    housedetail_http_prefix = 'http://zjj.sz.gov.cn/ris/bol/szfdc/'
    
    # fetch part buildings url
    req = urllib3.PoolManager()
    res = req.request('GET', url)
    soup = BeautifulSoup(res.data, 'html.parser')
    contents = soup.find_all('a', href=True)
    part_buildings = set()
    for link in contents:
        link = link['href']
        if link.startswith('building.aspx'):
            link = os.path.join(building_http_prefix, link)
            logging.info('find part building: %s' % unquote(link))
            part_buildings.add(link)
            
    # fetch full buildings url
    full_buildings = set()
    for url in part_buildings:
        req = urllib3.PoolManager()
        res = req.request('GET', url)
        soup = BeautifulSoup(res.data, 'html.parser')
        contents = soup.find_all('a', href=True)
        for link in contents:
            link = link['href']
            if link.startswith('building.aspx'):
                link = os.path.join(building_http_prefix, link)
                logging.info(u'find full building: %s' % unquote(link))
                full_buildings.add(link)
                
    # fetch all rooms url
    rooms = set()
    for url in full_buildings:
        req = urllib3.PoolManager()
        res = req.request('GET', url)
        soup = BeautifulSoup(res.data, 'html.parser')
        contents = soup.find_all('a', href=True)
        for link in contents:
            link = link['href']
            if link.startswith('housedetail.aspx'):
                link = os.path.join(housedetail_http_prefix, link)
                logging.debug(u'find room: %s' % unquote(link))
                rooms.add(link)
                
    # fetch all rooms information
    data = []
    for url in tqdm(rooms):
        res = req.request('GET', url)
        soup = BeautifulSoup(res.data, 'html.parser')
        data.append(soup)
    # data = []
    # def f(url):
    #     req = urllib3.PoolManager()
    #     res = req.request('GET', url)
    #     soup = BeautifulSoup(res.data, 'html.parser')
    #     return soup
    # with Pool(4) as p:
    #     for soup in tqdm(p.imap(f, rooms)):
    #         data.append(soup)
    
    # generate yi-fang-yi-jia
    tables = defaultdict(lambda: [])
    for soup in data:
        item = {}
        tds = soup.find_all("td", text="")
        for i in range(0, len(tds), 2):
            key = tds[i].text.strip()
            value = tds[i+1].text.strip()
            if key not in item:
                item[key] = value
        private_key = item[u'项目楼栋情况'] + item[u'座号']
        tables[private_key].append(item)
    project = ""
    for kword in zip(*list(tables.keys())):
        if len(set(kword))>1:
            break
        else:
            project += kword[0]
    os.makedirs(output, exist_ok=True)
    os.makedirs(os.path.join(output, project), exist_ok=True)
    for private_key, table in tables.items():
        logging.info(private_key)
        try:
            table = sorted(table, key=lambda x: int(x['房号']), reverse=True)
        except:
            table = sorted(table, key=lambda x: x['房号'], reverse=True)
        df = pd.DataFrame(data=table)
        df.to_excel(os.path.join(output, project, '%s.xls' % private_key))
    pickle.dump(dict(tables), open(os.path.join(output, '%s.pkl'%project_id), 'wb'))
        
    
