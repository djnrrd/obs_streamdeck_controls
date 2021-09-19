from configparser import ConfigParser
from appdirs import user_config_dir
import os
import tkinter as tk
from tkinter import font as tk_font
from tkinter import messagebox as tk_mb
from .obs_controls import get_all_sources, get_source_settings
from . import text_includes as ti
from .conf import CLIENT_ID, REDIRECT_URI
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from functools import partial
from urllib.parse import urlencode
from simpleobsws import ConnectionFailure
import os


def load_config():
    """Load the config file and return the ConfigParser object

    :return: the ConfigParser object
    :rtype: ConfigParser
    """
    # Attempt to load the config file
    config_dir = user_config_dir('obs-streamdeck-ctl', 'djnrrd')
    if not os.path.isdir(config_dir):
        # On windows appdirs always have to be %appdir%//author//appname so
        # we have to create the author folder first
        if not os.path.isdir(os.path.join(user_config_dir(), 'djnrrd')):
            os.mkdir(os.path.join(user_config_dir(), 'djnrrd'))
        os.mkdir(config_dir)
    config_file = os.path.join(config_dir, 'obs-streamdeck.ini')
    config = ConfigParser()
    config.read(config_file)
    return config


def save_config(config):
    """Save the config file to the user's local config directory.

    :param config: The ConfigParser object
    :type config: ConfigParser
    """
    config_dir = user_config_dir('obs-streamdeck-ctl', 'djnrrd')
    config_file = os.path.join(config_dir, 'obs-streamdeck.ini')
    if not all([os.path.exists(config_dir), os.path.isdir(config_dir)]):
        os.mkdir(config_dir)
    with open(config_file, 'w') as f:
        config.write(f)


class SetupApp(tk.Tk):
    """The main Tkinter GUI for the config setup wizard

    :param config: The ConfigParser object that was loaded from
        config_mgmt.load_config
    :type config: ConfigParser
    :cvar obs_config: The stored ConfigParser object
    """

    def __init__(self, config):
        super().__init__()
        # Add the config to the application, we'll be calling it from some of
        # the wizard frames
        self.obs_config = config
        self.title(ti.APP_HEADER)
        self.title_font = tk_font.Font(family='Helvetica', size=18,
                                       weight='bold', slant='italic')
        self.geometry('800x360')
        self.resizable(False, False)
        # Make sure the main app only has one square in the grid that fills
        # everything
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        # Set the main app container frame which again only has one square
        # and fills everything
        container = tk.Frame(self, name='main_frame')
        container.grid(row=0, column=0, sticky='nsew')
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        # Add the frames that will make up the wizard and show the first one.
        self.frames = self.load_frames(container)
        self.show_frame('WelcomePage')

    def load_frames(self, container):
        """Loop through the frames defined in this module, create them and add
        them to the returned dictionary

        :param container: The main application container frame that all
            frames wil be attached to
        :type: tk.Frame
        :return: A dictionary of frame names and the objects created
        :rtype: dict
        """
        ret_dict = dict()
        for f in (WelcomePage, ExistingConfig, ObsWsPass, ObsAudioSources,
                  ObsAlertSources, LaunchTwitch, StartStopOptions,
                  LiveSafetyOptions, AdditionalSafetyOptions, SetupComplete):
            page_name = f.__name__
            frame = f(container, self, name=page_name.lower())
            frame.grid(row=0, column=0, sticky='nsew')
            ret_dict[page_name] = frame
        return ret_dict

    def show_frame(self, page_name):
        """Bring the requested frame to the foreground

        :param page_name: The name of the frame to bring forward
        :type page_name: str
        """
        frame = self.frames[page_name]
        frame.tkraise()

    def show_busy(self):
        """Change the cursor to 'watch' to reflect waiting on a  background
        operation
        """
        self.config(cursor='watch')

    def clear_busy(self):
        """Set the cursor back to normal"""
        self.config(cursor='')


