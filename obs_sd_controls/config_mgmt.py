from configparser import ConfigParser
from appdirs import user_config_dir
import os
import tkinter as tk
from tkinter import font as tk_font
from tkinter import messagebox as tk_mb
from .obs_controls import get_all_sources
from . import text_includes as ti
from .conf import CLIENT_ID, REDIRECT_URI
import webbrowser

def load_config():
    """Load the config file and return the ConfigParser object

    :return: the ConfigParser object
    :rtype: ConfigParser
    """
    # Attempt to load the config file
    config_dir = user_config_dir('obs-streamdeck-ctl')
    config_file = os.path.join(config_dir, 'obs-streamdeck.ini')
    config = ConfigParser()
    config.read(config_file)
    return config


def save_config(config):
    """Save the config file to the user's local config directory.

    :param config: The ConfigParser object
    :type config: ConfigParser
    """
    config_dir = user_config_dir('obs-streamdeck-ctl')
    config_file = os.path.join(config_dir, 'obs-streamdeck.ini')
    if not all([os.path.exists(config_dir), os.path.isdir(config_dir)]):
        os.mkdir(config_dir)
    with open(config_file, 'w') as f:
        config.write(f)


def swap_browser_sources(config, source, url):
    if not config.has_option('obs_browser_sources', source):
        config['obs_browser_sources'][source] = url
    # Swap Browser source between saved URl and invalid.lan
    if url == config['obs_browser_sources'][source]:
        url = 'http://invalid.lan'
    elif url == 'http://invalid.lan':
        url = config['obs_browser_sources'][source]
    else:
        raise ValueError('Browser source matches neither the saved value '
                         'in the ini file or \'http://invalid.lan/\'')
    return url, config


class SetupApp(tk.Tk):
    """The main Tkinter GUI for the config setup wizard

    :param config: The ConfigParser object that was loaded from
        config_mgmt.load_config
    :type config
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
        self.show_frame('LaunchTwitch')

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
                  ObsAlertSources, LaunchTwitch):
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
    creates the split between the main wizard section at the top and the
    navigation buttons below.

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    :cvar controller: The main application GUI
    :cvar top_frame: The main frame for the wizard pages
    :cvar bottom_frame: The navigation frame
    """

    def __init__(self, parent, controller, name=''):
        super().__init__(parent, name=name)
        self.controller = controller
        # Create 2 frames The top one is for the actual config bits and the
        # lower one for navigation
        self.top_frame = tk.Frame(self, name='top_frame')
        self.bottom_frame = tk.Frame(self, name='bottom_frame')
        # Favour the top row, so the bottom row is only as big as it needs to
        # be with a little padding
        self.top_frame.grid(row=0, column=0, sticky='nsew')
        self.bottom_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

    def setup_navigation(self, next_function, back_function=None, final=False):
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

    def setup_header(self, header_text, body_text, col_span=1):
        """Setup the heading section in the top frame. Weighting of the grid
        sections is not completed in this function, and should be completed
        after the other components have been laid out

        :param header_text: The text to render as the header for the frame
        :type header_text: str
        :param body_text: The text to render as the body for the frame
        :type body_text: str
        :param col_span: If the header section
        :return:
        """
        heading = tk.Label(self.top_frame, text=header_text,
                           font=self.controller.title_font)
        heading.grid(row=0, column=0, sticky='nsew', pady=10,
                     columnspan=col_span)
        description = tk.Message(self.top_frame, text=body_text, width=780)
        description.grid(row=1, column=0, sticky='nw', columnspan=col_span,
                         pady=10, padx=5)

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

    def setup_list_frame(self, select_mode='single'):
        """Create a frame for a list box with a scroll bar to be added to the
        top frame. Weighting of the outer grid sections is not completed in
        this function, and should be completed after the other components have
        been laid out

        :return: The frame and listbox for further interaction
        :rtype: (tk.Frame, tk.Listbox)
        """
        frame = tk.Frame(self.top_frame)
        list_box = tk.Listbox(frame, selectmode=select_mode)
        list_box.grid(row=0, column=0)
        scroll = tk.Scrollbar(frame)
        scroll.grid(row=0, column=1, sticky='ns')
        scroll.config(command=list_box.yview)
        list_box.config(yscrollcommand=scroll.set)
        return frame, list_box


class WelcomePage(SetupPage):
    """Introduction page for the Setup Wizard

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    """

    def __init__(self, parent, controller, name=''):
        super().__init__(parent, controller, name=name)
        self.setup_header(ti.WELCOME_HEADING, ti.WELCOME_TEXT)
        # Favour the body of the text over the header
        self.top_frame.grid_rowconfigure(0, weight=0)
        self.top_frame.grid_rowconfigure(1, weight=1)
        self.top_frame.grid_columnconfigure(0, weight=1)
        self.setup_navigation(self.check_existing)

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


