'''
This code will be responsible for fetching all relevant
data for a given film from IMDb, boxofficemojo, etc.
and dumping it all into our own database.

I think eventually will want to get all available film
data, but for now just a handful relevant fields.
'''

import pandas as pd

import imdb
import tmdbsimple as tmdb

from bom import bom

__author__ = "Karlen Shahinyan"
__license__ = "GPL"
__version__ = "0.0.1"
__status__ = "Dev"

INFLATION_DATA = "bom/bom_tprice_inflation.dat"

def get_inflation():
    inf_df = pd.read_csv(INFLATION_DATA,delim_whitespace=True,\
                        names=['year','infl'])
    inf_df = inf_df.set_index('year')


class DBInfoFetcher(object):
    '''
    Class to interact with IMDb and TMDB databases.

    (might structure operations in series to delay time
    between queries and reduce timeout chance.)
    '''

    def __init__(self):
        self.ia = imdb.IMDb()

    def _get_IMDb_Movie_Info(self,imdb_obj):

        try:
            self.ia.update(imdb_obj, info=['main'])
        #might want to catch timeouts here
        except imdb.IMDbError as e:
            print(e)

    def get_IMDb_Person_Info(self,imdb_obj):

        try:
            self.ia.update(imdb_obj, info=['biography','filmography'])
        #might want to catch timeouts here
        except imdb.IMDbError as e:
            print(e)


    def get_IMDb_info(self,key,pom='m'):

        if pom == 'p':
            try:
                search = self.ia.search_person(key)
                self.get_IMDb_Person_Info(search[0])
            except imdb.IMDbError as e:
                print(e)

        elif pom == 'm':
            title,year = key
            try:
                search = self.ia.search_movie(title)
            except imdb.IMDbError as e:
                print(e)

            if search[0]['year'] == year and search[0]['kind'] == 'movie':
                iobj = search[0]
                self._get_IMDb_Movie_Info(iobj)
            else:
                for i in range(1,len(search),1):
                    try:
                        yr = search[i]['year']
                        kind = search[i]['kind']
                    except:
                        continue

                    if yr == year and kind == 'movie':
                        iobj = search[i]
                    else:
                        continue
                try:
                    self._get_IMDb_Movie_Info(iobj)
                except:
                    print('No match for: {}'.format(title))
                    return None

        return iobj


    def get_TMDB_Info(self,tid):

        movie = tmdb.Movies(tid)
        res = movie.info()

    def search_TMDB(self, key):
        search = tmdb.Search(query=key)
        res = search.info()

        return search.results

class BOMInfoFetcher(object):

    def __init__(self):
        self.bom_filename = 'bom/bom_all_time_chart.csv'
        self.bom_infl_filename = 'bom/bom_tprice_inflation.dat'

    def _adj_gross(self,df):
        '''
        Adjusting gross earnings to 2019
        '''

        inf_df = inf_df = pd.read_csv(self.bom_infl_filename,\
                                      delim_whitespace=True,names=['year','infl'])
        df = df.merge(inf_df,on='year')

        df['adj_gross'] = df['gross']/df['infl']

        return df

    def _filter_BOM_chart(self,df,grosslower=0,yearlower=0):

        df = self._adj_gross(df)

        return df[(df.year >= yearlower) & (df.adj_gross >= grosslower)]

    def get_BOM_all_time_dom_chart(self,grosslower=0,yearlower=0):

        try:
            atd_chart_df = pd.read_csv(self.bom_filename)

        except FileNotFoundError:
            print('{} not found. Rebuilding it - will take some minutes.'.format(filename))

            bomi = bom.BOM()
            atd_chart_df = bomi.build_alltime_dom_chart()
            atd_chart_df.to_csv('bom/bom_all_time_chart.csv')

        atd_chart_df = self._filter_BOM_chart(atd_chart_df,\
                                              grosslower=grosslower,\
                                              yearlower=yearlower)

        atd_chart_df = atd_chart_df.set_index('rank')

        return atd_chart_df.sort_index()
