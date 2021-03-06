from PIL import Image, ImageDraw, ImageFont
from hammerhal.text_drawer import FontFinder
import inspect


class Enum:
    @classmethod
    def find_value(cls, key):
        if (isinstance(key, str)):
            _members = inspect.getmembers(cls)
            for _member in _members:
                if (_member[0] == key):
                    # print("{0} is {1}!".format(*_member))
                    return _member[1]

            # print("{0} not found".format(key))
            return None

        else:
            # print("{0} is not a string; returning it")
            return key

class TextDrawer:

    class CapitalizationModes(Enum):
        Normal = 1
        UpperCase = 2
        AllCaps = 2
        LowerCase = 3
        NoCaps = 3
        Capitalize = 4
        SmallCaps = 5

    class TextAlignment(Enum):
        Left = 1
        Top = 1
        Center = 2
        Right = 3
        Bottom = 3
        Justify = 4

    __drawer = None
    __font_finder = None

    __current_font_size = None
    __current_font_family = None
    __current_font_filepath = None
    __bold = None
    __italic = None

    __current_text_horizontal_alignment = None
    __current_text_vertical_alignment = None
    __current_text_capitalization = None
    __font_base = None

    character_width_scale  = None
    text_character_separator_scale = None
    text_vertical_space_scale = None
    text_paragraph_vertical_space = None
    text_space_scale = None

    color = None

    def __init__(self, im:Image.Image, font_nane=None, font_size=None, color=None, bold=None, italic=None, font_finder=None):
        if (font_finder):
            self.__font_finder = font_finder
        else:
            if (not TextDrawer.__font_finder):
                TextDrawer.__font_finder = FontFinder()
            self.__font_finder = TextDrawer.__font_finder

        self.set_font(font_name=font_nane, font_size=font_size, color=color, bold=bold, italic=italic)
        self.__drawer = ImageDraw.ImageDraw(im)

    def set_font(self, font_name=None, font_size=None, color=None, bold=None, italic=None, horizontal_alignment=None, vertical_alignment=None, character_width_scale=None, space_scale=None, vertical_space_scale=None, paragraph_vertical_space=None, character_separator_scale=None, capitalization=None):
        self.__current_font_size = int(font_size or self.__current_font_size or 10)
        self.__current_font_family = font_name or self.__current_font_family or 'Times New Roman'

        if (not bold is None):
            self.__bold = bold
        else:
            self.__bold = self.__bold or False

        if (not italic is None):
            self.__italic = italic or self.__italic or False
        else:
            self.__italic = self.__italic or False

        if not (font_name is None and bold is None and italic is None):
            _test_font = None
            if (font_name or self.__current_font_family is None):
                _test_font = self.__font_finder.find_font_file_by_filename(font_name)
                if (_test_font):
                    self.__current_font_family = None

            if not (_test_font):
                _test_font = self.__font_finder.find_font_file_by_fontname(family_name=self.__current_font_family, bold=self.__bold, italic=self.__italic)
                if (_test_font):                    
                    self.__current_font_family = font_name
                    
            if not (_test_font):
                raise FileNotFoundError("Requested font ({font_family}{bold}{italic}) is not installed".format(font_family=self.__current_font_family, bold=", Bold" if self.__bold else '', italic=", Italic" if self.__italic else ''))

            self.__current_font_filepath = _test_font
        else:
            self.__current_font_filepath = self.__current_font_filepath or 'times.ttf'
        self.__font_base = ImageFont.truetype(font=self.__current_font_filepath, size=self.__current_font_size, encoding='unic')

        self.__current_text_vertical_alignment = TextDrawer.TextAlignment.find_value(vertical_alignment) or self.__current_text_vertical_alignment or TextDrawer.TextAlignment.Top
        self.__current_text_horizontal_alignment = TextDrawer.TextAlignment.find_value(horizontal_alignment) or self.__current_text_horizontal_alignment or TextDrawer.TextAlignment.Left
        self.__current_text_capitalization = TextDrawer.CapitalizationModes.find_value(capitalization) or self.__current_text_capitalization or TextDrawer.CapitalizationModes.Normal

        if (not space_scale is None):
            self.text_space_scale = space_scale
        else:
            self.text_space_scale = self.text_space_scale or 1.0

        if (not vertical_space_scale is None):
            self.text_vertical_space_scale = vertical_space_scale
        else:
            self.text_vertical_space_scale = self.text_vertical_space_scale or 0.0

        if (not paragraph_vertical_space is None):
            self.text_paragraph_vertical_space = paragraph_vertical_space
        else:
            self.text_paragraph_vertical_space = self.text_paragraph_vertical_space or 0

        if (not character_separator_scale is None):
            self.text_character_separator_scale = character_separator_scale
        else:
            self.text_character_separator_scale = self.text_character_separator_scale or 0.0

        if (not character_width_scale is None):
            self.character_width_scale = character_width_scale
        else:
            self.character_width_scale = self.character_width_scale or 1.0

        self.color = color or self.color or 'white'

    def get_font(self):
        result_dict = \
        {
            'font_name': self.__current_font_family,
            'font_size': self.__current_font_size,
            'color': self.color,
            'bold': self.__bold,
            'italic': self.__italic,
            'horizontal_alignment': self.__current_text_horizontal_alignment,
            'vertical_alignment': self.__current_text_vertical_alignment,
            'character_width_scale': self.character_width_scale,
            'space_scale': self.text_space_scale,
            'vertical_space_scale': self.text_paragraph_vertical_space,
            'paragraph_vertical_space': self.text_paragraph_vertical_space,
            'character_separator_scale': self.text_character_separator_scale,
            'capitalization': self.__current_text_capitalization,
        }

        return result_dict

    def print_line(self, position, text:str):
        self.__print(position, text, real_print=True)

    def print_in_region(self, region, text:str, offset_borders:bool=True):
        return self.__print_in_region(region, text, offset_borders, real_print=True)

    def get_text_size(self, region, text:str, offset_borders:bool=True):
        return self.__print_in_region(region, text, offset_borders, real_print=False)

    def __print_in_region(self, region, text:str, offset_borders, real_print):
        if (offset_borders):
            x, y, w, h = region
        else:
            x, y, x2, y2 = region
            w = x2 - x
            h = y2 - y

        max_width = 0
        space_width, _ = self.__print(None, ' ', real_print=False)
        _, line_height = self.__print(None, 'LINE HEIGHT', real_print=False)
        paragraphs = []
        for paragraph in text.split('\n'):
            _horizontal_alignment = self.__current_text_horizontal_alignment
            paragraph_words = []
            paragraph_lines_width = 0
            words = paragraph.split()
            lines = []
            line = { 'words': [], 'width': 0, 'horizontal_alignment': _horizontal_alignment }
            for word in words:
                if (word.startswith('$$')):
                    if (word == '$$HA_L'):
                        _horizontal_alignment = TextDrawer.TextAlignment.Left
                        line['horizontal_alignment'] = _horizontal_alignment
                        continue
                    if (word == '$$HA_C'):
                        _horizontal_alignment = TextDrawer.TextAlignment.Center
                        line['horizontal_alignment'] = _horizontal_alignment
                        continue
                    if (word == '$$HA_R'):
                        _horizontal_alignment = TextDrawer.TextAlignment.Right
                        line['horizontal_alignment'] = _horizontal_alignment
                        continue
                    if (word == '$$HA_J'):
                        _horizontal_alignment = TextDrawer.TextAlignment.Justify
                        line['horizontal_alignment'] = _horizontal_alignment
                        continue
                    raise KeyError("Unsupported operand: {word}".format(word=word))

                paragraph_words.append(word)
                paragraph_total_width, _ = self.__print(None, ' '.join(paragraph_words), real_print=False)
                paragraph_total_width -= len(lines) * space_width
                test_width = paragraph_total_width - paragraph_lines_width

                if (not w or test_width <= w):
                    line['width'] = test_width
                    line['words'].append(word)
                else:
                    lines.append(line)
                    word_width, _ = self.__print(None, word, real_print=False)
                    paragraph_lines_width = paragraph_total_width - word_width - space_width
                    line = { 'words': [ word ], 'width': word_width, 'horizontal_alignment': _horizontal_alignment }

                if (max_width < line['width']):
                    max_width = line['width']

            lines.append(line)
            paragraphs.append(lines)

        num_lines = sum(len(paragraph) for paragraph in paragraphs)
        total_height = int(num_lines * (1 + self.text_vertical_space_scale) * line_height + self.text_paragraph_vertical_space * (len(paragraphs) - 1))

        if (real_print):
            if (self.__current_text_vertical_alignment == TextDrawer.TextAlignment.Bottom):
                _y = y + h - total_height
            elif (self.__current_text_vertical_alignment == TextDrawer.TextAlignment.Center):
                _y = y + (h - total_height) // 2
            else:
                _y = y

            for paragraph in paragraphs:
                for i in range(len(paragraph)):
                    line = paragraph[i]
                    last_line = (i + 1 == len(paragraph))

                    new_space_width = space_width
                    if (line['horizontal_alignment'] == TextDrawer.TextAlignment.Right):
                        _x = x + w - line['width']
                    elif (line['horizontal_alignment'] == TextDrawer.TextAlignment.Center):
                        _x = x + (w - line['width']) // 2
                    elif (line['horizontal_alignment'] == TextDrawer.TextAlignment.Justify and not last_line and len(line['words']) > 0):
                        _x = x
                        num_spaces = len(line['words']) - 1
                        if (num_spaces > 0):
                            new_space_width = space_width + (w - line['width']) / num_spaces
                    else:
                        _x = x

                    self.__print((_x, _y), ' '.join(line['words']), real_print=True, restricted_space_width=new_space_width)
                    _y += (1 + self.text_vertical_space_scale) * self.__current_font_size
                _y += self.text_paragraph_vertical_space

        return max_width, total_height


    def __print(self, position, text: str, real_print:bool, restricted_space_width=None, debug_console_print:bool=False):
        x, y = position or (0, 0)
        max_height = 0



        _text = text
        if (self.__current_text_capitalization == TextDrawer.CapitalizationModes.UpperCase):
            _text = _text.upper()
        elif (self.__current_text_capitalization == TextDrawer.CapitalizationModes.LowerCase):
            _text = _text.lower()
        elif (self.__current_text_capitalization == TextDrawer.CapitalizationModes.Capitalize):
            _text = ' '.join(_word.capitalize() for _word in _text.split(' '))

        original_bold = self.__bold
        original_italic = self.__italic
        _continue = False

        if (self.__current_text_capitalization == TextDrawer.CapitalizationModes.SmallCaps):
            # _, _new_size = self._drawer.textsize(_char, font=_font)
            _new_size = int(self.__current_font_size * 0.75)
            _char = 'ixz'
            _char = _char.upper()

            _font = self.__font_base
            _small_caps_font = ImageFont.truetype(font=self.__current_font_filepath, size=_new_size, encoding='unic')
            _, _y1 = self.__drawer.textsize(_char, font=_small_caps_font)
            _, _y2 = self.__drawer.textsize(_char, font=_font)
            _small_caps_dy = _y2 - _y1

        for i in range(len(_text)):
            if (_continue):
                _continue = False

                if (self.__current_text_capitalization == TextDrawer.CapitalizationModes.SmallCaps):
                    # _, _new_size = self._drawer.textsize(_char, font=_font)
                    _new_size = int(self.__current_font_size * 0.75)
                    _char = 'ixz'
                    _char = _char.upper()

                    _font = self.__font_base
                    _small_caps_font = ImageFont.truetype(font=self.__current_font_filepath, size=_new_size, encoding='unic')
                    _, _y1 = self.__drawer.textsize(_char, font=_font)
                    _, _y2 = self.__drawer.textsize(_char, font=_small_caps_font)
                    _small_caps_dy = _y2 - _y1

                continue
            if (i + 2 <= len(_text)):
                if(_text[i:i+2] == '__'):
                    self.set_font(italic=not self.__italic)
                    _continue = True
                    continue
                if (_text[i:i + 2] == '**'):
                    self.set_font(bold=not self.__bold)
                    _continue = True
                    continue

            _char = _text[i]; _x = int(x); _y = int(y); _font = self.__font_base

            if (self.__current_text_capitalization == TextDrawer.CapitalizationModes.SmallCaps and _char != _char.upper()):
                _char = _char.upper()
                _y += _small_caps_dy
                _font = _small_caps_font
            w, h = self.__drawer.textsize(_char, font=_font)
            if (real_print):
                if (debug_console_print):
                    print(text[i], end='')
                self.__drawer.text((_x, _y), _char, self.color, font=_font)
            if (_char == ' '):
                if (restricted_space_width):
                    x += restricted_space_width
                else:
                    x += w * self.text_space_scale
            else:
                x += w + self.text_character_separator_scale * self.__current_font_size
            if (max_height < h):
                max_height = h

        initial_x, _ = position or (0, 0)
        if (debug_console_print):
            print('', end='\n')
        self.set_font(bold=original_bold, italic=original_italic)
        return (x - initial_x, max_height)