class SetupPage(tk.Frame):
    """A superclass frame that should not be called directly, but instead
    manages the split between the main wizard, the header, and the navigation
    sections below.

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    :param name: The name to refer to this frame
    :type name: str
    :param headers: A pair of text strings in a tuple (HEADING,
        HEADING_TEXT), to provide to the top frame
    :type headers: tuple
    :param footers: A tuple of arguments to pass to the _setup_footer method
    :type tuple:
    :cvar controller: The main application GUI
    :cvar top_frame: The header frame
    :cvar middle_frame: The main frame for the wizard pages
    :cvar bottom_frame: The navigation frame
    """

    def __init__(self, parent, controller, name='', headers=(), footers=()):
        super().__init__(parent, name=name)
        self.controller = controller
        # Layouts
        self._layout_frames()
        self._setup_header(*headers)
        self._setup_footer(*footers)

    def _layout_frames(self):
        """Create the main 3 layout frames and grid them.
        """
        self.top_frame = tk.Frame(self, name='top_frame')
        self.middle_frame = tk.Frame(self, name='middle_frame')
        self.bottom_frame = tk.Frame(self, name='bottom_frame')
        self.top_frame.grid(row=0, column=0, sticky='nsew')
        self.middle_frame.grid(row=1, column=0, sticky='nsew')
        # Add some padding to make the navigation buttons stand out
        self.bottom_frame.grid(row=2, column=0, sticky='nsew', padx=10, pady=10)
        # Favour the middle row, so the bottom and top rows are only as big as
        # they need to be.
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

    def _setup_footer(self, next_function, back_function=None, final=False):
        """ Setup the navigation buttons in the bottom frame

        :param next_function: The function to call when clicking the Next button
        :type next_function: function
        :param back_function: The function to call when clicking the Back button
        :type back_function: function
        :param final: Change the Next button into a Finish button if this is
            the final page of the wizard
        :type final: bool
        """
        # Do we have a back function? If so, renumber the position of the
        # Next button
        next_col = 1
        next_text = 'Finish' if final else 'Next'
        if back_function:
            next_col = 2
            back_btn = tk.Button(self.bottom_frame, text='Back',
                                 command=back_function, name='back',
                                 state='normal')
            back_btn.grid(row=0, column=1, sticky='e', padx=5)
        cancel_btn = tk.Button(self.bottom_frame, text='Cancel',
                               command=self.controller.destroy, name='cancel',
                               state='normal')
        cancel_btn.grid(row=0, column=0, sticky='e')
        next_btn = tk.Button(self.bottom_frame, text=next_text,
                             command=next_function, name='next', state='normal')
        next_btn.grid(row=0, column=next_col, sticky='e')
        # Favour the left hand column to force everything to the right
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=0)
        if back_function:
            self.bottom_frame.grid_columnconfigure(2, weight=0)

    def _setup_header(self, header_text, body_text):
        """Setup the heading section in the top frame.

        :param header_text: The text to render as the header for the frame
        :type header_text: str
        :param body_text: The text to render as the body for the frame
        :type body_text: str
        :param col_span: If the header section
        :return:
        """
        heading = tk.Label(self.top_frame, text=header_text,
                           font=self.controller.title_font)
        description = tk.Message(self.top_frame, text=body_text, width=780)
        heading.grid(row=0, column=0, sticky='nsew', pady=10)
        description.grid(row=1, column=0, sticky='nw', pady=10, padx=5)
        self.top_frame.grid_rowconfigure(0, weight=0)
        self.top_frame.grid_rowconfigure(1, weight=1)
        self.top_frame.grid_columnconfigure(0, weight=1)

    @staticmethod
    def list_to_entry(list_widget, entry_widget):
        """Swap the selected entry in a Listbox widget with the value in an
        Entry widget

        :param list_widget: The Listbox widget
        :type list_widget: tk.Listbox
        :param entry_widget: The Entry widget
        :type entry_widget: tk.Entry
        """
        old_source = entry_widget.get()
        new_source = list_widget.get(list_widget.curselection())
        entry_widget.set(new_source)
        list_widget.insert(list_widget.curselection(), old_source)
        list_widget.delete(list_widget.curselection())

    @staticmethod
    def list_to_list(list_a, list_b):
        """Move selected items from list_a to list_b

        :param list_a: The listbox widget to move items from
        :type list_a: tk.Listbox
        :param list_b: The listbox widget to move items to
        :type list_b: tk.Listbox
        """
        items = []
        item_idx = list_a.curselection()
        for idx in reversed(item_idx):
            items.append(list_a.get(idx))
            list_a.delete(idx)
        for item in items:
            list_b.insert('end', item)

    def setup_list_frame(self, header='', name='', select_mode='single'):
        """Create a frame for a list box with a scroll bar to be added to the
        top frame. Weighting of the outer grid sections is not completed in
        this function, and should be completed after the other components have
        been laid out

        :param header: Header text for the frame
        :type header: str
        :param name: The name to give to the listbox
        :type name: str
        :param select_mode: Value for select_mode for the Listbox widget
        :type select_mode: str
        :return: The frame
        :rtype: tk.Frame
        """
        frame = tk.Frame(self.middle_frame, name=f"{name}_frame")
        list_box = tk.Listbox(frame, selectmode=select_mode, name=f"{name}_lbx")
        row_start = 0
        if header:
            row_start = 1
            header_label = tk.Label(frame, text=header)
            header_label.grid(row=0, column=0, columnspan=2)
        list_box.grid(row=row_start, column=0)
        scroll = tk.Scrollbar(frame)
        scroll.grid(row=row_start, column=1, sticky='ns')
        scroll.config(command=list_box.yview)
        list_box.config(yscrollcommand=scroll.set)
        return frame

    def get_list_frame_lbx(self, name, target_frame='middle_frame'):
        """Return the listbox widget that was created in a frame.

        :param name: The name of the listbox/frame widget created earlier
        :type name: str
        :param target_frame: The name of the frame that contains the
            listbox/frame
        :type target_frame: str
        :return: The listbox widget
        :rtype: tk.Listbox
        """
        screen_name = str(self)
        lbx_path = f"{screen_name}.{target_frame}.{name}_frame.{name}_lbx"
        return self.controller.nametowidget(lbx_path)

    def enable_disable_widgets(self, test, widgets,
                               target_frame='middle_frame'):
        """Enable or Disable a set of widgets based on a truthiness test

        :param test: The statement to evaluate for truthiness
        :param test: Bool
        :param widgets: A list or tuple of widgets to enable or disable
        :type widgets: tuple
        :param target_frame: the name of the target frame where the widgets are
        :type target_frame: str
        """
        screen_name = str(self)
        if test:
            state = 'normal'
        else:
            state = 'disabled'
        for name in widgets:
            next_button_path = f"{screen_name}.{target_frame}.{name}"
            self.controller.nametowidget(next_button_path)['state'] = state


