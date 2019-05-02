'''
This is where all of the data collection
will be coordinated.
'''
import numpy as np
import pandas as pd
import json
import argparse

from time import sleep

import pymysql
from tqdm import tqdm

import InfoFetcher
import genderify

__author__ = "Karlen Shahinyan"
__license__ = "GPL"
__version__ = "0.0.1"
__status__ = "Dev"


def get_BOM_data(glow,ylow):

    bom = InfoFetcher.BOMInfoFetcher()

    return bom.get_BOM_all_time_dom_chart(grosslower=glow,\
                                          yearlower=ylow)

def get_gender(name,bio,filmog):
    '''
    Logic is a little complicated here, but to summarize,
    using 2 methods to figure out gender:

    - if bio info is good use it
    - otherwise, try looking it up
    - One of the methods is uninformative while the
    other gives an answer:
        M or F
    - Methods conflict:
        U#, where # is gender_score
    - Both are uninformative:
        X
    '''

    gender_score = genderify.get_gender_score(bio)

    if gender_score > 0:
        return 'F'
    elif gender_score < 0:
        return 'M'
    else:
        gender_lookup = genderify.lookup_name_gender(name)

        if gender_lookup == -1:
            return 'M'
        elif gender_lookup == 1:
            return 'F'
        else:
            #can try checking actor/actress
            a = genderify.check_filmography(filmog)
            if a == 'M' or a == 'F':
                return a
            else:
                print('failed filmography check')
                return 'X'
    #else:
    #    return 'U{}'.format(gender_score)

def prep_ids(peeps):
    ids = pd.unique([p.getID() for p in peeps if p.getID() != None])
    return {"ids" : ids.tolist()}

def get_IMDb_data(rank,title,year,dbif,client):

    movie = dbif.get_IMDb_info([title,year],pom='m')
    if movie == None:
        failf = open('faillist.txt','a+')
        failf.write('{r} | {t} | {y}'.format(r=rank,t=title,y=year))
        failf.close()
        print('skipping {}'.format(title))
        return []

    print(rank, movie)
    mid = movie.getID()

    try:
        genres = movie['genres']
        cast = movie['cast']
        directors = movie['directors']
        writers = movie['writers']
    except KeyError:
        failf = open('faillist.txt','a+')
        failf.write('{r} | {t} | {y}'.format(r=rank,t=title,y=year))
        failf.close()
        return []

    cids = prep_ids(cast)
    dids = prep_ids(directors)
    wids = prep_ids(writers)

    try:
        producers = movie['producers']
        prids = prep_ids(producers)
    except KeyError:
        producers = []
        pids = {"ids:": []}

    try:
        cgs = movie['cinematographers']
        cgids = prep_ids(cgs)
    except KeyError:
        cgs = []
        cgids = {"ids:": []}

    try:
        composers = movie['composers']
        coids = prep_ids(composers)
    except KeyError:
        composers = []
        coids = {"ids:": []}


    sql = "update `movies` set `id`='{mid}',genres='{gens}',`cast`='{cids}',"\
            "`directors`='{dids}',`producers`='{prids}',"\
            "`writers`='{wids}',`cgs`='{cgids}',`composers`='{coids}'"\
            "where `mrank`='{mrank}'".format(dids=json.dumps(dids),
                                             cids=json.dumps(cids),
                                             wids=json.dumps(wids),
                                             prids=json.dumps(prids),
                                             coids=json.dumps(coids),
                                             cgids=json.dumps(cgids),
                                             gens=json.dumps(genres),
                                             mid=mid,
                                             mrank=rank)

    with client.cursor() as cursor:
        cursor.execute(sql)
    client.commit()

    #something like this for getting uniques
    #peeps = [p for p in x if p.getID() != None]
    #pd.unique(peeps)


    people = np.concatenate([cast,directors,producers,writers,cgs,composers])
    return pd.unique([p for p in people if p.getID() != None])

def get_people_data(df,client):
    '''
    Make a pass and collect gender info for everyone involved
    in each movie... either keep a separate DF/DB or add people info
    to movie DF.

    Eventually want male/female counts per movie for each category
    (director,producer,writer,cast members) which will then get binned
    by year. Can also explore by gross cutoff...

        -ooo can setup an interactive slider situation to see what happens
        as you shift the gross cutoff
    '''

    dbif = InfoFetcher.DBInfoFetcher()

    peeps = []
    for rank,m in df.iterrows():
        title = '{title}'.format(title=m['title'])
        peeps = pd.unique(
            np.concatenate([peeps,get_IMDb_data(rank,title,m['year'],dbif,client)]))

    return peeps

def add_to_people_db(people,client):

    dbif = InfoFetcher.DBInfoFetcher()

    print('Number of peeps: {}'.format(np.size(people)))
    for person in tqdm(people):

        dbif.get_IMDb_Person_Info(person)
        name = person['name']


        firstname = name.split(' ')[0]
        pid = person.getID()

        try:
            bio = person['biography']
        except:
            print('likely connection issue, sleeping a sec')
            sleep(1)
            dbif.get_IMDb_Person_Info(person)
            try:
                bio = person['biography']
            except:
                print('waiting didnt help.')
                bio = ['']

        try:
            filmog = person['filmography']
        except KeyError:
            print('setting filmog to None for {}'.format(name))
            filmog = None

        gender = get_gender(firstname,bio,filmog)

        sql = 'INSERT INTO `people` (id,name,gender)'\
                ' VALUES ("{pid}","{name}","{gender}")'.format(pid=pid,
                                                        name=name,gender=gender)

        with client.cursor() as cursor:
            cursor.execute(sql)
        client.commit()


def main():

    parser = argparse.ArgumentParser('This is a tool for gathering \
                                     BOM and IMDb data.')
    parser.add_argument('-ylow',default=1980,help='Earliest year.')
    parser.add_argument('-glow',default=1000000,help='Lowest gross earning.')
    args = parser.parse_args()

    bom_df = get_BOM_data(args.glow,args.ylow)

    client = pymysql.connect(host='localhost',
                             user='root',
                             password='temppass',
                             db='imdb_add',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)


    people = get_people_data(bom_df[200:1000],client)

    ##might wanna update for checking for fails (defined as couldn't connect)



    add_to_people_db(people,client)
    client.close()


if __name__ == '__main__':
    main()
