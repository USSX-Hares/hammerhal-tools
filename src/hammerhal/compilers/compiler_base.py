import json
import jsonschema.exceptions
from jsonschema import validate
from PIL import Image

from hammerhal import ConfigLoader
from hammerhal.text_drawer import TextDrawer
from logging import getLogger
logger = getLogger('hammerhal.compilers.compiler_base')

class CompilerBase():

    compiler_type = None
    schema_path = None
    raw_directory = None
    sources_directory = None
    output_directory = None
    output_name = None

    raw = None
    compiled = None

    def __init__(self):
        self.schema_path = "{directory}{type}.json".format(directory=ConfigLoader.get_from_config('schemasDirectory', 'compilers'), type=self.compiler_type)
        self.raw_directory = "{rawRoot}{rawOffset}".format(rawRoot=ConfigLoader.get_from_config('rawDirectoryRoot'), rawOffset=ConfigLoader.get_from_config('compilerTypeSpecific/{type}/rawDirectory'.format(type=self.compiler_type), 'compilers'))
        self.output_directory = "{rawRoot}{rawOffset}".format(rawRoot=ConfigLoader.get_from_config('outputDirectoryRoot', 'compilers'), rawOffset=ConfigLoader.get_from_config('compilerTypeSpecific/{type}/outputDirectory'.format(type=self.compiler_type), 'compilers'))
        self.sources_directory = ConfigLoader.get_from_config('sourcesDirectory', 'compilers')

    def search(self, name):
        # Temporary decision
        # TODO: Search files
        return "{directory}{name}.json".format(directory=self.raw_directory, name=name)

    def open(self, name):
        filename = self.search(name)
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
        except jsonschema.exceptions.ValidationError:
            logger.error("Raw file is not valid")
            self.raw = None
        else:
            logger.debug("Raw file is valid")
            self.raw = raw

        return self.raw

    def compile(self):
        raise NotImplementedError

    def save(self):
        if (not self.compiled):
            logger.error("Could not save not compiled result")
            return None

        name = self.output_name or self.raw.get('name', None)
        if (not name):
            logger.error("Could find proper name")
            return None

        filename = "{directory}{name}.png".format(directory=self.output_directory, name=name)
        try:
            logger.debug("Saving compiled file: '{filename}'".format(filename=filename))
            self.compiled.save(filename)
        except:
            logger.exception("Error while saving file '{filename}'".format(filename=filename))
            return None
        else:
            return filename

    def insert_table(self, vertical_columns, top, cell_height, data, body_row_template, body_text_drawer, body_row_interval, body_capitalization=None, header_row=None, header_text_drawer=None, header_row_interval=None, header_capitalization=None):
        y1 = top
        y2 = top + cell_height

        if (header_row):
            text_drawer = header_text_drawer or body_text_drawer
            text_drawer.set_font(capitalization=header_capitalization)
            dy = header_row_interval or body_row_interval
            data_row = {}
            table_row = header_row
            _h = self.__print_table_row(y1=y1, y2=y2, text_drawer=text_drawer, vertical_columns=vertical_columns, table_row=table_row, data_row=data_row)
            y1 += _h + dy
            y2 += _h + dy

        text_drawer = body_text_drawer
        text_drawer.set_font(capitalization=body_capitalization)
        dy = body_row_interval
        for data_row in data:
            table_row = body_row_template
            _h = self.__print_table_row(y1=y1, y2=y2, text_drawer=text_drawer, vertical_columns=vertical_columns, table_row=table_row, data_row=data_row)
            y1 += _h + dy
            y2 += _h + dy

    def __print_table_row(self, y1, y2, text_drawer, vertical_columns, table_row, data_row):
        for i, _cell in enumerate(table_row):
            x1 = vertical_columns[i]
            x2 = vertical_columns[i + 1]
            _, _h = text_drawer.print_in_region((x1, y1, x2, y2), _cell.format(**data_row), offset_borders=False)
        return _h

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

        result_image = base_image.copy()
        result_image.paste(_image, (x, y))
        result_image.paste(base_image, (0, 0), base_image)
        return result_image

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
        base_image.paste(image, (_x, _y), image)
        return _x, _y, _w, _h
