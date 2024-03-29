import datetime
from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from modules.Attachment.AttachmentHandler import AttachmentHandler
from sqlalchemy import select, or_
from sqlalchemy.exc import NoResultFound, MultipleResultsFound

from ..db_connecter import get_session
from .. import Models

from ..aux_scripts.form_dict import form_server_side_json, form_hardware_dict
from ..aux_scripts.Templates_params import sidebar_urls
from ..aux_scripts.forms import Cat_form, Hardware_form, FileField
from ..aux_scripts.check_role import check_id, check_inspector

hardware = Blueprint('hardware', __name__)

attach_handler = AttachmentHandler.getInstance()

@hardware.route("/reports/hardware", methods=('GET', 'POST'))
@login_required
def hardware_list():
    username = current_user.get_name() # type: ignore
    is_admin = current_user.get_role() == 'admin' # type: ignore
    session_db = get_session()
    manufacturers = list(session_db.scalars(select(Models.Catalogue.manufacturer).join_from(Models.Hardware, Models.Catalogue).distinct()).all())
    owners = list(session_db.scalars(select(Models.Company.name).join_from(Models.Hardware, Models.Company).distinct()).all())
    setups = list(session_db.scalars(select(Models.Unit.setup_name).join_from(Models.Hardware, Models.Unit).distinct()).all())
    locations = list(session_db.scalars(select(Models.Unit.location).join_from(Models.Hardware, Models.Unit).distinct()).all())
    return render_template('reports_hardware.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, manufacturers=manufacturers, owners=owners, setups=setups, locations=locations)

@hardware.route("/api/data/reports/hardware")
@login_required
def hardware_json():
    def owner_filter(selected, model, filter_val):
        if not filter_val is None and filter_val != 'Все':
            selected = selected.join_from(model, Models.Company).where(Models.Company.name == filter_val)
        return selected
    
    def setup_filter(selected, model, filter_val):
        if not filter_val is None and filter_val != 'Все':
            selected = selected.join_from(model, Models.Unit).where(Models.Unit.setup_name == filter_val)
        return selected
    
    def manufacturer_filter(selected, model, filter_val):
        if not filter_val is None and filter_val != 'Все':
            selected = selected.join_from(model, Models.Catalogue).where(Models.Catalogue.manufacturer == filter_val)
        return selected
    
    def location_filter(selected, model, filter_val):
        if not filter_val is None and filter_val != 'Все':
            selected = selected.join_from(model, Models.Unit).where(Models.Unit.location == filter_val)
        return selected
    
    filter_dict = {
        'owner_filter': owner_filter,
        'setup_filter': setup_filter,
        'manufacturer_filter': manufacturer_filter,
        'location_filter': location_filter
    }
    search_clause = lambda search_val: or_(
        Models.Hardware.type.has(Models.Catalogue.name.like(f'%{search_val}%')),
        Models.Hardware.type.has(Models.Catalogue.name.like(f'%{search_val}%')),
        Models.Hardware.type.has(Models.Catalogue.comment.like(f'%{search_val}%')),
        Models.Hardware.type.has(Models.Catalogue.batch_number.like(f'%{search_val}%')),
        Models.Hardware.serial_number.like(f'%{search_val}%'),
        Models.Hardware.tape_number.like(f'%{search_val}%'),
        Models.Hardware.unit.has(Models.Unit.company.has(Models.Company.name.like(f'%{search_val}%'))),
        Models.Hardware.unit.has(Models.Unit.setup_name.like(f'%{search_val}%')),
        )
    json = form_server_side_json(get_session(), Models.Hardware, form_hardware_dict, lambda: True, search_clause, filter_dict, [Models.Hardware.type])
    return json


@hardware.route("/reports/hardware/add", methods=('GET', 'POST'))
@hardware.route("/reports/hardware/edit/<id>", methods=('GET', 'POST'), endpoint='edit_hardware')
@login_required
def add_hardware(id=None):
    check_id(id, 'Reports.hardware')
    check_inspector()
    req_form = request.form
    form = Hardware_form(req_form)
    type_form = Cat_form(req_form, prefix='type')
    for fieldname, _ in type_form.data.items():
        field = type_form[fieldname]
        field.render_kw = {'readonly': True, 'disabled' : True}
        if(type(field) is FileField):
            del field

    session_db = get_session()
    
    owners = list(session_db.execute(select(Models.Company.id, Models.Company.name)).all())
    setups = list(session_db.execute(select(Models.Unit.id, Models.Unit.setup_name)).all())
    form.owner.choices = [(key, val) for (key, val) in owners]
    form.setup.choices = [(key, val) for (key, val) in setups]
    
    fill_from_form = req_form.get('fill_from_form', type=lambda req: req.lower() == 'true')
    
    is_admin = current_user.get_role() == 'admin' # type: ignore
    username = current_user.get_name() # type: ignore
    add_or_edit = 'Добавить'
    data = {}
    
    if not id is None and not fill_from_form is True:  
        hardware_obj = session_db.scalars(select(Models.Hardware).where(Models.Hardware.id == str(id))).one_or_none()
        if(hardware_obj is None):
            current_app.logger.exception('RuntimeError: hardware_obj #%s is none.', id, exc_info=True)
            return redirect(url_for(sidebar_urls['Reports.hardware']))
        
        form.owner.data = hardware_obj.unit.company_id
        form.setup.data = hardware_obj.unit_id
        # form.location.data = str(hardware_obj.unit.location)
        form.tape_number.data = hardware_obj.tape_number
        form.serial_number.data = hardware_obj.serial_number
        form.batch_number.data = hardware_obj.type.batch_number
        
        if not hardware_obj.commissioned is None:
            form.commissioned.data = datetime.datetime.strptime(str(hardware_obj.commissioned), "%Y-%m-%d").date()
        add_or_edit = 'Редактировать'
        return render_template('add_hardware.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form, 
                               type_form=type_form, trigger_change=True)
    
    try:
        is_unique_tape_number = session_db.scalars(select(Models.Hardware.id).where(Models.Hardware.tape_number == form.tape_number.data)).one() is None
    except MultipleResultsFound as e:
        current_app.logger.warn('Houston, we have a trouble with obtaining data from DB: %s', e, exc_info=True)
        is_unique_tape_number = False
    except NoResultFound as e:
        is_unique_tape_number = True
        
    # TODO: Add info banner to the screen about uniqueness of tape number.
    if not is_unique_tape_number:
        tmp = list(form.tape_number.errors)
        tmp.append("Номер бандажной ленты должен быть уникальным.")
        form.tape_number.errors = tuple(tmp)
        print(form.tape_number.errors)
        
    if request.method == 'POST' and form.validate() and is_unique_tape_number:
        current_app.logger.info('Hardware/tape_number = #%s', form.tape_number.data, exc_info=True)
        data = {
            'company_id': form.owner.data,
            'unit_id': session_db.scalars(select(Models.Unit.id).where(Models.Unit.id == form.setup.data)).one_or_none(),
            'catalogue_id': session_db.scalars(select(Models.Catalogue.id).where(Models.Catalogue.batch_number == form.batch_number.data)).one_or_none(),
            'tape_number': form.tape_number.data,
            'serial_number': form.serial_number.data,
            'commissioned': form.commissioned.data
        }
        for key, val in data.items():
            if type(val) is str:
                val = val.strip()
                
        if not id is None:
            hardware = session_db.scalars(select(Models.Hardware).where(Models.Hardware.id == str(id))).one()           
            for key, val in data.items():
                setattr(hardware, key, val)
            current_app.logger.info('Hardware #%s was successfully edited.', hardware.id, exc_info=True)
        else:       
            hardware = Models.Hardware(**data) 
            session_db.add(hardware)
            current_app.logger.info('Hardware #%s was successfully added.', hardware.id, exc_info=True)
            
        session_db.commit()
        return redirect(url_for(sidebar_urls['Reports.hardware']))
    
    return render_template('add_hardware.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form, type_form=type_form)

@hardware.route("/api/data/reports/hardware/type/<batch_number>", methods=('GET', 'POST'))
@login_required
def get_hardware_type_info(batch_number=None):
    if batch_number is None:
        return {}
    session_db = get_session()
    current_app.logger.info('Trying to access hardware type info; batch number = %s', str(batch_number))
    selected = select(Models.Catalogue).where(Models.Catalogue.batch_number == str(batch_number))
    try:
        hardware_type = session_db.scalars(selected).one()
    except (NoResultFound, MultipleResultsFound) as e:
        current_app.logger.warn('Houston, we have a trouble with obtaining data from DB: %s', e, exc_info=True)
        return {}
    current_app.logger.info('Hardware type info accessed; batch number = %s', str(batch_number))
    res = {
        'type-batch_number' : hardware_type.batch_number,
        'type-name': hardware_type.name,
        'type-comment': hardware_type.comment,
        'type-manufacturer': hardware_type.manufacturer,
        'type-life_time': hardware_type.life_time,
        'type-T1': hardware_type.T1,
        'type-T2': hardware_type.T2,
        'type-T3': hardware_type.T3,
        'type-T4': hardware_type.T4,
        'type-T5': hardware_type.T5,
        'type-T6': hardware_type.T6,
        'type-T7': hardware_type.T7,
        'type-stage1': hardware_type.stage1,
        'type-duration1': hardware_type.duration1,
        'type-stage2': hardware_type.stage2,
        'type-duration2': hardware_type.duration2,
        'type-stage3': hardware_type.stage3,
        'type-duration3': hardware_type.duration3,
        'type-stage4': hardware_type.stage4,
        'type-duration4': hardware_type.duration4
    }
    return jsonify(res)