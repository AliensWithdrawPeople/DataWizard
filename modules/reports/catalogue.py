from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from modules.Attachment.AttachmentHandler import AttachmentHandler
from sqlalchemy import select 

from ..db_connecter import get_session
from .. import Models

from ..aux_scripts.form_dict import form_cat_dict, form_json
from ..aux_scripts.Templates_params import sidebar_urls
from ..aux_scripts.forms import Cat_form
from ..aux_scripts.check_role import check_id, check_inspector

catalogue = Blueprint('catalogue', __name__)

attach_handler = AttachmentHandler.getInstance()
    
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
    def manufacturer_filter(selected, model, filter_val):
        if filter_val is not None and filter_val.lower().strip() != 'все':
            selected = selected.where(model.manufacturer == filter_val)
        return selected
    
    def pressure_filter(selected, model, filter_val):
        if not filter_val is None and filter_val.lower().strip() != 'все':
            selected = selected.where(model.max_pressure.between(float(filter_val) - 1e-3,  float(filter_val) + 1e-3))
        return selected
    filters = { "manufacturer_filter": manufacturer_filter,
                "pressure_filter": pressure_filter}
    return form_json(get_session(), Models.Catalogue, form_cat_dict, check_inspector, filters)

@catalogue.route("/reports/cat/add", methods=('GET', 'POST'))
@catalogue.route("/reports/cat/edit/<id>", methods=('GET', 'POST'), endpoint='edit_cat')
@login_required
def add_cat(id=None):
    check_inspector()
    check_id(id, 'Reports.cat')
        
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
        
        form.manufacturer_logo_img.process_data(f"/api/data/img/{obj.manufacturer_logo_id}")
        form.sketch_VIC_img.process_data(f"/api/data/img/{obj.sketch_VIC_id}")
        form.sketch_UZT_img.process_data(f"/api/data/img/{obj.sketch_UZT_id}")
        form.sketch_UK_img.process_data(f"/api/data/img/{obj.sketch_UK_id}")
        form.sketch_MK_img.process_data(f"/api/data/img/{obj.sketch_MK_id}")
        form.sketch_diagram_img.process_data(f"/api/data/img/{obj.sketch_diagram_id}")
        
        add_or_edit = 'Редактировать'
        return render_template('add_cat.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form)
        
    if request.method == 'POST' and form.validate():
        data = {
            'name'  : form.name.data.strip(),
            'comment'  : form.comment.data.strip(),
            'manufacturer' : form.manufacturer.data.strip(),
            
            'batch_number' : form.batch_number.data.strip(),
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
            manufacturer_logo_id = attach_handler.load_img_from_form(form.manufacturer_logo_img, obj.manufacturer_logo_id)
            sketch_VIC_id = attach_handler.load_img_from_form(form.sketch_VIC_img, obj.sketch_VIC_id)
            sketch_UZT_id = attach_handler.load_img_from_form(form.sketch_UZT_img, obj.sketch_UZT_id)
            sketch_UK_id = attach_handler.load_img_from_form(form.sketch_UK_img, obj.sketch_UK_id)
            sketch_MK_id = attach_handler.load_img_from_form(form.sketch_MK_img, obj.sketch_MK_id)
            sketch_diagram_id = attach_handler.load_img_from_form(form.sketch_diagram_img, obj.sketch_diagram_id)
            for key, val in data.items():
                setattr(obj, key, val)
        else:
            manufacturer_logo_id = attach_handler.load_img_from_form(form.manufacturer_logo_img)
            sketch_VIC_id = attach_handler.load_img_from_form(form.sketch_VIC_img)
            sketch_UZT_id = attach_handler.load_img_from_form(form.sketch_UZT_img)
            sketch_UK_id = attach_handler.load_img_from_form(form.sketch_UK_img)
            sketch_MK_id = attach_handler.load_img_from_form(form.sketch_MK_img)
            sketch_diagram_id = attach_handler.load_img_from_form(form.sketch_diagram_img)
            
            data['manufacturer_logo_id'] = manufacturer_logo_id if type(manufacturer_logo_id) is int else None
            data['sketch_VIC_id'] = sketch_VIC_id if type(sketch_VIC_id) is int else None
            data['sketch_UZT_id'] = sketch_UZT_id if type(sketch_UZT_id) is int else None
            data['sketch_UK_id'] = sketch_UK_id if type(sketch_UK_id) is int else None
            data['sketch_MK_id'] = sketch_MK_id if type(sketch_MK_id) is int else None
            data['sketch_diagram_id'] = sketch_diagram_id if type(sketch_diagram_id) is int else None   
            for key, val in data.items():
                if type(val) is str:
                    val = val.strip()     
            obj = Models.Catalogue(**data) 
            session_db.add(obj)
            
        session_db.commit()
        return redirect(url_for(sidebar_urls['Reports.cat']))
    
    return render_template('add_cat.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form)    