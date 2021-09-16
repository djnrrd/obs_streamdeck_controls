##################
OBS Streamdeck CTL
##################

Introduction
============

A command line tool for controlling OBS Studio [1]_ via the `OBS WebSockets API
<https://github.com/Palakis/obs-websocket>`_, designed for use with tools
such as the Elgato Stream Deck, or any hardware tool where you can assign a
command to a single button press.


Features
********

* Start/Stop streaming, including enabling/disabling chat safety features
* Mute/Unmute Microphone and Desktop Audio sources, including supporting custom audio sources
* Scene switching
* Live Safety mode to combat the effects of hate raids.

Installation
============

OBS Streamdeck CTL is written in Python, and is planned to be published to
PyPi

Requirements
************

* `Python <https://www.python.org/>`_ >= 3.6
* Pip [2]_ and Internet access
* OBS Studio [1]_
* `OBS WebSockets API <https://github.com/Palakis/obs-websocket>`_

Installing From Source
**********************

Obtaining Source code
---------------------

Download the required release from the `releases page <https://github
.com/djnrrd/obs_streamdeck_controls/releases>`_ or clone the git repository
to obtain the main branch::

 git clone https://github.com/djnrrd/obs_streamdeck_controls.git

Pre Installation
----------------

Register a new application on `dev.twitch.com. <https://dev.twitch.com>`_ Then
edit the file ``obs_sd_controls/conf.py`` and update the CLIENT_ID variable
with your own Client ID.

Installing
----------

Windows users need more documentation, `but this guide <https://projects
.raspberrypi.org/en/projects/using-pip-on-windows>`_ should help.

Change directory into the downloaded folder and install locally via pip. It
is recommended that you use the ``--user`` flag to install in your user
directory.::

 cd obs_streamdeck_controls
 pip install --user --use-feature=in-tree-build .

Post Install
------------

Linux
^^^^^

This will install the command line program ``obs-streamdeck-ctl`` to your
``$HOME/.local/bin`` folder. Add::

 PATH=$PATH:$HOME/.local/bin

to your ``.bashrc`` file, if you haven't already.

Windows
^^^^^^^

This will install ``obs-streamdeck-ctl.exe`` to your
``C:\Users\%USERNAME%\AppData\Roaming\Python\Python39\Scripts`` folder and you
may see an error regarding this when you install.

You can add this to your path with the following command::

 setx PATH "C:\Users\%USERNAME%\AppData\Roaming\Python\Python39\Scripts\;%PATH%"

Restart your computer to make sure that the %PATH% is loaded correctly

Using
=====

Initial Setup
*************

After installing OBS Streamdeck Controls you will need to provide information
regarding your OBS WebSockets password, names of your Microphone, Desktop,
and alert overlay sources, authorise the application with twitch, and set
your safety options.

Run the following command on a terminal/command line to launch a setup wizard::

   obs-streamdeck-ctl setup

Using the Scripts
*****************

All scripts are launched by the same command line program::

   obs-streamdeck-ctl SCRIPT_NAME

Where SCRIPT_NAME is one of the following:

* `start_stop`_
* `mute_mic`_
* `mute_desk`_
* `mute_all`_
* `scene X`_
* `live_safety`_
* `setup`_

start_stop
----------

Start or Stop live streaming, and if Twitch chat safety features are enabled,
toggle these.  Safety features may put chat into Subscriber or Follower only
mode and optionally switch Emote only mode on.

Because the Subscriber, Follower, and Emote only modes function like a toggle
switch, If you enable any of these modes when live and don't disable them
before using this function to stop the stream, it may disable that mode when
you are offline.

mute_mic
--------

Toggle the mute function on your Microphone input source. If you use a
different Microphone source to the default you can select that with the setup
wizard.

mute_desk
---------

Toggle the mute function on your Desktop Audio input source. If you use a
different Desktop Audio source to the default you can select that with the setup
wizard.

mute_all
--------

Toggle the mute function on both the Desktop and Microphone Audio sources

scene X
-------

Switch to Scene X in OBS Studio. X is the number of the Scene in the Scene
List, counting down from the top and starting with 1.

live_safety
-----------

Sadly, people have taken to "Hate Raids" on Twitch, where your chat can be
overwhelmed with hateful messages from multiple bot accounts. These bot
accounts will also mass follow the channel, to queue up repeated alerts from
any sound/screen alert web overlay services.

Live Safety can enable and disable Subscriber or Follower only mode in chat and
optionally enable and disable Emote only mode.

Live Safety can also enable and disable sound/screen alert web overlay
services, as well as any other web overlay services that you may use, like
chat.

Like the `start_stop`_ function, enabling and disabling the chat modes and
web overlay services is like a toggle function. So ending a stream before
running Live Safety again could leave your web overlay services disabled.


setup
-----

Launch the setup wizard, see Initial Setup for details

Footnotes
=========

.. [1] Streamlabs OBS/SLOBS is *not* currently supported
.. [2] Pip is a package manager and should be included when you install
       Python. Some Linux distributions may not include pip automatically and it
       may have to be installed from your Linux distribution package manager

