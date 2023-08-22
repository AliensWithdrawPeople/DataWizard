from wtforms import Form, DateField, StringField, PasswordField, validators, SelectField, EmailField, FileField

class Add_user_form(Form):
    username = StringField('ФИО', [validators.Length(min=4, max=250)])
    role = SelectField('Роль', choices=[('admin', 'admin'), ('inspector', 'inspector'), ('client', 'client')])
    position = StringField('Должность', [validators.Length(max=250)])
    email = EmailField('E-mail', [validators.DataRequired()])
    password = PasswordField('Пароль', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Пароли должны совпадать')
    ])
    confirm = PasswordField('Повторите пароль')
    phone_number = StringField('Номер телефона', [validators.Length(min=11, max=12)])
    birthdate = DateField('Дата рождения', [validators.Optional()])
    certificate_number = StringField('Номер удостоверения', [validators.Length(max=25)])
    certificated_till = DateField('Срок действия удостоверения', [validators.Optional()])
    certificate_img = FileField('Скан удостоверенья')
    facsimile_img = FileField('Факсимиле')
    
class Add_tool_form(Form):
    name = StringField('Наименование', [validators.Length(min=4, max=250)])
    model = StringField('Модель', [validators.Length(min=4, max=250)])
    factory_number = StringField('Заводской номер', [validators.Length(min=1, max=250)])
    inventory_number = StringField('Инвентарный номер', [validators.Length(min=1, max=250)])
    method =  SelectField('Метод', choices=[('ВИК', 'ВИК'), ('УЗТ', 'УЗТ'), ('МК', 'МК')])
    prev_checkup = DateField('Дата поверки')
    next_checkup = DateField('Дата следующей поверки')
    checkup_certificate_number = StringField('Номер свидетельства о поверке', [validators.Length(min=1, max=250)])
    checkup_certificate_img = FileField('Скан свидетельства')
    passport_img = FileField('Скан паспорта')
    is_active =  SelectField('Статус', choices=[('Активный', 'Активный'), ('Неактивный', 'Неактивный')])