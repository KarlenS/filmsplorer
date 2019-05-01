'''
This is where all of the data collection
will be coordinated.
'''
import numpy as np
import pandas as pd
import argparse

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

def get_gender(name,bio):
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
            return 'X'
    #else:
    #    return 'U{}'.format(gender_score)

def get_IMDb_data(title,year,dbif):

    movie = dbif.get_IMDb_info([title,year],pom='m')
    mid = movie.getID()
    genres = movie['genres']

    cast = movie['cast']
    directors = movie['directors']
    writers = movie['writers']
    producers = movie['producers']
    try:
        cgs = movie['cinematographers']
    except KeyError:
        cgs = []


    #something like this for getting uniques
    #peeps = [p for p in x if p.getID() != None]
    #pd.unique(peeps)

    try:
        composers = movie['composers']
    except KeyError:
        composers = []

    people = np.concatenate([cast,directors,producers,writers,cgs,composers])
    return pd.unique([p for p in people if p.getID() != None])

def get_people_data(df):
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
    for rank,m in tqdm(df.iterrows()):
        title = '{title}'.format(title=m['title'])
        peeps = pd.unique(
            np.concatenate([peeps,get_IMDb_data(title,m['year'],dbif)]))

    return peeps

def add_to_people_df(people):

    dbif = InfoFetcher.DBInfoFetcher()

    for person in people:

        dbif.get_IMDb_Person_Info(person)
        name = person['name']
        firstname = name.split(' ')[0]
        pid = person.getID()
        gender = get_gender(firstname,person['biography'])
        print('{name} | {pid} | {gender}'.format(name=name,
                                                 pid=pid,
                                                 gender=gender))


def main():

    parser = argparse.ArgumentParser('This is a tool for gathering \
                                     BOM and IMDb data.')
    parser.add_argument('-ylow',default=1980,help='Earliest year.')
    parser.add_argument('-glow',default=1000000,help='Lowest gross earning.')
    args = parser.parse_args()

    bom_df = get_BOM_data(args.glow,args.ylow)
    people = get_people_data(bom_df[0:2])

    #client = pymysql.connect(host='localhost',
    #                         user='root',
    #                         password='temppass',
    #                         db='imdb_add',
    #                         charset='utf8mb4',
    #                         cursorclass=pymysql.cursors.DictCursor)


    #get_data(ia,client)
    #client.close()

    #sql = 'INSERT INTO gender (id,primaryName,gender_score) VALUES (%07i,"%s",%i)' %(c,name,gs)
    ##might wanna update for checking for fails (defined as couldn't connect)

    #with client.cursor() as cursor:
    #    cursor.execute(sql)

    #client.commit()

    make_people_df(people)


if __name__ == '__main__':
    main()
