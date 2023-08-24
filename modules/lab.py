import datetime
from flask import Blueprint, redirect, render_template, request, flash, url_for, session
from flask_login import login_required, current_user
from sqlalchemy import or_, select 
from passlib.hash import pbkdf2_sha256

from .db_connecter import get_session
from . import Models

from .aux_scripts.form_dict import form_tool_dict, form_user_dict
from .aux_scripts.Templates_params import sidebar_urls
from .aux_scripts.forms import Add_user_form, Add_tool_form
from .aux_scripts.check_role import check_admin, check_inspector


lab = Blueprint('lab', __name__)

#------------------------ Users ------------------------#
    
@lab.route("/lab/users", methods=('GET', 'POST'))
@login_required
def show_Lab_users():
    check_admin()
    username = current_user.get_name() # type: ignore
    return render_template('lab_users.html', is_admin=True, username=username, sidebar_urls=sidebar_urls)

@lab.route("/api/data/lab/users")
@login_required
def users_json():
    check_admin()
    
    session_db = get_session()
    
    selected = select(Models.User)
    total = len(session_db.scalars(selected).all())
    
    # delete users
    delete_users = request.args.get('delete_users')
    if(not delete_users is None and delete_users != ''):
        delete_users = list(map(int, delete_users.split(",")))
        if(len(delete_users) > 0):
            user_objs = list(session_db.scalars(selected.where(Models.User.id.in_(delete_users))).all())
            for user_obj in user_objs:
                if(str(user_obj.id) != current_user.get_id()): # type: ignore
                    session_db.delete(user_obj)
            session_db.commit()
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
    total_filtered = len(session_db.scalars(selected).all())
    
    # TODO: sorting

    # pagination
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
         
    users = session_db.scalars(selected.offset(start).limit(length)).all()
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
    add_or_edit = 'Добавить'
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
        session_db = get_session()
        session_db.add(user)
        session_db.commit()
        return redirect(url_for(sidebar_urls['Lab.users']))
    
    username = current_user.get_name() # type: ignore
    return render_template('add_user.html', is_admin=True, username=username, sidebar_urls=sidebar_urls, form=form)


@lab.route("/lab/users/edit/<id>", methods=('GET', 'POST'))
@login_required
def edit_user(id):
    check_admin()
    form = Add_user_form(request.form)
    edit_id = str(id)
    is_first = request.args.get('is_first', type=bool)
        
    session_db = get_session()
    user_obj = session_db.scalars(select(Models.User).where(Models.User.id == edit_id)).one_or_none()
    if(user_obj is None):
        raise RuntimeError('edit_user: user_obj is none')
        
    user_data = {
            'password': user_obj.password,
            'name': user_obj.name,
            'role': user_obj.role, 
            'phone_number': user_obj.phone_number,
            'email': user_obj.email,
            'birthdate': user_obj.birthdate,
            'position': user_obj.position,
            'certificate_number': user_obj.certificate_number,
            'certificated_till': user_obj.certificated_till
        }
    del form.password
    del form.confirm
    
    if not edit_id is None and is_first:        
        form.username.data = user_obj.name
        role = user_obj.role
        if not role is None:
            form.role.data = role # type: ignore
        form.phone_number.data = user_obj.phone_number
        form.email.data = user_obj.email
        form.birthdate.data = user_obj.birthdate
        form.position.data = user_obj.position
        form.certificate_number.data = user_obj.certificate_number
        form.certificated_till.data = user_obj.certificated_till
        return render_template('edit_user.html', is_admin=True, username=user_obj.name, sidebar_urls=sidebar_urls, form=form)
    
    if request.method == 'POST' and form.validate():
        user_obj.name = form.username.data
        user_obj.role = form.role.data  # type: ignore
        user_obj.phone_number = form.phone_number.data
        user_obj.email = form.email.data
        user_obj.birthdate = form.birthdate.data
        user_obj.position = form.position.data
        user_obj.certificate_number = form.certificate_number.data
        user_obj.certificated_till = form.certificated_till.data        
        session_db.commit()
        
        return redirect(url_for(sidebar_urls['Lab.users']))
            
    username = current_user.get_name() # type: ignore
    return render_template('edit_user.html', is_admin=True, username=username, sidebar_urls=sidebar_urls, form=form)

