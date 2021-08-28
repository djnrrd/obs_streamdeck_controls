import asyncio
import simpleobsws


def _load_obs_ws(ws_password=''):
    """Load the simpleobsws object and return it.

    :param ws_password: The password for the OBS WebSockets server
    :type ws_password: str
    :return: The simpleobsws object
    :rtype: simpleobsws.obsws
    """
    if ws_password:
        ws = simpleobsws.obsws(password=ws_password)
    else:
        ws = simpleobsws.obsws()
    return ws


async def _ws_toggle_mute(source, ws):
    """Use the OBS-Websocket to mute/unmute an audio source

    :param source: The OBS audio source to mute/unmute
    :type source: str
    :param ws: OBS WebSockets library created in cli_tools
    :type ws: simpleobsws.obsws
    """
    # Make the connection to obs-websocket
    await ws.connect()
    data = {'source': source}
    await ws.call('ToggleMute', data)
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await ws.disconnect()


async def _ws_get_scene_list(ws):
    """Use the OBS-Websocket to get the list of scenes

    :param ws: OBS WebSockets library created in cli_tools
    :type ws: simpleobsws.obsws
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


async def _ws_set_scene(scene, ws):
    """Use the OBS-Websocket to set the current scene

    :param scene: The name of the scene in OBS to make active
    :type scene: str
    :param ws: OBS WebSockets library created in cli_tools
    :type ws: simpleobsws.obsws
    """
    # Make the connection to obs-websocket
    await ws.connect()
    data = {'scene-name': scene}
    await ws.call('SetCurrentScene', data)
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await ws.disconnect()


async def _ws_start_stop_stream(ws):
    """Use the OBS-Websocket to start or stop streaming

    :param ws: OBS WebSockets library created in cli_tools
    :type ws: simpleobsws.obsws
    """
    # Make the connection to obs-websocket
    await ws.connect()
    await ws.call('StartStopStreaming')
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await ws.disconnect()


async def _ws_get_source_settings(source, ws):
    """Use the OBS-Websocket to get the settings for a source

    :param source: The OBS source to get the settings for
    :type source: str
    :param ws: OBS WebSockets library created in cli_tools
    :type ws: simpleobsws.obsws
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


async def _ws_set_source_settings(source, settings, ws):
    """Use the OBS-Websocket to set new settings for a source

    :param source: The OBS source to update
    :type source: str
    :param settings: The updated settings to apply to the source in the same
        format as the sourceSettings section returned from
        _ws_get_source_settings
    :type settings: dict
    :param ws: OBS WebSockets library created in cli_tools
    :type ws: simpleobsws.obsws
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


async def _ws_get_all_sources(ws):
    """Use the OBS-Websocket to get a list of sources

    :param ws: OBS WebSockets library created in cli_tools
    :type ws: simpleobsws.obsws
    :return: a list of all sources configured in OBS
    :rtype: dict
    """
    # Make the connection to obs-websocket
    await ws.connect()
    result = await ws.call('GetSourcesList')
    # Clean things up by disconnecting. Only really required in a few specific
    # situations, but good practice if you are done making requests or listening
    # to events.
    await ws.disconnect()
    return result


def mute_audio_source(source, ws_password):
    """Mute/Unmute the Microphone audio source as configured in sd_controls.ini

    :param source: the audio source to mute
    :type source: str
    :param ws_password: The password for the OBS WebSockets server
    :type ws_password: str
    """
    ws = _load_obs_ws(ws_password)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_ws_toggle_mute(source, ws))


def set_scene(scene_number, ws_password):
    """Set the active scene in OBS using the number of the scene as counted
    from the top down of the scene list in OBS

    :param scene_number: The scene number to make active
    :type scene_number: int
    :param ws_password: The password for the OBS WebSockets server
    :type ws_password: str
    """
    ws = _load_obs_ws(ws_password)
    loop = asyncio.get_event_loop()
    scene_list = loop.run_until_complete(_ws_get_scene_list(ws))
    # Adjust for zero indexing
    scene_number = scene_number - 1
    new_scene = scene_list['scenes'][scene_number]['name']
    loop.run_until_complete(_ws_set_scene(new_scene, ws))


def start_stop_stream(ws_password):
    """Start/Stop the stream

    :param ws_password: The password for the OBS WebSockets server
    :type ws_password: str
    """
    ws = _load_obs_ws(ws_password)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_ws_start_stop_stream(ws))


def get_source_settings(source, ws_password):
    """Get the current settings for an OBS Source

    :param source: The name of the OBS source
    :type source: str
    :param ws_password: The password for the OBS WebSockets server
    :type ws_password: str
    :return: The current settings for the OBS source
    :rtype: dict
    """
    ws = _load_obs_ws(ws_password)
    loop = asyncio.get_event_loop()
    settings = loop.run_until_complete(_ws_get_source_settings(source, ws))
    settings = settings['sourceSettings']
    return settings


def set_source_settings(source, settings, ws_password):
    """Apply new settings for the selected source

    :param source: The name of the OBS source
    :type source: str
    :param settings: The updated settings to apply to the source in the same
        format as the sourceSettings section returned from
        get_source_settings
    :type settings: dict
    :param ws_password: The password for the OBS WebSockets server
    :type ws_password: str
    """
    ws = _load_obs_ws(ws_password)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_ws_set_source_settings(source, settings, ws))


def get_all_sources(ws_password):
    """Get a list of all sources currently configured in OBS

    :param ws_password: The password for the OBS WebSockets server
    :type ws_password: str
    :return: A list of sources
    :rtype: list
    """
    ws = _load_obs_ws(ws_password)
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(_ws_get_all_sources(ws))
    return results['sources']
