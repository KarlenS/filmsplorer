'''
This code will be responsible for fetching all relevant
data for a given film from IMDb, boxofficemojo, etc.
and dumping it all into our own database.

I think eventually will want to get all available film
data, but for now just a handful relevant fields.
'''

import imdb
import tmdbsimple as tmdb

__author__ = "Karlen Shahinyan"
__license__ = "GPL"
__version__ = "0.0.1"
__status__ = "Dev"

class InfoFetcher(object):

    def __init__(self,ID):
        self.id = ID
        self.ia = imdb.IMDb()

    def getIMDBInfo(self,iid,pom='m'):

        if pom == 'p':
            p = self.ia.get_person('%07i' %iid, info=['awards', 'biography','filmography',
                                               'genres links','keywords links',
                                               'main','official sites',
                                               'other works','publicity'])
        elif pom == 'm':

            m = self.ia.get_movie('%07i' %iid, info=[])

    def searchIMDB(self,key,pom='m'):

        if pom == 'p':
            search = self.ia.search_person(key)
        elif pom == 'm':
            search = self.ia.search_movie(key)

        return search[0]


    def getTMDBInfo(self,tid):

        movie = tmdb.Movies(tid)
        res = movie.info()

    def searchTMDB(self, key):
        search = tmdb.Search(query=key)
        res = search.info()

        return search.results
