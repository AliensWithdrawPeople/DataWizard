from typing import Callable
from urllib import response
from flask import Blueprint, redirect, render_template, request, send_from_directory, url_for, session
from flask_login import login_required, current_user
from sqlalchemy import or_, select 

from .db_connecter import get_session
from . import Models

from .aux_scripts.form_dict import form_organization_dict, form_unit_dict, form_json
from .aux_scripts.Templates_params import sidebar_urls
from .aux_scripts.forms import Company_form
from .aux_scripts.check_role import check_admin, check_inspector


organizations = Blueprint('organizations', __name__)

@organizations.route("/clients", methods=('GET', 'POST'))
@login_required
def orgs():
    check_inspector()
    username = current_user.get_name() # type: ignore
    
    session_db = get_session()
    selected = select(Models.Company.name).join_from(Models.Unit, Models.Company).distinct()
    companies = list(session_db.scalars(selected).all())
    return render_template('organizations.html', is_admin=True, username=username, sidebar_urls=sidebar_urls, companies=companies)

@organizations.route("/api/data/companies")
@login_required
def organizations_json():
    return form_json(get_session(), Models.Company, form_organization_dict, check_inspector)

@organizations.route("/api/data/units")
@login_required
def units_json():
    return form_json(get_session(), Models.Unit, form_unit_dict, check_inspector)


@organizations.route("/clients/company/add", methods=('GET', 'POST'))
@organizations.route("/clients/company/edit/<id>", methods=('GET', 'POST'))
@login_required
def add_company(id=None):
    check_inspector()
    req_form = request.form
    form = Company_form(req_form)
    
    fill_from_form = req_form.get('fill_from_form', type=lambda req: req.lower() == 'true')
    
    is_admin = True if current_user.get_role() == 'admin' else False # type: ignore
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
        data = {
            'name'  : form.name.data,
            'logo_id' : 1
        }
        session_db = get_session()
        if not id is None:
            obj = session_db.scalars(select(Models.Company).where(Models.Company.id == str(id))).one()
            for key, val in data.items():
                setattr(obj, key, val)
        else:        
            obj = Models.Company(**data) 
            session_db.add(obj)
            
        session_db.commit()
        return redirect(url_for(sidebar_urls['Organizations']))
    
    return render_template('add_company.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form)

@organizations.route('/api/data/companies/logos/<id>')
@login_required
def send_logo(id):
    check_inspector()
    res = send_from_directory("C:/work/DataWizard/static/img/", "tiny_logo.png")
    return res