APP_HEADER = 'OBS Streamdeck CTL Setup Wizard'

WELCOME_HEADING = 'OBS Streamdeck CTL Setup'
WELCOME_TEXT = 'Welcome to the setup wizard for OBS Streamdeck Controls. ' \
               'These controls are designed for use with OBS Studio and the ' \
               'OBS WebSockets server plugin. Please make sure that you have ' \
               'the OBS WebSockets server plugin installed, and that OBS is ' \
               'running.'

EXISTING_HEADING = 'Existing Configuration Warning'
EXISTING_TEXT = 'OBS Streamdeck Control already has a config file. Press Next ' \
                'to replace it, or Cancel to exit the Setup Wizard'

OBSWSPASS_HEADING = 'Connect to OBS WebSockets Server'
OBSWSPASS_TEXT = 'Please enter the password for OBS WebSockets server, or ' \
                 'leave blank for no password'
OBSWSPASS_PROMPT = 'Password:'
OBSWSPASS_WARN_HEADER = 'Could not connect to OBS WebSocket Server'
OBSWSPASS_WARN = """Unable to connect to OBS WebSockets.  Please make sure that:
            
1) OBS is running
2) OBS WebSockets is enabled
3) The password and port number are correct"""

OBSAUDIO_HEADING = 'Select OBS Audio Sources'
OBSAUDIO_TEXT = 'Please select your Microphone and Desktop Audio sources. ' \
                'These will be used for the Mute functions'
OBSAUDIO_MIC_PROMPT = 'Microphone Source'
OBSAUDIO_DESK_PROMPT = 'Desktop Audio Source'

OBSALERT_HEADING = 'Select OBS Notification and Chat Sources'
OBSALERT_TEXT = 'Please select the browser sources used for notifications ' \
                'and/or chat that you wish to disable when using the ' \
                '"Live Safety" function'
OBSALERT_SOURCE_PROMPT = 'OBS Sources'
OBSALERT_ALERT_PROMPT = 'Notification/Chat Sources'

LAUNCH_TWITCH_HEADING = 'Authorise OBS Streamdeck CTL with Twitch'
LAUNCH_TWITCH_TEXT = 'Please provide your Twitch channel name then click Next' \
                     ' to launch a new web browser tab and authorise OBS ' \
                     'Streamdeck CTL to use your twitch account.'
LAUNCH_TWITCH_PROMPT = 'Twitch channel name'

START_STOP_HEADING = 'Offline Safety Features'
START_STOP_TEXT = 'The Start/Stop function can be used to lock down your chat' \
                  ' while you\'re offline, limiting what can happen while you ' \
                  'and your mods aren\'t watching'
START_STOP_CHECK = 'Enable Start/Stop safety features?'

LIVE_SAFETY_HEADING = 'Live Safety Features'
LIVE_SAFETY_TEXT = 'The Live Safety function can be used to lock down your ' \
                    'chat in case of "hate raids" or other activities that ' \
                   'put your communities at risk.'
LIVE_SAFETY_CHECK = 'Enable Live Safety features?'


ADDITIONAL_HEADING = 'Additional Live Safety Features'
ADDITIONAL_TEXT = 'The Live Safety function may also do the following:'
ADDITIONAL_AD_CHECK = 'Play an advert'
ADDITIONAL_CLEAR_CHECK = 'Clear chat history'


SAFETY_EMOTE = 'Enable emote only mode additionally'
SAFETY_FOLLOW = 'Follower only mode'
SAFETY_FOLLOW_TIME = 'Follow duration before allowing chat (Examples ' \
                         '\'3h\', \'2d\', \'1w\')'
SAFETY_SUB = 'Subscriber only mode'

COMPLETE_HEADING = 'Setup Complete'
COMPLETE_TEXT = 'Click Finish to close this setup wizard'