from .. import Models
from flask import request, url_for, current_app
from sqlalchemy import select


def form_json(session_db, model, form_dict_func, check_role_func, filter_dict: dict={}):
    """JSON for a client side table

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
    dict
    """
    check_role_func()
    selected = select(model)
    
    # delete users
    delete_list = request.args.get('delete_list')
    if(not delete_list is None and delete_list != ''):
        delete_list = list(map(int, delete_list.split(",")))
        if(len(delete_list) > 0):
            current_app.logger.info('Wow! I am deleting them (of type %s): %s', str(model), delete_list, exc_info=True)
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
    session_db.connection().close()    
    return {'data': objs}

def form_server_side_json(session_db, model, form_dict_func, check_role_func, where_clause, filter_dict: dict={}):
    """JSON for a server side table

    Parameters
    ----------
    session_db : Session
        sqlalchemy session for the database
    model :
        sqlalchemy ORM model with id field
    form_dict_func : Callable
    check_role_func : Callable
    where_clause: function that takes search from frontend and returns a valid SQLalchemy where clause used in search
    filter_dict : dict, optional
        {filter_name, filter_func}, by default {}
        filter_func(selected, model, filter_val)->selected

    Returns
    -------
    dict
    """
    check_role_func()
        
    selected = select(model)
    total = len(session_db.scalars(selected).all())
    
    # delete users
    delete_list = request.args.get('delete')
    if(not delete_list is None and delete_list != ''):
        delete_list = list(map(int, delete_list.split(",")))
        if(len(delete_list) > 0):      
            current_app.logger.info('Wow! I am deleting them (of type %s): %s', str(model), delete_list, exc_info=True)
            objs = list(session_db.scalars(selected.where(model.id.in_(delete_list))).all())
            for obj in objs:
                session_db.delete(obj)
            session_db.commit()
            selected = select(model)
            
    # search filter
    for name, filter in filter_dict.items():
        filter_val = request.args.get(name)
        selected = filter(selected, model, filter_val)
    
    # search
    search = request.args.get('search[value]')
    if search:
        selected = selected.where(where_clause(search))
    total_filtered = len(session_db.scalars(selected).all())
    
    # TODO: sorting

    # pagination
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
         
    objs = session_db.scalars(selected.offset(start).limit(length)).all()
    tools = [form_dict_func(obj) for obj in objs]
        
    return {'data': tools,
            'recordsFiltered': total_filtered,
            'recordsTotal': total,
            'draw': request.args.get('draw', type=int),
        }

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

def form_cat_dict(elem: Models.Catalogue)->dict:
    res = {
        'id' : elem.id,
        'Наименование' : elem.name,
        'Характеристики' : elem.comment,
        'Производитель' : elem.manufacturer,
        'Партийный номер' : elem.batch_number,
        'Максимальное рабочее давление' : elem.max_pressure
    }
    return res

def form_hardware_dict(elem: Models.Hardware)->dict:
    res = {
            'id' : elem.id,
            'Наименование' : elem.type.name,
            'Хар-ки' : elem.type.comment,
            'Производитель' : elem.type.manufacturer,
            'Партийный №' : elem.type.batch_number,
            'Серийный №' : elem.serial_number,
            'Бандаж №' : elem.tape_number,
            'Дата ввэ' : elem.commissioned,
            'Владелец' : elem.unit.company.name,
            'Установка' : elem.unit.setup_name
        }
    return res

def format_report_field(elem: Models.Report)-> str:
    def bool_to_human_readable(is_good: bool, opts: tuple[str, str]=('герметичный', 'негерметичный'))->str:
        return 'годен' if is_good else 'негоден'
        
    is_good = {
        'ВИК' : bool_to_human_readable(elem.visual_good) if elem.visual_good is not None else None,
        'УЗТ' : bool_to_human_readable(elem.UZT_good) if elem.UZT_good is not None else None,
        'МК' : bool_to_human_readable(elem.UK_good) if elem.UK_good is not None else None,
        'МК' : bool_to_human_readable(elem.MK_good) if elem.MK_good is not None else None,
        'ГИ' : bool_to_human_readable(elem.GI_preventor_good) if elem.GI_preventor_good is not None else None
    } 
    res = [f"{key} : {val}" for key, val in is_good.items() if val is not None]
    return '\n'.join(res)
    
def form_report_dict(elem: Models.Report)->dict:
    res = {
        'id' : elem.id,
        'Бандаж №' : elem.hardware.tape_number,
        'Наименование' :elem.hardware.type.name,
        'Серийный №' : elem.hardware.serial_number,
        'Дата проведения' : elem.checkup_date,
        'Отчёт' : format_report_field(elem)
    }
    return res