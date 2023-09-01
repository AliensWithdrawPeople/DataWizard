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

root = os.path.dirname(os.path.abspath(__file__))

def get_logo() -> str | None:
    weatherford_logo = None
    with open(pathlib.PurePath(root, 'html', 'Weatherford_Logo_small.png'), "rb") as image_file:
        weatherford_logo = 'data:image/png;base64,' + base64.b64encode(image_file.read()).decode()
    return weatherford_logo

def mk_if_not_exist(path: os.PathLike):
    if not os.path.isdir(path):
        os.mkdir(path)

def get_report(id: int | str, config: list[tuple[templates, str]], zip_files: bool, **kwargs) -> pathlib.PurePath | list[pathlib.PurePath]:
    """_summary_

    id : int | str
        user id.
    config : list[tuple[templates, str]]
        list of (template_name, filename) tuples.
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
    
    weatherford_logo = get_logo()
    outputs = []
    for template_name, filename in config:
        template = env.get_template(template_name.value)
        html_file_path = pathlib.PurePath(root, 'html', str(id), f'report_{template_name.value}')
        with open(html_file_path, 'w') as html_file:
            html_file.write(template.render(weatherford_logo=weatherford_logo, **kwargs))
    
        output_file_path = pathlib.PurePath(root, 'pdf', str(id), filename)
        # TODO: Add margin.
        HTML(str(html_file_path)).write_pdf(str(output_file_path))
        outputs.append(output_file_path)

    if zip_files:
        output_zip = pathlib.PurePath(root, 'pdf', f'{id}.zip')
        with ZipFile(output_zip, 'w') as myzip:
            for output in outputs:
                myzip.write(output)
        return output_zip
    
    return outputs
    
    
template_params = {"title_add" : 'НК-061А0028 (22.02.25)',
                    "report_number" : "03604",
                    "date" : "30 августа 2023 г.",
                    "object_name" : 'Кран пробковый 3x3" 1502 MxF Master Valve',
                    "reg_number" : "WFT MV 12502", 
                    "serial_number" : "0119", 
                    "manufacturer" : "Омега", 
                    "batch_number" : "ИМЗ - 08.330.99", 
                    "number_1C" : "-", 
                    "location_and_kit_number" : 'БПО Ноябрьского филиала ООО "Везерфорд"  г.Ноябрьск Склад', 
                    "standard" : "3997-00.001 МУ., ГОСТ 34004-2016., ГОСТ Р ЕН 13018-2014., РД 03-606-03., 0398.00.000 МУ.,  РД 03-606-03., СТО 9701105632-003-2021., ГОСТ Р ИСО 17637-2014.",
                    "tools" : ["Лупаизмерительная ЛИ-3-10 No230236", 'Линейка измерительная "Калиброн" No3158 от 18.04.23 г.', 'Штангенциркуль "Калиброн" 0-150 No102201991 от 18.04.23 г.', 
                            'Набор шаблонов  "Etalon" No 1 No2021491 от 18.04.23 г.', 'Набор шаблонов  "Etalon" No 3 No20201487 от 18.04.23 г.', 
                            'Шаблон универсальный сварщика УШС–3 No0783 от 18.04.23  г.', 'Магнитометр переносной ИМАГ-400Ц No2598 от 15.01.23 г.',],
                    "ambient_temp" : "+14",
                    "general_light" : "541",
                    "surf_light" : "1890",
                    "executor_position" : 'Специалист II уровня/Specialist of the 2nd level',
                    "identification" : '0041-2871',
                    "executor_name" : 'В.Р. Иванов',
                    "stamp" : get_logo(),
                    "facsimile" : get_logo()
                }
import time
start = time.perf_counter()
get_report(1, [(templates.VCM, 'test.pdf')], zip_files = False, **template_params)
end = time.perf_counter()
print(end - start)