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


def add_args():
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
    # Make the connection to obs-websocket
    await ws.connect()
    # Select the source with a data attachment and call the ToggleMute api
    data = {'source': source}
    result = await ws.call('ToggleMute', data)
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await ws.disconnect()


async def _ws_get_scene_list():
    # Make the connection to obs-websocket
    await ws.connect()
    result = await ws.call('GetSceneList')
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await ws.disconnect()
    return result


async def _ws_set_scene(scene):
    # Make the connection to obs-websocket
    await ws.connect()
    # Select the source with a data attachment and call the SetCurrentScene api
    data = {'scene-name': scene}
    result = await ws.call('SetCurrentScene', data)
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await ws.disconnect()


async def _ws_start_stop_stream():
    # Make the connection to obs-websocket
    await ws.connect()
    # Select the source with a data attachment and call the StartStopStreaming
    # api
    result = await ws.call('StartStopStreaming')
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await ws.disconnect()


async def _ws_get_source_settings(source):
    # Make the connection to obs-websocket
    await ws.connect()
    # Select the source with a data attachment and call the GetSourceSettings
    # api
    data = {'sourceName': source}
    result = await ws.call('GetSourceSettings', data)
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await ws.disconnect()
    return result


async def _ws_set_source_settings(source, settings):
    # Make the connection to obs-websocket
    await ws.connect()
    # Select the source with a data attachment and call the SetSourceSettings
    # api
    data = {'sourceName': source, 'sourceSettings': settings}
    result = await ws.call('SetSourceSettings', data)
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await ws.disconnect()
    return result


def mute_desktop_audio():
    loop.run_until_complete(_ws_toggle_mute(config['obs']['desktop_source']))


def mute_mic_audio():
    loop.run_until_complete(_ws_toggle_mute(config['obs']['mic_source']))


def mute_both_audio():
    for source in (config['obs']['mic_source'],
                   config['obs']['desktop_source']):
        loop.run_until_complete(_ws_toggle_mute(source))


def set_scene(scene_number):
    scene_list = loop.run_until_complete(_ws_get_scene_list())
    # Adjust for zero indexing
    scene_number = scene_number - 1
    new_scene = scene_list['scenes'][scene_number]['name']
    loop.run_until_complete(_ws_set_scene(new_scene))
    return scene_list


def start_stop_stream():
    loop.run_until_complete(_ws_start_stop_stream())


def panic_button():
    # rewrite and mute URL sources
    for source in config['obs']['alert_sources'].split(':'):
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
        if settings['reroute_audio']:
            settings['reroute_audio'] = False
        else:
            settings['reroute_audio'] = True

        loop.run_until_complete(_ws_set_source_settings(source, settings))
        loop.run_until_complete(_ws_toggle_mute(source))


def get_source_settings():
    ret = loop.run_until_complete(_ws_get_source_settings('streamlabs_alerts'))
    return ret


def do_action(arg):
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
    parser = add_args()
    arg = parser.parse_args()
    do_action(arg)


if __name__ == '__main__':
    main()