class WelcomePage(SetupPage):
    """Introduction page for the Setup Wizard

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    :param name: The name for the frame widget
    :type name: str
    :cvar controller: The main application GUI
    :cvar top_frame: The header frame
    :cvar middle_frame: The main frame for the wizard pages
    :cvar bottom_frame: The navigation frame
    """

    def __init__(self, parent, controller, name=''):
        headers = (ti.WELCOME_HEADING, ti.WELCOME_TEXT)
        footers = (self.check_existing,)
        super().__init__(parent, controller, name, headers, footers)

    def _layout_frames(self):
        """Add the button to launch hte OBS WebSockets site

        """
        super()._layout_frames()
        obsws_btn = tk.Button(self.middle_frame, text='Get OBS WebSockets',
                              command=self.get_obsws, name='obsws_btn',
                              state='normal')
        obsws_btn.grid(row=0, column=0, sticky='nw', padx=10)
        self.middle_frame.grid_rowconfigure(0, weight=1)
        self.middle_frame.grid_columnconfigure(0, weight=1)

    def check_existing(self):
        """Check the controller to see if the loaded config file had valid
        sections.  If it did redirect the user to a confirmation page about
        changing existing configs, otherwise step past to the OBS WebSockets
        Password configuration
        """
        if self.controller.obs_config.has_section('obs'):
            self.controller.show_frame('ExistingConfig')
        else:
            self.controller.show_frame('ObsWsPass')

    @staticmethod
    def get_obsws():
        """Open a new web browser tab and load the github release page
        for the latest release of OBS WebSockets server
        """
        webbrowser.open_new_tab('https://github.com/Palakis/obs-websocket/'
                                'releases/tag/4.9.1')


class ExistingConfig(SetupPage):
    """A Page to confirm if the user is happy to edit their already existing
    config, as determined after the Welcome page

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    :param name: The name for the frame widget
    :type name: str
    :cvar controller: The main application GUI
    :cvar top_frame: The header frame
    :cvar middle_frame: The main frame for the wizard pages
    :cvar bottom_frame: The navigation frame
    """

    def __init__(self, parent, controller, name=''):
        headers = (ti.EXISTING_HEADING, ti.EXISTING_TEXT)
        footers = (lambda: controller.show_frame('ObsWsPass'),
                   lambda: controller.show_frame('WelcomePage'))
        super().__init__(parent, controller, name, headers, footers)


class ObsWsPass(SetupPage):
    """A Page to determine the password for the OBS WebSockets server, if any.

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    :param name: The name for the frame widget
    :type name: str
    :cvar controller: The main application GUI
    :cvar top_frame: The header frame
    :cvar middle_frame: The main frame for the wizard pages
    :cvar bottom_frame: The navigation frame
    """

    def __init__(self, parent, controller, name=''):
        headers = (ti.OBSWSPASS_HEADING, ti.OBSWSPASS_TEXT)
        footers = (self.update_password,
                   lambda: controller.show_frame('WelcomePage'))
        # Set the variables before calling super, then manipulate them
        # afterwards
        self.ws_password = tk.StringVar()
        super().__init__(parent, controller, name, headers, footers)
        self.ws_password.set(self.load_password())

    def _layout_frames(self):
        """Layout the OBS WS password and port number form
        """
        super()._layout_frames()
        password_prompt_lbl = tk.Label(self.middle_frame,
                                       text=ti.OBSWSPASS_PROMPT)
        ws_password_entry = tk.Entry(self.middle_frame,
                                     textvariable=self.ws_password)
        password_prompt_lbl.grid(row=0, column=0, sticky='e', padx=5)
        ws_password_entry.grid(row=0, column=1, sticky='w')
        self.middle_frame.grid_rowconfigure(0, weight=1)
        self.middle_frame.grid_columnconfigure(0, weight=1)
        self.middle_frame.grid_columnconfigure(1, weight=1)

    def load_password(self):
        """If there is an existing password, return that value.

        :return: The existing password
        :rtype: str
        """
        config = self.controller.obs_config
        # Make sure there is an 'obs' section in the config, adding it if
        # there isn't since this is the first time we're checking
        None if config.has_section('obs') else config.add_section('obs')
        if config.has_option('obs', 'ws_password'):
            return config['obs']['ws_password']
        else:
            return ''

    def update_password(self):
        """Get the updated value from the entry box and update the config.
        Before showing the next frame, load the sources from OBS
        """
        config = self.controller.obs_config
        config['obs']['ws_password'] = self.ws_password.get()
        self.get_obs_sources()

    def get_obs_sources(self):
        """Load the OBS Source list from the OBS WebSockets interface,
        raising an alert if we're unable to connect.  Then pass that list to
        the next frame to load into its Listbox before showing the next frame
        """
        self.controller.show_busy()
        config = self.controller.obs_config
        try:
            obs_sources = get_all_sources(config['obs']['ws_password'])
            self.controller.clear_busy()
            self.controller.frames['ObsAudioSources']. \
                load_obs_sources(obs_sources)
            self.controller.show_frame('ObsAudioSources')
        except (ConnectionRefusedError, NameError, ConnectionFailure):
            self.controller.clear_busy()
            tk_mb.showwarning(title=ti.OBSWSPASS_WARN_HEADER,
                              message=ti.OBSWSPASS_WARN)


