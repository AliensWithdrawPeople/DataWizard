from wtforms import Form, DateField, StringField, IntegerField, DecimalField, TextAreaField, PasswordField, validators, SelectField, EmailField, FileField, BooleanField
import datetime

class RequiredIf(validators.DataRequired):
    """Validator which makes a field required if another field is set and has a truthy value.

    Sources:
        - http://wtforms.simplecodes.com/docs/1.0.1/validators.html
        - http://stackoverflow.com/questions/8463209/how-to-make-a-field-conditionally-optional-in-wtforms
        - https://gist.github.com/devxoul/7638142#file-wtf_required_if-py
    """
    field_flags = ('requiredif',) # type: ignore

    def __init__(self, other_field_name, message=None):
        super(RequiredIf).__init__()
        self.message = message
        self.other_field_name = other_field_name

    # field is requiring that name field in the form is data value in the form
    def __call__(self, form, field):
        other_field = form[self.other_field_name]
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        if bool(other_field.data) and len(str(other_field.data).strip()) != 0 and not field.data:
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
    certificate_img = FileField('Скан удостоверенья', name = "certificate_img")
    facsimile_img = FileField('Факсимиле', name = "facsimile_img")
    
class Add_tool_form(Form):
    name = StringField('Наименование', [validators.Length(min=4, max=250)])
    model = StringField('Модель', [validators.Length(min=4, max=250)])
    factory_number = StringField('Заводской номер', [validators.Length(min=1, max=250)])
    inventory_number = StringField('Инвентарный номер', [validators.Optional(), validators.Length(max=250)])
    method =  SelectField('Метод', choices=[('ВИК', 'ВИК'), ('УЗТ', 'УЗТ'), ('УК', 'УК'), ('МК', 'МК'), ('ПВК', 'ПВК'), ('ГИ', 'ГИ')])
    checkup_certificate_number = StringField('Номер свидетельства о поверке', [validators.Optional(), validators.Length(max=250)])
    prev_checkup = NullableDateField('Дата поверки', validators=[RequiredIf(other_field_name='checkup_certificate_number', message='Введите даты поверки')])
    next_checkup = NullableDateField('Дата следующей поверки', validators=[RequiredIf(other_field_name='checkup_certificate_number', message='Введите даты поверки')])
    checkup_certificate_img = FileField('Скан свидетельства', name = "checkup_certificate_img") # It also must have [RequiredIf('checkup_certificate_number')]
    passport_img = FileField('Скан паспорта', name = "passport_img")
    is_active =  SelectField('Статус', choices=[('Активный', 'Активный'), ('Неактивный', 'Неактивный')])
    
    
class Company_form(Form):
    name = StringField('Наименование', [validators.Length(min=4, max=250)])
    logo_img = FileField('Логотип', name = "logo_img")

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
    manufacturer_logo_img = FileField('Логотип производителя', validators=[validators.Optional()], name = "manufacturer_logo_img")
    batch_number = StringField('Партийный номер', validators=[validators.Optional(), validators.Length(max=150)])
    life_time = IntegerField('Срок эксплуатации, лет', validators=[validators.Optional()])
    temp_min = DecimalField('Минимальная температура, \u2103', validators=[validators.Optional()])
    temp_max = DecimalField('Максимальная температура, \u2103', validators=[validators.Optional()])
    
    sketch_VIC_img = FileField('Эскиз ВИК', validators=[validators.Optional()], name = "sketch_VIC_img")
    sketch_UZT_img = FileField('Эскиз УЗТ', validators=[validators.Optional()], name = "sketch_UZT_img")
    sketch_UK_img = FileField('Эскиз УК', validators=[validators.Optional()], name = "sketch_UK_img")
    sketch_MK_img = FileField('Эскиз МК', validators=[validators.Optional()], name = "sketch_MK_img")
    sketch_diagram_img = FileField('Эскиз диаграммы', validators=[validators.Optional()], name = "sketch_diagram_img")
    
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
    
