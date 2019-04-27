'''
Initial play with guessing male/female for
person objects on IMDb based on bio.
'''

import argparse
#from joblib import Parallel, delayed

import pymysql.cursors

from tqdm import tqdm

import nltk
from nltk.corpus import stopwords

import imdb

__author__ = "Karlen Shahinyan"
__license__ = "GPL"
__status__ = "Dev"

def get_gender_score(bio,sr):

    clean_ts = []
    for w in bio[0].split():
        if w.lower() in sr:
            continue
        elif w[-1] == ',':
            clean_ts.append(w[:-1])
        else:
            clean_ts.append(w.lower())

    freq = nltk.FreqDist(clean_ts)

    return freq['he']+freq['his']-freq['she']-freq['her']


def get_data(ia,client):

    gws = ['he','his','she','her']

    sr = stopwords.words('english')
    for gw in gws:
        if gw in sr:
            sr.remove(gw)

    for c in tqdm(range(10001,100000,1)):
        p = ia.get_person('%07i' %c, info=['main','biography'])
        #p = ia.get_person('%07i' %c, info=['awards', 'biography','filmography',
        #                                   'genres links','keywords links',
        #                                   'main','official sites',
        #                                   'other works','publicity'])

        try:
            name = p['name']
        except:
            continue

        try:
            bio = p['biography']
            gs = get_gender_score(bio,sr)
        except KeyError:
            bio = None
            gs = 0

        sql = 'INSERT INTO gender (id,primaryName,gender_score) VALUES (%07i,"%s",%i)' %(c,name,gs)
        #might wanna update for checking for fails (defined as couldn't connect)

        with client.cursor() as cursor:
            cursor.execute(sql)

        client.commit()

def main():

    parser = argparse.ArgumentParser('This is an exploratory tool for looking \
                                     through IMDb data.')
    parser.add_argument('-d',default=None,help='Director name.')
    args = parser.parse_args()

    ia = imdb.IMDb()

    client = pymysql.connect(host='localhost',
                             user='root',
                             password='leanna88',
                             db='imdb_add',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

    get_data(ia,client)
    client.close()



if __name__ == '__main__':
    main()
