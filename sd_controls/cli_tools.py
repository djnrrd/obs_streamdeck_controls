import argparse
from .sd_controls import *
import sys
import os

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


def _do_action(arg):
    """Check the command line arguments and run the appropriate function

    :param arg: The command line arguments as gathered by argparser
    :type arg: argparse.ArgumentParser
    """
    if arg.action == 'panic_button':
        panic_button()
    elif arg.action == 'start_stop':
        start_stop_stream()
    elif arg.action == 'mute_mic':
        mute_mic_audio()
    elif arg.action == 'mute_desk':
        mute_desktop_audio()
    elif arg.action == 'mute_all':
        mute_both_audio()
    elif arg.action == 'scene':
        set_scene(arg.scene_number)
    elif arg.action == 'setup':
        config_setup()
    else:
        raise ValueError('Could not find a valid action from the command line '
                         'arguments')


def config_setup():
    # Check if config exists
    if CONFIG.has_section('obs'):
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
    CONFIG.add_section('obs')
    # Get the optional password
    obsws_password = input('Please enter the password for OBS WebSockets '
                            'server, or leave blank for no password []: ')
    if obsws_password:
        CONFIG['obs']['obsws_password'] = obsws_password
    # Get the mic source
    mic_source = input('Please enter the name of your Microphone source, '
                       '(case sensitive) [Mic/Aux]: ')
    if not mic_source:
        mic_source = 'Mic/Aux'
    CONFIG['obs']['mic_source'] = mic_source
    # Get the desktop audio source
    desktop_source = input('Please enter the name of your Desktop audio '
                           'source, (case sensitive) [Desktop Audio]: ')
    if not desktop_source:
        desktop_source = 'Desktop Audio'
    CONFIG['obs']['desktop_source'] = desktop_source
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
    CONFIG['obs']['alert_sources'] = ':'.join(alert_sources)
    # Add the section for the Alert overlay URLs, they can be captured later
    # when the panic button is hit
    CONFIG.add_section('obs_browser_sources')
    # Make sure the directory exists
    if not all([os.path.exists(CONFIG_DIR), os.path.isdir(CONFIG_DIR)]):
        os.mkdir(CONFIG_DIR)
    # Save the config file
    with open(CONFIG_FILE, 'w') as f:
        CONFIG.write(f)

def main():
    parser = _add_args()
    arg = parser.parse_args()
    _do_action(arg)


if __name__ == '__main__':
    main()
