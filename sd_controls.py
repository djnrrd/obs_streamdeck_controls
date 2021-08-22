import asyncio
import simpleobsws
import argparse
from configparser import ConfigParser
from os import path

work_dir = path.dirname(path.abspath(__file__))
config_file = path.join(work_dir, 'sd_controls.ini')
config = ConfigParser()
config.read(config_file)

ws = simpleobsws.obsws(password=config['obs']['obsws_password'])

loop = asyncio.get_event_loop()


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
    return parser


async def _ws_toggle_mute(source):
    """Use the OBS-Websocket to mute/unmute an audio source

    :param source: The OBS audio source to mute/unmute
    :type source: str
    """
    # Make the connection to obs-websocket
    await ws.connect()
    data = {'source': source}
    await ws.call('ToggleMute', data)
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await ws.disconnect()


async def _ws_get_scene_list():
    """Use the OBS-Websocket to get the list of scenes

    :return: The currently active scene and an ordered list of all scenes
        configured in OBS
    :rtype: dict
    """
    # Make the connection to obs-websocket
    await ws.connect()
    result = await ws.call('GetSceneList')
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await ws.disconnect()
    return result


async def _ws_set_scene(scene):
    """Use the OBS-Websocket to set the current scene

    :param scene: The name of the scene in OBS to make active
    :type scene: str
    """
    # Make the connection to obs-websocket
    await ws.connect()
    data = {'scene-name': scene}
    await ws.call('SetCurrentScene', data)
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await ws.disconnect()


async def _ws_start_stop_stream():
    """Use the OBS-Websocket to start or stop streaming
    """
    # Make the connection to obs-websocket
    await ws.connect()
    await ws.call('StartStopStreaming')
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await ws.disconnect()


async def _ws_get_source_settings(source):
    """Use the OBS-Websocket to get the settings for a source

    :param source: The OBS source to get the settings for
    :type source: str
    :return: Details on the source name, type and the settings for the source
    :rtype: dict
    """
    # Make the connection to obs-websocket
    await ws.connect()
    data = {'sourceName': source}
    result = await ws.call('GetSourceSettings', data)
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await ws.disconnect()
    return result


async def _ws_set_source_settings(source, settings):
    """Use the OBS-Websocket to set new settings for a source

    :param source: The OBS source to update
    :type source: str
    :param settings: The updated settings to apply to the source in the same
        format as the sourceSettings section returned from
        _ws_get_source_settings
    :type settings: dict
    :return: Details on the source name, type and the updated settings for the
        source
    :rtype: dict
    """
    # Make the connection to obs-websocket
    await ws.connect()
    data = {'sourceName': source, 'sourceSettings': settings}
    result = await ws.call('SetSourceSettings', data)
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await ws.disconnect()
    return result


def mute_desktop_audio():
    """Mute/Unmute the Desktop audio source as configured in sd_controls.ini
    """
    loop.run_until_complete(_ws_toggle_mute(config['obs']['desktop_source']))


def mute_mic_audio():
    """Mute/Unmute the Microphone audio source as configured in sd_controls.ini
    """
    loop.run_until_complete(_ws_toggle_mute(config['obs']['mic_source']))


def mute_both_audio():
    """Mute/Unmute both Desktop and Microphone audio sources as configured in
    sd_controls.ini
    """
    for source in (config['obs']['mic_source'],
                   config['obs']['desktop_source']):
        loop.run_until_complete(_ws_toggle_mute(source))


def set_scene(scene_number):
    """Set the active scene in OBS using the number of the scene as counted
    from the top down of the scene list in OBS

    :param scene_number: The scene number to make active
    :type scene_number: int
    """
    scene_list = loop.run_until_complete(_ws_get_scene_list())
    # Adjust for zero indexing
    scene_number = scene_number - 1
    new_scene = scene_list['scenes'][scene_number]['name']
    loop.run_until_complete(_ws_set_scene(new_scene))


def start_stop_stream():
    """Start/Stop the stream"""
    loop.run_until_complete(_ws_start_stop_stream())


def panic_button():
    """Sadly, people are performing "hate raids" on twitch, raiding channels
    and getting bot accounts to follow the streamer and spam chat with
    hateful messages.

    The follows will cause sound alert overlays to queue up notifications,
    so this function will disable and re-enable those overlays as configured
    in sd_controls.ini

    :todo: Integrate with twitch APIs to set chat to "Subscriber only mode"
    or "Followers only mode" (based on follow duration) to block hateful
    messages in chat.

    :raises ValueError: If there is a conflict between either the saved URL for
        the source, or the invalid.lan address that temporarily overwrites
        the source's URL.
    """
    # Loop through configured alert sources
    for source in config['obs']['alert_sources'].split(':'):
        # Get the current settings for the alert source.
        settings = loop.run_until_complete(_ws_get_source_settings(source))
        settings = settings['sourceSettings']
        # check if the source url is saved to the ini file, if not assume
        # this is the first time we've run this and save it
        if not config.has_option('obs_browser_sources', source):
            config['obs_browser_sources'][source] = settings['url']
            with open(config_file, 'w') as f:
                config.write(f)
        # Swap Browser source between saved URl and invalid.lan
        if settings['url'] == config['obs_browser_sources'][source]:
            settings['url'] = 'http://invalid.lan'
        elif settings['url'] == 'http://invalid.lan':
            settings['url'] = config['obs_browser_sources'][source]
        else:
            raise ValueError('Browser source matches neither the saved value '
                             'in the ini file or \'http://invalid.lan/\'')
        # Swap reroute_audio settings to make sure the audio for the browser
        # source is routed through the OBS audio mixer and can be muted,
        # instead of through the default Desktop audio source
        if settings['reroute_audio']:
            settings['reroute_audio'] = False
        else:
            settings['reroute_audio'] = True
        # Update the settings and mute the sources.
        loop.run_until_complete(_ws_set_source_settings(source, settings))
        loop.run_until_complete(_ws_toggle_mute(source))


def do_action(arg):
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
    else:
        raise ValueError('Could not find a valid action from the command line '
                         'arguments')


def main():
    parser = _add_args()
    arg = parser.parse_args()
    do_action(arg)


if __name__ == '__main__':
    main()
