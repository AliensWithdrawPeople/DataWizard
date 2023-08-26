import datetime
from flask import Blueprint, redirect, render_template, request, flash, url_for, session
from flask_login import login_required, current_user
from sqlalchemy import or_, select 
from passlib.hash import pbkdf2_sha256

from .db_connecter import get_session
from . import Models

from .aux_scripts.form_dict import form_tool_dict, form_user_dict, form_json
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
    if not role_filter is None and role_filter in Models.role_python_enum._member_names_:
            selected = selected.where(Models.User.role == role_filter)
    
    users = session_db.scalars(selected).all()
    users = [form_user_dict(user) for user in users]
        
    return {'data': users}

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
    req_form = request.form
    form = Add_user_form(req_form)
    edit_id = str(id)
    fill_from_form = request.form.get('fill_from_form', type=lambda req: req.lower() == 'true')
    
    session_db = get_session()
    user_obj = session_db.scalars(select(Models.User).where(Models.User.id == edit_id)).one_or_none()
    if(user_obj is None):
        raise RuntimeError('edit_user: user_obj is none')
        
    del form.password
    del form.confirm
    
    if not edit_id is None and not fill_from_form is True:        
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
    is_admin = current_user.get_role() == 'admin' # type: ignore
    username = current_user.get_name() # type: ignore
    return render_template('lab_tools.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls)

@lab.route("/api/data/lab/tools")
@login_required
def tools_json():
    
    def method_filter(selected, model, filter_val):
        if not filter_val is None and filter_val in Models.method_python_enum._member_names_:
            selected = selected.where(model.method == filter_val)
        return selected
    
    def is_active_filter(selected, model, filter_val):
        if not filter_val is None and filter_val != 'Все':
            is_active = filter_val == 'Активные'
            selected = selected.where(model.is_active == is_active)
        return selected
    
    filter_dict = {
        'method_filter': method_filter,
        'is_active': is_active_filter
    }
    json = form_json(get_session(), Models.Tool, form_tool_dict, check_inspector, filter_dict)
    return json

@lab.route("/lab/tools/add", methods=('GET', 'POST'))
@lab.route("/lab/tools/edit/<id>", methods=('GET', 'POST'), endpoint='edit_tool')
@login_required
def add_tool(id=None):
    check_inspector()
    req_form = request.form
    form = Add_tool_form(req_form)
    
    fill_from_form = req_form.get('fill_from_form', type=lambda req: req.lower() == 'true')
    
    is_admin = current_user.get_role() == 'admin' # type: ignore
    username = current_user.get_name() # type: ignore
    add_or_edit = 'Добавить'
    tool_data = {}
    
    if not id is None and not fill_from_form is True:  
        session_db = get_session()
        tool_obj = session_db.scalars(select(Models.Tool).where(Models.Tool.id == str(id))).one_or_none()
        if(tool_obj is None):
            raise RuntimeError('edit_tool: tool_obj is none')
        
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
            for key, val in tool_data.items():
                setattr(tool, key, val)
        else:        
            tool = Models.Tool(**tool_data) 
            session_db.add(tool)
            
        session_db.commit()
        return redirect(url_for(sidebar_urls['Lab.tools']))
    
    return render_template('add_tool.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form)