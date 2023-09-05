from enum import Enum
from typing import Any
from zipfile import ZipFile
from attr import dataclass
import dataclasses

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from sqlalchemy import select
from flask import request, session
from flask_login import current_user
from jinja2 import Environment, FileSystemLoader
import os
import pathlib
import base64
import uuid
import sys
import datetime

gtk_path = pathlib.PurePath(os.environ['GTK'])
if os.path.isdir(gtk_path) and not str(gtk_path) in sys.path: 
    sys.path.append(str(gtk_path))
from weasyprint import HTML

from ..db_connecter import get_session
from ..Models import Report, report_type, Img

# Helper functions
def date_to_rus(date: datetime.date)->str:
    months: dict[int, str] = {1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля', 5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа', 9: 'сентября', 10: 'октябра', 11: 'ноября', 12: 'декабря'}
    return f'{date.day} {months[date.month]} {date.year} г.'

def get_name(fullname: str)->str:
    name = list(filter(lambda _: bool(_.strip()), fullname.split(' ')))
    return f'{name[1][0]}. {name[2][0]}. {name[0]}'

def get_type_specific_params(report: Report, rep_type: report_type)->dict[str, Any]:
    res = {}
    session_db = get_session()
    match str(rep_type):
        case report_type.VCM.value:
            res = { "tools" : ["Лупаизмерительная ЛИ-3-10 No230236", 'Линейка измерительная "Калиброн" No3158 от 18.04.23 г.', 'Штангенциркуль "Калиброн" 0-150 No102201991 от 18.04.23 г.', 
                            'Набор шаблонов  "Etalon" No 1 No2021491 от 18.04.23 г.', 'Набор шаблонов  "Etalon" No 3 No20201487 от 18.04.23 г.', 
                            'Шаблон универсальный сварщика УШС–3 No0783 от 18.04.23  г.', 'Магнитометр переносной ИМАГ-400Ц No2598 от 15.01.23 г.',]
                }
            
        case report_type.UTM.value:
            res = { "tools" : ["Толщиномер УТ-11 ЛУЧ  №0518 от 20.03.23 г.", "Преобразователь ПЭП П112-5-10/2-Т-003 №5404 от 19.03.23 г.", "Номинальная частота контроля: 5 МГц; СОП №7448."],
                    "ts" : [report.T1, report.T2, report.T3, report.T4, report.T5, report.T6, report.T7],
                    "minimal_ts" : [report.hardware.type.T1, report.hardware.type.T2, report.hardware.type.T3, report.hardware.type.T4, report.hardware.type.T5, report.hardware.type.T6, report.hardware.type.T7],
                    "sketch" : Reporter.get_image(session_db.scalars(select(Img.src).where(Img.id == report.hardware.type.sketch_UZT_id)).one_or_none())
                }
            
        case report_type.MPI.value:
            res = { "tools" : ["Магнит постоянный ПМ-30 №0036", "Лампа УФ UV-Inspector 150 №20249", "СОП для МК №А40 (Условный уровень чувствительности А);", 
                               "Магнитометр переносной ИМАГ-400Ц №2598 от 15.01.23 г.", 'Штангенциркуль "Калиброн" 0-150 №102201991 от 18.04.23 г.', 
                               'Магнитный индикатор: люминесцентный магнитный концентрат для мокрого способа контроля 14А;', 'носитель на масляной основе Carrier II.'],
                    "sketch" : Reporter.get_image(session_db.scalars(select(Img.src).where(Img.id == report.hardware.type.sketch_MK_id)).one_or_none()),
                    "is_good" : report.MK_good,
                    "defects_position" : report.MK_comment,
                    "defects_description" : report.MK_comment
                }
        case report_type.HT.value:
            res = { "tools" : ['Гидравлическая станция: Пневмогидростанция НС-7 зав.№:1553', 'Манометр высокого давления: Manotherm 316L NiFe S/N:191651768', 
                               'Дублирующий манометр высокого давления: Manotherm 316L NiFe S/N:191651767'],
                    # FIXME:Is it true?
                   "actual_max_pressure" : report.hardware.type.max_pressure,
                   "is_good" : report.GI_preventor_good,
                    # FIXME: Which GI_*_sketch to print?
                    "sketch" : Reporter.get_image(session_db.scalars(select(Img.src).where(Img.id == report.GI_body_sketch_id)).one_or_none()),
                }
    return res

# Custom types
class templates(Enum):
    VCM = 'VCM.html'
    UTM = 'UTM.html'
    MPI = 'MPI.html'
    HT = 'HT.html'
    
class img(Enum):
    LOGO = 'Weatherford_logo.png'
    STAMP = 'Weatherford_stamp.png'
    SIGNATURE = 'ivanov_sign.png'
    
@dataclass
class Report_Config:
    # (template_name, filename, parameters) 
    template: templates
    filename: str
    parameters: dict[str, str | None]
            
