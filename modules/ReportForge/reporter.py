from enum import Enum
from typing import Any
from zipfile import ZipFile
import dataclasses

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from sqlalchemy import select, and_
from flask import current_app
from flask_login import current_user
from jinja2 import Environment, FileSystemLoader
import os
import pathlib
import base64
import uuid
import sys
import datetime
from multiprocessing.pool import ThreadPool
import numpy as np

if 'GTK' in os.environ.keys():
    gtk_path = pathlib.PurePath(os.environ['GTK'])
    if os.path.isdir(gtk_path) and not str(gtk_path) in sys.path: 
        sys.path.append(str(gtk_path))
from weasyprint import HTML

from ..db_connecter import get_session
from ..Models import Report, report_type, Img, Tool
import config

# Helper functions
def date_to_rus(date: datetime.date)->str:
    months: dict[int, str] = {1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля', 5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа', 9: 'сентября', 10: 'октябра', 11: 'ноября', 12: 'декабря'}
    return f'{date.day} {months[date.month]} {date.year} г.'

def get_name(fullname: str)->str:
    try:
        name = list(filter(lambda _: bool(_.strip()), fullname.split(' ')))
        return f'{name[1][0]}. {name[2][0]}. {name[0]}'
    except:
        return 'admin'

def get_type_specific_params(report: Report, rep_type: report_type)->dict[str, Any]:
    res = {}
    session_db = get_session()
    raw_tools = list(session_db.scalars(select(Tool).where(and_(Tool.method == report_type[str(rep_type)].value, Tool.is_active == True))).all())
    tools = [f"{tool.name} {tool.model} {tool.factory_number} от {tool.prev_checkup.strftime('%m.%d.%Y')} г." for tool in raw_tools] # type: ignore
    match str(rep_type):
        case report_type.VCM.name:
            res = { "tools" : tools}
            
        case report_type.UTM.name:
            res = { "tools" : tools + ["Номинальная частота контроля: 5 МГц; СОП №7448."],
                    "ts" : list(np.round([report.T1, report.T2, report.T3, report.T4, report.T5, report.T6, report.T7], 2)),
                    "minimal_ts" : [report.hardware.type.T1, report.hardware.type.T2, report.hardware.type.T3, report.hardware.type.T4, report.hardware.type.T5, report.hardware.type.T6, report.hardware.type.T7],
                    "sketch" : Reporter.get_image(session_db.scalars(select(Img.src).where(Img.id == report.hardware.type.sketch_UZT_id)).one_or_none())
                }
            
        case report_type.MPI.name:
            res = { "tools" : tools,
                    "sketch" : Reporter.get_image(session_db.scalars(select(Img.src).where(Img.id == report.hardware.type.sketch_MK_id)).one_or_none()),
                    "is_good" : report.MK_good,
                    "defects_position" : report.MK_comment,
                    "defects_description" : report.MK_comment
                }
        case report_type.HT.name:
            res = { "tools" : tools,
                    # FIXME:Is it true?
                   "actual_max_pressure" : round(report.hardware.type.max_pressure, 2),
                   "is_good" : report.GI_preventor_good,
                    # FIXME: Which GI_*_sketch to print?
                    "sketch" : Reporter.get_image(session_db.scalars(select(Img.src).where(Img.id == report.GI_body_sketch_id)).one_or_none()),
                }
            
    session_db.connection().close()
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
    
@dataclasses.dataclass
class Report_Config:
    # (template_name, filename, parameters) 
    template: templates
    filename: str
    parameters: dict[str, str | None]
            
# Main part
def generate_config(report: Report, with_facsimile: bool, with_stamp: bool)->list[Report_Config]:
    rep_types: list[report_type] = list(report.report_types)    # type: ignore
    session_db = get_session()
    params_base: dict[str, Any] = {  
                                   "report_number" : f"{report.id}-",
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
                                    "facsimile" : Reporter.get_image(session_db.scalars(select(Img.src).where(Img.id == report.inspector.facsimile_id)).one_or_none()) if with_facsimile else None, 
                                    "with_stamp" : with_stamp
                                }
    session_db.connection().close()
    configs: list[Report_Config] = []
    for rep_type in rep_types:
        params = params_base | get_type_specific_params(report, rep_type)
        params['report_number'] = params['report_number'] + str(rep_type)
        filename = f'report_{report.id}_{str(rep_type)}.pdf'
        configs.append(Report_Config(template=templates[str(rep_type)], filename=filename, parameters=params))
    
    return configs


