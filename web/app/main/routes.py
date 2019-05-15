from flask import session, redirect, url_for, render_template, request, Response
from flask_socketio import emit
from . import main
#from . import tvratings
import subprocess
from .forms import LoginForm

@main.route('/', methods=['GET', 'POST'])
def tv_ratings():
    """Main page"""
    form = LoginForm()
    if form.validate_on_submit():
        session['title'] = form.title.data

        session['style'] = form.style.data

        tmp = subprocess.Popen(['python','get_IMDb_rankings.py',\
                          '-name',session['title'],\
                          '-style',session['style'],\
                          '--save'],stdout=subprocess.PIPE)

        fname = str(tmp.communicate()[0].strip(b'\n'),'utf-8')

    elif request.method == 'GET':
        form.title.data = session.get('title', '')
        form.style.data = session.get('style','')
        fname = '/static/images/default.png'

    return render_template('tvratings.html', form=form, ratings_image=fname)