class ObsAudioSources(SetupPage):
    """A Page to determine the Microphone and Desktop Audio sources in OBS.

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    :param name: The name for the frame widget
    :type name: str
    :cvar controller: The main application GUI
    :cvar top_frame: The header frame
    :cvar middle_frame: The main frame for the wizard pages
    :cvar bottom_frame: The navigation frame
    """

    def __init__(self, parent, controller, name=''):
        headers = (ti.OBSAUDIO_HEADING, ti.OBSAUDIO_TEXT)
        footers = (self.update_sources,
                   lambda: self.controller.show_frame('ObsWsPass'))
        # Set the variables before calling super, then manipulate them
        # afterwards
        self.mic_source = tk.StringVar()
        self.desktop_source = tk.StringVar()
        super().__init__(parent, controller, name, headers, footers)
        self.mic_source.set(self.load_mic_source())
        self.desktop_source.set(self.load_desktop_source())
        self.obs_sources = self.get_list_frame_lbx('obs_sources')

    def _layout_frames(self):
        """Layout the OBS Audio source selection form
        """
        super()._layout_frames()
        obs_lbxf = self.setup_list_frame(ti.OBSALERT_SOURCE_PROMPT,
                                         'obs_sources')
        obs_lbxf.grid(row=0, column=0, rowspan=6, padx=5, sticky='ne')
        mic_source_btn = tk.Button(self.middle_frame, text=' <<  >> ',
                                   command=self.select_mic_source)
        mic_source_btn.grid(row=2, column=1, padx=10, sticky='ew')
        mic_source_lbl = tk.Label(self.middle_frame,
                                  text=ti.OBSAUDIO_MIC_PROMPT)
        mic_source_lbl.grid(row=1, column=2, sticky='sw')
        mic_source_entry = tk.Entry(self.middle_frame,
                                    textvariable=self.mic_source)
        mic_source_entry.grid(row=2, column=2, sticky='w')
        desktop_source_button = tk.Button(self.middle_frame, text=' <<  >> ',
                                          command=self.select_desktop_source)
        desktop_source_button.grid(row=5, column=1, padx=10, sticky='ew')
        desktop_source_label = tk.Label(self.middle_frame,
                                        text=ti.OBSAUDIO_DESK_PROMPT)
        desktop_source_label.grid(row=4, column=2, sticky='sw')
        desktop_source_entry = tk.Entry(self.middle_frame,
                                        textvariable=self.desktop_source)
        desktop_source_entry.grid(row=5, column=2, sticky='w')
        # Prefer the bottom row to force everything up and the right hand
        # column to force everything left
        self.middle_frame.grid_rowconfigure(0, weight=0)
        self.middle_frame.grid_rowconfigure(1, weight=0)
        self.middle_frame.grid_rowconfigure(2, weight=0)
        self.middle_frame.grid_rowconfigure(3, weight=0)
        self.middle_frame.grid_rowconfigure(4, weight=0)
        self.middle_frame.grid_rowconfigure(5, weight=0)
        self.middle_frame.grid_columnconfigure(0, weight=1)
        self.middle_frame.grid_columnconfigure(1, weight=0)
        self.middle_frame.grid_columnconfigure(2, weight=1)

    def load_mic_source(self):
        """If there is an existing Mic source, return that value, otherwise
        return the default

        :return: The existing password
        :rtype: str
        """
        config = self.controller.obs_config
        if config.has_option('obs', 'mic_source'):
            return config['obs']['mic_source']
        else:
            return 'Mic/Aux'

    def load_desktop_source(self):
        """If there is an existing Desktop source, return that value.
        Otherwise return the default

        :return: The existing password
        :rtype: str
        """
        config = self.controller.obs_config
        if config.has_option('obs', 'desktop_source'):
            return config['obs']['desktop_source']
        else:
            return 'Desktop Audio'

    def load_obs_sources(self, obs_sources):
        """Load the OBS Sources from the previous frame into the Listbox"""
        self.obs_sources.delete(0, 'end')
        sources = [x['name'] for x in obs_sources]
        default_sources = (self.mic_source.get(), self.desktop_source.get())
        for source in sources:
            if source not in default_sources:
                self.obs_sources.insert('end', source)

    def update_sources(self):
        """Get the updated value from the entry box and update the config
        before moving onto the next frame
        """
        config = self.controller.obs_config
        config['obs']['mic_source'] = self.mic_source.get()
        config['obs']['desktop_source'] = self.desktop_source.get()
        obs_sources = self.obs_sources.get(0, 'end')
        obs_sources += (self.mic_source.get(), self.desktop_source.get())
        self.controller.frames['ObsAlertSources'].load_obs_sources(obs_sources)
        self.controller.show_frame('ObsAlertSources')

    def select_mic_source(self):
        """Move a source from the Listbox to the Microphone Entry widget"""
        self.list_to_entry(self.obs_sources, self.mic_source)

    def select_desktop_source(self):
        """Move a source from the Listbox to the Desktop Entry widget"""
        self.list_to_entry(self.obs_sources, self.desktop_source)