class Reporter:
    @staticmethod 
    def __mk_if_not_exist(path: os.PathLike):
        if not os.path.isdir(path):
            current_app.logger.info('Oops! I am gonna mkdir %s cause it does not exist.', path, exc_info=True)
            os.mkdir(path)
            
    root = os.path.dirname(os.path.abspath(__file__))
    storage_dir = config.reports_folder
    templates_dir = pathlib.PurePath(root, 'templates')
    __instance = None
    @staticmethod 
    def getInstance():
        """ Static access method. """
        if Reporter.__instance is None:
            current_app.logger.info('Reporter was created.', exc_info=True)
            return Reporter()
        return Reporter.__instance
    
    def __init__(self):
        if Reporter.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            Reporter.__instance = self
    
    @classmethod
    def get(cls, report_id: str | int, with_facsimile: bool, with_stamp: bool) -> pathlib.PurePath | None:
        """Generate report with report_id

        Parameters
        ----------
        report_id : str | int
            id in Reports table in the DB.
        with_facsimile: bool
            Generate with or without facsimile.
        with_stamp: bool
            Generate with or without stamp.

        Returns
        -------
        pathlib.PurePath | None
            path to a zip with report.
        """
        session_db = get_session()
        try:
            report = session_db.scalars(select(Report).where(Report.id == int(report_id))).one()
            try:
                current_app.logger.info('Creating report #%s for user #%s.', report_id, current_user.get_id(), exc_info=True) # type: ignore
                config = generate_config(report, with_facsimile=with_facsimile, with_stamp=with_stamp)
                _, res = cls.__create_report(current_user.get_id(), config, True) # type: ignore
                return res
            except FileNotFoundError as e:
                current_app.logger.critical('ALARM!!! %s', e, exc_info=True)
                return None
            finally:
                session_db.connection().close()
        except (NoResultFound, MultipleResultsFound) as e:
            current_app.logger.error('Report_id is wrong: %s', e, exc_info=True)
            session_db.connection().close()
            return None 
        finally:
            session_db.connection().close()
    
    @classmethod
    def get_many(cls, report_ids: list[str | int], with_facsimile: bool, with_stamp: bool) -> pathlib.PurePath:
        """Generate reports for ids in report_ids.

        Parameters
        ----------
        report_ids : list[str  |  int]
            list of ids.
        with_facsimile: bool
            Generate with or without facsimile.
        with_stamp: bool
            Generate with or without stamp.

        Returns
        -------
        pathlib.PurePath | None
            path to a zip with reports.
        """
        reports_path = [cls.get(id, with_facsimile=with_facsimile, with_stamp=with_stamp) for id in report_ids]
        cls.__mk_if_not_exist(pathlib.PurePath(cls.storage_dir, 'request'))
        output_zip = pathlib.PurePath(cls.storage_dir, 'request', f'{uuid.uuid1()}.zip')
        current_app.logger.info('Generated reports  and now will pack it to one zip file.')
        with ZipFile(output_zip, 'w') as report_zip:
            for rep_path in reports_path:
                if rep_path is not None:
                    report_zip.write(rep_path, arcname=rep_path.name) 
        current_app.logger.info('Successfully packed reports zip to one zip file.')
        return output_zip
           
    @classmethod    
    def get_image(cls, image: img | str | os.PathLike | None) -> str | None:
        weatherford_logo = None
        if image is None:
            current_app.logger.info('No images cause i did not find file None was passed', exc_info=True)
            return None
        filename: pathlib.PurePath = pathlib.PurePath(cls.templates_dir, image.value) if type(image) is img else pathlib.PurePath(str(image))
        if not os.path.isfile(filename):
            current_app.logger.warning('No images cause i did not find file %s', filename, exc_info=True)
            return None
        with open(filename, "rb") as image_file:
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
            raise FileNotFoundError("No folder with templates. It's gone!!!")
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
        stamp = cls.get_image(img.STAMP) if config[0].parameters.get('with_stamp') is True else None
        outputs: list[tuple[templates, pathlib.PurePath]] = []
        
        def task(config_tuple):
            template_name, filename, params = config_tuple
            template = env.get_template(template_name.value)
            html_file_path = pathlib.PurePath(cls.storage_dir, 'html', folder_name, f'report_{template_name.value}')
            with open(html_file_path, 'w') as html_file:
                html_file.write(template.render(weatherford_logo=logo, stamp=stamp, **params))
        
            output_file_path = pathlib.PurePath(cls.storage_dir, 'pdf', folder_name, filename)
            HTML(str(html_file_path)).write_pdf(str(output_file_path))
            return (template_name, output_file_path)
        
        with ThreadPool() as pool:
            for output in pool.imap(task, list(map(lambda x: dataclasses.astuple(x), config))):
                outputs.append(output)
            
        output_zip = None
        if zip_files:
            output_zip = pathlib.PurePath(cls.storage_dir, 'pdf', folder_name, f'{request_id}.zip')
            with ZipFile(output_zip, 'w') as report_zip:
                for _, output in outputs:
                    report_zip.write(output, arcname=output.name)
        return outputs, output_zip
    