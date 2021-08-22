import asyncio
import simpleobsws

# Setup the asyncio event loop as a global, the simpleobsws library crashes
# if you use asyncio.run and prefers to use the lower level get_event_loop API
LOOP = asyncio.get_event_loop()


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


def mute_desktop_audio(config, ws):
    """Mute/Unmute the Desktop audio source as configured in sd_controls.ini

    :param config: ConfigParser object created in cli_tools
    :type config: ConfigParser
    :param ws: OBS WebSockets library created in cli_tools
    :type ws:  simpleobsws.obsws
    """
    LOOP.run_until_complete(
        _ws_toggle_mute(config['obs']['desktop_source'], ws))


def mute_mic_audio(config, ws):
    """Mute/Unmute the Microphone audio source as configured in sd_controls.ini

    :param config: ConfigParser object created in cli_tools
    :type config: ConfigParser
    :param ws: OBS WebSockets library created in cli_tools
    :type ws:  simpleobsws.obsws
    """
    LOOP.run_until_complete(_ws_toggle_mute(config['obs']['mic_source'], ws))


def mute_both_audio(config, ws):
    """Mute/Unmute both Desktop and Microphone audio sources as configured in
    sd_controls.ini

    :param config: ConfigParser object created in cli_tools
    :type config: ConfigParser
    :param ws: OBS WebSockets library created in cli_tools
    :type ws:  simpleobsws.obsws
    """
    for source in (config['obs']['mic_source'],
                   config['obs']['desktop_source']):
        LOOP.run_until_complete(_ws_toggle_mute(source, ws))


def set_scene(ws, scene_number):
    """Set the active scene in OBS using the number of the scene as counted
    from the top down of the scene list in OBS

    :param ws: OBS WebSockets library created in cli_tools
    :type ws:  simpleobsws.obsws
    :param scene_number: The scene number to make active
    :type scene_number: int
    """
    scene_list = LOOP.run_until_complete(_ws_get_scene_list(ws))
    # Adjust for zero indexing
    scene_number = scene_number - 1
    new_scene = scene_list['scenes'][scene_number]['name']
    LOOP.run_until_complete(_ws_set_scene(new_scene, ws))


def start_stop_stream(ws):
    """Start/Stop the stream

    :param ws: OBS WebSockets library created in cli_tools
    :type ws:  simpleobsws.obsws
    """
    LOOP.run_until_complete(_ws_start_stop_stream(ws))


def panic_button(config, ws):
    """Sadly, people are performing "hate raids" on twitch, raiding channels
    and getting bot accounts to follow the streamer and spam chat with
    hateful messages.

    The follows will cause sound alert overlays to queue up notifications,
    so this function will disable and re-enable those overlays as configured
    in sd_controls.ini

    TODO Integrate with twitch APIs to set chat to "Subscriber only mode"
    or "Followers only mode" (based on follow duration) to block hateful
    messages in chat.

    :param config: ConfigParser object created in cli_tools
    :type config: ConfigParser
    :param ws: OBS WebSockets library created in cli_tools
    :type ws: simpleobsws.obsws
    :raises ValueError: If there is a conflict between either the saved URL for
        the source, or the invalid.lan address that temporarily overwrites
        the source's URL.
    """
    # Loop through configured alert sources
    for source in config['obs']['alert_sources'].split(':'):
        # Get the current settings for the alert source.
        settings = LOOP.run_until_complete(_ws_get_source_settings(source, ws))
        settings = settings['sourceSettings']
        # check if the source url is saved to the ini file, if not assume
        # this is the first time we've run this and create it
        if not config.has_option('obs_browser_sources', source):
            config['obs_browser_sources'][source] = settings['url']
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
        LOOP.run_until_complete(_ws_set_source_settings(source, settings, ws))
        LOOP.run_until_complete(_ws_toggle_mute(source, ws))