class ObsAlertSources(SetupPage):
    """A Page to determine the Notification and chat sources in OBS that
    would be disabled in the Live Safety functions.

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    :param name: The name for the frame widget
    :type name: str
    :cvar controller: The main application GUI
    :cvar top_frame: The header frame
    :cvar middle_frame: The main frame for the wizard pages
    :cvar bottom_frame: The navigation frame
    """

    def __init__(self, parent, controller, name=''):
        headers = (ti.OBSALERT_HEADING, ti.OBSALERT_TEXT)
        footers = (self.update_sources,
                   lambda: self.controller.show_frame('ObsAudioSources'))
        super().__init__(parent, controller, name, headers, footers)
        self.obs_sources = self.get_list_frame_lbx('obs_sources')
        self.alert_sources = self.get_list_frame_lbx('alert_sources')
        # Load the default alert sources after the layout since we're adding
        # directly to the listbox
        self.load_default_alert_sources()

    def _layout_frames(self):
        """Layout the OBS Alert sources selection form
        """
        super()._layout_frames()
        obs_frame = self.setup_list_frame(ti.OBSALERT_SOURCE_PROMPT,
                                          'obs_sources', 'extended')
        obs_frame.grid(row=1, column=0, padx=5, rowspan=5, sticky='e')
        add_source_button = tk.Button(self.middle_frame, text=' >> ',
                                      command=self.select_alert_source)
        add_source_button.grid(row=2, column=1, padx=10)
        remove_source_button = tk.Button(self.middle_frame, text=' << ',
                                         command=self.remove_alert_source)
        remove_source_button.grid(row=4, column=1, padx=10)
        alert_frame = self.setup_list_frame(ti.OBSALERT_ALERT_PROMPT,
                                            'alert_sources', 'extended')
        alert_frame.grid(row=1, column=2, padx=5, rowspan=5, sticky='w')
        # Prefer the bottom row to force everything up and the right hand
        # column to force everything left
        self.middle_frame.grid_rowconfigure(0, weight=0)
        self.middle_frame.grid_rowconfigure(1, weight=0)
        self.middle_frame.grid_rowconfigure(2, weight=0)
        self.middle_frame.grid_rowconfigure(3, weight=0)
        self.middle_frame.grid_rowconfigure(4, weight=0)
        self.middle_frame.grid_rowconfigure(5, weight=0)
        self.middle_frame.grid_rowconfigure(6, weight=0)
        self.middle_frame.grid_columnconfigure(0, weight=1)
        self.middle_frame.grid_columnconfigure(1, weight=0)
        self.middle_frame.grid_columnconfigure(2, weight=1)

    def select_alert_source(self):
        """Move sources from the list of OBS Sources to the list of config
        sources"""
        self.list_to_list(self.obs_sources, self.alert_sources)

    def remove_alert_source(self):
        """Move sources from the list of config Sources to the list of OBS
        sources"""
        self.list_to_list(self.alert_sources, self.obs_sources)

    def load_default_alert_sources(self):
        """If there are existing alert sources configured, add them to the
        listbox
        """
        config = self.controller.obs_config
        if config.has_option('obs', 'alert_sources'):
            alert_sources = config['obs']['alert_sources'].split(':')
            for source in alert_sources:
                self.alert_sources.insert('end', source)

    def load_obs_sources(self, obs_sources):
        """Load the OBS Sources from the previous frame into the Listbox"""
        default_sources = self.alert_sources.get(0, 'end')
        for source in obs_sources:
            if source not in default_sources:
                self.obs_sources.insert('end', source)

    def update_sources(self):
        """Get the updated values from the Alert sources Listbox and add them to
        the config. Then save the config and move to the twitch stage"""
        alerts = self.alert_sources.get(0, 'end')
        config = self.controller.obs_config
        None if config.has_section('obs_browser_sources') else \
            config.add_section('obs_browser_sources')
        config['obs']['alert_sources'] = ':'.join(alerts)
        for source in alerts:
            config['obs_browser_sources'][source] = self.get_source_url(source)
        self.controller.show_frame('LaunchTwitch')

    def get_source_url(self, source):
        """Connect to OBS to get the URL for the supplied source
        """
        config = self.controller.obs_config
        ws_password = config['obs']['ws_password']
        settings = get_source_settings(source, ws_password)
        return settings['url']


