from configparser import ConfigParser
from appdirs import user_config_dir
import os
import tkinter as tk
from tkinter import font as tk_font
from .obs_controls import get_all_sources


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


def _check_overwrite_config(config):
    """Check if a config file has already been loaded and if we should be
    overwriting the settings.

    :param config: The ConfigParser object
    :type config: ConfigParser
    :return: True or False depending on user input
    :rtype: bool
    """
    # Assume there is no config and it's OK to continue
    ret_bool = True
    if config.has_section('obs'):
        # There is config, it might not be OK to continue
        ret_bool = False
        response_loop = True
        while response_loop:
            print()
            print('obs-streamdeck-ctl already has a config file, would you '
                  'like to replace it?')
            r = input('(Y/N) [N]: ')
            if r.upper() in ('N', ''):
                # Stop asking and continue to return False
                response_loop = False
            elif r.upper() == 'Y':
                # Stop asking and return True
                ret_bool = True
                response_loop = False
    return ret_bool


def _get_audio_sources():
    """Ask user for the Microphone and Desktop audio sources, supplying the
    defaults if user entry is blank.

    :return: the Microphone and Desktop audio sources
    :rtype: str, str
    """
    print()
    mic_source = input('Please enter the name of your Microphone source, '
                       '(case sensitive) [Mic/Aux]: ')
    if not mic_source:
        mic_source = 'Mic/Aux'
    print()
    print('Please enter the name of your Desktop audio source, (case '
          'sensitive)')
    desktop_source = input('[Desktop Audio]: ')
    if not desktop_source:
        desktop_source = 'Desktop Audio'
    return mic_source, desktop_source


def _get_alert_overlay_sources():
    """Ask user for the alert overlay source names and return them as a list

    :return: A list of the alert overlays
    :rtype: list
    """
    alert_sources = list()
    response_loop = True
    while response_loop:
        print()
        print('Please enter the source name of your alert and chat overlays one '
              'at a time (case')
        alert_source = input('sensitive). Please enter a blank line when '
                             'complete: ')
        if alert_source:
            alert_sources.append(alert_source)
        else:
            response_loop = False
    return alert_sources


def _get_obsws_password():
    """Ask user for the password for the OBS WebSockets server

    :return: The OBS WebSockets server password
    :rtype: str
    """
    print()
    print('Please enter the password for OBS WebSockets server, or leave '
          'blank for no ')
    obsws_password = input('password []: ')
    return obsws_password


def config_setup(config):
    """Run a CLI wizard to setup the ini file

    :return: The updated ConfigParser object
    :rtype: ConfigParser
    """
    if _check_overwrite_config(config):
        None if config.has_section('obs') else config.add_section('obs')
        # Get the optional password
        obsws_password = _get_obsws_password()
        if obsws_password:
            config['obs']['obsws_password'] = obsws_password
        # Get the audio sources
        mic_source, desktop_source = _get_audio_sources()
        config['obs']['mic_source'] = mic_source
        config['obs']['desktop_source'] = desktop_source
        # Get the alert overlays list
        alert_sources = _get_alert_overlay_sources()
        config['obs']['alert_sources'] = ':'.join(alert_sources)
        # Add the section for the Alert overlay URLs, they can be captured later
        # when the panic button is hit
        None if config.has_section('obs_browser_sources') else \
            config.add_section('obs_browser_sources')
        # Config settings complete
    return config


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

    def __init__(self, config):
        """The main Tkinter GUI for the config setup wizard

        :param config: The ConfigParser object that was loaded from
            config_mgmt.load_config
        :type config
        """
        super().__init__()
        # Add the config to the application, we'll be calling it from some of
        # the wizard frames
        self.config = config
        self.geometry('800x360')
        self.title('OBS Streamdeck Control Setup Wizard')
        self.title_font = tk_font.Font(family='Helvetica', size=18,
                                       weight='bold', slant='italic')
        # Set the main app container frame
        container = tk.Frame(self)
        container.pack(side='top', fill='both', expand=True)
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
                  ObsAlertSources):
            page_name = f.__name__
            frame = f(container, self)
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


