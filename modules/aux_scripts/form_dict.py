from .. import Models
from datetime import timedelta
from flask import request, url_for
from sqlalchemy import select 

from pathlib import PurePath


def form_json(session_db, model, form_dict_func, check_role_func, filter_dict: dict={}):
    """_summary_

    Parameters
    ----------
    session_db : Session
        sqlalchemy session for the database
    model :
        sqlalchemy ORM model with id field
    form_dict_func : Callable
    check_role_func : Callable
    filter_dict : dict, optional
        {filter_name, filter_func}, by default {}
        filter_func(selected, model, filter_val)->selected

    Returns
    -------
    _type_
        _description_
    """
    check_role_func()
    selected = select(model)
    
    # delete users
    delete_list = request.args.get('delete_list')
    if(not delete_list is None and delete_list != ''):
        print("Exterminate!!!", delete_list, flush=True)
        delete_list = list(map(int, delete_list.split(",")))
        if(len(delete_list) > 0):
            objs = list(session_db.scalars(selected.where(model.id.in_(delete_list))).all())
            for obj in objs:
                session_db.delete(obj)
            session_db.commit()
            selected = select(model)
        
    # search filter
    for name, filter in filter_dict.items():
        filter_val = request.args.get(name)
        selected = filter(selected, model, filter_val)

    objs = session_db.scalars(selected).all()
    objs = [form_dict_func(obj) for obj in objs]
        
    return {'data': objs}

    
def form_hardware_dict(hardware: Models.Hardware, is_inspector: bool)->dict:
    res = {
        'Компания' : hardware.unit.company.name,
        'Юнит' : hardware.unit_id,
        'Место дислокации' : hardware.unit.location,
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

def form_user_dict(user: Models.User)->dict:
    res = {
        'id' : user.id,
        'ФИО' : user.name,
        'Должность' : user.position,
        'Номер удостоверения' : user.certificate_number,
        'Удостоверение годно до' : user.certificated_till,
        'e-mail' : user.email,
        'Тел' : user.phone_number,
        'Дата рождения' : user.birthdate,
        'Роль' : user.role
    }
    return res


def form_tool_dict(tool: Models.Tool)->dict:
    res = {
        'id' : tool.id,
        'Наименование' : tool.name,
        'Модель' : tool.model,
        'Метод' : tool.method,
        'Заводской номер' : tool.factory_number,
        'Инвентарный номер' : tool.inventory_number,
        'Номер свидетельства' : tool.checkup_certificate_number,
        'Дата поверки' : tool.prev_checkup,
        'Дата следующей поверки' : tool.next_checkup,
        'Статус' : 'Активный' if tool.is_active else 'Неактивный'
    }
    return res

# TODO: Create a normal implementation.
def get_logo_src(id: int):
    return "C:/work/DataWizard/static/img/" + "small_logo.png"

def form_organization_dict(org: Models.Company)->dict:
    res = {
        'id' : org.id,
        'Наименование' : org.name,
        'Логотип' : url_for('organizations.send_logo', id=org.logo_id)
    }
    return res

def form_unit_dict(unit: Models.Unit)->dict:
    res = {
        'id' : unit.id,
        'Наименование компании' : unit.company.name,
        'Место дислокации' : unit.location,
        'Номер установки' : unit.setup_name,
        'Участок' : unit.sector,
        'Ответственный' : unit.supervisor.name
    }
    return res