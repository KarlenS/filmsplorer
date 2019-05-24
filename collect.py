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
from _dbclient import CLIENT

__author__ = "Karlen Shahinyan"
__license__ = "GPL"
__version__ = "0.1.1"
__status__ = "Dev"


def get_BOM_data(glow,ylow):

    bom = InfoFetcher.BOMInfoFetcher()

    return bom.get_BOM_all_time_dom_chart(grosslower=glow,\
                                          yearlower=ylow)

def get_gender(name,bio,filmog):
    '''
    Given a first name, bio and filmography info from IMDb
    returns best guess at a person's gender as either M or F
    or X if none of the methods can be applied successfully.

    Logic is a little complicated here, but to summarize,
    using 2 methods to figure out gender:

    - if bio info is good use it (seems to be most accurate)
    - then, try looking it up by first name (ton of overlap in M/F names)
    - if that doesn't work either, use filmography actor/actress key
    - No method succeeds: return X


    Args:
        name (str): First name of person
        bio (str): Biography text from IMDb
        filmog (dict): person's filmography from IMDb

    Returns:
        str: A character (F,M,X) to indicate gender determination
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
            a = genderify.check_filmography(filmog)
            if a == 'M' or a == 'F':
                return a
            else:
                print('failed filmography check')
                return 'X'

def prep_ids(peeps):
    '''
    Helper method to return a unique list of IMDb IDs
    given a list of IMDb objects.

    Args:
        peeps (array_like): array/list of IMDb objects

    Returns:
        dict: dict with a list of ids set to a keyword "ids"
    '''
    ids = pd.unique([p.getID() for p in peeps if p.getID() != None])
    return {"ids" : ids.tolist()}

def count_genders(ids,client,dbif):
    '''
    For a given movie (but really a list of IMDb ids),
    uses the gender flags to total the number of people per gender

    Args:
        ids (array_like): list of IMDb person IDs
        client (pymysql.connections.Connection): pymysql client object
        dbif (InfoFetcher.DBInfoFetcher): object for interacting with

    Returns:
        int,int,int: The number of male, female, undetermined people.
    '''

    M = 0
    F = 0
    X = 0
    for pid in ids:

        sql ='SELECT `gender` FROM `people` WHERE `id`={pid}'.format(pid=pid)

        with client.cursor() as cursor:
            cursor.execute(sql)
        client.commit()

        qres = cursor.fetchall()

        if len(qres) == 0:
            gender = get_single_gender(pid,dbif,client)
        else:
            gender = qres[0]['gender']


        if gender == 'M':
            M += 1
        elif gender == 'F':
            F+=1
        elif gender == 'X':
            X+=1
        else:
            print('what is gender even...')

    return M,F,X

def get_movie_gender_counts(rank,client):

    '''
    Given the movie rank in bom chart, returns number of people
    for each category (cast,writers,etc) broken down by gender.

    Args:
        rank (int): BoxOfficeMojo (BOM) all-time domestic chart rank of movie
        client (pymysql.connections.Connection): pymysql client object

    Returns:
        dict: dictionary with different roles (cast,writers,etc.) as keys and a list with number of people per gender as values.
    '''

    dbif = InfoFetcher.DBInfoFetcher()

    fields = ['cast','directors','producers',\
             'writers','composers','cgs']


    counts = {}
    sql ='SELECT * FROM `movies` WHERE `mrank`={rank}'.format(rank=rank)

    with client.cursor() as cursor:
        cursor.execute(sql)
    client.commit()

    qres = cursor.fetchall()

    for field in fields:

        try:
            ids = json.loads(qres[0][field])['ids']
        except:
            try:
                ids = json.loads(qres[0][field])['ids']
            except:
                return counts


        if len(ids)>0:
            ids = [int(i) for i in ids]
            M,F,X = count_genders(ids,client,dbif)
        else:
            M = 0
            F = 0

        counts[field] = [M,F,X]

    return counts

def get_IMDb_data(rank,title,year,dbif,client):

    '''
    Uses the IMDb API to fetch pre-specified data fields
    for a given movie. IMDb IDs of Cast/writers/etc. separated by role
    are stored for each movie in a local database.

    Args:
        rank (int): BoxOfficeMojo all-time domestic chart rank
        title (str): movie title
        year (int): Year of the movie in XXXX format
        dbif (InfoFetcher.DBInfoFetcher): object for interacting with
        IMDb database and BoxOfficeMojo chart info
        client (pymysql.connections.Connection): pymysql client object

    Returns:
        list: a combined unique list of IMDb IDs of people involved in a movie
    '''

    ##this is patchwork - should really handle this in InfoFetcher
    try:
        movie = dbif.get_IMDb_info([title,year],pom='m')
    except:
        movie = None

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
        prids = {"ids": []}

    try:
        cgs = movie['cinematographers']
        cgids = prep_ids(cgs)
    except KeyError:
        cgs = []
        cgids = {"ids": []}

    try:
        composers = movie['composers']
        coids = prep_ids(composers)
    except KeyError:
        composers = []
        coids = {"ids": []}


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

    people = np.concatenate([cast,directors,producers,writers,cgs,composers])
    return pd.unique([p for p in people if p.getID() != None])


def get_people_data(df,client):
    '''
    Make a pass and collect gender info for everyone involved
    in each movie adding gender info to a local database..

    Args:
        df (pd.DataFrame): contains a movie per row with info from BOM.
        client (pymysql.connections.Connection): pymysql client object

    Returns:
        list: a combined unique list of IMDb IDs of people involved in a movie
    '''

    dbif = InfoFetcher.DBInfoFetcher()

    peeps = []
    for rank,m in df.iterrows():
        title = '{title}'.format(title=m['title'])
        peeps = pd.unique(
            np.concatenate([peeps,get_IMDb_data(rank,title,m['year'],dbif,client)]))

    return peeps


def get_single_gender(pid,dbif,client):
    '''
    Uses person's IMDb ID to determine,
    record in a local database, and return gender.

    Args:
        pid (str): IMDb person ID
        dbif (InfoFetcher.DBInfoFetcher): object for interacting with
        IMDb database and BoxOfficeMojo chart info.
        client (pymysql.connections.Connection): pymysql client object
    '''

    person = dbif.ia.get_person(pid,info=['main','biography','filmography'])


    try:
        name = person['name']
    except:
        print('timing out, waiting couple secs')
        sleep(2)
        person = dbif.ia.get_person(pid,info=['main','biography','filmography'])
        try:
            name = person['name']
        except:
            return 'X'

    firstname = name.split(' ')[0]

    try:
        bio = person['biography'][0]
    except:
        try:
            bio = person['biography'][0]
        except:
            print('bio empty or something went wrong')
            bio = ''

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
        try:
            cursor.execute(sql)
        except:
            print('failed at executing: '.format(sql))

    try:
        client.commit()
    except:
        print('failed at committing to mysql')

    return gender


def add_to_people_db(people,client):
    '''
    Given a list of IMDb person objects, populates DB with
    desired information (for now: ID, Name, Gender).

    args:
        people (array_like): list of IMDb person objects
        client (pymysql.connections.Connection): pymysql client object
    '''

    dbif = InfoFetcher.DBInfoFetcher()

    print('Number of peeps: {}'.format(np.size(people)))
    for person in tqdm(people):

        dbif.get_IMDb_Person_Info(person)
        name = person['name']


        firstname = name.split(' ')[0]
        pid = person.getID()

        try:
            bio = person['biography'][0]
        except:
            print('likely connection issue, sleeping a sec')
            sleep(1)
            dbif.get_IMDb_Person_Info(person)
            try:
                bio = person['biography'][0]
            except:
                print('waiting didnt help.')
                bio = ''

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

    parser = argparse.ArgumentParser('This is a tool for gathering' \
                                     'BOM and IMDb data.')
    parser.add_argument('-ylow',default=1980,help='Earliest year.')
    parser.add_argument('-glow',default=1000000,help='Lowest gross earning.')
    parser.add_argument('--get_people_info',action='store_true',\
                        help='When true will populate'\
                        'database tables with people info.')
    args = parser.parse_args()

    bom_df = get_BOM_data(args.glow,args.ylow)


    if args.get_people_info:
        people = get_people_data(bom_df[4000:5000],CLIENT)

    #patching the gender data...
    for rank,m in tqdm(bom_df[4000:5000].iterrows()):
        print('---- working on movie: {}'.format(m['title']))
        count = get_movie_gender_counts(rank,CLIENT)
        sql = "update `movies` set `counts`='{c}' where"\
            "`mrank`={r}".format(c=json.dumps(count),r=rank)

        with CLIENT.cursor() as cursor:
            cursor.execute(sql)
        CLIENT.commit()


    CLIENT.close()


if __name__ == '__main__':
    main()