# Main part
def generate_config(report: Report)->list[Report_Config]:
    rep_types: list[report_type] = list(report.report_types)    # type: ignore
    session_db = get_session()
    params_base: dict[str, Any] = {  "report_number" : f"{report.id}-",
                    "date" : date_to_rus(report.checkup_date), # type: ignore
                    "object_name" : report.hardware.type.name,
                    "reg_number" : report.hardware.tape_number, 
                    "serial_number" : report.hardware.serial_number, 
                    "manufacturer" : report.hardware.type.manufacturer, 
                    "batch_number" : report.hardware.type.batch_number, 
                    "number_1C" : "-", 
                    "location_and_kit_number" : report.hardware.unit.location, 
                    "ambient_temp" : f"+{report.ambient_temp}" if report.ambient_temp > 0 else str(report.ambient_temp),
                    "general_light" : str(report.total_light),
                    "surf_light" : str(report.surface_light),
                    "executor_position" : report.inspector.position,
                    "identification" : report.inspector.certificate_number,
                    "executor_name" : get_name(report.inspector.name),
                    "facsimile" : Reporter.get_image(session_db.scalars(select(Img.src).where(Img.id == report.inspector.facsimile_id)).one_or_none())
                }
    configs: list[Report_Config] = []
    for rep_type in rep_types:
        params = params_base | get_type_specific_params(report, rep_type)
        filename = f'report_{report.id}_{rep_type.value}.pdf'
        configs.append(Report_Config(template=templates[rep_type.value], filename=filename, parameters=params))
    
    return configs


class Reporter:
    @staticmethod 
    def __mk_if_not_exist(path: os.PathLike):
        if not os.path.isdir(path):
            os.mkdir(path)
            
    root = os.path.dirname(os.path.abspath(__file__))
    # FIXME: Change storage directory.
    storage_dir = pathlib.PurePath(root)
    templates_dir = pathlib.PurePath(root, 'templates')
    __instance = None
    @staticmethod 
    def getInstance():
        """ Static access method. """
        if Reporter.__instance is None:
            return Reporter()
        return Reporter.__instance
    
    def __init__(self):
        if Reporter.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            Reporter.__instance = self
    
    @classmethod
    def get(cls, report_id: str | int) -> pathlib.PurePath | None:
        session_db = get_session()
        try:
            report = session_db.scalars(select(Report).where(Report.id == int(report_id))).one()
            try:
                config = generate_config(report)
                _, res = cls.__create_report(current_user.id, config, True) # type: ignore
                return res
            except FileNotFoundError as e:
                raise e
        except (NoResultFound, MultipleResultsFound) as e:
            #TODO: Log that report_id is wrong. 
            return None 
        
        
    @classmethod    
    def get_image(cls, image: img | str | None) -> str | None:
        weatherford_logo = None
        if image is None:
            return None
        filename = image.value if type(image) is img else str(image)
        with open(pathlib.PurePath(cls.storage_dir, 'templates', filename), "rb") as image_file:
            weatherford_logo = 'data:image/png;base64,' + base64.b64encode(image_file.read()).decode()
        return weatherford_logo
    
    @classmethod 
    def __create_report(cls, id: int | str, config: list[Report_Config], zip_files: bool) \
        -> tuple[list[tuple[templates, pathlib.PurePath]], pathlib.PurePath | None]:
        """
        id : int | str
            user id.
        config : list[tuple[templates, str, dict[str, str]]]
            list of (template_name, filename, parameters) tuples.
        zip_files : bool
            save files as zip

        Returns
        -------
        pathlib.PurePath | list[pathlib.PurePath]
            if zip_files is True: 
                zip_path: PurePath
            else:
                list[output_pdf_path: PurePath]

        Raises
        ------
        FileNotFoundError
            Can't find folder with templates.
        """
        if not os.path.isdir(cls.templates_dir):
            # TODO: Log that 'templates folder' went MIA.
            raise FileNotFoundError("No templates folder. It's gone!!!")
        env = Environment( loader = FileSystemLoader(cls.templates_dir))
        request_id = uuid.uuid1()
        folder_name = f"{id}_{request_id}"
        html_folder = pathlib.PurePath(cls.storage_dir, 'html', folder_name)
        pdf_folder = pathlib.PurePath(cls.storage_dir, 'pdf', folder_name)
        cls.__mk_if_not_exist(pathlib.PurePath(cls.storage_dir, 'html'))
        cls.__mk_if_not_exist(pathlib.PurePath(cls.storage_dir, 'pdf'))
        cls.__mk_if_not_exist(html_folder)
        cls.__mk_if_not_exist(pdf_folder)
        
        logo = cls.get_image(img.LOGO)
        stamp = cls.get_image(img.STAMP)
        outputs: list[tuple[templates, pathlib.PurePath]] = []
        for template_name, filename, params in map(lambda _: dataclasses.astuple(_), config):
            template = env.get_template(template_name.value)
            html_file_path = pathlib.PurePath(cls.storage_dir, 'html', folder_name, f'report_{template_name.value}')
            with open(html_file_path, 'w') as html_file:
                html_file.write(template.render(weatherford_logo=logo, stamp=stamp, **params))
        
            output_file_path = pathlib.PurePath(cls.storage_dir, 'pdf', folder_name, filename)
            HTML(str(html_file_path)).write_pdf(str(output_file_path))
            outputs.append((template_name, output_file_path))

        output_zip = None
        if zip_files:
            output_zip = pathlib.PurePath(cls.storage_dir, 'pdf', folder_name, f'{request_id}.zip')
            with ZipFile(output_zip, 'w') as report_zip:
                for _, output in outputs:
                    report_zip.write(output, arcname=output.name)
        
        return outputs, output_zip