class SetupPage(tk.Frame):
    """A superclass frame that should not be called directly, but instead
    creates
    the split between the main wizard section at the top and the navigation
    buttons below.

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.top_frame = tk.Frame(self)
        self.bottom_frame = tk.Frame(self)
        # use grid layouts to create a 10:1 split between the top config frame
        # and the lower navigation one
        self.top_frame.grid(row=0, column=0, sticky='nsew')
        self.bottom_frame.grid(row=1, column=0, sticky='nsew')
        self.grid_rowconfigure(0, weight=10)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)


class WelcomePage(SetupPage):
    """Introduction page for the Setup Wizard

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    """

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        heading = tk.Label(self.top_frame, text='OBS Streamdeck Control Setup',
                           font=self.controller.title_font)
        heading.pack(side='top', fill='x', pady=10)
        description_text = 'Welcome to the setup wizard for OBS Streamdeck ' \
                           'Controls.'
        description = tk.Label(self.top_frame, text=description_text)
        description.pack(side='top', fill='x', pady=10)
        next_btn = tk.Button(self.bottom_frame, text='Next',
                             command=self.check_existing)
        next_btn.pack(side='right', padx=10)

    def check_existing(self):
        """Check the controller to see if the loaded config file had valid
        sections.  If it did redirect the user to a confirmation page about
        changing existing configs, otherwise step past to the OBS WebSockets
        Password configuration
        """
        if self.controller.config.has_section('obs'):
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
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        heading = tk.Label(self.top_frame,
                           text='Existing Configuration Warning',
                           font=self.controller.title_font)
        heading.pack(side='top', fill='x', pady=10)
        desc_text = 'OBS Streamdeck Control already has a config file. Press ' \
                    'Next to replace it, or Cancel to exit the Setup Wizard'
        description = tk.Label(self.top_frame, text=desc_text)
        description.pack(side='top', fill='x', pady=10)
        next_btn = tk.Button(self.bottom_frame, text='Next',
                             command=lambda:
                             controller.show_frame('ObsWsPass'))
        next_btn.pack(side='right', padx=10)
        cancel_btn = tk.Button(self.bottom_frame, text='Cancel',
                               command=controller.destroy)
        cancel_btn.pack(side='right', padx=10)


class ObsWsPass(SetupPage):
    """A Page to determine the password for the OBS WebSockets server, if any.

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    """
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        # Set the password as a tk variable and load it from config if possible
        self.obsws_pass = tk.StringVar()
        self.obsws_pass.set(self.load_password())
        desc_text = 'Please enter the password for OBS WebSockets server, ' \
                    'or leave blank for no password'
        description = tk.Label(self.top_frame, text=desc_text)
        description.pack(side='top', fill='x', pady=10)
        obsws_pass_entry = tk.Entry(self.top_frame,
                                    textvariable=self.obsws_pass)
        obsws_pass_entry.pack(side='top', pady=10)
        next_btn = tk.Button(self.bottom_frame, text='Next',
                             command=self.update_password)
        next_btn.pack(side='right', padx=10)
        cancel_btn = tk.Button(self.bottom_frame, text='Cancel',
                               command=controller.destroy)
        cancel_btn.pack(side='right', padx=10)

    def load_password(self):
        """If there is an existing password, return that value.

        :return: The existing password
        :rtype: str
        """
        config = self.controller.config
        # Make sure there is an 'obs' section in the config, adding it if
        # there isn't
        None if config.has_section('obs') else config.add_section('obs')
        if config.has_option('obs', 'obsws_password'):
            return config['obs']['obsws_password']
        else:
            return ''

    def update_password(self):
        """Get the updated value from the entry box and update the config
        before moving onto the next frame
        """
        config = self.controller.config
        config['obs']['obsws_password'] = self.obsws_pass.get()
        self.controller.show_frame('ObsAudioSources')


class ObsAudioSources(SetupPage):
    """A Page to determine the Microphone and Desktop Audio sources in OBS.

    :param parent: The parent frame to attach this frame to
    :type parent: tk.Frame
    :param controller: The main application GUI
    :type controller: tk.Tk
    """

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        # Set the sources as a tk variable and load them from config if possible
        self.mic_source = tk.StringVar()
        self.desktop_source = tk.StringVar()
        self.mic_source.set(self.load_mic_source())
        self.desktop_source.set(self.load_desktop_source())

        desc_text = 'Please select your Microphone and Desktop Audio sources'
        description = tk.Label(self.top_frame, text=desc_text)
        description.pack(side='top', fill='x', pady=10)
        mic_source_entry = tk.Entry(self.top_frame,
                                    textvariable=self.mic_source)
        mic_source_entry.pack(side='top', pady=10)
        desktop_source_entry = tk.Entry(self.top_frame,
                                        textvariable=self.desktop_source)
        desktop_source_entry.pack(side='top', pady=10)
        next_btn = tk.Button(self.bottom_frame, text='Next',
                             command=self.update_sources)
        next_btn.pack(side='right', padx=10)
        back_btn = tk.Button(self.bottom_frame, text='Back',
                             command=lambda:
                             self.controller.show_frame('ObsWsPass'))
        back_btn.pack(side='right', padx=10)
        cancel_btn = tk.Button(self.bottom_frame, text='Cancel',
                               command=controller.destroy)
        cancel_btn.pack(side='right', padx=10)

    def load_mic_source(self):
        """If there is an existing Mic source, return that value, otherwise
        return the default

        :return: The existing password
        :rtype: str
        """
        config = self.controller.config
        # Make sure there is an 'obs' section in the config, adding it if
        # there isn't
        None if config.has_section('obs') else config.add_section('obs')
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
        config = self.controller.config
        # Make sure there is an 'obs' section in the config, adding it if
        # there isn't
        None if config.has_section('obs') else config.add_section('obs')
        if config.has_option('obs', 'desktop_source'):
            return config['obs']['desktop_source']
        else:
            return 'Desktop Audio'

    def update_sources(self):
        config = self.controller.config
        config['obs']['mic_source'] = self.mic_source.get()
        config['obs']['desktop_source'] = self.desktop_source.get()
        self.controller.show_frame('ObsAlertSources')


class ObsAlertSources(SetupPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)