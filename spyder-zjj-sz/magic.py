# -*- coding: utf-8 -*-
"""
Created on Tue Jul 13 00:05:51 2021

@author: zck
"""

import argparse
import logging
import pickle
import os
import re
import pandas as pd
from collections import defaultdict
from urllib.parse import urlparse, parse_qs


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
    tables = pickle.load(open(os.path.join(output, '%s.pkl'%project_id), 'rb'))
    
    project = ""
    for kword in zip(*list(tables.keys())):
        if len(set(kword))>1:
            break
        else:
            project += kword[0]
    # format
    writer = pd.ExcelWriter(os.path.join(output, '%s.xls' % project))
    for private_key, table in sorted(tables.items(), key=lambda x: x[0]):
        logging.info(private_key)
        matrix = defaultdict(lambda:{})
        table = sorted(table, key=lambda x: int(x['房号']))
        for item in table:
            room_number = item["房号"][-2:]
            matrix["%s-%s"%(room_number, u"房号")][item["楼层"]] = item["房号"]
            area = float(re.sub('[^\d.]', '', item["建筑面积"]))
            try:
                price = float(re.sub('[^\d.]', '', item["拟售价格"]))
            except:
                price = 0
            total_price = "%s 万元" % (area*price / 1e4)
            matrix["%s-%s"%(room_number, u"总价")][item["楼层"]] = total_price
            matrix["%s-%s"%(room_number, u"单价")][item["楼层"]] = item["拟售价格"]
            matrix["%s-%s"%(room_number, u"建筑面积")][item["楼层"]] = item["建筑面积"]
            matrix["%s-%s"%(room_number, u"户内面积")][item["楼层"]] = item["户内面积"]
            matrix["%s-%s"%(room_number, u"用途")][item["楼层"]] = item["用途"]
        df = pd.DataFrame(data=matrix)
        df.to_excel(excel_writer=writer, sheet_name=private_key[len(project):], index=False)
    writer.close()
