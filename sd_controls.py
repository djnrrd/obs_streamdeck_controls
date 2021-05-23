import asyncio
import simpleobsws
import argparse

password = 'Str34mD3ck'
ws = simpleobsws.obsws(password=password)
loop = asyncio.get_event_loop()


def add_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['start_stop', 'mute_mic',
                                           'mute_desk', 'mute_all',
                                           'holding_page',
                                           'full_cam', '4x3', '16x9',
                                           'cat_cam'])
    return parser


async def _ws_toggle_mute(source):
    # Make the connection to obs-websocket
    await ws.connect()
    # Select the source with a data attachment and call the GetMute api
    data = {'source': source}
    result = await ws.call('ToggleMute', data)
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await ws.disconnect()


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


def mute_desktop_audio():
    loop.run_until_complete(_ws_toggle_mute('pulse_obs_sink'))


def mute_mic_audio():
    loop.run_until_complete(_ws_toggle_mute('Mic/Aux'))


def mute_both_audio():
    for source in ('pulse_obs_sink', 'Mic/Aux'):
        loop.run_until_complete(_ws_toggle_mute(source))


def set_scene(scene):
    lookup = {'holding_page': 'Holding Page', 'full_cam': 'Full Cam',
              '4x3': '4 x 3 Game', '16x9': '16 x 9 Game', 'cat_cam': 'Cat Cam'}
    loop.run_until_complete(_ws_set_scene(lookup[scene]))


def start_stop_stream():
    loop.run_until_complete(_ws_start_stop_stream())


def do_action(action):
    if action == 'start_stop':
        start_stop_stream()
    elif action == 'mute_mic':
        mute_mic_audio()
    elif action == 'mute_desk':
        mute_desktop_audio()
    elif action == 'mute_all':
        mute_both_audio()
    else:
        set_scene(action)


def main():
    parser = add_args()
    arg = parser.parse_args()
    do_action(arg.action)


if __name__ == '__main__':
    main()