class ExistingConfig(SetupPage):
    """A Page to confirm if the user is happy to edit their already existing
    config, as determined after the Welcome page

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    """
    def __init__(self, parent, controller, name=''):
        super().__init__(parent, controller, name=name)
        self.setup_header(ti.EXISTING_HEADING, ti.EXISTING_TEXT)
        # Favour the body of the text over the header
        self.top_frame.grid_rowconfigure(0, weight=0)
        self.top_frame.grid_rowconfigure(1, weight=1)
        self.top_frame.grid_columnconfigure(0, weight=1)
        self.setup_navigation(lambda: controller.show_frame('ObsWsPass'))


class ObsWsPass(SetupPage):
    """A Page to determine the password for the OBS WebSockets server, if any.

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    """
    def __init__(self, parent, controller, name=''):
        super().__init__(parent, controller, name=name)
        # Set the password as a tk variable and load it from config if possible
        self.obsws_pass = tk.StringVar()
        self.obsws_pass.set(self.load_password())
        # Layout
        self.setup_header(ti.OBSWSPASS_HEADING, ti.OBSWSPASS_TEXT, 2)
        password_prompt = tk.Label(self.top_frame, text=ti.OBSWSPASS_PROMPT)
        password_prompt.grid(row=2, column=0, sticky='ne', padx=5)
        obsws_pass_entry = tk.Entry(self.top_frame,
                                    textvariable=self.obsws_pass)
        obsws_pass_entry.grid(row=2, column=1, sticky='nw')
        # Prefer the bottom row to force everything up and the right hand
        # column to force everything left
        self.top_frame.grid_rowconfigure(0, weight=0)
        self.top_frame.grid_rowconfigure(1, weight=0)
        self.top_frame.grid_rowconfigure(2, weight=1)
        self.top_frame.grid_columnconfigure(0, weight=0)
        self.top_frame.grid_columnconfigure(1, weight=1)
        self.setup_navigation(self.update_password)

    def load_password(self):
        """If there is an existing password, return that value.

        :return: The existing password
        :rtype: str
        """
        config = self.controller.obs_config
        # Make sure there is an 'obs' section in the config, adding it if
        # there isn't since this is the first time we're checking
        None if config.has_section('obs') else config.add_section('obs')
        if config.has_option('obs', 'obsws_password'):
            return config['obs']['obsws_password']
        else:
            return ''

    def update_password(self):
        """Get the updated value from the entry box and update the config.
        Before showing the next frame, load the sources from OBS
        """
        config = self.controller.obs_config
        config['obs']['obsws_password'] = self.obsws_pass.get()
        self.get_obs_sources()

    def get_obs_sources(self):
        """Load the OBS Source list from the OBS WebSockets interface,
        raising an alert if we're unable to connect.  Then pass that list to
        the next frame to load into its Listbox before showing the next frame
        """
        self.controller.show_busy()
        config = self.controller.obs_config
        try:
            obs_sources = get_all_sources(config['obs']['obsws_password'])
            self.controller.clear_busy()
            self.controller.frames['ObsAudioSources'].\
                load_obs_sources(obs_sources)
            self.controller.show_frame('ObsAudioSources')
        except (ConnectionRefusedError, NameError):
            self.controller.clear_busy()
            tk_mb.showwarning(title=ti.OBSWSPASS_WARN_HEADER,
                              message=ti.OBSWSPASS_WARN)


