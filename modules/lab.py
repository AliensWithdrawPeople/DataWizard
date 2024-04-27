import datetime
from flask import Blueprint, current_app, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from modules.Attachment.AttachmentHandler import AttachmentHandler
from sqlalchemy import select 
from passlib.hash import pbkdf2_sha256

from .db_connecter import get_session
from . import Models

from .aux_scripts.form_dict import form_tool_dict, form_user_dict, form_json
from .aux_scripts.Templates_params import sidebar_urls
from .aux_scripts.forms import Add_user_form, Add_tool_form
from .aux_scripts.check_role import check_admin, check_id, check_inspector

lab = Blueprint('lab', __name__)

attach_handler = AttachmentHandler.getInstance()
        
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
            current_app.logger.info('Wow! I am deleting them: %s', delete_users, exc_info=True)
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
    session_db.connection().close()
    return {'data': users}

@lab.route("/lab/users/add", methods=('GET', 'POST'))
@login_required
def add_user():
    check_admin()
    form = Add_user_form(request.form)
    if request.method == 'POST' and form.validate():
        certificate_img_id = attach_handler.load_img_from_form(form.certificate_img)
        facsimile_id = attach_handler.load_img_from_form(form.facsimile_img)
        data = {
            "password" : pbkdf2_sha256.hash(form.password.data),
            "name" : form.username.data,
            "role" : form.role.data, 
            "phone_number" : form.phone_number.data,
            "email" : form.email.data,
            "birthdate" : form.birthdate.data,
            "position" : form.position.data,
            "certificate_number" : form.certificate_number.data,
            "certificated_till" : form.certificated_till.data,
            "certificate_scan_id" : certificate_img_id,
            "facsimile_id" : facsimile_id
        } 
        for _, val in data.items():
            if type(val) is str:
                val = val.strip()
        user = Models.User(**data)
        session_db = get_session()
        session_db.add(user)
        session_db.flush()
        session_db.commit()
        current_app.logger.info('User #%s was successfully added.', user.id, exc_info=True)
        session_db.connection().close()
        return redirect(url_for(sidebar_urls['Lab.users']))
    
    username = current_user.get_name() # type: ignore
    return render_template('add_user.html', is_admin=True, username=username, sidebar_urls=sidebar_urls, form=form)


@lab.route("/lab/users/edit/<id>", methods=('GET', 'POST'))
@login_required
def edit_user(id):
    check_admin()
    check_id(id, 'Lab.users')
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
        
        form.certificate_img.process_data(f"/api/data/img/{user_obj.certificate_scan_id}")
        form.facsimile_img.process_data(f"/api/data/img/{user_obj.facsimile_id}")
        session_db.connection().close()
        return render_template('edit_user.html', is_admin=True, username=current_user.get_name(), sidebar_urls=sidebar_urls, form=form)
    
    if request.method == 'POST' and form.validate():
        certificate_img_id = attach_handler.load_img_from_form(form.certificate_img, user_obj.certificate_scan_id)
        facsimile_img_id = attach_handler.load_img_from_form(form.facsimile_img, user_obj.facsimile_id)
        
        user_obj.name = form.username.data
        user_obj.role = form.role.data  # type: ignore
        user_obj.phone_number = form.phone_number.data
        user_obj.email = form.email.data
        user_obj.birthdate = form.birthdate.data
        user_obj.position = form.position.data
        user_obj.certificate_number = form.certificate_number.data
        user_obj.certificated_till = form.certificated_till.data      
         
        current_app.logger.info('User #%s was successfully edited.', user_obj.id, exc_info=True)
        session_db.commit()
        session_db.connection().close()
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
    check_id(id, 'Lab.tools')
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
            current_app.logger.exception('RuntimeError: tool_obj #%s is none.', id, exc_info=True)
            return redirect(url_for(sidebar_urls['Lab.tools']))
        
        form.name.data = tool_obj.name
        form.method.data = tool_obj.method # type: ignore
        form.model.data = tool_obj.model
        form.factory_number.data = tool_obj.factory_number
        form.inventory_number.data = tool_obj.inventory_number
        form.checkup_certificate_number.data = tool_obj.checkup_certificate_number
        form.checkup_certificate_img.process_data(f"/api/data/img/{tool_obj.checkup_certificate_scan_id}")
        form.passport_img.process_data(f"/api/data/img/{tool_obj.passport_scan_id}")
        
        
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
        for _, val in tool_data.items():
            if type(val) is str:
                val = val.strip()
        session_db = get_session()
        if not id is None:
            tool = session_db.scalars(select(Models.Tool).where(Models.Tool.id == str(id))).one()
            checkup_certificate_scan_id = attach_handler.load_img_from_form(form.checkup_certificate_img, tool.checkup_certificate_scan_id)
            passport_scan_id = attach_handler.load_img_from_form(form.passport_img, tool.passport_scan_id)
           
            for key, val in tool_data.items():
                setattr(tool, key, val)
            current_app.logger.info('Tool #%s was successfully edited.', tool.id, exc_info=True)
        else:       
            checkup_certificate_scan_id = attach_handler.load_img_from_form(form.checkup_certificate_img)
            passport_scan_id = attach_handler.load_img_from_form(form.passport_img) 
            tool = Models.Tool(**tool_data, checkup_certificate_scan_id=checkup_certificate_scan_id, passport_scan_id=passport_scan_id) 
            session_db.add(tool)
            current_app.logger.info('Tool #%s was successfully added.', tool.id, exc_info=True)
            
        session_db.commit()
        return redirect(url_for(sidebar_urls['Lab.tools']))
    
    return render_template('add_tool.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form)