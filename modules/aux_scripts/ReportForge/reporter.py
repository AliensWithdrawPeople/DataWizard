from enum import Enum
from genericpath import isdir
from zipfile import ZipFile
from jinja2 import Environment, FileSystemLoader
import os
import pathlib
import base64

import sys
# FIXME: Change path to GTK3.
gtk_path = pathlib.PurePath("C:/Program Files/GTK3-Runtime Win64/bin")
if not str(gtk_path) in sys.path: 
    sys.path.append(str(gtk_path))
from weasyprint import HTML

class templates(Enum):
    VCM = 'VCM.html'
    UTM = 'UTM.html'
    
class img(Enum):
    LOGO = 'Weatherford_logo.png'
    STAMP = 'Weatherford_stamp.png'
    SIGNATURE = 'ivanov_sign.png'

root = os.path.dirname(os.path.abspath(__file__))

def get_image(image_type: img | str) -> str | None:
    weatherford_logo = None
    filename = image_type.value if type(image_type) is img else str(image_type)
    with open(pathlib.PurePath(root, 'templates', filename), "rb") as image_file:
        weatherford_logo = 'data:image/png;base64,' + base64.b64encode(image_file.read()).decode()
    return weatherford_logo

def mk_if_not_exist(path: os.PathLike):
    if not os.path.isdir(path):
        os.mkdir(path)

def get_report(id: int | str, config: list[tuple[templates, str, dict[str, str]]], zip_files: bool) -> pathlib.PurePath | list[pathlib.PurePath]:
    """_summary_

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
    
    # FIXME: Change tmp storage directory.
    templates_dir = pathlib.PurePath(root, 'templates')
    if not os.path.isdir(pathlib.PurePath(root, 'html')):
        # TODO: Log that 'templates folder' went MIA.
        raise FileNotFoundError("No templates folder. It's gone!!!")
    env = Environment( loader = FileSystemLoader(templates_dir))
    html_folder = pathlib.PurePath(root, 'html', str(id))
    pdf_folder = pathlib.PurePath(root, 'pdf', str(id))
    mk_if_not_exist(pathlib.PurePath(root, 'html'))
    mk_if_not_exist(pathlib.PurePath(root, 'pdf'))
    mk_if_not_exist(html_folder)
    mk_if_not_exist(pdf_folder)
    
    logo = get_image(img.LOGO)
    stamp = get_image(img.STAMP)
    outputs: list[pathlib.PurePath] = []
    for template_name, filename, params in config:
        template = env.get_template(template_name.value)
        html_file_path = pathlib.PurePath(root, 'html', str(id), f'report_{template_name.value}')
        with open(html_file_path, 'w') as html_file:
            html_file.write(template.render(weatherford_logo=logo, stamp=stamp, **params))
    
        output_file_path = pathlib.PurePath(root, 'pdf', str(id), filename)
        HTML(str(html_file_path)).write_pdf(str(output_file_path))
        outputs.append(output_file_path)

    if zip_files:
        output_zip = pathlib.PurePath(root, 'pdf', f'{id}.zip')
        with ZipFile(output_zip, 'w') as myzip:
            for output in outputs:
                myzip.write(output, arcname=output.name)
        return output_zip
    
    return outputs
    
    
params_VCM = {"title_add" : 'НК-061А0028 (22.02.25)',
                    "report_number" : "03604-VCM",
                    "date" : "30 августа 2023 г.",
                    "object_name" : 'Кран пробковый 3x3" 1502 MxF Master Valve',
                    "reg_number" : "WFT MV 12502", 
                    "serial_number" : "0119", 
                    "manufacturer" : "Омега", 
                    "batch_number" : "ИМЗ - 08.330.99", 
                    "number_1C" : "-", 
                    "location_and_kit_number" : 'БПО Ноябрьского филиала ООО "Везерфорд"  г.Ноябрьск Склад', 
                    "tools" : ["Лупаизмерительная ЛИ-3-10 No230236", 'Линейка измерительная "Калиброн" No3158 от 18.04.23 г.', 'Штангенциркуль "Калиброн" 0-150 No102201991 от 18.04.23 г.', 
                            'Набор шаблонов  "Etalon" No 1 No2021491 от 18.04.23 г.', 'Набор шаблонов  "Etalon" No 3 No20201487 от 18.04.23 г.', 
                            'Шаблон универсальный сварщика УШС–3 No0783 от 18.04.23  г.', 'Магнитометр переносной ИМАГ-400Ц No2598 от 15.01.23 г.',],
                    "ambient_temp" : "+14",
                    "general_light" : "541",
                    "surf_light" : "1890",
                    "executor_position" : 'Специалист II уровня/Specialist of the 2nd level',
                    "identification" : '0041-2871',
                    "executor_name" : 'В.Р. Иванов',
                    "facsimile" : get_image(img.SIGNATURE)
                }
params_UTM = {"title_add" : 'НК-061А0028 (22.02.25)',
                    "report_number" : "03604-VCM",
                    "date" : "30 августа 2023 г.",
                    "object_name" : 'Кран пробковый 3x3" 1502 MxF Master Valve',
                    "reg_number" : "WFT MV 12502", 
                    "serial_number" : "0119", 
                    "manufacturer" : "Омега", 
                    "batch_number" : "ИМЗ - 08.330.99", 
                    "number_1C" : "-", 
                    "location_and_kit_number" : 'БПО Ноябрьского филиала ООО "Везерфорд"  г.Ноябрьск Склад', 
                    "tools" : ["Толщиномер УТ-11 ЛУЧ  №0518 от 20.03.23 г.", "Преобразователь ПЭП П112-5-10/2-Т-003 №5404 от 19.03.23 г.", "Номинальная частота контроля: 5 МГц; СОП №7448."],
                    "ambient_temp" : "+14",
                    "general_light" : "541",
                    "surf_light" : "1890",
                    "executor_position" : 'Специалист II уровня/Specialist of the 2nd level',
                    "identification" : '0041-2871',
                    "executor_name" : 'В.Р. Иванов',
                    "facsimile" : get_image(img.SIGNATURE),
                    
                    "ts" : [21.0] + 6 * [None],
                    "minimal_ts" : [10.7] + 6 * [None],
                    "sketch" : get_image('stock_sketch.png')
                }

import time
start = time.perf_counter()
# get_report(1, [(templates.VCM, 'test_VCM.pdf', params_VCM)], zip_files = False)


get_report(1, [(templates.VCM, 'test_VCM.pdf', params_VCM), (templates.UTM, 'test_UTM.pdf', params_UTM),], zip_files = True)
end = time.perf_counter()
print(end - start)