class Hardware_form(Form):
    owner = SelectField('Компания владелец')
    setup = SelectField('Установка')
    tape_number = StringField('Номер бандажной ленты', validators=[validators.Optional(), validators.Length(max=150)])
    serial_number = StringField('Серийный номер', validators=[validators.Optional(), validators.Length(max=150)])
    commissioned = DateField('Дата ввода в эксплуатацию')
    batch_number = StringField('Партийный номер', validators=[validators.Optional(), validators.Length(max=150)])
    
def coerce_bool(x):
    if isinstance(x, str):
        return x == "True" if x != "None" else None
    else:
        return bool(x) if x is not None else None
    
class Report_form(Form):
    checkup_date = DateField('Дата контроля')
    next_checkup_date = DateField('Дата следующего контроля')
    inspector = SelectField('Инспектор', validators=[validators.Optional()])
    ambient_temp = DecimalField('t окружающей среды, \u00B0C')
    total_light = DecimalField('Общая освещённость')
    surface_light = DecimalField('Освещённость объекта контроля')
    tape_number = StringField('Номер бандажной ленты')

    owner = StringField('Компания владелец', render_kw={'readonly': True, 'disabled':'disabled'})
    setup = StringField('Установка', render_kw={'readonly': True, 'disabled':'disabled'})
    location = StringField('Место дислокации', render_kw={'readonly': True, 'disabled':'disabled'})
    serial_number = StringField('Серийный номер', render_kw={'readonly': True, 'disabled':'disabled'})
    name = StringField('Наименование', render_kw={'readonly': True, 'disabled':'disabled'})
    comment = StringField('Характеристики', render_kw={'readonly': True, 'disabled':'disabled'})
    manufacturer = StringField('Производитель', render_kw={'readonly': True, 'disabled':'disabled'})
    batch_number = StringField('Партийный номер', render_kw={'readonly': True, 'disabled':'disabled'})
    life_time = IntegerField('Срок эксплуатации, лет', render_kw={'readonly': True, 'disabled':'disabled'})
    commissioned = DateField('Дата ввода в эксплуатацию', render_kw={'readonly': True, 'disabled':'disabled'})

    
# class VIC_Report_form(Form):
    VIC = BooleanField('ВИК')
    visual_good = SelectField('Пригодность', 
                                choices=[(None, ""), (True, 'годен'), (False, 'негоден')], 
                                coerce=coerce_bool, # type: ignore
                                validators=[RequiredIf(other_field_name='VIC', message='Выберите значение')],
                                render_kw={'readonly':True, 'disabled':'disabled'})
    visual_comment = TextAreaField('Комментарий', validators=[validators.Length(max=300)], render_kw={'readonly':True, 'disabled':'disabled'})
    vic_fields = visual_good, visual_comment
    vic_fields_names = visual_good.name, visual_comment.name

