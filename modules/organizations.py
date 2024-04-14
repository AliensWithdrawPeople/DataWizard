from flask import Blueprint, redirect, render_template, request, send_from_directory, url_for, current_app
from flask_login import login_required, current_user
from modules.Attachment.AttachmentHandler import AttachmentHandler
from sqlalchemy import or_, select 
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from .db_connecter import get_session
from . import Models

from .aux_scripts.form_dict import form_organization_dict, form_server_side_json, form_unit_dict, form_json
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
    session_db.connection().close()
    return render_template('organizations.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, companies=companies)

@organizations.route("/api/data/companies")
@login_required
def organizations_json():
    current_app.logger.info('Loading %s', '/api/data/companies', exc_info=True)
    json = form_json(get_session(), Models.Company, form_organization_dict, check_inspector)
    return json

@organizations.route("/api/data/units")
@login_required
def units_json():
    current_app.logger.info('Loading %s', "/api/data/units", exc_info=True)
    def owner_filter(selected, model, filter_val):
        selected = selected.join_from(model, Models.Company)
        if not filter_val is None and filter_val.strip().lower() != 'все':
            selected = selected.where(Models.Company.name == filter_val)
        return selected
    filter_dict = {
        'filter': owner_filter,
    }
    search_clause = lambda search_val: or_(
        Models.Unit.location.like(f'%{search_val}%'),
        Models.Unit.sector.like(f'%{search_val}%'),
        Models.Unit.setup_name.like(f'%{search_val}%'),
        )
    json = form_server_side_json(get_session(), Models.Unit, form_unit_dict, check_inspector, search_clause, filter_dict)
    return json


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
            session_db.connection().close()
            raise RuntimeError('edit_company: obj is none')
        form.name.data = obj.name
        add_or_edit = 'Редактировать'
        session_db.connection().close()
        return render_template('add_company.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form)
        
    if request.method == 'POST' and form.validate():
        data = {'name'  : form.name.data}
        for _, val in data.items():
            if type(val) is str:
                val = val.strip()
                
        session_db = get_session()         
        if not id is None:
            obj = session_db.scalars(select(Models.Company).where(Models.Company.id == str(id))).one()
            logo_img_id = attach_handler.load_img_from_form(form.logo_img, obj.logo_id)
            if logo_img_id is True:
                data['logo_id'] = obj.logo_id
                
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
        session_db.connection().close()
        return redirect(url_for(sidebar_urls['Organizations']))
    
    return render_template('add_company.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form)

@organizations.route('/api/data/companies/logos/<id>')
@login_required
def send_logo(id):
    check_inspector()
    check_id(id, 'Organizations')
    session_db = get_session()
    current_app.logger.info(f'Requested logo_id = {id}')
    try:
        logo_id = session_db.scalars(select(Models.Company.logo_id).where(Models.Company.logo_id == id)).one()
    except (MultipleResultsFound, NoResultFound) as e: 
        current_app.logger.warning("Can't find logo_id for company_id = %s cause %s", id, e, exc_info=True)
        logo_id = None
    finally:
        session_db.connection().close()
    current_app.logger.info(f'Found logo with logo_id = {id}')
    default_res = send_from_directory("C:/work/DataWizard/static/img/", "tiny_logo.png") 
    if not logo_id is None:
        try:
            current_app.logger.info('Passing logo_id = %s to attach_handler', logo_id, exc_info=True)
            return attach_handler.download(int(logo_id))
        except ValueError as e:
            current_app.logger.warning('Yo! Im gonna return default logo cause %s', e, exc_info=True)
            return default_res
        except FileNotFoundError as e:
            current_app.logger.warning('Yo! Im gonna return default logo cause %s', e, exc_info=True)
            return default_res   
    current_app.logger.warning('Yo! Im gonna return default logo cause logo_id = %s is None', logo_id, exc_info=True)
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
        print("unit's company_name = ", obj.company.name, flush=True)
        form.company_name.data = obj.company.id
        # form.company_name.default = obj.company.id

        form.location.data = obj.location
        form.setup_name.data = obj.setup_name
        form.sector.data = obj.sector
        form.supervisor_name.data = obj.supervisor_id
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
        for _, val in data.items():
            if type(val) is str:
                val = val.strip()
                
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

@organizations.route("/api/data/get_units/<org_id>", methods=('GET', 'POST')) # type: ignore
@login_required
def get_units(org_id):
    if not org_id is None:  
        session_db = get_session()
        try:
            units = session_db.scalars(select(Models.Unit).where(Models.Unit.company_id == org_id)).all()
            session_db.close()
            current_app.logger.info(f'Returning units for company_id = {org_id}.')
            return {unit.id : str(unit.setup_name) for unit in units}
        except Exception as e:
            current_app.logger.exception(f'While loading units for company_id = {org_id}, shit happened: {str(e)}', exc_info=True)
            session_db.close()
    return {}
    