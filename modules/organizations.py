from flask import Blueprint, redirect, render_template, request, send_from_directory, url_for, current_app
from flask_login import login_required, current_user
from modules.Attachment.AttachmentHandler import AttachmentHandler
from sqlalchemy import or_, select 

from .db_connecter import get_session
from . import Models

from .aux_scripts.form_dict import form_organization_dict, form_unit_dict, form_json
from .aux_scripts.Templates_params import sidebar_urls
from .aux_scripts.forms import Company_form, Unit_form
from .aux_scripts.check_role import check_id, check_inspector


organizations = Blueprint('organizations', __name__)

attach_handler = AttachmentHandler.getInstance()
    
@organizations.route("/clients", methods=('GET', 'POST'))
@login_required
def orgs():
    check_inspector()
    username = current_user.get_name() # type: ignore
    is_admin = current_user.get_role() == 'admin' # type: ignore
    
    session_db = get_session()
    selected = select(Models.Company.name).join_from(Models.Unit, Models.Company).distinct()
    companies = list(session_db.scalars(selected).all())
    return render_template('organizations.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, companies=companies)

@organizations.route("/api/data/companies")
@login_required
def organizations_json():
    current_app.logger.info('Loading %s', '/api/data/companies', exc_info=True)
    return form_json(get_session(), Models.Company, form_organization_dict, check_inspector)

@organizations.route("/api/data/units")
@login_required
def units_json():
    current_app.logger.info('Loading %s', "/api/data/units", exc_info=True)
    return form_json(get_session(), Models.Unit, form_unit_dict, check_inspector)


@organizations.route("/clients/company/add", methods=('GET', 'POST'))
@organizations.route("/clients/company/edit/<id>", methods=('GET', 'POST'), endpoint='edit_company')
@login_required
def add_company(id=None):
    check_inspector()
    check_id(id, 'Organizations')
    req_form = request.form
    
    form = Company_form(req_form)
    
    fill_from_form = req_form.get('fill_from_form', type=lambda req: req.lower() == 'true')
    
    is_admin = current_user.get_role() == 'admin' # type: ignore
    username = current_user.get_name() # type: ignore
    add_or_edit = 'Добавить'
    data = {}
    
    if not id is None and not fill_from_form is True:  
        session_db = get_session()
        obj = session_db.scalars(select(Models.Company).where(Models.Company.id == str(id))).one_or_none()
        if(obj is None):
            raise RuntimeError('edit_company: obj is none')
        form.name.data = obj.name
        add_or_edit = 'Редактировать'
        return render_template('add_company.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form)
        
    if request.method == 'POST' and form.validate():
        data = {'name'  : form.name.data}
        session_db = get_session()         
        if not id is None:
            obj = session_db.scalars(select(Models.Company).where(Models.Company.id == str(id))).one()
            logo_img_id = attach_handler.load_img_from_form(form.logo_img, obj.logo_id)
            if logo_img_id is True:
                data['logo_id'] = logo_img_id
                
            for key, val in data.items():
                setattr(obj, key, val)
            current_app.logger.info('Company #%s was successfully edited.', obj.id, exc_info=True)
        else:        
            logo_img_id = attach_handler.load_img_from_form(form.logo_img)
            if type(logo_img_id) is int:
                data['logo_id'] = logo_img_id
            obj = Models.Company(**data) 
            session_db.add(obj)
            current_app.logger.info('Company #%s was successfully added.', obj.id, exc_info=True)
            
        session_db.commit()
        return redirect(url_for(sidebar_urls['Organizations']))
    
    return render_template('add_company.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form)

@organizations.route('/api/data/companies/logos/<id>')
@login_required
def send_logo(id):
    check_inspector()
    check_id(id, 'Organizations')
    session_db = get_session()
    logo_id = session_db.scalars(select(Models.Company.logo_id)).one_or_none()
    default_res = send_from_directory("C:/work/DataWizard/static/img/", "tiny_logo.png") 
    if not logo_id is None:
        try:
            return attach_handler.download(int(logo_id))
        except ValueError as e:
            current_app.logger.warning('Yo! Im gonna return default logo cause %s', e, exc_info=True)
            return default_res
        except FileNotFoundError as e:
            current_app.logger.warning('Yo! Im gonna return default logo cause %s', e, exc_info=True)
            return default_res   
    return default_res 

@organizations.route("/clients/unit/add", methods=('GET', 'POST'))
@organizations.route("/clients/unit/edit/<id>", methods=('GET', 'POST'), endpoint='edit_unit')
@login_required
def add_unit(id=None):
    check_inspector()
    check_id(id, 'Organizations')
        
    req_form = request.form
    form = Unit_form(req_form)
    fill_from_form = req_form.get('fill_from_form', type=lambda req: req.lower() == 'true')
    
    is_admin = current_user.get_role() == 'admin' # type: ignore
    username = current_user.get_name() # type: ignore
    add_or_edit = 'Добавить'
    data = {}
    
    session_db = get_session()
    companies = list(session_db.execute(select(Models.Company.id, Models.Company.name)).all())
    supervisors = list(session_db.execute(select(Models.User.id, Models.User.name).where(
        or_(
            Models.User.role == 'client',
            Models.User.role == 'admin'
        )
    )).all())

    form.company_name.choices = [(key, val) for (key, val) in companies]
    form.supervisor_name.choices = [(key, val) for (key, val) in supervisors]
            
    if not id is None and not fill_from_form is True:  
        obj = session_db.scalars(select(Models.Unit).where(Models.Unit.id == str(id))).one_or_none()
        if(obj is None):
            raise RuntimeError('edit_unit: obj is none')
        form.company_name.data = obj.company.name
        form.location.data = obj.location
        form.setup_name.data = obj.setup_name
        form.sector.data = obj.sector
        form.supervisor_name.data = obj.supervisor.name
        add_or_edit = 'Редактировать'
        return render_template('add_unit.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form)
        
    if request.method == 'POST' and form.validate():
        data = {
            'company_id'  : form.company_name.data,
            'supervisor_id'  : form.supervisor_name.data,
            'location' : form.location.data,
            'sector' : form.sector.data,
            'setup_name' : form.setup_name.data,
        }
        if not id is None:
            obj = session_db.scalars(select(Models.Unit).where(Models.Unit.id == str(id))).one()
            for key, val in data.items():
                setattr(obj, key, val)
            session_db.commit()
            current_app.logger.info('Unit #%s was successfully edited.', obj.id, exc_info=True)    
        else:        
            obj = Models.Unit(**data) 
            session_db.add(obj)
            session_db.commit()
            current_app.logger.info('Unit #%s was successfully added.', obj.id, exc_info=True)
            
        return redirect(url_for(sidebar_urls['Organizations']))
    
    return render_template('add_unit.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form)    
