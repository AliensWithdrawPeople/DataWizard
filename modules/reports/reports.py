import datetime
from flask import Blueprint, current_app, jsonify, redirect, render_template, request, send_file, send_from_directory, url_for
from flask_login import login_required, current_user
from modules.Attachment.AttachmentHandler import AttachmentHandler
from modules.ReportForge.reporter import Reporter
from sqlalchemy import select, or_, update
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from wtforms import FileField

from ..db_connecter import get_session
from .. import Models

from ..aux_scripts.form_dict import form_report_dict, form_server_side_json, form_hardware_dict
from ..aux_scripts.Templates_params import sidebar_urls
from ..aux_scripts.forms import Cat_form, Hardware_form, Main_Report_form, VIC_Report_form, UZT_Report_form, UK_Report_form, MK_Report_form, Hydro_Report_form, Hydro_preventer_Report_form, Calibration_Report_form, Tests_Report_form
from ..aux_scripts.check_role import check_id, check_inspector
from app import app

reports = Blueprint('reports', __name__)

with app.app_context():
    reporter = Reporter.getInstance()

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
    search_clause = lambda search_val: or_(
        Models.Report.checkup_date.like(f'%{search_val}%'),
        Models.Report.hardware.tape_number.like(f'%{search_val}%')
        )
    json = form_server_side_json(get_session(), Models.Report, form_report_dict, lambda: True, search_clause, filter_dict)
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
    
    # TODO: Check debug print and delete it.
    print("reports/send_reports.py: with_facsimile =", with_facsimile, flush=True)
    print("reports/send_reports.py: with_stamp =", with_stamp, flush=True)
    with_facsimile = True if with_facsimile is None else bool(with_facsimile)
    with_stamp = True if with_stamp is None else bool(with_stamp)
    if report_ids is None:
        session_db = get_session()
        report_ids = session_db.execute(select(Models.Report.hardware_id, Models.Report.id, Models.Report.checkup_date)
                                        .join_from(Models.Hardware, Models.Report)
                                        .where(Models.Hardware.id.in_(hardware_ids)
                                        .order_by(Models.Report.checkup_date.asc()))
                                        ).all()
    reports = {}
    for hardware_id, report_id in report_ids:
        reports[hardware_id] = report_id
    report_ids = [report_id for _, report_id in reports.items()]
    res_zip = reporter.get_many(report_ids, with_facsimile=with_facsimile, with_stamp=with_stamp)
    return send_file(res_zip, as_attachment=True)


