'''
Guessing male/female for person objects on IMDb
based on bio, first name, and filmography (in that order).
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
__version__ = "0.1.1"
__status__ = "Dev"

FNAMES = np.array(pd.read_csv(FURL,comment='#',names=['name'],squeeze=True))
MNAMES = np.array(pd.read_csv(MURL,comment='#',names=['name'],squeeze=True))

def check_filmography(fg):
    '''
    Uses filmography as returned by the IMDb API to attempt gender
    determination based on 'actor'/'actress' distinction.

    Args:
        fg (dict): dictionary of filmography from IMDb

    Returns (str): character (F, M, or X) to indicate gender
    '''

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
    '''
    Uses a biography text to determine a gender score of the subject
    based on the counts of gendered pronouns:
    Female - more positive, Male - more negative

    Args:
        bio (str): biography text

    Returns:
        score (int): gender score based on gender pronoun counts
    '''

    clean_ts = []
    for w in bio.split():
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
    Given a first name, looks up the name in a collection
    of male and female names and returns a code:
    1 - female
    -1 - male
    0 - both (probably should check if there is any overlap)
    nan - if can't find name in either collection

    Using Copyright (C) 1991 Mark Kantrowitz (Additions by Bill Ross)
    corpus of male and female names.

    Args:
        name (str): first name to look up gender

    Returns:
        code (int): an integer code to indicate gender
    '''

    if name in MNAMES:
        if name in FNAMES:
            return 0
        else:
            return -1
    elif name in FNAMES:
        return 1
    else:
        return float('NaN')

def _get_sw():

    gws = ['he','him','his','she','her']

    sw = stopwords.words('english')
    for gw in gws:
        if gw in sw:
            sw.remove(gw)

    return sw

SW = _get_sw()