class ObsAudioSources(SetupPage):
    """A Page to determine the Microphone and Desktop Audio sources in OBS.

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    """

    def __init__(self, parent, controller, name=''):
        super().__init__(parent, controller, name=name)
        # Set the sources as a tk variable and load them from config if possible
        self.mic_source = tk.StringVar()
        self.desktop_source = tk.StringVar()
        self.mic_source.set(self.load_mic_source())
        self.desktop_source.set(self.load_desktop_source())
        # Layout
        self.setup_header(ti.OBSAUDIO_HEADING, ti.OBSAUDIO_TEXT, 3)
        listbox_frame, self.obs_sources = self.setup_list_frame()
        listbox_frame.grid(row=2, column=0, rowspan=6, padx=5, sticky='ne')
        mic_source_button = tk.Button(self.top_frame, text=' > ',
                                      command=self.select_mic_source)
        mic_source_button.grid(row=3, column=1, padx=10, sticky='ew')
        mic_source_label = tk.Label(self.top_frame, text=ti.OBSAUDIO_MIC_PROMPT)
        mic_source_label.grid(row=2, column=2, sticky='sw')
        mic_source_entry = tk.Entry(self.top_frame,
                                    textvariable=self.mic_source)
        mic_source_entry.grid(row=3, column=2, sticky='w')
        desktop_source_button = tk.Button(self.top_frame, text=' > ',
                                          command=self.select_desktop_source)
        desktop_source_button.grid(row=6, column=1, padx=10, sticky='ew')
        desktop_source_label = tk.Label(self.top_frame,
                                        text=ti.OBSAUDIO_DESK_PROMPT)
        desktop_source_label.grid(row=5, column=2, sticky='sw')
        desktop_source_entry = tk.Entry(self.top_frame,
                                        textvariable=self.desktop_source)
        desktop_source_entry.grid(row=6, column=2, sticky='w')
        # Prefer the bottom row to force everything up and the right hand
        # column to force everything left
        self.top_frame.grid_rowconfigure(0, weight=0)
        self.top_frame.grid_rowconfigure(1, weight=0)
        self.top_frame.grid_rowconfigure(2, weight=0)
        self.top_frame.grid_rowconfigure(3, weight=0)
        self.top_frame.grid_rowconfigure(4, weight=0)
        self.top_frame.grid_rowconfigure(5, weight=0)
        self.top_frame.grid_rowconfigure(6, weight=0)
        self.top_frame.grid_columnconfigure(0, weight=0)
        self.top_frame.grid_columnconfigure(1, weight=0)
        self.top_frame.grid_columnconfigure(2, weight=1)
        self.setup_navigation(self.update_sources, lambda:
                              self.controller.show_frame('ObsWsPass'))

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
    """A Page to determine the Notifcation and chat sources in OBS that would be
    disabled in the Panic Button functions.

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    """

    def __init__(self, parent, controller, name=''):
        super().__init__(parent, controller, name=name)
        self.setup_header(ti.OBSALERT_HEADING, ti.OBSALERT_TEXT, 3)
        obs_source_label = tk.Label(self.top_frame,
                                    text=ti.OBSALERT_SOURCE_PROMPT)
        obs_source_label.grid(row=2, column=0, padx=5)
        # Setup the first Frame and listbox
        obs_frame, self.obs_sources = self.setup_list_frame('extended')
        obs_frame.grid(row=3, column=0, padx=5, rowspan=5)
        add_source_button = tk.Button(self.top_frame, text=' > ',
                                      command=self.select_alert_source)
        add_source_button.grid(row=4, column=1, padx=10)
        remove_source_button = tk.Button(self.top_frame, text=' < ',
                                         command=self.remove_alert_source)
        remove_source_button.grid(row=6, column=1, padx=10)
        alert_source_label = tk.Label(self.top_frame,
                                    text=ti.OBSALERT_ALERT_PROMPT)
        alert_source_label.grid(row=2, column=2, padx=5)
        alert_frame, self.alert_sources = self.setup_list_frame('extended')
        alert_frame.grid(row=3, column=2, padx=5, rowspan=5)
        # Prefer the bottom row to force everything up and the right hand
        # column to force everything left
        self.top_frame.grid_rowconfigure(0, weight=0)
        self.top_frame.grid_rowconfigure(1, weight=0)
        self.top_frame.grid_rowconfigure(2, weight=0)
        self.top_frame.grid_rowconfigure(3, weight=0)
        self.top_frame.grid_rowconfigure(4, weight=0)
        self.top_frame.grid_rowconfigure(5, weight=0)
        self.top_frame.grid_rowconfigure(6, weight=0)
        self.top_frame.grid_rowconfigure(7, weight=0)
        self.top_frame.grid_columnconfigure(0, weight=1)
        self.top_frame.grid_columnconfigure(1, weight=0)
        self.top_frame.grid_columnconfigure(2, weight=1)
        self.setup_navigation(self.update_sources, lambda:
                              self.controller.show_frame('ObsAudioSources'),
                              True)
        # Load the default alert sources after the layout since we're adding
        # directly to the listbox
        self.load_default_alert_sources()

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
        the config. Then save the config and close the setup wizard"""
        alerts = self.alert_sources.get(0, 'end')
        config = self.controller.obs_config
        config['obs']['alert_sources'] = ':'.join(alerts)
        save_config(config)
        self.controller.destroy()


class LaunchTwitch(SetupPage):

    def __init__(self, parent, controller, name=''):
        super().__init__(parent, controller, name=name)
        self.setup_header(ti.LAUNCH_TWITCH_HEADING, ti.LAUNCH_TWITCH_TEXT)
        self.setup_navigation(self.launch_browser,
                              lambda: self.controller.show_frame(
                                                            'ObsAlertSources'))

    def launch_browser(self):
        # Disable my next button
        next_button_path = 'main_frame.launchtwitch.bottom_frame.next'
        self.controller.nametowidget(next_button_path)['state'] = 'disabled'
        url = 'https://id.twitch.tv/oauth2/authorize'
        params = {'client_id': CLIENT_ID, 'redirect_uri': REDIRECT_URI,
                  'response_type': 'token',
                  'scope': 'channel:moderate chat:edit chat:read'}
        url += '&'.join([f"{k}={v}" for k, v in params.items()])
        #webbrowser.open_new_tab(url)