@reports.route("/reports/reporter/add", methods=('GET', 'POST'))
@reports.route("/reports/reporter/edit/<id>", methods=('GET', 'POST'), endpoint='edit_report')
@login_required
def add_report(id=None):
    check_id(id, 'Reports.reports')
    check_inspector()
    req_form = request.form
    
    main_form = Main_Report_form(req_form)
    VIC_form = VIC_Report_form(req_form)
    UZT_form = UZT_Report_form(req_form)
    UK_form = UK_Report_form(req_form)
    MK_form = MK_Report_form(req_form)
    Hydro_form = Hydro_Report_form(req_form)
    Hydro_preventer_form = Hydro_preventer_Report_form(req_form)
    Calibration_form = Calibration_Report_form(req_form)
    Tests_form = Tests_Report_form(req_form)
    
    forms = {
            'main_form' : main_form,
            'VIC_form' : VIC_form,
            'UZT_form' : UZT_form,
            'UK_form' : UK_form,
            'MK_form' : MK_form,
            'Hydro_form' : Hydro_form,
            'Hydro_preventer_form' : Hydro_preventer_form,
            'Calibration_form' : Calibration_form,
            'Tests_form' : Tests_form
        }
    
    # session_db = get_session()
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
            main_form.checkup_date.data = datetime.datetime.strptime(str(report_obj.checkup_date), "%Y-%m-%d").date()
        main_form.inspector.data = report_obj.inspector.name
        main_form.ambient_temp.data = report_obj.ambient_temp
        main_form.total_light.data = report_obj.total_light
        main_form.surface_light.data = report_obj.surface_light
        main_form.tape_number.data = report_obj.hardware.tape_number
        
        
        def fill_fields(fields: tuple, obj):
            for field in fields:
                if hasattr(obj, field.name) and type(field) is not FileField:
                    field = obj.__getattribute__(field.name)
                    
        VIC_form.VIC.data = report_obj.visual_good is not None
        if report_obj.visual_good is not None:
            fill_fields(VIC_form.vic_fields, report_obj)
               
        UZT_form.UZT.data = report_obj.UZT_good is not None 
        if report_obj.T1 is not None:
            fill_fields(UZT_form.uzt_fields, report_obj)
                
        UK_form.UK.data = report_obj.UK_good is not None
        if report_obj.UK_good is not None:
            fill_fields(UK_form.uk_fields, report_obj)        
        
        MK_form.MK.data = report_obj.MK_good is not None
        if report_obj.MK_good is not None:
            fill_fields(MK_form.mk_fields, report_obj)    
            
        Hydro_form.Hydro.data = report_obj.hydro_result is not None
        if report_obj.hydro_result is not None:
            fill_fields(Hydro_form.hydro_fields, report_obj)    
            
        Hydro_preventer_form.Hydro_preventer.data = report_obj.GI_preventor_good is not None
        if report_obj.hydro_result is not None:
            fill_fields(Hydro_preventer_form.hydro_preventer_fields, report_obj)
        
        Calibration_form.calibration.data = report_obj.double_test is not None
        if report_obj.calibration_pressure is not None:
            fill_fields(Calibration_form.calibration_fields, report_obj)
            
        Tests_form.multiple_tests.data = report_obj.double_test is not None
        if report_obj.double_test is not None:
            fill_fields(Tests_form.multiple_tests_fields, report_obj)
                 
        add_or_edit = 'Редактировать'
        return render_template('add_report.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=forms)
    
    
    forms_validated = (main_form.validate() and VIC_form.validate() and UZT_form.validate() and UK_form.validate() and MK_form.validate() and 
                       Hydro_form.validate() and Hydro_preventer_form.validate() and Calibration_form.validate() and Tests_form.validate())
    
    if request.method == 'POST' and forms_validated:
        forms_list = VIC_form, UZT_form, UK_form, MK_form, Hydro_form, Hydro_preventer_form, Calibration_form, Tests_form
        is_report = VIC_form.VIC, UZT_form.UZT, UK_form.UK, MK_form.MK, Hydro_form.Hydro, Hydro_preventer_form.Hydro_preventer, Calibration_form.calibration, Tests_form.multiple_tests
        report_types = [(form, is_rep.label) for form, is_rep in list(zip(forms_list, is_report)) if is_rep.data]
        with get_session() as session:
            hardware_id = session.scalars(select(Models.Hardware.id).where(Models.Hardware.tape_number == main_form.tape_number.data)).one_or_none()
            
        data = {
            'inspector_id': current_user.get_id(), # type: ignore
            'hardware_id': hardware_id,
            'checkup_date' : main_form.checkup_date.data,
            'ambient_temp' : main_form.ambient_temp.data,
            'total_light' : main_form.total_light.data,
            'surface_light' : main_form.surface_light.data,
            'report_types' : [rep_type for _, rep_type in report_types]
        }
        
        vic_data = {
            'visual_good' : VIC_form.visual_good.data,
            'visual_comment' : VIC_form.visual_comment.data
        }
        
        UZT_data = {
            'T1' : UZT_form.T1.data,
            'T2' : UZT_form.T2.data,
            'T3' : UZT_form.T3.data,
            'T4' : UZT_form.T4.data,
            'T5' : UZT_form.T5.data,
            'T6' : UZT_form.T6.data,
            'T7' : UZT_form.T7.data,
            'UZT_good' : UZT_form.UZT_good.data,
            'residual' : UZT_form.residual.data
        }
        UK_data = {
            'UK_good' : UK_form.UK_good.data,
            'UK_comment' : UK_form.UK_comment.data
        }
        MK_data = {
            'MK_good' : MK_form.MK_good.data,
            'MK_comment' : MK_form.MK_comment.data
        }
        Hydro_data = {
            'hydro_result' : Hydro_form.Hydro_good.data,
        }
        Hydro_preventer_data = {
            # FIXME: GI_preventor_good != Hydro_preventer_form.Hydro_preventer
            'GI_preventor_good' : Hydro_preventer_form.Hydro_preventer.data,
            'preventer_diameter' : Hydro_preventer_form.preventer_diameter.data
        }
        Calibration_data = {
            'calibration_pressure' : Calibration_form.calibration_pressure.data
        }
        Tests_data = {
            'double_test' : Tests_form.double_test.data,
            'one_and_a_half_test' : Tests_form.one_and_a_half_test.data,
            'one_and_a_fifth_test' : Tests_form.one_and_a_fifth_test.data,
        }
        # TODO: Load sketches!!!
        imgs_data = {
            
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
    
    return render_template('add_report.html', is_admin=is_admin, username=username, sidebar_urls=sidebar_urls, add_or_edit=add_or_edit, form=forms)
