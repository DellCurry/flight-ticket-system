#!/usr/bin/env python2.7
import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, url_for
from wtforms import Form
from flask_login import login_user, login_required
from flask_login import LoginManager, current_user
from flask_login import logout_user,UserMixin

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
stat_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'statics')
app = Flask(__name__,static_folder=stat_dir,template_folder=tmpl_dir)
# csrf protection
#srf = CsrfProtect()
#csrf.init_app(app)
#
DATABASEURI = "postgresql://yw3348:3.1415926535@34.74.165.156/proj1part2"

# use login manager to manage session
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app=app)

engine = create_engine(DATABASEURI)

app.secret_key = os.urandom(24)


@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; 
    traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def index():
  print request.args
  return render_template("Index.html",account=current_user.is_authenticated,user=current_user.get_id())
  
@app.route('/flightbook', methods=['POST'])
def flightBook():
  _from = request.form['from']
  to = request.form['to']
  year = request.form['year']
  month = request.form['month']
  day = request.form['day']
  if not (_from and to and year and month and day):
    return redirect('/')
  try:
    cursor=g.conn.execute(  "SELECT airline_name,fid, departure_time,arrival_time,dep_name,departure_terminal,arr_name,arrival_terminal \
                              FROM airline INNER JOIN ( SELECT airline_abbr,F.fid, F.departure_time,arrival_time,dep_abbr,departure_terminal,\
                                                        dep_name,arr_abbr,arrival_terminal,arr_name\
                                                        FROM Flight F INNER JOIN (SELECT F.fid, dep_abbr,dep_name,arr_abbr,arr_name,\
                                                                                  departure_terminal,arrival_terminal,F.departure_time\
                                                                                  FROM Departure_arrival D,Flight F,\
                                                                                  (SELECT airport_name as dep_name, \
                                                                                          airport_abbr as dep_abbr,city_name as dep_city From Airport) A1,\
                                                                                  (SELECT airport_name as arr_name, \
                                                                                          airport_abbr as arr_abbr,city_name as arr_city From Airport) A2\
                                                                                  Where D.departure_airport=A1.dep_abbr and F.fid=D.fid and\
                                                                                  D.arrival_airport=A2.arr_abbr and A1.dep_city='%s' \
                                                                                  and A2.arr_city='%s' and date_trunc('day',F.departure_time)='%s-%s-%s')\
                                                                      as F1 on F.fid=F1.fid and F.departure_time=F1.departure_time)\
                                                      as T1 on T1.airline_abbr=airline.airline_abbr"%(_from,to,year,month,day))
    
    flights=[]
    for result in cursor:
      fid=result[1]
      time=result[2]
      max_ticket= int(g.conn.execute(" SELECT COUNT(*)\
                                    FROM Tickets \
                                    WHERE Tickets.fid='%s' and Tickets.departure_time='%s'"%(fid,time)).fetchall()[0][0])
      left=max_ticket-int(g.conn.execute(" SELECT COUNT(*)\
                              FROM Buys \
                              WHERE Buys.tid IN ( SELECT tid \
                                                  FROM Tickets \
                                                  WHERE Tickets.fid='%s' and Tickets.departure_time='%s')"%(fid,time)).fetchall()[0][0])
      if left>0:
        price=str(g.conn.execute(" SELECT DISTINCT price \
                                FROM tickets \
                                WHERE tickets.fid='%s' and Tickets.departure_time='%s'"%(fid,time)).fetchall()[0][0])
          #print(result,price)
        result=list(result)
        result.append(price)
        flights.append(result)
      else:
        continue
    context=dict(data=flights)
    cursor.close()
    return render_template('flightlist.html',account=current_user.is_authenticated,user=current_user.get_id(),**context)
  except:
    return redirect('/')

@app.route('/flightid',methods=['POST'])
def flightid():
  fid=request.form['fid']
  year = request.form['year']
  month = request.form['month']
  day = request.form['day']
  if not (fid and year and month and day):
    return redirect('/')
  try:
    cursor=g.conn.execute(" SELECT airline_name,fid, departure_time,arrival_time,dep_name,departure_terminal,arr_name,arrival_terminal \
                            FROM airline INNER JOIN ( SELECT  airline_abbr,F.fid, F.departure_time,arrival_time,dep_abbr,departure_terminal,\
                                                              dep_name,arr_abbr,arrival_terminal,arr_name\
                                                      FROM Flight F INNER JOIN (SELECT  F.fid, dep_abbr,dep_name,arr_abbr,arr_name,\
                                                                                        departure_terminal,arrival_terminal,F.departure_time\
                                                                                FROM Departure_arrival D,Flight F,\
                                                                                (SELECT airport_name as dep_name, \
                                                                                        airport_abbr as dep_abbr,city_name as dep_city From Airport) A1,\
                                                                                (SELECT airport_name as arr_name, \
                                                                                        airport_abbr as arr_abbr,city_name as arr_city From Airport) A2 \
                                                                                Where F.fid='%s' and F.fid=D.fid and \
                                                                                      D.departure_airport=A1.dep_abbr and D.arrival_airport=A2.arr_abbr \
                                                                                      and date_trunc('day',F.departure_time)='%s-%s-%s') as F1\
                                                                    on F.fid=F1.fid and F.departure_time=F1.departure_time) as T1\
                                          on T1.airline_abbr=airline.airline_abbr"%(fid,year,month,day))
    flights=[]
    for result in cursor:
      fid=result[1]
      time=result[2]
      max_ticket= int(g.conn.execute(" SELECT COUNT(*)\
                                    FROM Tickets \
                                    WHERE Tickets.fid='%s' and Tickets.departure_time='%s'"%(fid,time)).fetchall()[0][0])
      left=max_ticket-int(g.conn.execute(" SELECT COUNT(*)\
                              FROM Buys \
                              WHERE Buys.tid IN ( SELECT tid \
                                                  FROM Tickets \
                                                  WHERE Tickets.fid='%s' and Tickets.departure_time='%s')"%(fid,time)).fetchall()[0][0])
      if left>0:
        price=str(g.conn.execute(" SELECT DISTINCT price \
                                FROM tickets \
                                WHERE tickets.fid='%s' and Tickets.departure_time='%s'"%(fid,time)).fetchall()[0][0])
          #print(result,price)
        result=list(result)
        result.append(price)
        flights.append(result)
      else:
        continue
    context=dict(data=flights)
    cursor.close()
    return render_template('flightlist.html',account=current_user.is_authenticated,user=current_user.get_id(),**context)
  except:
    redirect('/')



