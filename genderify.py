'''
Initial play with guessing male/female for
person objects on IMDb based on bio.
'''

import pymysql.cursors

import numpy as np
import pandas as pd
import nltk
from nltk.corpus import stopwords

from tqdm import tqdm
import imdb

from const import FURL,MURL

__author__ = "Karlen Shahinyan"
__license__ = "GPL"
__version__ = "0.0.1"
__status__ = "Dev"

FNAMES = np.array(pd.read_csv(FURL,comment='#',names=['name'],squeeze=True))
MNAMES = np.array(pd.read_csv(MURL,comment='#',names=['name'],squeeze=True))

def check_filmography(fg):

    if fg:
        for f in fg:
            if 'actor' in f.keys():
                return 'M'
            elif 'actress' in f.keys():
                return 'F'
            else:
                continue
        return 'X'
    else:
        return 'X'

def get_gender_score(bio):

    clean_ts = []
    for w in bio[0].split():
        if w.lower() in SW:
            continue
        elif w[-1] == ',':
            clean_ts.append(w[:-1])
        else:
            clean_ts.append(w.lower())

    freq = nltk.FreqDist(clean_ts)

    return freq['she']+freq['her']-freq['he']-freq['his']-freq['him']

def lookup_name_gender(name):
    '''
    Given a name, looks up the name in a collection of male and female
    names and returns a code:
        1 - female
       -1 - male
        0 - both (probably should check if there is any overlap)
      nan - if can't find name in either collection

    Using Copyright (C) 1991 Mark Kantrowitz (Additions by Bill Ross)
    corpus of male and female names.
    '''

    #this is dumb, improve and make sure we're doing this once per session

    if name in MNAMES:
        if name in FNAMES:
            return 0
        else:
            return -1
    elif name in FNAMES:
        return 1
    else:
        return float('NaN')
    '''
    if mnames.str.contains(name).any():

        if fnames.str.contains(name).any():
            return 0
        else:
            return -1
    elif fnames.str.contains(name).any():
        return 1
    else:
        return float('NaN')
    '''

def get_sw():

    gws = ['he','him','his','she','her']

    sw = stopwords.words('english')
    for gw in gws:
        if gw in sw:
            sw.remove(gw)

    return sw

SW = get_sw()

'''

    client = pymysql.connect(host='localhost',
                             user='root',
                             password='temppass',
                             db='imdb_add',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

    get_data(ia,client)
    client.close()

    sql = 'INSERT INTO gender (id,primaryName,gender_score) VALUES (%07i,"%s",%i)' %(c,name,gs)
    #might wanna update for checking for fails (defined as couldn't connect)

    with client.cursor() as cursor:
        cursor.execute(sql)

    client.commit()

'''