class LaunchTwitch(SetupPage):
    """A Page to launch Twitch Authorisation in a web browser and handle the
    return with a small web server.

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    :param name: The name for the frame widget
    :type name: str
    :cvar controller: The main application GUI
    :cvar top_frame: The header frame
    :cvar middle_frame: The main frame for the wizard pages
    :cvar bottom_frame: The navigation frame
    """

    def __init__(self, parent, controller, name=''):
        headers = (ti.LAUNCH_TWITCH_HEADING, ti.LAUNCH_TWITCH_TEXT)
        footers = (self.launch_browser,
                   lambda: self.controller.show_frame('ObsAlertSources'))
        self.twitch_channel = tk.StringVar()
        super().__init__(parent, controller, name, headers, footers)
        self.twitch_channel.set(self.load_channel())

    def _layout_frames(self):
        """Layout the Twitch channel form
        """
        super()._layout_frames()
        channel_lbl = tk.Label(self.middle_frame, text=ti.LAUNCH_TWITCH_PROMPT)
        channel_entry = tk.Entry(self.middle_frame,
                                 textvariable=self.twitch_channel)
        channel_lbl.grid(row=0, column=0, padx=5, sticky='e')
        channel_entry.grid(row=0, column=1, padx=5, sticky='w')
        self.middle_frame.grid_rowconfigure(0, weight=1)
        self.middle_frame.grid_columnconfigure(0, weight=1)
        self.middle_frame.grid_columnconfigure(1, weight=1)

    def load_channel(self):
        """If there is an existing channel, return that value.

        :return: The existing channel
        :rtype: str
        """
        config = self.controller.obs_config
        # Make sure there is an 'twitch' section in the config, adding it if
        # there isn't since this is the first time we're checking
        None if config.has_section('twitch') else config.add_section('twitch')
        if config.has_option('twitch', 'channel'):
            return config['twitch']['channel']
        else:
            return ''

    def launch_browser(self):
        """Disable the Next button, launch the user's web browser and take
        them to the Twitch OAuth page.  Start a web server to listen for the
        response"""
        # Disable my next button
        self.enable_disable_widgets(False, ('next',), 'bottom_frame')
        base_url = 'https://id.twitch.tv/oauth2/authorize'
        params = {'client_id': CLIENT_ID, 'redirect_uri': REDIRECT_URI,
                  'response_type': 'token',
                  'scope': 'channel:moderate chat:edit chat:read '
                           'channel_commercial channel_editor'}
        url_params = urlencode(params)
        url = f"{base_url}?{url_params}"
        # Placeholder while building. don't want to hammer Twitch
        # url = 'http://localhost:8000/'
        webbrowser.open_new_tab(url)
        # Launch the Web Server in a separate thread to wait for the response
        httpd = threading.Thread(target=self.start_web_server)
        httpd.daemon = True
        httpd.start()

    def start_web_server(self):
        """Start a web server using the custom response handler which will
        have a reference to the controller app to return the values from twitch.
        """
        # Use partial to add custom arguments to the TwitchResponseHandler
        handler = partial(TwitchResponseHandler, self.controller)
        server_address = ('', 8000)
        httpd = HTTPServer(server_address, handler)
        httpd.serve_forever()

    def return_from_web_server(self, return_object):
        """Receive the Twitch object from the web server and update the
        config. Take user to the next frame

        :param return_object: The JSON object returned from the thanks.js file
        :type return_object: dict
        """
        # Verify we've got the keys and values we expect:
        expected_keys = ('#access_token', 'scope', 'token_type')
        for key in return_object:
            if key not in expected_keys:
                raise KeyError('Did not receive expected keys from Twitch')
        if return_object['scope'] != 'channel:moderate chat:edit chat:read ' \
                                     'channel_commercial channel_editor':
            raise ValueError('Did not match scope requested')
        if return_object['token_type'] != 'bearer':
            raise ValueError('Did not receive expected token_type')
        # Update the config file with the access_token
        config = self.controller.obs_config
        config['twitch']['oauth_token'] = return_object['#access_token']
        config['twitch']['channel'] = self.twitch_channel.get()
        next_button_path = 'main_frame.launchtwitch.bottom_frame.next'
        self.controller.nametowidget(next_button_path)['state'] = 'active'
        self.controller.show_frame('StartStopOptions')


