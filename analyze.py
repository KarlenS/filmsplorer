'''
Bunch of 'analysis' methods, tho mostly still for
data exploration at the moment.....real analysis soon...
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


def corner_plot(ystart=1980,yend=2019,glim=[0,1E10]):

    df = get_gender_data_from_db(ylim=[ystart,yend],glim=glim)

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

            if M+F+X == 0:
                print('poop')
                temp.append(0)
            else:
                temp.append(F/float(M+F+X))

        cdata.append(temp)

    figure = corner.corner(cdata,labels=relfields)


def corr_plot(f1,f2,f3val=None,ylim=[1980,2019],glim=[0,1E10]):

    df = get_gender_data_from_db(ylim=ylim,glim=glim)

    field1 = []
    field2 = []
    field3 = []

    for rank,m in df.iterrows():
        cdict = json.loads(m['counts'])

        try:
            M1,F1,X1 = cdict[f1]
            M2,F2,X2 = cdict[f2]
        except KeyError:
            continue

        if M1+F1+X1 == 0 or M2 + F2 + X2 == 0:
            continue
        else:
            field1.append(F1/float(M1+F1+X1))
            field2.append(F2/float(M2+F2+X2))

        if f3val:
            field3.append(m[f3val])

    fig,ax = plt.subplots(1)

    inds = np.where(np.array(field1) > 0.2)

    field1 = np.array(field1)
    field2 = np.array(field2)
    field3 = np.array(field3)

    if f3val:
        ax.scatter(field3[inds],field1[inds],marker='o',alpha=0.7,label='ff {}'.format(f1))
        ax.scatter(field3[inds],field2[inds],marker='o',alpha=0.7,label='ff {}'.format(f2))
        ax.set_xlabel(f3val)
    else:
        ax.scatter(field1,field2,marker='o',alpha=0.7,label='fraction female')
        ax.set_xlabel(f1,fontsize=16)
        ax.set_ylabel(f2,fontsize=16)

    pr = np.corrcoef(field1,field2)
    print('Pearson r: {}'.format(pr[0][1]))

    ax.legend()


def plot_yearly_data(ystart,yend,field='total',glim=[0,1E10]):

    fig = plt.figure(figsize=(10,6))
    gs = GridSpec(3, 3)

    gs.update(hspace=0)
    ax = plt.subplot(gs[:-1, :])
    ax.get_xaxis().set_visible(False)
    axr = plt.subplot(gs[-1, :],sharex=ax)

    axr.set_ylim([0,0.99])

    ax.yaxis.grid()
    axr.grid()

    years = np.arange(ystart,yend+1,1)

    width = 0.35
    for year in years:
        df = get_gender_data_from_db(ylim=[year,year],
                                     glim=glim)
        counts = get_count_totals(df)
        nmov = float(len(df.index))

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

def get_gender_data_from_db(rlim=[0,5200],ylim=[1980,2019],glim=[0,1E10]):

    sql ="SELECT `mrank`,`id`,`title`,`year`,`studio`,`gross`,`counts` "\
            "FROM `movies` WHERE (`mrank` BETWEEN '{r1}' AND '{r2}') AND "\
            "(`gross` BETWEEN '{g1}' AND '{g2}') AND "\
            "(`year` BETWEEN '{y1}' AND '{y2}')".format(r1=rlim[0],r2=rlim[1],\
                                                      y1=ylim[0],y2=ylim[1],\
                                                      g1=glim[0],g2=glim[1])

    return pd.read_sql(sql,CLIENT,index_col='mrank')
