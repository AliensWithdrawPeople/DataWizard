from .. import Models
from datetime import timedelta

def form_hardware_dict(hardware: Models.Hardware, is_inspector: bool)->dict:
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