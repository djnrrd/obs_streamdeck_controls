from setuptools import setup
import os
import sys
sys.path.extend([os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'src')])
from obs_sd_controls.conf import VERSION

setup(
    version=VERSION,
)
