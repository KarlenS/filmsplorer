'''
Partial/very limited (for now) "API" for pulling data from BoxOfficeMojo.com

using this  deprecated API as a guide:
    https://github.com/earthican/BoxOfficeMojoAPI
'''

import re
from urllib import request

import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup

__author__ = "Karlen Shahinyan"
__license__ = "GPL"
__version__ = "0.1.1"
__status__ = "Dev"


def get_page_source(url):
    '''
    Returns the BSed page source for a given URL
    '''

    try:
        res = request.urlopen(url).read()
    except HTTPError:
        return None

    return BeautifulSoup(res,'html.parser')

class BOM(object):
    '''
    Class to parse BOM site and collect movie/earnings info
    '''
    BOM_MAIN_URL = "https://www.boxofficemojo.com"
    ALLTIME_DOM_EXT = "/alltime/domestic.htm"
    ALLTIME_DOM_PAGES = 170

    def __init__(self,ext=ALLTIME_DOM_EXT):
        self.url = BOM.BOM_MAIN_URL + ext

    def _get_alltime_chart_movies(self,url,chart_df):
        '''
        Goes through a single page of the alltime domestic
        earnings chart and adds each movie info to an input
        dataframe.
        '''

        src = get_page_source(url)

        try:
            ctable = src.findChildren('table')[5]
        except IndexError:
            return chart_df
        else:
            movies = ctable.findChildren('tr')[1:]

            for movie in movies:

                mattr = movie.findChildren('td')
                rank = int(mattr[0].string)
                title = mattr[1].string
                studio = mattr[2].string
                gross = mattr[3].string[1:]
                gross = float(re.sub(',', '', gross))
                year = mattr[4].string

                try:
                    year = int(re.sub('\^','',year))
                except ValueError:
                    print('year field for {t} was {y}. Skipping.'.format(t=title,y=year))
                    continue

                chart_df = chart_df.append({
                            'rank': rank,
                            'title': title,
                            'studio': studio,
                            'gross': gross,
                            'year': year
                            },ignore_index=True)

            return chart_df


    def build_alltime_dom_chart(self):

        chart_df = pd.DataFrame(columns=['rank','title','studio',\
                                         'gross','year'])

        for pnum in tqdm(range(1,BOM.ALLTIME_DOM_PAGES,1)):

            chart_page_url = '{main}?page={num}&p=.htm'.format(main=self.url,num = pnum)

            chart_df = self._get_alltime_chart_movies(chart_page_url,chart_df)

        return chart_df
