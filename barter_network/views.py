"""Barter Network App"""
from barter_network import app
import random

from jinja2 import StrictUndefined

from flask import render_template, request, flash, redirect, session, jsonify


from model import connect_to_db, db, User, Skill, UserSkill
import bcrypt
import os

import helper_fun
import network

import sys
sys.path.append('..')

from barter_network import app



app.jinja_env.undefined = StrictUndefined
app.jinja_env.auto_reload = True


app.secret_key = os.environ["APP_KEY"]
map_key = os.environ["GOOGLE_API_KEY"]



@app.route('/')
def index():
    """Homepage"""

    return render_template("homepage.html")


@app.route('/pagerank.json')
def pagerank():
    """Return data about Melon Sales."""


    data_dict = {
                "labels": network.node_names,
                "datasets": [
                    {
                        "data": network.page_rank,
                        "backgroundColor": network.random_col,
                      
                        "hoverBackgroundColor": network.random_col
                
                    }]
            }

    return jsonify(data_dict)

@app.route('/register', methods=['GET'])
def barter_up_form():
    """Sign Up form"""

    return render_template("barter_up_form.html")


@app.route('/register', methods=['POST'])
def barter_up_process():
    """Sign Up process"""

    email = request.form.get('email')
    password = request.form.get('password')
    fname = request.form.get('fname')
    lname = request.form.get('lname')
    dob = request.form.get('dob')
    occupation = request.form.get('occupation')
    zipcode = request.form.get('zipcode')
    street_address = request.form.get('street-address')
    city = request.form.get('city')
    state = request.form.get('state')


    if User.query.filter_by(user_email=email).first():
        flash('Please log in, you are alreday registered')

        return redirect('/login')
    else:
        new_user = User(user_fname=fname,user_lname=lname,
            user_zipcode=zipcode,user_street_address=street_address, user_city=city, user_state=state,user_dob=dob, user_occupation=occupation, 
            user_email=email, user_password=bcrypt.hashpw(password.encode('UTF_8'), bcrypt.gensalt()))

        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.user_id
        flash('You are now logged in!')
        helper_fun.add_node(network.Z, new_user.user_id,new_user.user_fname)
    return render_template("user_skill.html", user=new_user)


@app.route("/users/<int:user_id>")
def user_detail(user_id):
    """Show info about user."""

    user = User.query.get(user_id)

    return render_template("user_profile.html", user=user, map_key_api=map_key)




@app.route('/network_graph.json')
def network_data():
    """JSON information about ."""
    network.add_nodes(network.nodes)
    network.add_edges(network.skill_to, network.skill_from)

    graph_data = network.json_my_net_data(network.Z)
    return jsonify(graph_data)



@app.route('/simple_cycle.json/<int:user_id>')
def cycle_data(user_id):
    """JSON information about ."""
  
    # info for the smaller closed loop graph
    network.B.clear()
    lp = network.find_loop(network.Z, user_id)
    if lp == "Loop Not Found":
        network.find_ngbrs(network.B,network.Z,user_id)
    #     lp = network.find_other(network.Z, user_id)
    #     ed = network.generate_edges(lp)
    #     network.add_attributes(network.B, lp, ed)

    ed = network.generate_loop_edges(lp)
    network.add_attributes(network.B, lp, ed)

    user_graph_data = network.json_my_smallnet_data(network.B)
    return jsonify(user_graph_data)

@app.route('/logout')
def log_out():

    del session['user_id']
    flash("logged out!")
    return redirect('/')

@app.route('/user_skill', methods=['POST'])
def user_skill():

    skill_name_to = request.form.get('skill-name-to')
    skill_name_from = request.form.get('skill-name-from')

    # user_insession = User.query.filter_by(user_email=session['username']).first()
    # user_id_insession = user_insession.user_id

    user_id_insession = session['user_id']

    skillz_to_eval = [(skill_name_to,'to'), (skill_name_from, 'from')]

    # Adding skill to db
    for skill_name, direction in skillz_to_eval:
        skill = db.session.query(Skill.skill_name, Skill.skill_id).join(UserSkill).filter(
                Skill.skill_name==skill_name,
                UserSkill.skill_direction==direction).first()

        if not skill:
            new_skill = Skill(skill_name=skill_name)
            db.session.add(new_skill)
            db.session.commit()
            skill = new_skill

        new_userskill = UserSkill(user_id=user_id_insession, 
                                  skill_id=skill.skill_id, skill_direction=direction)
        db.session.add(new_userskill)
        db.session.commit()
        flash("your skills have been added to our network")
        skillto = network.skill_to
        skillfrom = network.skill_from
        network.add_edges(skillto,skillfrom )
        network.json_my_net_data(network.Z)
        print network.Z.nodes(data=True)
        print network.Z.edges(data=True)
    return redirect("/users/%s" % session['user_id'])

@app.route('/update_skill')
def update_skill():
    pass


@app.route('/login', methods=['GET'])
def login_form():
    """Show login form."""
    return render_template("login_form.html")


@app.route('/login', methods=['POST'])
def login_process():
    """Process login."""

    # Get form variables
    email = request.form["email"]
    password = request.form["password"]

    user = User.query.filter_by(user_email=email).first()

    if not user:
        flash("No such user")
        return redirect("/register")

    if bcrypt.hashpw(password.encode('UTF_8'), user.user_password.encode('UTF_8')).decode() == user.user_password:
        flash("it Matches")
    else:
        flash("Incorrect password")
         

    session["user_id"] = user.user_id

    flash("Logged in")
    return redirect("/users/%s" % user.user_id)

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r



####################

# if __name__ == "__main__":
#     connect_to_db(app)
#     DebugToolbarExtension(app)
#     app.run(host='0.0.0.0', debug=True)

    
    

    