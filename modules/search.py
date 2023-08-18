from flask import Blueprint, redirect, render_template, request, flash, url_for, session
from flask_login import login_required, current_user
from sqlalchemy import or_, select 
from datetime import timedelta

from .db_connecter import get_session
from . import Models


search = Blueprint('search', __name__)

@search.route("/search", methods=('GET', 'POST'))
@login_required
def show_cat():
    role =  current_user.get_role() # type: ignore
    is_inspector = True if role == 'admin' or role == 'inspector' else False
    return render_template('catalogue_table.html', is_inspector=is_inspector)

@search.route("/api/data/cat")
@login_required
def catalogue_json():
    role =  current_user.get_role() # type: ignore
    session = get_session()
    
    selected = select(Models.Hardware)
    total = len(session.scalars(selected).all())
    
    # search filter
    search = request.args.get('search[value]')
    if search:
        selected = select(Models.Hardware).where(or_(
            Models.Hardware.unit_id.like(f'%{search}%'),
            Models.Hardware.unit.placement.like(f'%{search}%'),
            Models.Hardware.type.name.like(f'%{search}%'),
            Models.Hardware.type.comment.like(f'%{search}%'),
            Models.Hardware.type.manufacturer.like(f'%{search}%'),
            Models.Hardware.type.batch_number.like(f'%{search}%'),
            Models.Hardware.type.serial_number.like(f'%{search}%'),
            Models.Hardware.commissioned.like(f'%{search}%'),
            Models.Hardware.last_checkup.like(f'%{search}%'),
        ))
    total_filtered = len(session.scalars(selected).all())
    
    # pagination
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    
    selected = select(Models.Hardware)
    
    
    hardwares = session.scalars(selected.offset(start).limit(length)).all()
    
    is_inspector = True if role == 'admin' or role == 'inspector' else False
    hardwares = [form_dict(hardware, is_inspector) for hardware in hardwares]
    
    for i in range(len(hardwares)):
        hardwares[i]['#'] = i + 1
        
    return {'data': hardwares,
            'recordsFiltered': total_filtered,
            'recordsTotal': total,
            'draw': request.args.get('draw', type=int),
        }

def form_dict(hardware: Models.Hardware, is_inspector: bool)->dict:
    res = {
        'Компания' : hardware.unit.company.name,
        'Юнит' : hardware.unit_id,
        'Место дислокации' : hardware.unit.placement,
        'Название' : hardware.type.name,
        'Характеристики' : hardware.type.comment,
        'Производитель' : hardware.type.manufacturer,
        'Номер партии' : hardware.type.batch_number,
        'Серийный номер' : hardware.serial_number,
        'Дата ввода в эксплуатацию' : hardware.commissioned,
        'Дата списания' : hardware.commissioned + timedelta(days=365 * hardware.type.life_time),
        'Дата последнего исследования' : hardware.last_checkup,
        'Дата следующего исследования' : hardware.next_checkup
    }
    if(not is_inspector):
        res.pop('Компания')
    return res
    