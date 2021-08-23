from configparser import ConfigParser
from appdirs import user_config_dir
import os


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