from flask import Blueprint, redirect, render_template, request, flash, url_for, session
from flask_login import login_required, current_user
from sqlalchemy import or_, select 
from passlib.hash import pbkdf2_sha256
from sqlalchemy import update, delete

import modules.Models as Models
import modules.db_connecter as db_connecter
from .db_connecter import get_session
from . import Models

from .aux_scripts.form_dict import form_tool_dict, form_user_dict
from .aux_scripts.Templates_params import sidebar_urls
from .aux_scripts.forms import Add_user_form
from .aux_scripts.check_role import check_admin, check_inspector


lab = Blueprint('lab', __name__)

#------------------------ Users ------------------------#
    
@lab.route("/lab/users", methods=('GET', 'POST'))
@login_required
def show_Lab_users():
    check_admin()
    return render_template('lab_users.html', is_admin=True, sidebar_urls=sidebar_urls)

@lab.route("/api/data/lab/users")
@login_required
def users_json():
    check_admin()
    
    session = get_session()
    
    selected = select(Models.User)
    total = len(session.scalars(selected).all())
    
    # delete users
    delete_users = request.args.get('delete_users')
    if(not delete_users is None and delete_users != ''):
        delete_users = list(map(int, delete_users.split(",")))
        if(len(delete_users) > 0):
            user_objs = list(session.scalars(selected.where(Models.User.id.in_(delete_users))).all())
            for user_obj in user_objs:
                if(str(user_obj.id) != current_user.get_id()): # type: ignore
                    session.delete(user_obj)
            session.commit()
            selected = select(Models.User)
        
    # search filter
    role_filter = request.args.get('role_filter')    
    search = request.args.get('search[value]')
    if not role_filter is None and role_filter in Models.role_python_enum._member_names_:
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
    check_admin()
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


#------------------------ Tools ------------------------#

@lab.route("/lab/tools", methods=('GET', 'POST'))
@login_required
def show_Lab_tools():
    check_inspector()
    is_admin = True if current_user.get_role() == 'admin' else False # type: ignore
    return render_template('lab_tools.html', is_admin=is_admin, sidebar_urls=sidebar_urls)

@lab.route("/api/data/lab/tools")
@login_required
def tools_json():
    check_inspector()
    
    session = get_session()
    
    selected = select(Models.Tool)
    total = len(session.scalars(selected).all())
    
    # delete users
    delete_list = request.args.get('delete_users')
    if(not delete_list is None and delete_list != ''):
        delete_list = list(map(int, delete_list.split(",")))
        if(len(delete_list) > 0):
            objs = list(session.scalars(selected.where(Models.Tool.id.in_(delete_list))).all())
            for obj in objs:
                session.delete(obj)
            session.commit()
            selected = select(Models.Tool)
            
    # search filter
    method_filter = request.args.get('method_filter')
    if not method_filter is None and method_filter in Models.method_python_enum._member_names_:
            print('method_filter =', method_filter, flush=True)
            selected = selected.where(Models.Tool.method == method_filter)
    
    is_active = request.args.get('is_active')
    if not is_active is None and is_active != 'Все':
            is_active = True if is_active == 'Активные' else False
            print('is_active =', is_active, flush=True)
            selected = selected.where(Models.Tool.is_active == is_active)
            
    search = request.args.get('search[value]')
    if search:
        selected = selected.where(or_(
                Models.Tool.name.like(f'%{search}%'),
                Models.Tool.model.like(f'%{search}%'),
                Models.Tool.factory_number.like(f'%{search}%'),
                Models.Tool.inventory_number.like(f'%{search}%'),
                Models.Tool.checkup_certificate_number.like(f'%{search}%')
            )
        )
    total_filtered = len(session.scalars(selected).all())
    
    # TODO: sorting

    # pagination
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
         
    tools = session.scalars(selected.offset(start).limit(length)).all()
    tools = [form_tool_dict(tool) for tool in tools]
        
    return {'data': tools,
            'recordsFiltered': total_filtered,
            'recordsTotal': total,
            'draw': request.args.get('draw', type=int),
        }

@lab.route("/lab/tools/add", methods=('GET', 'POST'))
@login_required
def add_tool():
    check_inspector()
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
        return redirect(url_for(sidebar_urls['Lab.tools']))
    
    is_admin = True if current_user.get_role() == 'admin' else False # type: ignore
    return render_template('add_user.html', is_admin=is_admin, sidebar_urls=sidebar_urls, form=form)