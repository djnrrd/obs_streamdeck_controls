import argparse
from .obs_controls import panic_button, mute_audio_source, start_stop_stream, \
    set_scene
from .config_mgmt import load_config, save_config, config_setup


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


def _do_action(arg, config):
    """Check the command line arguments and run the appropriate function

    :param arg: The command line arguments as gathered by argparser
    :type arg: argparse.ArgumentParser
    :param config: Config details loaded by ConfigParser
    :type config: ConfigParser
    """
    if config.has_option('obs', 'obsws_password'):
        ws_password = config['obs']['obsws_password']
    else:
        ws_password = ''
    if arg.action == 'setup':
        config = config_setup(config)
    elif arg.action == 'panic_button':
        panic_button(config, ws_password)
    elif arg.action == 'start_stop':
        start_stop_stream(ws_password)
    elif arg.action == 'mute_mic':
        mute_audio_source(config['obs']['mic_source'], ws_password)
    elif arg.action == 'mute_desk':
        mute_audio_source(config['obs']['desktop_source'], ws_password)
    elif arg.action == 'mute_all':
        for source in (config['obs']['desktop_source'],
                       config['obs']['mic_source']):
            mute_audio_source(source, ws_password)
    elif arg.action == 'scene':
        set_scene(arg.scene_number, ws_password)
    else:
        raise ValueError('Could not find a valid action from the command line '
                         'arguments')
    return config


def main():
    """Entry point for the console script 'obs-streamdeck-ctl'
    """
    config = load_config()
    # Get CLI arguments
    parser = _add_args()
    arg = parser.parse_args()
    # Main functions.
    config = _do_action(arg, config)
    # Finally save the config, checking to make sure the directory exists
    save_config(config)


if __name__ == '__main__':
    main()
