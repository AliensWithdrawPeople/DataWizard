from flask import Blueprint, redirect, render_template, request, flash, url_for, session
from flask_login import login_required, current_user
from sqlalchemy import or_, select 
from enum import Enum

from .db_connecter import get_session
from . import Models
from .aux_scripts.form_dict import form_user_dict
from .aux_scripts.Templates_params import sidebar_urls


lab = Blueprint('lab', __name__)

def check_admin_status():
    role =  current_user.get_role() # type: ignore
    if role != 'admin':
        return redirect(url_for('index'))
    
@lab.route("/lab/users", methods=('GET', 'POST'))
@login_required
def show_Lab_users():
    check_admin_status()
    return render_template('lab_users.html', sidebar_urls=sidebar_urls)

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
    return render_template('lab_users_add.html')

    
    