# class UZT_Report_form(Form):
    UZT = BooleanField('УЗТ')
    T1 = DecimalField('T1', validators=[RequiredIf(other_field_name='UZT', message='Выберите значение')], render_kw={'readonly':True, 'disabled':'disabled'})
    T2 = DecimalField('T2', validators=[RequiredIf(other_field_name='UZT', message='Выберите значение')], render_kw={'readonly':True, 'disabled':'disabled'})
    T3 = DecimalField('T3', validators=[RequiredIf(other_field_name='UZT', message='Выберите значение')], render_kw={'readonly':True, 'disabled':'disabled'})
    T4 = DecimalField('T4', validators=[RequiredIf(other_field_name='UZT', message='Выберите значение')], render_kw={'readonly':True, 'disabled':'disabled'})
    T5 = DecimalField('T5', validators=[RequiredIf(other_field_name='UZT', message='Выберите значение')], render_kw={'readonly':True, 'disabled':'disabled'})
    T6 = DecimalField('T6', validators=[RequiredIf(other_field_name='UZT', message='Выберите значение')], render_kw={'readonly':True, 'disabled':'disabled'})
    T7 = DecimalField('T7', validators=[RequiredIf(other_field_name='UZT', message='Выберите значение')], render_kw={'readonly':True, 'disabled':'disabled'})
    
    min_T1 = DecimalField('min T1', render_kw={'readonly': True, 'disabled':'disabled'})
    min_T2 = DecimalField('min T2', render_kw={'readonly': True, 'disabled':'disabled'})
    min_T3 = DecimalField('min T3', render_kw={'readonly': True, 'disabled':'disabled'})
    min_T4 = DecimalField('min T4', render_kw={'readonly': True, 'disabled':'disabled'})
    min_T5 = DecimalField('min T5', render_kw={'readonly': True, 'disabled':'disabled'})
    min_T6 = DecimalField('min T6', render_kw={'readonly': True, 'disabled':'disabled'})
    min_T7 = DecimalField('min T7', render_kw={'readonly': True, 'disabled':'disabled'})
    UZT_good = SelectField('Пригодность', 
                            choices=[(None, ""), (True, 'годен'), (False, 'негоден')], 
                            coerce=coerce_bool, # type: ignore
                            validators=[RequiredIf(other_field_name='UZT', message='Выберите значение')],
                            render_kw={'readonly':True, 'disabled':'disabled'})
    residual = DecimalField('Остаточный ресурс, мм', validators=[RequiredIf(other_field_name='UZT', message='Выберите значение')], render_kw={'readonly': True})
    uzt_fields = T1, T2, T3, T4, T5, T6, T7, UZT_good, residual
    uzt_fields_names = T1.name, T2.name, T3.name, T4.name, T5.name, T6.name, T7.name, UZT_good.name, residual.name

# class UK_Report_form(Form):    
    UK = BooleanField('УК')
    UK_good = SelectField('Пригодность', 
                            choices=[(None, ""), (True, 'годен'), (False, 'негоден')], 
                            coerce=coerce_bool, # type: ignore
                            validators=[RequiredIf(other_field_name='UK', message='Выберите значение')], 
                            render_kw={'readonly':True, 'disabled':'disabled'})
    UK_comment = TextAreaField('Комментарий', validators=[validators.Length(max=300)], render_kw={'readonly':True, 'disabled':'disabled'})
    uk_fields = UK_good, UK_comment
    uk_fields_names = UK_good.name, UK_comment.name
    
# class MK_Report_form(Form): 
    MK = BooleanField('МК')
    MK_good = SelectField('Пригодность', 
                            choices=[(None, ""), (True, 'годен'), (False, 'негоден')], 
                            coerce=coerce_bool, # type: ignore
                            validators=[RequiredIf(other_field_name='MK', message='Выберите значение')], 
                            render_kw={'readonly':True, 'disabled':'disabled'}) 
    MK_comment = TextAreaField('Комментарий', validators=[validators.Length(max=300)], render_kw={'readonly':True, 'disabled':'disabled'})
    mk_fields = MK_good, MK_comment
    mk_fields_names = MK_good.name, MK_comment.name

