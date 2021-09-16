import argparse
from .obs_controls import mute_audio_source, start_stop_stream, set_scene, \
    get_source_settings, set_source_settings
from .config_mgmt import load_config, SetupApp
from .twitch_controls import start_stop_safety, live_safety


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
    sub_parser.add_parser('live_safety',
                          description='Disable/Enable alert sources in OBS '
                                      'and lockdown Twitch chat in case of '
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
    :param config: Config details loaded by ConfigParser
    :type config: ConfigParser
    """
    config = load_config()
    if config.has_option('obs', 'ws_password'):
        ws_password = config['obs']['ws_password']
    else:
        ws_password = ''
    if arg.action == 'setup':
        app = SetupApp(config)
        app.mainloop()
    elif arg.action == 'live_safety':
        live_safety_button(config, ws_password)
    elif arg.action == 'start_stop':
        start_stop(config, ws_password)
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


def start_stop(config, ws_password):
    """Start/Stop streaming in OBS and if twitch chat safety features have
    been enabled switch those as well

    :param config: Config details loaded by ConfigParser
    :type config: ConfigParser
    :param ws_password: The password for the OBS WebSockets server
    :type ws_password: str
    """
    start_stop_stream(ws_password)
    if config.has_option('start_stop_safety', 'enabled'):
        username = config['twitch']['channel']
        token = config['twitch']['oauth_token']
        enabled = eval(config['start_stop_safety']['enabled'])
        emote_mode = eval(config['start_stop_safety']['emote_mode']) if \
            config.has_option('start_stop_safety', 'emote_mode') else False
        method = config['start_stop_safety']['method'] if \
            config.has_option('start_stop_safety', 'method') else ''
        follow_time = config['start_stop_safety']['follow_time'] if \
            config.has_option('start_stop_safety', 'follow_time') else ''
        start_stop_safety(username, token, enabled, emote_mode, method,
                          follow_time)


def live_safety_button(config, ws_password):
    """Sadly, people are performing "hate raids" on twitch, raiding channels
    and getting bot accounts to follow the streamer and spam chat with
    hateful messages.

    The follows will cause sound alert overlays to queue up notifications,
    so this function will disable and re-enable those overlays as configured
    in the ini file.  Additionally, chat safety features can be enabled

    :param config: ConfigParser object created in cli_tools
    :type config: ConfigParser
    :param ws_password: The password for the OBS WebSockets server
    :type ws_password: str
    """
    for source in config['obs']['alert_sources'].split(':'):
        # Get the current settings for the alert source from OBS.
        settings = get_source_settings(source, ws_password)
        # Swap between invalid.lan and the value from config
        if settings['url'] == 'http://invalid.lan':
            settings['url'] = config['obs_browser_sources'][source]
        else:
            settings['url'] = 'http://invalid.lan'
        # Update the settings in OBS
        set_source_settings(source, settings, ws_password)
    if config.has_option('live_safety', 'enabled'):
        username = config['twitch']['channel']
        token = config['twitch']['oauth_token']
        # Use eval to make sure the string 'False' is passed as a boolean False
        enabled = eval(config['live_safety']['enabled'])
        emote_mode = eval(config['live_safety']['emote_mode']) if \
            config.has_option('live_safety', 'emote_mode') else False
        method = config['live_safety']['method'] if \
            config.has_option('live_safety', 'method') else ''
        follow_time = config['live_safety']['follow_time'] if \
            config.has_option('live_safety', 'follow_time') else ''
        advert = eval(config['additional']['advert']) if \
            config.has_option('additional', 'advert') else False
        clear_chat = eval(config['additional']['clear_chat']) if \
            config.has_option('additional', 'clear_chat') else False
        live_safety(username, token, enabled, emote_mode, method,
                    follow_time, advert, clear_chat)


def main():
    """Entry point for the console script 'obs-streamdeck-ctl'
    """
    # Get CLI arguments
    parser = _add_args()
    arg = parser.parse_args()
    # Main functions.
    _do_action(arg)


if __name__ == '__main__':
    main()
