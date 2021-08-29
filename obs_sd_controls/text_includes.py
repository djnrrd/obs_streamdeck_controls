APP_HEADER = 'OBS Streamdeck Control Setup Wizard'

WELCOME_HEADING = 'OBS Streamdeck Control Setup'
WELCOME_TEXT = 'Welcome to the setup wizard for OBS Streamdeck Controls.'

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
OBSAUDIO_TEXT = 'Please select your Microphone and Desktop Audio sources'
OBSAUDIO_MIC_PROMPT = 'Microphone Source'
OBSAUDIO_DESK_PROMPT = 'Desktop Audio Source'