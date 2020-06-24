from mstrio import __author__,  __version__
import os
from setuptools import setup, find_packages, dist
from setuptools.extern.packaging import version as packaging_version

if 'version.txt' in os.listdir():
    with open('version.txt') as f:
        dist_version = f.read().strip()
else:
    dist_version = __version__  # define the default version

# Patch Version class to preserve original version string
dist.pkg_resources.safe_version = lambda v: v


class NoNormalizeVersion(packaging_version.Version):
    def __init__(self, version):
        self._orig_version = version
        super().__init__(version)

    def __str__(self):
        return self._orig_version


packaging_version.Version = NoNormalizeVersion
with open('README.md') as f:
    long_description = f.read()


setup(name='mstrio-py',
      version=dist_version,
      description='Python interface for the MicroStrategy REST API',
      license='Apache License 2.0',
      url='https://github.com/MicroStrategy/mstrio-py',
      author=__author__,
      author_email='srigney@microstrategy.com, ssainz@microstrategy.com, mciesielski@microstrategy.com,zrogala@microstrategy.com, ihologa@microstrategy.com, pczyz@microstrategy.com, oduda@microstrategy.com, wantonczyk@microstrategy.com, mdrzazga@microstrategy.com, apiotrowski@microstrategy.com',
      project_urls={
        'Bug Tracker': 'https://github.com/MicroStrategy/mstrio-py/issues',
        'Documentation': 'http://www2.microstrategy.com/producthelp/Current/mstrio-py/',
        'Source Code': 'https://github.com/MicroStrategy/mstrio-py',
        'Quick Manual': 'https://www2.microstrategy.com/producthelp/current/MSTR-for-Jupyter/Content/mstr_for_jupyter.htm',
      },
      install_requires=[
          'requests',
          'requests_futures',
          'pandas',
          'numpy>=1.18.1',
          'tqdm>=4.41.1',
          'jupyter_contrib_nbextensions>=0.5.1',
          'ipywidgets>=7.5.1',
          'packaging'
      ],
      long_description=long_description,
      long_description_content_type='text/markdown',
      packages=find_packages(),
      include_package_data=True)