@app.route('/buy',methods=['POST'])
@login_required
def buy():
  fid=request.form['fid']
  time=request.form['time']
  try:
    cursor=g.conn.execute(" SELECT tid,seat_code\
                            FROM Tickets\
                            WHERE Tickets.fid='%s' and Tickets.departure_time='%s'\
                            EXCEPT \
                            SELECT tid,seat_code\
                            FROM Buys NATURAL JOIN Tickets\
                            WHERE fid='%s' and departure_time='%s'"%(fid,time,fid,time))
    seat=[]
    for result in cursor:
      seat.append(result)
    context=dict(data=seat)
    cursor.close()
    return render_template('buy.html',user=current_user.get_id(),**context)
  except:
    redirect('/buy')



@app.route('/buyresult',methods=['POST'])
@login_required
def buyresult():
  tid=str(request.form['tid'])
  email=current_user.get_id()
  uid=g.conn.execute("SELECT uid FROM Users WHERE email='%s'"%email).fetchall()[0][0]
  cursor=g.conn.execute("INSERT INTO Buys VALUES ('%s',NULL,'%s')"%(tid,uid))
  print("Buy successfully, ticket id is %s"%tid)
  cursor.close()
  return redirect('/mylist')

@app.route('/mylist',methods=['GET'])
@login_required
def mylist():
  email=current_user.get_id()
  try:
    uid=g.conn.execute("SELECT uid FROM Users WHERE email='%s'"%email).fetchall()[0][0]
    cursor=g.conn.execute(" SELECT tid,airline_abbr,fid,departure_time,arrival_time,dep_name,departure_terminal,arr_name,arrival_terminal,seat_code,price\
                            FROM  ( SELECT airport_name as dep_name,airport_abbr as dep_abbr,city_name as dep_city From Airport) A1,\
                                  ( SELECT airport_name as arr_name,airport_abbr as arr_abbr,city_name as arr_city From Airport) A2,\
                                  ( SELECT *\
                                    FROM departure_arrival NATURAL JOIN ( SELECT tid,airline_abbr,fid,departure_time,arrival_time,seat_code,price\
                                                                          FROM Tickets NATURAL JOIN Flight \
                                                                          WHERE tid IN (SELECT tid \
                                                                                        FROM Buys\
                                                                                        WHERE Buys.uid='%s')) AS F1) A3\
                            WHERE dep_abbr=departure_airport and arr_abbr=arrival_airport"%uid)
    tickets=[]
    for result in cursor:
      tickets.append(result)
    context=dict(data=tickets)
    cursor.close()
    return render_template('mylist.html',user=email,**context)
  except:
    return redirect('/mylist')

@login_manager.user_loader
def load_user(user_id):
  user=UserMixin()
  user.id=user_id
  return user

@app.route('/login',methods=['GET','POST'])
def login():
  if current_user.is_authenticated:
        return redirect('/')
  try:
    if request.method == 'POST':
      email = request.form['email']
      password = request.form['password']
      if not (email and password):
        error="Empty field detected"
        return render_template('login.html',error=error)
      cursor=g.conn.execute("SELECT password FROM Users WHERE email='%s'"%email)
      real=''
      for result in cursor:
        real=result['password']
      cursor.close()
      if real==password:
        cur_user = UserMixin()
        cur_user.id=email
        login_user(cur_user)
        print("login successfully")
        #_next=request.args.get('next')
        #print(_next)
        #if not next_is_valid(_next):
        #    return abort(400)
        return redirect('/')
      else:
        error="Email and password don't match"
        return render_template('login.html',error=error)
    else:
      return render_template('login.html')
  except:
    return redirect('/login')

@app.route('/signupcheck',methods=['GET','POST'])
def signup():
  if request.method == 'POST':
    uid=request.form['userid']
    first=request.form['firstname']
    last=request.form['lastname']
    age=request.form['age']
    gender=request.form['gender']
    age=request.form['age']
    email=request.form['email']
    password=request.form['password']
    if not (uid and first and last and age and gender and age and email and password):
      error="Empty fields detected"
      return render_template('login.html',error_signup=error)
    try:
      g.conn.execute("INSERT INTO Users VALUES ('%s','%s','%s','%s','%s','%s',%s)"%(email,last,first,gender,uid,password,age))
      cur_user = UserMixin()
      cur_user.id=email
      login_user(cur_user)
      return redirect('/')
    except:
      error="Some fields failed"
      return render_template('login.html',error_signup=error)
  else:
    return redirect('login')

@app.route('/logout')
def logout():
  logout_user()
  return redirect('/login')
  

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
