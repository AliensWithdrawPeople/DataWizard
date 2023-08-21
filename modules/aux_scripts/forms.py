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