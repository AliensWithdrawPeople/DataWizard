import datetime
from flask import Blueprint, current_app, redirect, render_template, request, send_file, url_for
from flask_login import login_required, current_user
from modules.Attachment.AttachmentHandler import AttachmentHandler
from modules.ReportForge.reporter import Reporter
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from wtforms import FileField

from ..db_connecter import get_session
from .. import Models

from ..aux_scripts.form_dict import form_report_dict, form_server_side_json
from ..aux_scripts.Templates_params import sidebar_urls
from ..aux_scripts.forms import Report_form
from ..aux_scripts.check_role import check_id, check_inspector
from app import app

reports = Blueprint('reports', __name__)

with app.app_context():
    reporter = Reporter.getInstance()
    attach_handler = AttachmentHandler.getInstance()

@reports.route('/reports/current', methods=('GET', 'POST'))
@login_required
def current_reports():
    username = current_user.get_name() # type: ignore
    is_admin = current_user.get_role() == 'admin' # type: ignore
    session_db = get_session()
    manufacturers = list(session_db.scalars(select(Models.Catalogue.manufacturer).join_from(Models.Hardware, Models.Catalogue).distinct()).all())
    owners = list(session_db.scalars(select(Models.Company.name).join_from(Models.Hardware, Models.Company).distinct()).all())
    setups = list(session_db.scalars(select(Models.Unit.setup_name).join_from(Models.Hardware, Models.Unit).distinct()).all())
    locations = list(session_db.scalars(select(Models.Unit.location).join_from(Models.Hardware, Models.Unit).distinct()).all())
    return render_template('reports_reports_list.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, manufacturers=manufacturers, owners=owners, setups=setups, locations=locations)

@reports.route("/api/data/reports/current", methods=('GET', 'POST'))
@login_required
def reports_json():
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
    
    def checkup_date_filter(selected, model, filter_val):
        if not filter_val is None:
            try:
                filter_val = datetime.datetime.strptime(filter_val, '%d.%m.%y').date()
            except ValueError as e:
                current_app.logger.info('Bad filter_val in checkup_date_filter: %s', e, exc_info=True)
                return selected   
            selected = selected.join_from(model, Models.Unit).where(Models.Unit.location == filter_val)
        return selected
        
    filter_dict = {
        'owner_filter': owner_filter,
        'setup_filter': setup_filter,
        'manufacturer_filter': manufacturer_filter,
        'location_filter': location_filter,
        'checkup_date_filter': checkup_date_filter
    }
    # FIXME: Wrong search in parents.
    search_clause = lambda search_val: None
        # or_(
        # Models.Report.checkup_date.like(f'%{search_val}%'),
        # Models.Report.hardware.tape_number.like(f'%{search_val}%')
        # )
    json = form_server_side_json(get_session(), Models.Report, form_report_dict, lambda: True, None, filter_dict)
    return json

@reports.route('/api/reporter/get', methods=('GET', 'POST'))
@login_required
def send_reports():
    requested_reports = request.json
    if requested_reports is None or requested_reports.get('name') != 'create_reports':
        current_app.logger.info('Weirdo(user id = %s) passed shitty json! And I returned NOTHING!!!', current_user.id, exc_info=True) # type: ignore
        return {}
    
    hardware_ids = requested_reports.get('hardware_ids')
    report_ids = requested_reports.get('report_ids')
    with_facsimile = requested_reports.get('Facsimile_check')
    with_stamp = requested_reports.get('Stamp_check')
    if report_ids is None and hardware_ids is None:
        current_app.logger.info('Weirdo(user id = %s) passed shitty json! Both hardware_ids and report_ids are None', current_user.id, exc_info=True) # type: ignore
        return {}
    
    with_facsimile = True if with_facsimile is None else bool(with_facsimile)
    with_stamp = True if with_stamp is None else bool(with_stamp)
    with get_session() as session_db:
        if report_ids is None:
            report_ids = session_db.scalars(select(Models.Report)
                                            .where(Models.Report.hardware_id.in_(hardware_ids))
                                            .order_by(Models.Report.checkup_date.asc())
                                            ).all()
        else:
            report_ids = session_db.scalars(select(Models.Report)
                                            .where(Models.Report.id.in_(report_ids))
                                            .order_by(Models.Report.checkup_date.asc())
                                            ).all()
        
        report_ids = [(x.hardware_id, x.id) for x in report_ids]

    reports = {}
    print('report_ids =', report_ids)
    for hardware_id, report_id in report_ids:
        reports[hardware_id] = report_id
    report_ids = [report_id for _, report_id in reports.items()]
    res_zip = reporter.get_many(report_ids, with_facsimile=with_facsimile, with_stamp=with_stamp)
    return send_file(res_zip, as_attachment=True)


@reports.route('/api/reporter/get_hardware_info/<tape_number>', methods=('GET', 'POST'))
@login_required
def get_hardware_info(tape_number=None):
    if tape_number is None:
        return {}
    with get_session() as session:
        try:
            hardware = session.execute(select(Models.Hardware).join_from(Models.Hardware, Models.Catalogue).join_from(Models.Hardware, Models.Unit).where(Models.Hardware.tape_number == tape_number)).one()
            hardware = hardware.tuple()[-1]
            
            unit = session.execute(select(Models.Unit).where(Models.Unit.id == hardware.unit_id)).one()
            unit = unit.tuple()[-1]
            
            hardware_type = session.execute(select(Models.Catalogue).where(Models.Catalogue.id == hardware.catalogue_id)).one()
            hardware_type = hardware_type.tuple()[-1]
            
            owner = session.execute(select(Models.Company).where(Models.Company.id == hardware.company_id)).one().tuple()[-1]
        except (MultipleResultsFound, NoResultFound) as e:
            return {}
    keys = ['owner', 'setup', 'location', 'serial_number', 'name', 'comment', 'manufacturer', 'batch_number', 'life_time', 'commissioned']
    keys += [f'min_T{i}' for i in range(1, 8)] + [f'stage{i}' for i in range(1, 5)] + [f'duration{i}' for i in range(1, 5)]
    hard_info = dict.fromkeys(keys, None)
    
    hard_info['owner'] = owner.name
    hard_info['setup'] = unit.setup_name
    hard_info['location'] = unit.location
    hard_info['serial_number'] = hardware.serial_number
    hard_info['name'] = hardware_type.name
    hard_info['comment'] = hardware_type.comment
    hard_info['manufacturer'] = hardware_type.manufacturer
    hard_info['batch_number'] = hardware_type.batch_number
    hard_info['life_time'] = hardware_type.life_time
    hard_info['commissioned'] = hardware.commissioned
    for i in range(1, 8):
        hard_info[f'min_T{i}'] =  hardware_type.__getattribute__(f'T{i}')
    for i in range(1, 5):
        hard_info[f'stage{i}'] = hardware_type.__getattribute__(f'stage{i}')
        hard_info[f'duration{i}'] = hardware_type.__getattribute__(f'duration{i}')
    return hard_info

@reports.route("/reports/reporter/add", methods=('GET', 'POST'))
@reports.route("/reports/reporter/edit/<id>", methods=('GET', 'POST'), endpoint='edit_report')
@login_required
def add_report(id=None):
    check_id(id, 'Reports.reports')
    check_inspector()
    req_form = request.form
    
    form = Report_form(req_form)
    with get_session() as session:
        inspectors = list(session.execute(select(Models.User.id, Models.User.name).where(Models.User.role.in_(('admin', 'inspector')))).all())
    inspectors = [tuple(_) for _ in inspectors]
    form.inspector.choices = inspectors
    fill_from_form = req_form.get('fill_from_form', type=lambda req: req.lower() == 'true')
    
    is_admin = current_user.get_role() == 'admin' # type: ignore
    username = current_user.get_name() # type: ignore
    add_or_edit = 'Добавить'
    data = {}
    
    if not id is None and not fill_from_form is True:  
        with get_session() as session:
            report_obj = session.scalars(select(Models.Report).where(Models.Report.id == str(id))).one_or_none()
        if(report_obj is None):
            current_app.logger.exception('RuntimeError: report_obj #%s is none.', id, exc_info=True)
            return redirect(url_for(sidebar_urls['Reports.reports']))
        
        if not report_obj.checkup_date is None:
            form.checkup_date.data = datetime.datetime.strptime(str(report_obj.checkup_date), "%Y-%m-%d").date()
        form.inspector.data = report_obj.inspector.name
        form.ambient_temp.data = report_obj.ambient_temp
        form.total_light.data = report_obj.total_light
        form.surface_light.data = report_obj.surface_light
        form.tape_number.data = report_obj.hardware.tape_number
        
        
        def fill_fields(fields: tuple, obj):
            for field in fields:
                if hasattr(obj, field.name) and type(field) is not FileField:
                    field = obj.__getattribute__(field.name)
                    
        form.VIC.data = report_obj.visual_good is not None
        if report_obj.visual_good is not None:
            fill_fields(form.vic_fields, report_obj)
               
        form.UZT.data = report_obj.UZT_good is not None 
        if report_obj.T1 is not None:
            fill_fields(form.uzt_fields, report_obj)
                
        form.UK.data = report_obj.UK_good is not None
        if report_obj.UK_good is not None:
            fill_fields(form.uk_fields, report_obj)        
        
        form.MK.data = report_obj.MK_good is not None
        if report_obj.MK_good is not None:
            fill_fields(form.mk_fields, report_obj)    
            
        form.Hydro.data = report_obj.hydro_result is not None
        if report_obj.hydro_result is not None:
            fill_fields(form.hydro_fields, report_obj)    
            
        form.Hydro_preventer.data = report_obj.GI_preventor_good is not None
        if report_obj.hydro_result is not None:
            fill_fields(form.hydro_preventer_fields, report_obj)
        
        form.calibration.data = report_obj.double_test is not None
        if report_obj.calibration_pressure is not None:
            fill_fields(form.calibration_fields, report_obj)
            
        form.multiple_tests.data = report_obj.double_test is not None
        if report_obj.double_test is not None:
            fill_fields(form.multiple_tests_fields, report_obj)
                 
        add_or_edit = 'Редактировать'
        return render_template('add_report.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form)
    
    print("form.validate() =", form.validate(), 'request.method =', request.method)     
    if request.method == 'POST' and form.validate():
        is_report = form.VIC, form.UZT, form.UK, form.MK, form.Hydro, form.Hydro_preventer, form.calibration, form.multiple_tests
        report_types_raw = [rep_field.name for rep_field in is_report if rep_field.data]
        report_types = []
        for rep in report_types_raw:
            match rep:
                case 'VIC':
                    report_types.append('VCM')
                case 'UZT':            
                    report_types.append('UTM')
                case 'MK':            
                    report_types.append('MPI')
                case 'Hydro':            
                    report_types.append('HT')

        with get_session() as session:
            hardware_id = session.scalars(select(Models.Hardware.id).where(Models.Hardware.tape_number == form.tape_number.data)).one_or_none()
        print('report_types=', report_types)
        data = {
            'inspector_id': current_user.get_id(), # type: ignore
            'hardware_id': hardware_id,
            'checkup_date' : form.checkup_date.data,
            'next_checkup_date' : form.next_checkup_date.data,
            'ambient_temp' : form.ambient_temp.data,
            'total_light' : form.total_light.data,
            'surface_light' : form.surface_light.data,
            'report_types' : list(report_types)
        }
        
        vic_data = {
            'visual_good' : form.visual_good.data,
            'visual_comment' : form.visual_comment.data
        }
        
        UZT_data = {
            'T1' : form.T1.data,
            'T2' : form.T2.data,
            'T3' : form.T3.data,
            'T4' : form.T4.data,
            'T5' : form.T5.data,
            'T6' : form.T6.data,
            'T7' : form.T7.data,
            'UZT_good' : form.UZT_good.data,
            'residual' : form.residual.data
        }
        UK_data = {
            'UK_good' : form.UK_good.data,
            'UK_comment' : form.UK_comment.data
        }
        MK_data = {
            'MK_good' : form.MK_good.data,
            'MK_comment' : form.MK_comment.data
        }
        Hydro_data = {
            'hydro_result' : form.Hydro_good.data,
        }
        Hydro_preventer_data = {
            'GI_preventor_good' : form.Hydro_preventer.data if form.Hydro_preventer.data else None,
            'preventer_diameter' : form.preventer_diameter.data
        }
        Calibration_data = {
            'calibration_pressure' : form.calibration_pressure.data
        }
        Tests_data = {
            'double_test' : form.double_test.data,
            'one_and_a_half_test' : form.one_and_a_half_test.data,
            'one_and_a_fifth_test' : form.one_and_a_fifth_test.data,
        }
        imgs_data = {
            'GI_body_sketch_id' : attach_handler.load_img_from_form(form.sketch_GI_body_img),
            'GI_pipes_sketch_id' : attach_handler.load_img_from_form(form.sketch_GI_pipes_img),
            'GI_gluhie_sketch_id' : attach_handler.load_img_from_form(form.sketch_GI_vac_img),
            'calibration_diagram_sketch_id' : attach_handler.load_img_from_form(form.sketch_calibration_img),
            'multiple_tests_diagram_sketch_id' : attach_handler.load_img_from_form(form.sketch_multiple_tests_img)
        }
        
        data.update(vic_data)
        data.update(UZT_data)
        data.update(UK_data)
        data.update(MK_data)
        data.update(Hydro_data)
        data.update(Hydro_preventer_data)
        data.update(Calibration_data)
        data.update(Tests_data)
        data.update(imgs_data)
        
        with get_session() as session_db:
            if not id is None:
                report = session_db.scalars(select(Models.Report).where(Models.Report.id == str(id))).one()           
                for key, val in data.items():
                    setattr(report, key, val)
                current_app.logger.info('Report #%s was successfully edited.', report.id, exc_info=True)
            else:       
                report = Models.Report(**data) 
                session_db.add(report)
                current_app.logger.info('Report #%s was successfully added.', report.id, exc_info=True)
            session_db.commit()
        return redirect(url_for(sidebar_urls['Reports.reports']))
    
    return render_template('add_report.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=form)
