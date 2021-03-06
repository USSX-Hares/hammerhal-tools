import json, os.path, glob
import jsonschema.exceptions
from jsonschema import validate
from PIL import Image

from yn_input import yn_input
from hammerhal import ConfigLoader
from logging import getLogger
logger = getLogger('hammerhal.compilers.compiler_base')

class CompilerBase():

    compiler_type = None
    modules = None

    schema_path = None
    raw_directory = None
    sources_directory = None
    output_directory = None
    output_name = None

    raw = None
    compiled = None
    compiled_modules = None

    def __init__(self):
        self.schema_path = "{directory}{type}.json".format(directory=ConfigLoader.get_from_config('schemasDirectory', 'compilers'), type=self.compiler_type)
        self.raw_directory = "{rawRoot}{rawOffset}".format(rawRoot=ConfigLoader.get_from_config('rawDirectoryRoot'), rawOffset=ConfigLoader.get_from_config('compilerTypeSpecific/{type}/rawDirectory'.format(type=self.compiler_type), 'compilers'))
        self.output_directory = "{rawRoot}{rawOffset}".format(rawRoot=ConfigLoader.get_from_config('outputDirectoryRoot', 'compilers'), rawOffset=ConfigLoader.get_from_config('compilerTypeSpecific/{type}/outputDirectory'.format(type=self.compiler_type), 'compilers'))
        self.sources_directory = ConfigLoader.get_from_config('sourcesDirectory', 'compilers')

        if (self.modules):
            self.compiled_modules = [] * len(self.modules)
            for _iter in self.modules:
                _module_type = None
                if (isinstance(_iter, type)):
                    _module_type = _iter
                    pass
                elif (isinstance(_iter, tuple)):
                    _module_type = _iter[0]
                    pass
                else:
                    raise TypeError("Module should be either type or tuple")

    def search(self):
        return glob.glob(self.raw_directory + "*.json")

    def find(self, name):
        filename = name
        if (os.path.isfile(filename)):
            return filename

        filename = "{directory}{name}.json".format(directory=self.raw_directory, name=name)
        if (os.path.isfile(filename)):
            return filename

        for filename in self.search():
            try:
                _file = open(filename)
                _json = json.load(_file)
                _file.close()

                _name = _json.get('name', None)
                if (_name and isinstance(_name, str) and name.lower() in _name.lower()):
                    message = "{type} found - {filename}:\n  {name}{subtitle}".format \
                    (
                        type = self.compiler_type.capitalize(),
                        filename = filename,
                        name = _name,
                        subtitle = " ({subtitle})".format(**_json) if (_json.get('subtitle', None)) else '',
                    )
                    print(message)
                    if (yn_input('Is it what you need?')):
                        return filename

            except (OSError, FileNotFoundError, json.JSONDecodeError):
                pass

        return None

    def open(self, name):
        filename = self.find(name)
        if (not filename):
            logger.error("Cannot find {type}: '{name}'".format(type=self.compiler_type, name=name))
            return None
        logger.info("Reading '{filename}'...".format(filename=filename))
        file = open(filename)
        raw = json.load(file)
        file.close()

        filename = self.schema_path
        logger.debug("Reading '{filename}'...".format(filename=filename))
        file = open(filename)
        schema = json.load(file)
        file.close()

        try:
            logger.debug("Validating {name}...".format(name=name))
            validate(raw, schema)
        except jsonschema.exceptions.ValidationError as e:
            logger.error("Raw file is not valid: {msg}".format(msg=e.message))
            self.raw = None
        else:
            logger.debug("Raw file is valid")
            self.raw = raw

        return self.raw

    def prepare_base(self):
        name_template = ConfigLoader.get_from_config('compilerTypeSpecific/{type}/baseNameTemplate'.format(type=self.compiler_type), 'compilers')
        name = name_template
        if ("{weaponsCount}" in name):
            name = name.replace('{weaponsCount}', str(len(self.raw['weapons'])))

        filepath = "{directory}{name}".format(directory=self.sources_directory, name=name)
        if (not os.path.isfile(filepath)):
            additional = ""
            if ("{weaponsCount}" in name_template):
                additional += " with proper number of weapons - {weaponsCount}".format(weaponsCount=len(self.raw['weapons']))
            logger.error("Cannot load {type} card template{additional}: '{filepath}'".format(type=self.compiler_type, filepath=filepath, additional=additional))
            return None

        base = Image.open(filepath)
        logger.info("Base prepared")
        return base

    def compile(self):
        base = self.prepare_base()
        if (not base):
            return None

        if not (self.compile_modules(base)):
            return None

        self.compiled = base
        logger.info("{type} compiled!".format(type=self.compiler_type.capitalize()))
        return self.compiled

    def compile_modules(self, base):
        self.compiled_modules = dict()

        for i, _ in enumerate(self.modules):
            try:
                _module = self.compile_module(i)
            except:
                logger.error("Error while compiling the module #{i}: {module}".format(i=i, module=self.modules[i]))
                return False
            else:
                _module.insert(base)

        return True

    def compile_module(self, index):
        module = self.modules[index]

        _module_type = None
        _module_args = None
        if (isinstance(module, type)):
            _module_type = module
        elif (isinstance(module, tuple)):
            _module_type = module[0]
            if (len(module) > 1):
                if (len(module) == 2 and isinstance(module[1], dict)):
                    _module_args = module[1]
                else:
                    _module_args = module[1:]
        else:
            raise TypeError("Module should be either type or tuple")

        _args = _module_args or dict()
        module_object = _module_type(self, index, **_args)
        self.compiled_modules[index] = module_object.compile()
        return module_object

    def save(self, forced_width=None):
        if (not self.compiled):
            logger.error("Could not save not compiled result")
            return None

        name = self.output_name or self.raw.get('name', None)
        if (not name):
            logger.error("Could find proper name")
            return None

        _image = self.compiled
        if (forced_width):
            _estimated_width = forced_width

            _actual_width = _image.width
            _actual_height = _image.height
            _image = _image.resize((int(_estimated_width), int(_estimated_width / _actual_width * _actual_height)), Image.ANTIALIAS)

        filename = "{directory}{name}.png".format(directory=self.output_directory, name=name)
        try:
            logger.info("Saving compiled file: '{filename}'".format(filename=filename))
            _image.save(filename)
        except:
            logger.exception("Error while saving file '{filename}'".format(filename=filename))
            return None
        else:
            return filename

    def insert_table \
    (
        self, vertical_columns, top, cell_height, data,
        body_row_template, body_text_drawer, body_row_interval, body_capitalization=None, body_bold=None, body_italic=None,
        header_row=None, header_text_drawer=None, header_row_interval=None, header_capitalization=None,header_bold=None, header_italic=None,
    ):
        if (top < 0):
            direction = -1
            indirect = True
        else:
            direction = 1
            indirect = False

        total_height = 0
        y1 = top
        y2 = cell_height and (top + cell_height)

        if (header_row and not indirect):
            y1, y2, total_height = self.__print_header_row \
            (
                vertical_columns=vertical_columns, y1=y1, y2=y2, total_height=total_height,
                body_row_template=body_row_template, body_text_drawer=body_text_drawer, body_row_interval=body_row_interval, body_capitalization=body_capitalization, body_bold=body_bold, body_italic=body_italic,
                header_row=header_row, header_text_drawer=header_text_drawer, header_row_interval=header_row_interval, header_capitalization=header_capitalization, header_bold=header_bold, header_italic=header_italic,
            )

        text_drawer = body_text_drawer
        _font = text_drawer.get_font()
        text_drawer.set_font(capitalization=body_capitalization, bold=body_bold, italic=body_italic)

        dy = body_row_interval
        _data = reversed(data) if (indirect) else data
        for data_row in _data:
            table_row = body_row_template
            _h = self.__print_table_row(y1=y1, y2=y2, text_drawer=text_drawer, vertical_columns=vertical_columns, table_row=table_row, data_row=data_row)
            y1 += _h + dy
            total_height += _h + dy
            if (y2):
                y2 += _h + dy

        logger.debug("Restoring font {font}".format(font=_font))
        text_drawer.set_font(**_font)

        if (header_row and indirect):
            y1, y2, total_height = self.__print_header_row \
                    (
                    vertical_columns=vertical_columns, y1=y1, y2=y2, total_height=total_height,
                    body_row_template=body_row_template, body_text_drawer=body_text_drawer, body_row_interval=body_row_interval, body_capitalization=body_capitalization, body_bold=body_bold, body_italic=body_italic,
                    header_row=header_row, header_text_drawer=header_text_drawer, header_row_interval=header_row_interval, header_capitalization=header_capitalization, header_bold=header_bold, header_italic=header_italic,
                )

        return total_height

    def __print_header_row \
    (
        self, vertical_columns, y1, y2, total_height,
        body_row_template, body_text_drawer, body_row_interval, body_capitalization=None, body_bold=None, body_italic=None,
        header_row=None, header_text_drawer=None, header_row_interval=None, header_capitalization=None,header_bold=None, header_italic=None,
    ):
        text_drawer = header_text_drawer or body_text_drawer

        _font = text_drawer.get_font()
        text_drawer.set_font(capitalization=header_capitalization, bold=header_bold, italic=header_italic)

        dy = header_row_interval or body_row_interval
        data_row = { }
        table_row = header_row
        _h = self.__print_table_row(y1=y1, y2=y2, text_drawer=text_drawer, vertical_columns=vertical_columns, table_row=table_row, data_row=data_row)
        y1 += _h + dy
        total_height += _h + dy
        if (y2):
            y2 += _h + dy

        logger.debug("Restoring font {font}".format(font=_font))
        text_drawer.set_font(**_font)
        return y1, y2, total_height

    def __print_table_row(self, y1, y2, text_drawer, vertical_columns, table_row, data_row):
        max_h = 0
        for i, _cell in enumerate(table_row):
            x1 = vertical_columns[i]
            x2 = vertical_columns[i + 1]
            _, _h = text_drawer.get_text_size((x1, y1, x2, y2), _cell.format(**data_row), offset_borders=False)
            if (max_h < _h):
                max_h = _h

        _y1 = -y1 - max_h if (y1 < 0) else y1
        _y2 = (-y2 - max_h if (y2 < 0) else y2) if y2 else _y1 + max_h

        for i, _cell in enumerate(table_row):
            x1 = vertical_columns[i]
            x2 = vertical_columns[i + 1]

            text_drawer.print_in_region((x1, _y1, x2, _y2), _cell.format(**data_row), offset_borders=False)

        return max_h

    def insert_image_scaled(self, base_image, region, image_path, offset_borders=True):
        if (offset_borders):
            x, y, w, h = region
        else:
            x, y, x2, y2 = region
            w = x2 - x
            h = y2 - y

        logger.debug("Inserting image '{path}' to position {region} with scaling and reversed mask".format(path=image_path, region=region))
        image = Image.open(image_path)

        _estimated_width = w
        _estimated_height = h

        _actual_width = image.width
        _actual_height = image.height

        _width_scale = _estimated_width / _actual_width
        _height_scale = _estimated_height / _actual_height

        _new_scale = max(_width_scale, _height_scale)
        _image = image.resize((int(_new_scale * _actual_width), int(_new_scale * _actual_height)), Image.ANTIALIAS)

        _im_copy = base_image.copy()
        base_image.paste(_image, (x, y))
        base_image.paste(_im_copy, (0, 0), _im_copy)
        return base_image

    def get_image_size(self, image_path):
        image = Image.open(image_path)
        _w = image.width
        _h = image.height
        return _w, _h

    def insert_image_centered(self, base_image, position, image_path, offset_borders=True):
        x, y = position

        logger.debug("Inserting image '{path}' to position {position}".format(path=image_path, position=position))
        image = Image.open(image_path)
        _w = image.width
        _h = image.height

        _x = x - _w // 2; _y = y - _h // 2
        _image = image
        if (image.mode.endswith('A')):
            _image = image.convert(image.mode[:-1])
        base_image.paste(_image, (_x, _y), image)
        return _x, _y, _w, _h
