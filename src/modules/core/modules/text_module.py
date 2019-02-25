from hammerdraw.module_base import ModuleBase
from hammerdraw.compilers.compiler_error import TextNotFitInAreaWarning

from hammerdraw import generator
if (generator.generator_supported):
    import System
    from System import Decimal as decimal

class TextModule(ModuleBase):
    module_name = None
    raw_field = None
    raw_font_size_scale_field = None
    multiline = None

    def initialize(self, name:str, field:str=None, scale_field:str=None, multiline:bool=False, **kwargs):
        self.module_name = name
        self.raw_field = field or name
        self.multiline = multiline
        if (scale_field):
            self.raw_font_size_scale_field = scale_field
        super().initialize(**kwargs)

    def _compile(self, base):
        text = self.parent.raw.get(self.raw_field)
        if (text):
            return self._print(base, self.parent.raw[self.raw_field])
        return 0
    def _print(self, base, text):
        td = self.get_text_drawer(base)
        if (self.raw_font_size_scale_field):
            _scale = self.parent.raw.get(self.raw_font_size_scale_field, 1.0)
            if (_scale != 1.0):
                td_font = td.get_font()
                td.set_font(font_size=td_font['font_size'] * _scale)

        w, h = td.print_in_region((0, 0, self.width, self.height), text, offset_borders=True)
        self.logger.info("{type} printed".format(type=self.module_name.capitalize()))
        if (w > self.width or h > self.height):
            self.setErrorState(True)
            raise TextNotFitInAreaWarning\
            (
                module=self,
                field=self.raw_field,
                required_size=(self.width, self.height),
                actual_size=(w, h),
                comment="Please, reduce either text length or font size."
            )
        elif (self.__error_state):
            self.setErrorState(False)

        return h

    ### =======================================
    ###   WinForms module generator
    ### =======================================

    textPanel = None
    textScalebar = None
    textFieldTextbox = None
    textFieldLabel = None
    textScaleUpDown = None
    textScaleLabel = None

    __error_state = False

    def _on_warn(self, warning):
        if (isinstance(warning, TextNotFitInAreaWarning)):
            if (warning.module == self):
                if (not self.textPanel):
                    self.logger.debug("Warning ignored, as long as there is no GUI attached.")
                    return
                pass # Nothing to do :)

    def _create_generator_tab_content(self):
        _y = 0
        _tab_index = 0

        self.textPanel = System.Windows.Forms.Panel();
        self.textFieldLabel = System.Windows.Forms.Label();
        if (self.multiline):
            self.textFieldTextbox = System.Windows.Forms.RichTextBox();
        else:
            self.textFieldTextbox = System.Windows.Forms.TextBox();
        if (self.raw_font_size_scale_field):
            self.textScaleUpDown = System.Windows.Forms.NumericUpDown();
            self.textScalebar = System.Windows.Forms.TrackBar();
            self.textScaleLabel = System.Windows.Forms.Label();

        #
        # namePanel
        #
        self.textPanel.Anchor = \
            System.Windows.Forms.AnchorStyles.Left \
            | System.Windows.Forms.AnchorStyles.Right \
            | System.Windows.Forms.AnchorStyles.Top;
        self.textPanel.Controls.Add(self.textFieldLabel);
        self.textPanel.Controls.Add(self.textFieldTextbox);
        self.textPanel.Controls.Add(self.textScaleLabel);
        self.textPanel.Controls.Add(self.textScalebar);
        self.textPanel.Controls.Add(self.textScaleUpDown);
        self.textPanel.Location = System.Drawing.Point(0, 0);
        self.textPanel.Name = "namePanel";
        self.textPanel.Size = System.Drawing.Size(222, 429);
        self.textPanel.TabIndex = 0;

        #
        # nameFieldLabel
        #
        _top = 3
        self.textFieldLabel.AutoSize = True;
        self.textFieldLabel.Location = System.Drawing.Point(6, _y + _top);
        self.textFieldLabel.Name = "nameFieldLabel";
        self.textFieldLabel.Size = System.Drawing.Size(44, 13);
        self.textFieldLabel.TabIndex = _tab_index;
        self.textFieldLabel.Text = "{name}:".format(name=self.human_readable_name);
        _y += self.textFieldLabel.Height + _top
        _tab_index += 1

        #
        # nameFieldTextbox
        #
        _top = 3
        self.textFieldTextbox.Anchor = \
            System.Windows.Forms.AnchorStyles.Left \
            | System.Windows.Forms.AnchorStyles.Right \
            | System.Windows.Forms.AnchorStyles.Top;
        self.textFieldTextbox.Location = System.Drawing.Point(3, _y + _top);
        self.textFieldTextbox.Name = "nameFieldTextbox";
        self.textFieldTextbox.Text = self.parent.raw.get(self.raw_field)
        self.textFieldTextbox.TabIndex = _tab_index
        if (self.multiline):
            self.textFieldTextbox.Multiline = True;
            self.textFieldTextbox.ScrollBars = System.Windows.Forms.ScrollBars.Vertical;
            self.textFieldTextbox.Size = System.Drawing.Size(213, 160);
        else:
            self.textFieldTextbox.Size = System.Drawing.Size(213, 20);
        self.textFieldTextbox.TextChanged += System.EventHandler(self.textFieldTextbox_TextChanged);
        _y += self.textFieldTextbox.Height + _top
        _tab_index += 1

        if (self.raw_font_size_scale_field):
            #
            # nameScaleLabel
            #
            _top = 21
            self.textScaleLabel.AutoSize = True;
            self.textScaleLabel.Location = System.Drawing.Point(6, _y + _top);
            self.textScaleLabel.Name = "nameScaleLabel";
            self.textScaleLabel.Size = System.Drawing.Size(84, 13);
            self.textScaleLabel.TabIndex = 3;
            self.textScaleLabel.Text = "Font Size Scale:";
            _y += self.textScaleLabel.Height + _top
            _tab_index += 1

            #
            # nameScalebar
            #
            _top = 3
            self.textScalebar.Anchor = \
                System.Windows.Forms.AnchorStyles.Left \
                | System.Windows.Forms.AnchorStyles.Right \
                | System.Windows.Forms.AnchorStyles.Top;
            self.textScalebar.AutoSize = False;
            self.textScalebar.BackColor = System.Drawing.SystemColors.ControlLightLight;
            self.textScalebar.LargeChange = 10;
            self.textScalebar.Location = System.Drawing.Point(3, _y + _top);
            self.textScalebar.Maximum = 200;
            self.textScalebar.Name = "nameScalebar";
            self.textScalebar.Size = System.Drawing.Size(147, 20);
            self.textScalebar.SmallChange = 1;
            self.textScalebar.TabIndex = 4;
            self.textScalebar.TickStyle = System.Enum.Parse(System.Windows.Forms.TickStyle, "None");
            self.textScalebar.Value = int(self.parent.raw.get(self.raw_font_size_scale_field, 1.0) * 100);
            self.textScalebar.Scroll += System.EventHandler(self.textScalebar_Scroll);
            # _y += self.textScalebar.Height + _top
            _tab_index += 1

            #
            # nameScaleUpDown
            #
            _top = 3
            self.textScaleUpDown.Anchor = \
                System.Windows.Forms.AnchorStyles.Right \
                | System.Windows.Forms.AnchorStyles.Bottom;
            self.textScaleUpDown.DecimalPlaces = 2;
            self.textScaleUpDown.Increment = decimal(5);
            self.textScaleUpDown.Location = System.Drawing.Point(156, _y + _top);
            self.textScaleUpDown.Maximum = decimal(200);
            self.textScaleUpDown.Name = "{type}ScaleUpDown".format(type=self.module_name);
            self.textScaleUpDown.Size = System.Drawing.Size(60, 20);
            self.textScaleUpDown.TabIndex = 5;
            self.textScaleUpDown.Value = decimal(self.parent.raw.get(self.raw_font_size_scale_field, 1.0) * 100);
            self.textScaleUpDown.ValueChanged += System.EventHandler(self.textScaleUpDown_ValueChanged);
            _y += self.textScaleUpDown.Height + _top
            _tab_index += 1

        return self.textPanel;

    __prevent_scroll = False

    def textScalebar_Scroll(self, sender, e):
        if (self.__prevent_scroll):
            return
        self.setScale(decimal(self.textScalebar.Value));

    def textScaleUpDown_ValueChanged(self, sender, e):
        if (self.__prevent_scroll):
            return
        self.setScale(self.textScaleUpDown.Value);

    def textFieldTextbox_TextChanged(self, sender, e):
        self.setText(self.textFieldTextbox.Text)


    def setScale(self, value):
        self.__prevent_scroll = True;
        self.textScalebar.Value = System.Convert.ToInt32(value);
        self.textScaleUpDown.Value = value;
        self.parent.raw[self.raw_font_size_scale_field] = System.Convert.ToDouble(value) / 100
        self.__prevent_scroll = False;
        self.update()

    def setText(self, value):
        self.parent.raw[self.raw_field] = value
        self.update()


    def setErrorState(self, is_error=True):
        if (not self.textPanel):
            return
        if (self.__error_state == is_error):
            return

        if (is_error):
            self.logger.debug("Setting input color to red due to warning on compilation.")
            self.__error_state = True
            self.textFieldTextbox.ForeColor = System.Drawing.Color.Red;
            if (self.raw_font_size_scale_field):
                self.textScaleUpDown.ForeColor = System.Drawing.Color.Red;

        else:
            self.logger.debug("Warnings fixed, returning color to its normal state.")
            self.__error_state = False
            self.textFieldTextbox.ForeColor = System.Drawing.SystemColors.WindowText;
            if (self.raw_font_size_scale_field):
                self.textScaleUpDown.ForeColor = System.Drawing.SystemColors.WindowText;