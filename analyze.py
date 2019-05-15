'''
This is where the analysis will be coordinated.
'''

import numpy as np
import pandas as pd
import json
import pymysql
from tqdm import tqdm
import corner

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

from _dbclient import CLIENT

__author__ = "Karlen Shahinyan"
__license__ = "GPL"
__version__ = "0.0.1"
__status__ = "Dev"


def corner_plot(ystart=1980,yend=2019):

    df = get_gender_data_from_db(ylim=[ystart,yend])

    relfields = ['directors','producers','writers','cast']

    cdata = []

    for rank,m in df.iterrows():
        cdict = json.loads(m['counts'])

        temp = []
        for field in relfields:
            try:
                M,F,X = cdict[field]
            except KeyError:
                M,F,X = [0,0,1] #bad, need better handling
            temp.append(F/float(M+F+X))

        cdata.append(temp)

    figure = corner.corner(cdata,labels=relfields)

def corr_plot(f1,f2):

    df = get_gender_data_from_db()

    field1 = []
    field2 = []

    for rank,m in df.iterrows():
        cdict = json.loads(m['counts'])

        try:
            M1,F1,X1 = cdict[f1]
            M2,F2,X2 = cdict[f2]
        except KeyError:
            continue

        field1.append(F1/float(M1+F1+X1))
        field2.append(F2/float(M2+F2+X2))


    fig,ax = plt.subplots(1)

    ax.scatter(field1,field2,marker='o',alpha=0.7,label='fraction female')

    pr = np.corrcoef(field1,field2)
    print('Pearson r: {}'.format(pr[0][1]))

    ax.set_xlabel(f1,fontsize=16)
    ax.set_ylabel(f2,fontsize=16)
    ax.legend()


def plot_yearly_data(ystart,yend,field='total'):

    fig = plt.figure(figsize=(10,6))
    gs = GridSpec(3, 3)

    gs.update(hspace=0)
    ax = plt.subplot(gs[:-1, :])
    axr = plt.subplot(gs[-1, :],sharex=ax)

    axr.set_ylim([0,0.99])
    axr.grid()

    years = np.arange(ystart,yend+1,1)

    width = 0.35
    for year in years:
        df = get_gender_data_from_db(ylim=[year,year+1])
        counts = get_count_totals(df)

        ax.bar([year], counts[field][0], width,color='C0')
        ax.bar([year], counts[field][1], width,color='C1',bottom=counts[field][0])

        axr.scatter([year],counts[field][1]/float(counts[field][0]+counts[field][1]),\
                    marker='s',color='k',alpha=0.6)


    cl = [Line2D([0], [0], color='C1', lw=4),
          Line2D([0], [0], color='C0', lw=4)]

    ax.legend(cl,['Female','Male'])
    ax.set_ylabel('Number of People',fontsize=16)
    axr.set_ylabel('Fraction Female',fontsize=16)
    axr.set_xlabel('Year',fontsize=16)


def get_count_totals(df):

    fields = ['cast','directors','producers',\
              'writers','composers','cgs','total']

    count_totals = {}
    for f in fields:
        count_totals[f] = np.array([0,0,0])

    for rank,m in df.iterrows():
        cdict = json.loads(m['counts'])

        for key, val in cdict.items():

            count_totals[key] = np.array(val) + count_totals[key]
            count_totals['total'] = count_totals['total']+np.array(val)

    return count_totals

def get_gender_data_from_db(rlim=[0,500],ylim=[1980,2019]):

    sql ="SELECT `mrank`,`id`,`title`,`year`,`studio`,`gross`,`counts` "\
            "FROM `movies` WHERE (`mrank` BETWEEN '{r1}' AND '{r2}') AND "\
            "`year` BETWEEN '{y1}' AND '{y2}'".format(r1=rlim[0],r2=rlim[1],\
                                                      y1=ylim[0],y2=ylim[1])

    return pd.read_sql(sql,CLIENT,index_col='mrank')

def main():

    #plot_yearly_data(1988,2018)

    #corner_plot()
    corr_plot('directors','cast')
    plt.show()


    #print(df.groupby)
    #print(json.loads(df.iloc[0]['counts'])['cast'])

    CLIENT.close()

if __name__ == '__main__':
    main()
