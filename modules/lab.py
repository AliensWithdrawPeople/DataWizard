from flask import Blueprint, redirect, render_template, request, flash, url_for, session
from flask_login import login_required, current_user
from sqlalchemy import or_, select 
from passlib.hash import pbkdf2_sha256
from datetime import date

import modules.Models as Models
import modules.db_connecter as db_connecter
from .db_connecter import get_session
from . import Models
from .aux_scripts.form_dict import form_user_dict
from .aux_scripts.Templates_params import sidebar_urls
from .aux_scripts.forms import Add_user_form


lab = Blueprint('lab', __name__)

def check_admin_status():
    role =  current_user.get_role() # type: ignore
    if role != 'admin':
        return redirect(url_for('index'))
    
@lab.route("/lab/users", methods=('GET', 'POST'))
@login_required
def show_Lab_users():
    check_admin_status()
    return render_template('lab_users.html', is_admin=True, sidebar_urls=sidebar_urls)

@lab.route("/api/data/lab/users")
@login_required
def users_json():
    check_admin_status()
    
    session = get_session()
    
    selected = select(Models.User)
    total = len(session.scalars(selected).all())
    
    # search filter
    role_filter = request.args.get('role_filter')
    print("role_filter is", role_filter, flush=True)
    search = request.args.get('search[value]')
    if not role_filter is None and role_filter in Models.role_python_enum._member_names_:
            print("role_filter is", role_filter, flush=True)
            selected = selected.where(Models.User.role == role_filter)
            
    if search:
        selected = selected.where(or_(
                Models.User.name.like(f'%{search}%'),
                Models.User.certificate_number.like(f'%{search}%'),
                Models.User.certificated_till.like(f'%{search}%'),
                Models.User.email.like(f'%{search}%'),
                Models.User.phone_number.like(f'%{search}%'),
                Models.User.role.like(f'%{search}%')
            )
        )
    total_filtered = len(session.scalars(selected).all())
    
    # TODO: sorting

    # pagination
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
         
    users = session.scalars(selected.offset(start).limit(length)).all()
    users = [form_user_dict(user) for user in users]
        
    return {'data': users,
            'recordsFiltered': total_filtered,
            'recordsTotal': total,
            'draw': request.args.get('draw', type=int),
        }

@lab.route("/lab/users/add", methods=('GET', 'POST'))
@login_required
def add_user():
    check_admin_status()
    form = Add_user_form(request.form)
    if request.method == 'POST' and form.validate():
        user = Models.User(
            password = pbkdf2_sha256.hash(form.password.data),
            name = form.username.data,
            role = form.role.data, 
            phone_number = form.phone_number.data,
            email = form.email.data,
            birthdate = form.birthdate.data,
            position = form.position.data,
            certificate_number = form.certificate_number.data,
            certificated_till = form.certificated_till.data
        ) 
        session = db_connecter.get_session()
        session.add(user)
        session.commit()
        return redirect(url_for(sidebar_urls['Lab.users']))
    
    return render_template('add_user.html', is_admin=True, sidebar_urls=sidebar_urls, form=form)