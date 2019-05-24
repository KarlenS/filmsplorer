import os.path
import time
import matplotlib.pyplot as plt
import numpy as np

import argparse
from tqdm import tqdm

import imdb

#import plotly
#import plotly.graph_objs as go

BASE = '/Users/karlen/Fun/filmsplorer/web/app/'

def get_IMDb_ratings(ia,name,style='bar'):

    s = ia.search_movie(name)

    try:
        g = s[0]
    except IndexError:
        return None



    if g['kind'] == 'tv series':
        ia.update(g,info=['episodes','main'])
    else:
        for c in s:
            if c['kind'] == 'tv series':
                g = c
                ia.update(g,info=['episodes','main'])
                break
        else:
            return None
            #raise ValueError('Did not find a TV Show with a name: {}'.format(name))

    title = '{t} ({y})'.format(t=g['title'],y=g['series years'])
    fname = 'static/images/{t}_{s}.png'.format(t=title.replace(' ','_'),s=style)

    checkname = BASE + fname

    if os.path.exists(checkname):

        if (time.time() - os.path.getctime(checkname) < 3600):
            return fname

    #print('Found a TV Show: {n} {y}'.format(n=g['title'],y=g['year']))

    nseasons = len(g['episodes'].keys())

    etot = 0
    elocs = []
    vals = []
    elabs = []
    slims = []

    for s in tqdm(range(1,nseasons+1,1)):

        try:
            season = g['episodes'][s]
        except KeyError:
            #print('Season fail...{}'.format(s))
            nseasons = nseasons - 1
            continue

        enum = 0
        for num,epi in season.items():
            ia.update(epi,info='vote details')

            try:
                vv = epi['arithmetic mean']
            except KeyError:
                #print('Skipping Episode S{s}E{e}'.format(s=s,e=enum+1))
                continue
            enum +=1
            etot +=1
            elocs.append(etot)
            vals.append(epi['arithmetic mean'])
            elabs.append(enum)

        slims.append((0,enum))


    return [vals,elocs,slims,elabs,nseasons,title]


def format_plot(vals_min,slims,nseasons,title):

    fig,ax = plt.subplots(1,figsize=(15,6))

    ax.yaxis.grid()

    ylow = 0 if vals_min <= 5 else 5

    slabs = ['{}'.format(i+1) for i in range(nseasons)]

    t = 0
    newlocs = []
    for l in slims:
        newlocs.append(t+l[1]/2. + 0.5)
        t+= l[1]

    ax.set_ylim(ylow,10)
    ax.set_xticks(newlocs)

    labs = ax.set_xticklabels(slabs,fontdict={'fontsize':20})
    tmp = ax.set_yticklabels(ax.get_yticks(),fontdict={'fontsize':20})
    ax.set_ylabel('Mean IMDb Ratings',fontdict={'fontsize':20})
    ax.set_xlabel('Season',fontdict={'fontsize':20})
    ax.set_title(title,fontdict={'fontsize':24},y=1.03)

    return ax,ylow


def plot_ratings(data,style='bar',save=True):

    if isinstance(data, str):
        fname = data
        print(fname)
        return fname

    else:
        try:
            vals,elocs,slims,elabs,nseasons,title = data
        except:
            fname = 'static/wompwomp2.gif'
            print(fname)
            return fname


    ax,ylow = format_plot(min(vals),slims,nseasons,title)

    lim2 = 0

    #plotting ratings split by season
    for s in range(0,nseasons,1):

        lims = slims[s]
        lim1 = lim2
        lim2 += lims[1]
        x = elocs[lim1:lim2]
        y = vals[lim1:lim2]

        if style == 'bar':
            ax.bar(x,y)
        elif style == 'line':
            ax.plot(x,y)
        else:
            raise ValueError('Invalid plot style argument.')

    elabfsize = 12 if style == 'bar' else 0

    xoff = 0.4 if len(elocs) > 30 else 0.1

    if len(elocs) < 100:
        for x,y,l in zip(elocs,vals,elabs):

            ax.annotate('E{l}'.format(l=l), xy=(x,y),\
                        xytext=(x-xoff,ylow+0.65),color='white',\
                        fontsize=elabfsize,rotation=90)
            ax.annotate('{y}'.format(y=y), xy=(x,y),\
                        xytext=(x-xoff,y*1.03),rotation=90)


    fname = 'static/images/{t}_{s}.png'.format(t=title.replace(' ','_'),s=style)

    plt.savefig('app/{}'.format(fname))
    print(fname)
    return fname


def make_interactive_plot(data,style='bar',save=True):

    try:
        vals,elocs,slims,elabs,nseasons,title = data
    except:
        fname = "<div><img> id='plot' src='static/wompwomp2.gif'</img></div>"
        return fname

    lim2 = 0
    data = []

    for s in range(0,nseasons,1):

        lims = slims[s]
        lim1 = lim2
        lim2 += lims[1]
        x = elocs[lim1:lim2]
        y = vals[lim1:lim2]
        labs = elabs[lim1:lim2]

        trace = go.Bar(x = x, y = y,\
                       text = labs)

        data.append(trace)


    layout = go.Layout(title=title,)

    divtxt = plotly.offline.plot({'data':data,'layout':layout},\
                                 include_plotlyjs=False, output_type='div')

    print(divtxt)


def run(name,style='bar',save=True):

    ia = imdb.IMDb()

    data = get_IMDb_ratings(ia,name)

    resp = plot_ratings(data,style=style,save=save)

def main():

    parser = argparse.ArgumentParser('Will plot show ratings.')
    parser.add_argument('-name',default=None,required=True,help='Name of TV Show')
    parser.add_argument('-style',default='bar',choices=['bar','line'],help='Plot Style')
    parser.add_argument('--save',action='store_true',help='Save plot')
    args = parser.parse_args()

    ia = imdb.IMDb()

    data = get_IMDb_ratings(ia,args.name,style=args.style)

    fname = plot_ratings(data,style=args.style,save=args.save)
    #make_interactive_plot(data,style=args.style,save=args.save)


if __name__ == '__main__':
    main()
