from PIL import Image
from logging import getLogger
from camel_case_switcher import dict_keys_camel_case_to_underscope
import threading
import datetime

from hammerhal import generator
if (generator.generator_supported):
    import time
    import System
    from System import Decimal as decimal

from hammerhal.config_loader import ConfigLoader
from hammerhal.text_drawer import TextDrawer
from hammerhal.compilers.compiler_error import CompilerError, CompilerWarning
from hammerhal.compilers.compiler_base import CompilerBase

class CompilerModuleBase:

    # These ones MUST be overwritten
    module_name = None

    # These ones CAN be overwritten
    human_readable_name = None
    update_timeout = 0
    update_delay = 0

    # These ones MUST NOT be overwritten
    index = None
    parent = None
    parent_type = None
    logger = None

    width = None
    height = None
    compiled = None

    update_function = None
    __update_requested = False
    __update_on_cooldown = False

    def __init__(self, parent:CompilerBase, index:int, **kwargs):
        self.parent = parent
        self.parent_type = parent.compiler_type
        self.index = index
        self.initialize(**kwargs)

        self.human_readable_name = self.human_readable_name or self.module_name.replace('_', ' ').capitalize()
        _logger_name = "hammerhal.compilers.{parentType}_compiler.{moduleName}_module".format \
        (
            parentType = self.parent_type,
            moduleName = self.module_name,
        )
        self.logger = getLogger(_logger_name)

        # Try config:
        path = 'compilerTypeSpecific/{parentType}/modules/{moduleName}'.format \
        (
            parentType = self.parent_type,
            moduleName = self.module_name,
        )
        if not (ConfigLoader.get_from_config(path, 'compilers')):
            message = "Module config not found: {parentType}/{moduleName}".format \
            (
                parentType = self.parent_type,
                moduleName = self.module_name,
            )

            self.logger.error(message)
            raise CompilerError(message)


    def initialize(self, **kwargs):
        pass

    def get_from_module_config(self, key):
        path = 'compilerTypeSpecific/{parentType}/modules/{moduleName}/{key}'.format \
        (
            parentType = self.parent_type,
            moduleName = self.module_name,
            key = key,
        )
        return ConfigLoader.get_from_config(path, 'compilers')

    def get_text_drawer(self, base:Image, font_prefix='font') -> TextDrawer:
        td = TextDrawer(base)
        font = self.get_from_module_config(font_prefix) or dict()
        font = dict_keys_camel_case_to_underscope(font)
        td.set_font(**font)
        return td


    def get_size(self):
        _width = self.get_from_module_config('width')
        _height = self.get_from_module_config('height')
        size = (_width, _height)
        return size

    def get_position(self):
        position = (self.get_from_module_config('positionX'), self.get_from_module_config('positionY'))
        return position

    def prepare(self):
        _size = self.get_size()
        base = Image.new('RGBA', _size, 0x00ffffff)
        self.width, self.height = _size
        return base

    def compile(self):
        _now = datetime.datetime.now()
        base = self.prepare()
        try:
            self._compile(base)
        except CompilerWarning as warn:
            self.logger.debug("Module {name} compiled with warnings. Time spent: {dt}ms".format(name=self.module_name, dt=(datetime.datetime.now() - _now).total_seconds() * 1000))
            self.logger.warning(warn)
            thr = threading.Thread(target=self._on_warn, args=(warn,), kwargs={ })
            thr.start()

        else:
            self.logger.debug("Module {name} compiled. Time spent: {dt}ms".format(name=self.module_name, dt=(datetime.datetime.now() - _now).total_seconds() * 1000))

        self.compiled = base
        return base
    def _compile(self, base:Image):
        raise NotImplementedError

    def insert(self, parent_base:Image.Image):
        _x, _y = self.get_position()
        if (_y < 0):
            _y = parent_base.height + _y - self.compiled.height
        _image = self.compiled.convert('RGB')
        _mask = self.compiled
        parent_base.paste(_image, (_x, _y), _mask)


    def update(self):
        if (self.__update_on_cooldown):
            self.logger.debug("Update on cooldown")

            if (not self.__update_requested):
                self.logger.debug("Update scheduled")
                self.__update_requested = True
            else:
                self.logger.debug("Update already scheduled")

        else:
            thr = threading.Thread(target=self.__delayed_update, args=(), kwargs={ })
            thr.start()


    # def recompileButtonNameTab_Click(self, sender, e):
    #     self.update()

    def __delayed_update(self):
        self.__update_on_cooldown = True
        if (self.update_delay):
            time.sleep(self.update_delay)
        self.__update_command()
        if (self.update_timeout):
            time.sleep(self.update_timeout)

        self.__update_on_cooldown = False
        if (self.__update_requested):
            self.__update_requested = False
            self.__update_command()

    def _on_update(self):
        pass

    def _on_warn(self, warning):
        pass

    def __update_command(self):
        self.__update_on_cooldown = True
        _start = datetime.datetime.now()

        _oldtime = _start
        self.parent.compile_module(self.index)
        _time = datetime.datetime.now()
        self.logger.debug("Module compile from remote time: {0}ms".format((_time - _oldtime).total_seconds() * 1000))

        _oldtime = _time
        self._on_update()
        _time = datetime.datetime.now()
        self.logger.debug("Module update event time: {0}ms".format((_time - _oldtime).total_seconds() * 1000))

        _oldtime = _time
        self.parent.update()
        _time = datetime.datetime.now()
        self.logger.debug("Update image time: {0}ms".format((_time - _oldtime).total_seconds() * 1000))

        _oldtime = _time
        self.update_function()
        _time = datetime.datetime.now()
        self.logger.debug("Update preview time: {0}ms".format((_time - _oldtime).total_seconds() * 1000))

        _oldtime = _start
        self.logger.debug("Total update time: {0}ms".format((_time - _oldtime).total_seconds() * 1000))

        if (self.__update_requested):
            thr = threading.Thread(target=self.__delayed_update, args=(), kwargs={ })
            thr.start()

    def create_generator_tab(self, update_function):
        if not (generator.generator_supported):
            raise generator.GeneratorNotSupported("Generator Feature is required for this function")

        module_tab = System.Windows.Forms.TabPage()

        module_tab.Location = System.Drawing.Point(4, 22)
        module_tab.Name = "{name}ModuleTab".format(name=self.module_name)
        module_tab.Padding = System.Windows.Forms.Padding(3)
        module_tab.Size = System.Drawing.Size(222, 472)
        module_tab.Anchor = \
            System.Windows.Forms.AnchorStyles.Top \
            | System.Windows.Forms.AnchorStyles.Left \
            | System.Windows.Forms.AnchorStyles.Right \
            | System.Windows.Forms.AnchorStyles.Bottom;
        module_tab.Text = "{name}".format(name=self.human_readable_name)
        module_tab.UseVisualStyleBackColor = True

        tab_content = self._create_generator_tab_content()

        # #
        # # recompileButtonNameTab
        # #
        # recompileButtonNameTab = System.Windows.Forms.Button();
        #
        # recompileButtonNameTab.Anchor = \
        #     System.Windows.Forms.AnchorStyles.Left \
        #     | System.Windows.Forms.AnchorStyles.Right \
        #     | System.Windows.Forms.AnchorStyles.Bottom;
        # recompileButtonNameTab.Location = System.Drawing.Point(6, 435);
        # recompileButtonNameTab.Name = "{name}UpdateButton".format(name=self.module_name);
        # recompileButtonNameTab.Size = System.Drawing.Size(210, 31);
        # recompileButtonNameTab.TabIndex = 1;
        # recompileButtonNameTab.Text = "Update";
        # recompileButtonNameTab.UseVisualStyleBackColor = True;
        # recompileButtonNameTab.Click += System.EventHandler(self.recompileButtonNameTab_Click);

        module_tab.Controls.Add(tab_content)
        # module_tab.Controls.Add(recompileButtonNameTab)

        self.update_function = update_function
        self.last_update = datetime.datetime.now()

        return module_tab


    def _create_generator_tab_content(self):
        raise NotImplementedError