#------------------------ Tools ------------------------#

@lab.route("/lab/tools", methods=('GET', 'POST'))
@login_required
def show_Lab_tools():
    check_inspector()
    is_admin = True if current_user.get_role() == 'admin' else False # type: ignore
    username = current_user.get_name() # type: ignore
    return render_template('lab_tools.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls)

@lab.route("/api/data/lab/tools")
@login_required
def tools_json():
    check_inspector()
    
    session_db = get_session()
    
    selected = select(Models.Tool)
    total = len(session_db.scalars(selected).all())
    
    # delete users
    delete_list = request.args.get('delete')
    if(not delete_list is None and delete_list != ''):
        delete_list = list(map(int, delete_list.split(",")))
        if(len(delete_list) > 0):
            objs = list(session_db.scalars(selected.where(Models.Tool.id.in_(delete_list))).all())
            for obj in objs:
                session_db.delete(obj)
            session_db.commit()
            selected = select(Models.Tool)
            
    # search filter
    method_filter = request.args.get('method_filter')
    if not method_filter is None and method_filter in Models.method_python_enum._member_names_:
            selected = selected.where(Models.Tool.method == method_filter)
    
    is_active = request.args.get('is_active')
    if not is_active is None and is_active != 'Все':
            is_active = True if is_active == 'Активные' else False
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
    total_filtered = len(session_db.scalars(selected).all())
    
    # TODO: sorting

    # pagination
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
         
    tools = session_db.scalars(selected.offset(start).limit(length)).all()
    tools = [form_tool_dict(tool) for tool in tools]
        
    return {'data': tools,
            'recordsFiltered': total_filtered,
            'recordsTotal': total,
            'draw': request.args.get('draw', type=int),
        }

@lab.route("/lab/tools/add", methods=('GET', 'POST'))
@lab.route("/lab/tools/edit/<id>", methods=('GET', 'POST'))
@login_required
def add_tool(id=None):
    check_inspector()
    
    form = Add_tool_form(request.form)
    is_first = request.args.get('is_first', type=bool)
    is_admin = True if current_user.get_role() == 'admin' else False # type: ignore
    username = current_user.get_name() # type: ignore
    add_or_edit = 'Добавить'
    tool_data = {}
    
    if not id is None and is_first:  
        session_db = get_session()
        tool_obj = session_db.scalars(select(Models.Tool).where(Models.Tool.id == str(id))).one_or_none()
        if(tool_obj is None):
            raise RuntimeError('edit_user: tool_obj is none')
        
        form.name.data = tool_obj.name
        form.method.data = tool_obj.method # type: ignore
        form.model.data = tool_obj.model
        form.factory_number.data = tool_obj.factory_number
        form.inventory_number.data = tool_obj.inventory_number
        form.checkup_certificate_number.data = tool_obj.checkup_certificate_number
        
        if not tool_obj.prev_checkup is None:
            form.prev_checkup.data = datetime.datetime.strptime(str(tool_obj.prev_checkup), "%Y-%m-%d").date()
        if not tool_obj.next_checkup is None:
            form.next_checkup.data = datetime.datetime.strptime(str(tool_obj.next_checkup), "%Y-%m-%d").date()
        form.is_active.data = 'Активный' if tool_obj.is_active else 'Неактивный'
        
        add_or_edit = 'Редактировать'
        return render_template('add_tool.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form)
        
    if request.method == 'POST' and form.validate():
        tool_data = {
            'name'  : form.name.data,
            'method' : form.method.data,
            'model'  : form.model.data,
            'factory_number'  : form.factory_number.data,
            'inventory_number'  : form.inventory_number.data,
            'checkup_certificate_number' : form.checkup_certificate_number.data,
            'prev_checkup' : form.prev_checkup.data,
            'next_checkup' : form.next_checkup.data,
            'is_active' : True if form.is_active.data == 'Активный' else False
        }
        session_db = get_session()
        if not id is None:
            tool = session_db.scalars(select(Models.Tool).where(Models.Tool.id == str(id))).one()
            for name, val in tool_data.items():
                tool.__dict__[name] = val
        else:        
            tool = Models.Tool(**tool_data) 
            session_db.add(tool)
            
        session_db.commit()
        return redirect(url_for(sidebar_urls['Lab.tools']))
    
    return render_template('add_tool.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form)