class SafetyOptions(SetupPage):
    """Create an intermediary class, since the next two setup pages are
    essentially the same

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    :param name: The name for the frame widget
    :type name: str
    :cvar controller: The main application GUI
    :cvar top_frame: The header frame
    :cvar middle_frame: The main frame for the wizard pages
    :cvar bottom_frame: The navigation frame
    :cvar safety_check_value: A Tkinter BooleanVar for safety pages
    :cvar emote_option: A Tkinter BooleanVar for safety pages
    :cvar safety_option: A Tkinter StringVar for safety pages
    :cvar follow_time: A Tkinter StringVar for safety pages
    """

    def __init__(self, parent, controller, name='', headers=(), footers=()):
        self.safety_check_value = tk.BooleanVar()
        self.emote_option = tk.BooleanVar()
        self.safety_option = tk.StringVar()
        self.follow_time = tk.StringVar()
        super().__init__(parent, controller, name, headers, footers)

    def _layout_frames(self, check_text):
        """Render the safety options. This has been moved up to the parent
        class as 2 setup pages will require it

        :param check_text: the text to render next to the enable check button
        :type check_text: str
        """
        super()._layout_frames()
        safety_chk = tk.Checkbutton(self.middle_frame,
                                    text=check_text,
                                    command=self.safety_check_changed,
                                    variable=self.safety_check_value)
        safety_chk.grid(row=1, column=0, sticky='nw', padx=10)
        emote_chk = tk.Checkbutton(self.middle_frame, text=ti.SAFETY_EMOTE,
                                   variable=self.emote_option,
                                   state='disabled', name='emote_chk')
        follower_rdo = tk.Radiobutton(self.middle_frame,
                                      text=ti.SAFETY_FOLLOW,
                                      variable=self.safety_option,
                                      value='FOLLOWER', state='disabled',
                                      name='follower_rdo',
                                      command=self.safety_radio_change)
        follow_time_ety = tk.Entry(self.middle_frame,
                                   textvariable=self.follow_time,
                                   state='disabled', name='follow_time_ety')
        follow_time_lbl = tk.Label(self.middle_frame,
                                   text=ti.SAFETY_FOLLOW_TIME,
                                   name='follow_time_lbl', state='disabled')
        sub_rdo = tk.Radiobutton(self.middle_frame, text=ti.SAFETY_SUB,
                                 variable=self.safety_option,
                                 value='SUBSCRIBER', state='disabled',
                                 name='sub_rdo',
                                 command=self.safety_radio_change)
        follower_rdo.grid(row=2, column=0, sticky='nw', padx=10)
        follow_time_ety.grid(row=2, column=1, sticky='nw', padx=10)
        follow_time_lbl.grid(row=3, column=1, sticky='nw', padx=10)
        sub_rdo.grid(row=3, column=0, sticky='nw', padx=10)
        emote_chk.grid(row=4, column=0, sticky='nw', padx=10)
        self.middle_frame.grid_rowconfigure(0, weight=0)
        self.middle_frame.grid_rowconfigure(1, weight=0)
        self.middle_frame.grid_rowconfigure(2, weight=0)
        self.middle_frame.grid_rowconfigure(3, weight=0)
        self.middle_frame.grid_rowconfigure(4, weight=0)
        self.middle_frame.grid_columnconfigure(0, weight=1)
        self.middle_frame.grid_columnconfigure(1, weight=0)

    def safety_check_changed(self):
        """Enable or disable the safety options when the checkbox is selected
        """
        self.enable_disable_widgets(self.safety_check_value.get(),
                                    ('emote_chk', 'follower_rdo', 'sub_rdo'))

    def safety_radio_change(self):
        """Enable or disable the additional follower option when the radio
        options are selected"""
        self.enable_disable_widgets(self.safety_option.get() == 'FOLLOWER',
                                    ('follow_time_ety', 'follow_time_lbl'))

    def update_safety(self, section_name, next_frame):
        """Get the updated values from the form and update the config.
        Then show the next frame

        :param section_name: The name for the config section
        :type section_name: str
        :param next_frame: The name of the next frame to load after updating
            the config
        :type next_frame: str
        """
        config = self.controller.obs_config
        config[section_name]['enabled'] = str(self.safety_check_value.get())
        if self.safety_check_value.get():
            config[section_name]['method'] = self.safety_option.get()
            if self.safety_option.get() == 'FOLLOWER':
                config[section_name]['follow_time'] = self.follow_time.get()
            config[section_name]['emote_mode'] = str(self.emote_option.get())
        self.controller.show_frame(next_frame)

    def load_safety(self, section_name):
        """If there are existing safety options, update the form to reflect
        them

        :param section_name:
        :type section_name: str
        """
        config = self.controller.obs_config
        None if config.has_section(section_name) else \
            config.add_section(section_name)
        if config.has_option(section_name, 'enabled'):
            self.safety_check_value.set(eval(config[section_name]['enabled']))
            self.safety_option.set(config[section_name]['method'])
            if self.safety_option.get() == 'FOLLOWER':
                self.follow_time.set(config[section_name]['follow_time'])
            self.emote_option.set(eval(config[section_name]['emote_mode']))
            self.safety_check_changed()
            self.safety_radio_change()


class StartStopOptions(SafetyOptions):
    """A Page to select the Start/Stop safety options.

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    :param name: The name for the frame widget
    :type name: str
    :cvar controller: The main application GUI
    :cvar top_frame: The header frame
    :cvar middle_frame: The main frame for the wizard pages
    :cvar bottom_frame: The navigation frame
    :cvar safety_check_value: A Tkinter BooleanVar for safety pages
    :cvar emote_option: A Tkinter BooleanVar for safety pages
    :cvar safety_option: A Tkinter StringVar for safety pages
    :cvar follow_time: A Tkinter StringVar for safety pages
    """

    def __init__(self, parent, controller, name=''):
        headers = (ti.START_STOP_HEADING, ti.START_STOP_TEXT)
        footers = (self.update_safety,
                   lambda: self.controller.show_frame('LaunchTwitch'))
        super().__init__(parent, controller, name, headers, footers)
        self.load_safety('start_stop_safety')

    def _layout_frames(self):
        """Layout the safety options for the Start/Stop function
        """
        super()._layout_frames(ti.START_STOP_CHECK)

    def update_safety(self):
        """Update the config for the Start/Stop safety features, then show
        the next screen"""
        super().update_safety('start_stop_safety', 'LiveSafetyOptions')


class LiveSafetyOptions(SafetyOptions):
    """A Page to select the Live Safety options.

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    :param name: The name for the frame widget
    :type name: str
    :cvar controller: The main application GUI
    :cvar top_frame: The header frame
    :cvar middle_frame: The main frame for the wizard pages
    :cvar bottom_frame: The navigation frame
    :cvar safety_check_value: A Tkinter BooleanVar for safety pages
    :cvar emote_option: A Tkinter BooleanVar for safety pages
    :cvar safety_option: A Tkinter StringVar for safety pages
    :cvar follow_time: A Tkinter StringVar for safety pages
    """

    def __init__(self, parent, controller, name=''):
        headers = (ti.LIVE_SAFETY_HEADING, ti.LIVE_SAFETY_TEXT)
        footers = (self.update_safety,
                   lambda: self.controller.show_frame('StartStopOptions'))
        super().__init__(parent, controller, name, headers, footers)
        self.load_safety('live_safety')

    def _layout_frames(self):
        """Layout the safety options for the Live Safety function"""
        super()._layout_frames(ti.LIVE_SAFETY_CHECK)

    def update_safety(self):
        """Update th2 config for the Live Safety features, then show
        the next screen"""
        super().update_safety('live_safety', 'AdditionalSafetyOptions')


