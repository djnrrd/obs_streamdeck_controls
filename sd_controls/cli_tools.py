import argparse
from .sd_controls import panic_button, mute_mic_audio, mute_desktop_audio, \
    mute_both_audio, start_stop_stream, set_scene
import simpleobsws
import sys
import os
from configparser import ConfigParser
from appdirs import user_config_dir


def _add_args():
    """Set up the script arguments using argparser

    :return: The argparse parser object
    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser()
    sub_parser = parser.add_subparsers(dest='action', required=True)
    sub_parser.add_parser('start_stop', description='Start/Stop the stream')
    sub_parser.add_parser('mute_mic',
                          description='Mute/Unmute the Microphone source')
    sub_parser.add_parser('mute_desk',
                          description='Mute/Unmute the Desktop audio source')
    sub_parser.add_parser('mute_all',
                          description='Mute/Unmute both Desktop and Microphone '
                                      'sources')
    sub_parser.add_parser('panic_button',
                          description='Disable/Enable alert sources in case of '
                                      'hate raids')
    scene_parser = sub_parser.add_parser('scene',
                                         description='Switch between scenes in '
                                                     'OBS')
    scene_parser.add_argument('scene_number', type=int,
                              help='The scene number to select (from the top '
                                   'down)')
    sub_parser.add_parser('setup', description='Run the setup wizard to '
                                               'create your configuration file')
    return parser


def config_setup(config, config_dir, config_file):
    """Run a CLI wizard to setup the ini file
    """
    # Check if config exists
    if config.has_section('obs'):
        response_loop = True
        while response_loop:
            r = input('obs-streamdeck-ctl already has a config file, would you '
                      'like to replace it? (Y/N) [N]: ')
            if r.upper() in ('N', ''):
                print('Exiting obs-streamdeck-ctl')
                sys.exit()
            elif r.upper() == 'Y':
                response_loop = False
    # The user has confirmed Y to the are you sure question
    config.add_section('obs')
    # Get the optional password
    obsws_password = input('Please enter the password for OBS WebSockets '
                            'server, or leave blank for no password []: ')
    if obsws_password:
        config['obs']['obsws_password'] = obsws_password
    # Get the mic source
    mic_source = input('Please enter the name of your Microphone source, '
                       '(case sensitive) [Mic/Aux]: ')
    if not mic_source:
        mic_source = 'Mic/Aux'
    config['obs']['mic_source'] = mic_source
    # Get the desktop audio source
    desktop_source = input('Please enter the name of your Desktop audio '
                           'source, (case sensitive) [Desktop Audio]: ')
    if not desktop_source:
        desktop_source = 'Desktop Audio'
    config['obs']['desktop_source'] = desktop_source
    # Get the alert overlays list
    alert_sources = list()
    response_loop = True
    while response_loop:
        alert_source = input('Please enter the source name of your alert and '
                             'chat overlays one at a time (case sensitive). '
                             'Please enter a blank line when complete: ')
        if alert_source:
            alert_sources.append(alert_source)
        else:
            response_loop = False
    config['obs']['alert_sources'] = ':'.join(alert_sources)
    # Add the section for the Alert overlay URLs, they can be captured later
    # when the panic button is hit
    config.add_section('obs_browser_sources')


def _do_action(arg, config, ws):
    """Check the command line arguments and run the appropriate function

    :param arg: The command line arguments as gathered by argparser
    :type arg: argparse.ArgumentParser
    :param config: Config details loaded by ConfigParser
    :type config: ConfigParser
    :param ws: OBS WebSockets library
    :type ws: simpleobsws.obsws
    """
    if arg.action == 'panic_button':
        panic_button(config, ws)
    elif arg.action == 'start_stop':
        start_stop_stream(ws)
    elif arg.action == 'mute_mic':
        mute_mic_audio(config, ws)
    elif arg.action == 'mute_desk':
        mute_desktop_audio(config, ws)
    elif arg.action == 'mute_all':
        mute_both_audio(config, ws)
    elif arg.action == 'scene':
        set_scene(ws, arg.scene_number)
    else:
        raise ValueError('Could not find a valid action from the command line '
                         'arguments')


def main():
    """Entry point for the console script 'obs-streamdeck-ctl'
    """
    # Attempt to load the config file
    config_dir = user_config_dir('obs-streamdeck-ctl')
    config_file = os.path.join(config_dir, 'obs-streamdeck.ini')
    config = ConfigParser()
    config.read(config_file)
    # Load OBS WebServices object
    if config.has_option('obs', 'obsws_password'):
        ws = simpleobsws.obsws(password=config['obs']['obsws_password'])
    else:
        ws = simpleobsws.obsws()
    # Get CLI arguments
    parser = _add_args()
    arg = parser.parse_args()
    # First check if we need to do setup of the ini file, otherwise over to
    # the main functions.
    if arg.action == 'setup':
        config_setup(config, config_dir, config_file)
    else:
        _do_action(arg, config, ws)
    # Finally save the config, checking to make sure the directory exists
    if not all([os.path.exists(config_dir), os.path.isdir(config_dir)]):
        os.mkdir(config_dir)
    with open(config_file, 'w') as f:
        config.write(f)


if __name__ == '__main__':
    main()
