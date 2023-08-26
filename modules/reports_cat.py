from flask import Blueprint, redirect, render_template, request, send_from_directory, url_for, session
from flask_login import login_required, current_user
from sqlalchemy import select 

from .db_connecter import get_session
from . import Models

from .aux_scripts.form_dict import form_cat_dict, form_json
from .aux_scripts.Templates_params import sidebar_urls
from .aux_scripts.forms import Cat_form
from .aux_scripts.check_role import check_inspector

catalogue = Blueprint('catalogue', __name__)

@catalogue.route("/reports/cat", methods=('GET', 'POST'))
@login_required
def cat():
    check_inspector()
    username = current_user.get_name() # type: ignore
    is_admin = current_user.get_role() == 'admin' # type: ignore
    
    session_db = get_session()
    manufacturers = list(session_db.scalars(select(Models.Catalogue.manufacturer).distinct()).all())
    pressures = list(session_db.scalars(select(Models.Catalogue.max_pressure).distinct()).all())
    return render_template('reports_cat.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, manufacturers=manufacturers, pressures=pressures)

@catalogue.route("/api/data/reports/cat")
@login_required
def cat_json():
    return form_json(get_session(), Models.Catalogue, form_cat_dict, check_inspector)

@catalogue.route("/reports/cat/add", methods=('GET', 'POST'))
@catalogue.route("/reports/cat/edit/<id>", methods=('GET', 'POST'), endpoint='edit_cat')
@login_required
def add_cat(id=None):
    check_inspector()
    if(not id is None and not id.isdigit()):
            # Log that some faggot tried to mess with me by passing me shitty id!
            return redirect(url_for(sidebar_urls['Reports.cat']))
        
    req_form = request.form
    form = Cat_form(req_form)
    fill_from_form = req_form.get('fill_from_form', type=lambda req: req.lower() == 'true')
    
    is_admin = current_user.get_role() == 'admin' # type: ignore
    username = current_user.get_name() # type: ignore
    add_or_edit = 'Добавить'
    data = {}
    
    session_db = get_session()
            
    if not id is None and not fill_from_form is True:  
        obj = session_db.scalars(select(Models.Catalogue).where(Models.Catalogue.id == str(id))).one_or_none()
        if(obj is None):
            raise RuntimeError('edit_cat: obj is none')
        form.name.data = obj.name
        form.comment.data = obj.comment
        form.manufacturer.data = obj.manufacturer
        form.batch_number.data = obj.batch_number
        form.life_time.data = obj.life_time
        
        form.temp_min.data = obj.temp_min
        form.temp_max.data = obj.temp_max
        
        form.T1.data = obj.T1
        form.T2.data = obj.T2
        form.T3.data = obj.T3
        form.T4.data = obj.T4
        form.T5.data = obj.T5
        form.T6.data = obj.T6
        form.T7.data = obj.T7
        
        form.stage1.data = obj.stage1
        form.stage2.data = obj.stage2
        form.stage3.data = obj.stage3
        form.stage4.data = obj.stage4
        
        form.duration1.data = obj.duration1
        form.duration2.data = obj.duration2
        form.duration3.data = obj.duration3
        form.duration4.data = obj.duration4
        
        form.max_pressure.data = obj.max_pressure
        
        add_or_edit = 'Редактировать'
        return render_template('add_cat.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form)
        
    if request.method == 'POST' and form.validate():
        # TODO: Handle images. 
        data = {
            'name'  : form.name.data,
            'comment'  : form.comment.data,
            'manufacturer' : form.manufacturer.data,
            
            'batch_number' : form.batch_number.data,
            'life_time' : form.life_time.data,
            'temp_min' : form.temp_min.data,
            'temp_max' : form.temp_max.data,
            
            'T1' : form.T1.data,
            'T2' : form.T2.data,
            'T3' : form.T3.data,
            'T4' : form.T4.data,
            'T5' : form.T5.data,
            'T6' : form.T6.data,
            'T7' : form.T7.data,
            
            'stage1' : form.stage1.data,
            'stage2' : form.stage2.data,
            'stage3' : form.stage3.data,
            'stage4' : form.stage4.data,
            
            'duration1' : form.duration1.data,
            'duration2' : form.duration2.data,
            'duration3' : form.duration3.data,
            'duration4' : form.duration4.data,
            
            'max_pressure' : form.max_pressure.data,
        }
        if not id is None:
            obj = session_db.scalars(select(Models.Catalogue).where(Models.Catalogue.id == str(id))).one()
            for key, val in data.items():
                setattr(obj, key, val)
        else:        
            obj = Models.Catalogue(**data) 
            session_db.add(obj)
            
        session_db.commit()
        return redirect(url_for(sidebar_urls['Reports.cat']))
    
    return render_template('add_cat.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form)    