class AdditionalSafetyOptions(SetupPage):
    """A Page to collect additional options for the Live Safety function.

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    :param name: The name for the frame widget
    :type name: str
    :cvar controller: The main application GUI
    :cvar top_frame: The header frame
    :cvar middle_frame: The main frame for the wizard pages
    :cvar bottom_frame: The navigation frame
    """

    def __init__(self, parent, controller, name=''):
        headers = (ti.ADDITIONAL_HEADING, ti.ADDITIONAL_TEXT)
        footers = (self.update_additional,
                   lambda: self.controller.show_frame('LiveSafetyOptions'))
        self.ad_check_value = tk.BooleanVar()
        self.clear_chat_check_value = tk.BooleanVar()
        super().__init__(parent, controller, name, headers, footers)
        self.load_additional()

    def _layout_frames(self):
        """Layout the additional options form"""
        super()._layout_frames()
        ad_chk = tk.Checkbutton(self.middle_frame,
                                text=ti.ADDITIONAL_AD_CHECK,
                                variable=self.ad_check_value)
        marker_chk = tk.Checkbutton(self.middle_frame,
                                    text=ti.ADDITIONAL_CLEAR_CHECK,
                                    variable=self.clear_chat_check_value)
        ad_chk.grid(row=0, column=0, sticky='nw', padx=10)
        marker_chk.grid(row=1, column=0, sticky='nw', padx=10)
        self.middle_frame.grid_rowconfigure(0, weight=0)
        self.middle_frame.grid_rowconfigure(1, weight=0)
        self.middle_frame.grid_columnconfigure(0, weight=1)

    def update_additional(self):
        """Update the config with the additional Live Safety options,
        then show the final screen"""
        config = self.controller.obs_config
        None if config.has_section('additional') else \
            config.add_section('additional')
        config['additional']['advert'] = str(self.ad_check_value.get())
        config['additional']['clear_chat'] = \
            str(self.clear_chat_check_value.get())
        self.controller.show_frame('SetupComplete')

    def load_additional(self):
        """If there are additional safety options update the form with those
        values
        """
        config = self.controller.obs_config
        None if config.has_section('additional') else \
            config.add_section('additional')
        if config.has_option('additional', 'advert'):
            self.ad_check_value.set(eval(config['additional']['advert']))
        if config.has_option('additional', 'clear_chat'):
            self.clear_chat_check_value.set(
                eval(config['additional']['clear_chat']))


class SetupComplete(SetupPage):
    """The final page of the setup wizard..

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    :param name: The name for the frame widget
    :type name: str
    :cvar controller: The main application GUI
    :cvar top_frame: The header frame
    :cvar middle_frame: The main frame for the wizard pages
    :cvar bottom_frame: The navigation frame
    """

    def __init__(self, parent, controller, name=''):
        headers = (ti.COMPLETE_HEADING, ti.COMPLETE_TEXT)
        footers = (self.complete,
                   lambda:
                   self.controller.show_frame('AdditionalSafetyOptions'),
                   True)
        super().__init__(parent, controller, name, headers, footers)

    def complete(self):
        """Save the config to the local file and quit the setup wizard"""
        save_config(self.controller.obs_config)
        self.controller.destroy()


class TwitchResponseHandler(BaseHTTPRequestHandler):
    """Local web server handler to handle the return request from the Twitch
    authentication portal.  Normally the __init__ method would not be
    overridden but we need to reference the Setup Wizard application
    stored in the object to change frames when complete

    :param controller: A reference to the main TK application
    :type controller: tk.Tk
    :param \*args: List of arguments accepted by BaseHTTPRequestHandler
    :param \*\*kwargs: Dictionary of keyword arguments accepted by
        BaseHTTPRequestHandler
    """

    def __init__(self, controller, *args, **kwargs):
        self.controller = controller
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """GET only serves 2 files, thanks.html and thanks.js. As the twitch
        response is in the document hash, it's easier to get through
        Javascript
        """
        base_dir = os.path.dirname(ti.__file__)
        self.send_response(200)
        file = 'thanks.js' if self.path == '/thanks.js' \
            else 'thanks.html'
        content_type = 'application/ecmascript' if self.path == '/thanks.js' \
            else 'text/html'
        with open(os.path.join(base_dir, file), 'r') as f:
            html = f.read()
        self.send_header('Content-type', content_type)
        self.end_headers()
        self.wfile.write(html.encode())

    def do_POST(self):
        """Receive the Twitch tokens via a POST from thanks.js. Update the
        original setup app with the values received and shut down the web
        server"""
        # Read the POST body and convert from JSON to a dict.
        data_string = self.rfile.read(int(self.headers['Content-Length']))
        new_object = json.loads(data_string.decode('utf-8'))
        # Send headers
        self.send_response(202)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        # Pass the twitch object back to the setup app and shut down the server
        self.controller.frames['LaunchTwitch']. \
            return_from_web_server(new_object)
        safe_shut = threading.Thread(target=self.server.shutdown)
        safe_shut.daemon = True
        safe_shut.start()
