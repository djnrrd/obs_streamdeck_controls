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

    def __init__(self, config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.geometry('800x360')
        self.title('obs-streamdeck-ctl Setup')
        self.frames = dict()
        self.title_font = tk_font.Font(family='Helvetica', size=18,
                                       weight='bold', slant='italic')
        container = tk.Frame(self)
        container.pack(side='top', fill='both', expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        for f in (WelcomePage, ExistingConfig, ObsWsPass, ObsAudioSources):
            page_name = f.__name__
            frame = f(container, self)
            frame.grid(row=0, column=0, sticky='nsew')
            self.frames[page_name] = frame
        self.show_frame('WelcomePage')

    def show_frame(self, page_name):
        """Show a frame for the given page name"""
        frame = self.frames[page_name]
        frame.tkraise()


class SetupPage(tk.Frame):

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.top_frame = tk.Frame(self)
        self.bottom_frame = tk.Frame(self)
        self.top_frame.grid(row=0, column=0, sticky='nsew')
        self.bottom_frame.grid(row=1, column=0, sticky='nsew')
        self.grid_rowconfigure(0, weight=10)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        heading = tk.Label(self.top_frame, text='obs-streamdeck-ctl Setup',
                           font=self.controller.title_font)
        heading.pack(side='top', fill='x', pady=10)


class WelcomePage(SetupPage):

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        description = tk.Label(self.top_frame, text='Welcome to the setup '
                                                    'wizard for the TKinker '
                                                    'tinker project')
        description.pack(side='top', fill='x', pady=10)
        next_btn = tk.Button(self.bottom_frame, text='Next',
                             command=self.check_existing)
        next_btn.pack(side='right', padx=10)

    def check_existing(self):
        if self.controller.config.has_section('obs'):
            self.controller.show_frame('ExistingConfig')
        else:
            self.controller.show_frame('ObsWsPass')


class ExistingConfig(SetupPage):

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        desc_text = 'obs-streamdeck-ctl already has a config file. Press Next ' \
                    'to replace it, or Cancel to exit the Setup Wizard'
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

    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.obsws_pass = tk.StringVar()
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

    def update_password(self):
        config = self.controller.config
        None if config.has_section('obs') else config.add_section('obs')
        config['obs']['obsws_password'] = self.obsws_pass.get()
        save_config(config)
        self.controller.show_frame('ObsAudioSources')


class ObsAudioSources(SetupPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)