import os
from setuptools import setup, find_packages, dist
from setuptools.extern.packaging import version as packaging_version

if 'version.txt' in os.listdir():
    with open('version.txt') as f:
        dist_version = f.read().strip()
else:
    dist_version = '11.2.0.002'  # define the default version


# Patch Version class to preserve original version string
dist.pkg_resources.safe_version = lambda v:v

class NoNormalizeVersion(packaging_version.Version):
    def __init__(self, version):
        self._orig_version = version
        super().__init__(version)

    def __str__(self):
        return self._orig_version

packaging_version.Version = NoNormalizeVersion

setup(name='mstrio-py',
      version=dist_version,
      description='Python interface for the MicroStrategy REST API',
      license='Apache License 2.0',
      url='https://github.com/MicroStrategy/mstrio-py',
      author='Scott Rigney, Peter Ott, Sergio Sainz Palacios, Michal Ciesielski, Zofia Rogala, Ignacy Hologa, Piotr Czyz',
      author_email='srigney@microstrategy.com, ssainz@microstrategy.com, mciesielski@microstrategy.com,'
                    'zrogala@microstrategy.com, ihologa@microstrategy.com, pczyz@microstrategy.com',
      install_requires=[
          'requests',
          'pandas',
          'tqdm',
          'jupyter_contrib_nbextensions',
          'ipywidgets',
          'packaging'
      ],
      packages=find_packages(),
      include_package_data=True)
