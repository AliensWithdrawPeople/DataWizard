from wtforms import Form, DateField, StringField, IntegerField, DecimalField, TextAreaField, PasswordField, validators, SelectField, EmailField, FileField
import datetime
from wtforms.widgets import Select, html_params

class RequiredIf(validators.DataRequired):
    """Validator which makes a field required if another field is set and has a truthy value.

    Sources:
        - http://wtforms.simplecodes.com/docs/1.0.1/validators.html
        - http://stackoverflow.com/questions/8463209/how-to-make-a-field-conditionally-optional-in-wtforms
        - https://gist.github.com/devxoul/7638142#file-wtf_required_if-py
    """
    field_flags = ('requiredif',)

    def __init__(self, other_field_name, message=None):
        super(RequiredIf).__init__()
        self.message = message
        self.other_field_name = other_field_name

    # field is requiring that name field in the form is data value in the form
    def __call__(self, form, field):
        other_field = form[self.other_field_name]
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        if bool(other_field.data) and len(other_field.data.strip()) != 0 and not field.data:
            validators.DataRequired.__call__(self, form, field)
        validators.Optional()(form, field)

class NullableDateField(DateField):
    """Native WTForms DateField throws error for empty dates.
    Let's fix this so that we could have DateField nullable."""
    def process_formdata(self, valuelist):
        if valuelist:
            date_str = ' '.join(valuelist).strip()
            if date_str == '':
                self.data = None
                return
            try:
                self.data = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                self.data = None
                raise ValueError(self.gettext('Not a valid date value'))            

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
    phone_number = StringField('Номер телефона', [validators.Length(max=13)])
    birthdate = NullableDateField('Дата рождения', validators=[validators.Optional()])
    certificate_number = StringField('Номер удостоверения', [validators.Length(max=25)])
    certificated_till = NullableDateField('Срок действия удостоверения', validators=[validators.Optional()])
    certificate_img = FileField('Скан удостоверенья')
    facsimile_img = FileField('Факсимиле')
    
class Add_tool_form(Form):
    name = StringField('Наименование', [validators.Length(min=4, max=250)])
    model = StringField('Модель', [validators.Length(min=4, max=250)])
    factory_number = StringField('Заводской номер', [validators.Length(min=1, max=250)])
    inventory_number = StringField('Инвентарный номер', [validators.Optional(), validators.Length(max=250)])
    method =  SelectField('Метод', choices=[('ВИК', 'ВИК'), ('УЗТ', 'УЗТ'), ('УК', 'УК'), ('МК', 'МК'), ('ПВК', 'ПВК'), ('ГИ', 'ГИ')])
    checkup_certificate_number = StringField('Номер свидетельства о поверке', [validators.Optional(), validators.Length(max=250)])
    prev_checkup = NullableDateField('Дата поверки', validators=[RequiredIf(other_field_name='checkup_certificate_number', message='Введите даты поверки')])
    next_checkup = NullableDateField('Дата следующей поверки', validators=[RequiredIf(other_field_name='checkup_certificate_number', message='Введите даты поверки')])
    checkup_certificate_img = FileField('Скан свидетельства') # It also must have [RequiredIf('checkup_certificate_number')]
    passport_img = FileField('Скан паспорта')
    is_active =  SelectField('Статус', choices=[('Активный', 'Активный'), ('Неактивный', 'Неактивный')])
    
    
class Company_form(Form):
    name = StringField('Наименование', [validators.Length(min=4, max=250)])
    logo_img = FileField('Логотип')

class Unit_form(Form):
    company_name = SelectField('Наименование компании') # type:ignore
    location = StringField('Место дислокации', validators=[validators.Optional()])
    setup_name = StringField('Номер установки')
    sector = StringField('Участок')
    supervisor_name = SelectField('Ответственный') # type:ignore
    
class Cat_form(Form):
    name = StringField('Наименование', validators=[validators.DataRequired(), validators.Length(max=150)])
    comment = TextAreaField('Характеристики', validators=[validators.Optional(), validators.Length(max=300)])
    manufacturer = StringField('Производитель', validators=[validators.Optional(), validators.Length(max=150)])
    manufacturer_logo_img = FileField('Логотип производителя', validators=[validators.Optional()])
    batch_number = StringField('Партийный номер', validators=[validators.Optional(), validators.Length(max=150)])
    life_time = IntegerField('Срок эксплуатации, лет', validators=[validators.Optional()])
    temp_min = DecimalField('Минимальная температура, \u2103', validators=[validators.Optional()])
    temp_max = DecimalField('Максимальная температура, \u2103', validators=[validators.Optional()])
    
    sketch_VIC_img = FileField('Эскиз ВИК', validators=[validators.Optional()])
    sketch_UZT_img = FileField('Эскиз УЗТ', validators=[validators.Optional()])
    sketch_UK_img = FileField('Эскиз УК', validators=[validators.Optional()])
    sketch_MK_img = FileField('Эскиз МК', validators=[validators.Optional()])
    sketch_diagram_img = FileField('Эскиз диаграммы', validators=[validators.Optional()])
    
    T1 = DecimalField('T1', validators=[validators.Optional()])
    T2 = DecimalField('T2', validators=[validators.Optional()])
    T3 = DecimalField('T3', validators=[validators.Optional()])
    T4 = DecimalField('T4', validators=[validators.Optional()])
    T5 = DecimalField('T5', validators=[validators.Optional()])
    T6 = DecimalField('T6', validators=[validators.Optional()])
    T7 = DecimalField('T7', validators=[validators.Optional()])
    
    stage1 = DecimalField('Этап 1, МПа', validators=[validators.Optional()])
    stage2 = DecimalField('Этап 2, МПа', validators=[validators.Optional()])
    stage3 = DecimalField('Этап 3, МПа', validators=[validators.Optional()])
    stage4 = DecimalField('Этап 4, МПа', validators=[validators.Optional()])
    
    duration1 = IntegerField('Выдержка 1, мин', validators=[validators.Optional()])
    duration2 = IntegerField('Выдержка 2, мин', validators=[validators.Optional()])
    duration3 = IntegerField('Выдержка 3, мин', validators=[validators.Optional()])
    duration4 = IntegerField('Выдержка 4, мин', validators=[validators.Optional()])
    
    max_pressure = DecimalField('Максимальное рабочее давленее, МПа', validators=[validators.Optional()])