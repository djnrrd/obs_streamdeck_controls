from setuptools import setup

setup(
    name='obs_streamdeck_controls',
    version='0.0.1',
    install_requires=['simpleobsws'],
    packages=[''],
    url='https://github.com/djnrrd/obs_streamdeck_controls',
    license='GPL-3.0 License',
    author='djnrrd',
    author_email='djnrrd@gmail.com',
    description='A command line tool for controlling OBS Studio via the '
                'OBS WebSockets API',
    keywords='twitch streamdeck obs',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Topic :: Games/Entertainment',
        'Topic :: Home Automation',
    ]
)