# class Hydro_Report_form(Form):  
    Hydro = BooleanField('ГИ')
    Hydro_good = SelectField('Пригодность', 
                            choices=[(None, ""), (True, 'годен'), (False, 'негоден')], 
                            coerce=coerce_bool, # type: ignore
                            validators=[RequiredIf(other_field_name='Hydro', message='Выберите значение')], 
                            render_kw={'readonly':True, 'disabled':'disabled'}) 
    stage1 = DecimalField('Этап 1, МПа', render_kw={'readonly':True, 'disabled':'disabled'})
    stage2 = DecimalField('Этап 2, МПа', render_kw={'readonly':True, 'disabled':'disabled'})
    stage3 = DecimalField('Этап 3, МПа', render_kw={'readonly':True, 'disabled':'disabled'})
    stage4 = DecimalField('Этап 4, МПа', render_kw={'readonly':True, 'disabled':'disabled'})
    duration1 = IntegerField('Выдержка 1, мин', render_kw={'readonly':True, 'disabled':'disabled'})
    duration2 = IntegerField('Выдержка 2, мин', render_kw={'readonly':True, 'disabled':'disabled'})
    duration3 = IntegerField('Выдержка 3, мин', render_kw={'readonly':True, 'disabled':'disabled'})
    duration4 = IntegerField('Выдержка 4, мин', render_kw={'readonly':True, 'disabled':'disabled'})
    hydro_fields = Hydro_good, stage1, stage2, stage3, stage4, duration1, duration2, duration3, duration4
    hydro_fields_names = Hydro_good.name, stage1.name, stage2.name, stage3.name, stage4.name, duration1.name, duration2.name, duration3.name, duration4.name

# class Hydro_preventer_Report_form(Form):
    Hydro_preventer = BooleanField('ГИ превентора')
    preventer_diameter = DecimalField('Диаметр плашек, мм', validators=[validators.NumberRange(min=0.0), RequiredIf(other_field_name='Hydro_preventer', message='Введите диаметр плашек')], render_kw={'disabled':'disabled'})
    sketch_GI_body_img = FileField('Эскиз ГИ корпус', validators=[validators.Optional()], name = "sketch_GI_body_img", render_kw={'readonly':True, 'disabled':'disabled'})
    sketch_GI_pipes_img = FileField('Эскиз ГИ трубные', validators=[validators.Optional()], name = "sketch_GI_pipes_img", render_kw={'readonly':True, 'disabled':'disabled'})
    sketch_GI_vac_img = FileField('Эскиз ГИ глухие', validators=[validators.Optional()], name = "sketch_GI_vac_img", render_kw={'readonly':True, 'disabled':'disabled'})
    hydro_preventer_fields = preventer_diameter, sketch_GI_body_img, sketch_GI_pipes_img, sketch_GI_vac_img
    hydro_preventer_fields_names = preventer_diameter.name, sketch_GI_body_img.name, sketch_GI_pipes_img.name, sketch_GI_vac_img.name

# class Calibration_Report_form(Form):
    calibration = BooleanField('Тарировка')
    calibration_pressure = DecimalField('Давление тарировки, МПа', validators=[RequiredIf(other_field_name='calibration', message='Введите значение'), validators.NumberRange(min=0.0)], render_kw={'readonly':True, 'disabled':'disabled'})
    sketch_calibration_img = FileField('Эскиз диаграммы калибровки', validators=[validators.Optional()], name = "sketch_calibration_img", render_kw={'readonly':True, 'disabled':'disabled'})
    calibration_fields = calibration_pressure, sketch_calibration_img
    calibration_fields_names = calibration_pressure.name, sketch_calibration_img.name

# class Tests_Report_form(Form):
    multiple_tests = BooleanField('Кратные испытания')
    double_test = BooleanField('2-x кратные', render_kw={'readonly':True, 'disabled':'disabled'})
    one_and_a_half_test = BooleanField('1.5-x кратные', render_kw={'readonly':True, 'disabled':'disabled'})
    one_and_a_fifth_test = BooleanField('1.2-x кратные', render_kw={'readonly':True, 'disabled':'disabled'})
    sketch_multiple_tests_img = FileField('Эскиз диаграммы испытания', validators=[validators.Optional()], name = "sketch_multiple_tests_img", render_kw={'readonly':True, 'disabled':'disabled'})
    multiple_tests_fields = double_test, one_and_a_half_test, one_and_a_fifth_test, sketch_multiple_tests_img
    multiple_tests_fields_names = double_test.name, one_and_a_half_test.name, one_and_a_fifth_test.name, sketch_multiple_tests_img.name
    