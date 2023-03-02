import os

import pkg_resources
from setuptools import find_packages, setup
from setuptools.extern.packaging import version as packaging_version

from mstrio import (__author__, __author_email__, __description__, __license__, __title__,
                    __version__)

MANIFEST_FILE = 'MANIFEST.in'

if 'version.txt' in os.listdir():
    with open('version.txt') as f:
        dist_version = f.read().strip()
else:
    dist_version = __version__  # define the default version

# Patch Version class to preserve original version string
pkg_resources.safe_version = lambda v: v


class NoNormalizeVersion(packaging_version.Version):

    def __init__(self, version):
        self._orig_version = version
        super().__init__(version)

    def __str__(self):
        return self._orig_version


def find_in_file(text, file):
    if file in os.listdir():
        with open(file, 'r') as f:
            manifest = f.read()
        return text in manifest
    else:
        raise ValueError(f'Could not find file {file}')


packaging_version.Version = NoNormalizeVersion
with open('README.md') as f:
    long_description = f.read()


peer_force_version = [  # peer dependency (dep of dep)
                        # but we need to force version for SEC
                        # backend only (front peers are
                        # handled in code ~20 lines below)
    'urllib3>=1.26.0',  # ver 1.25.x is incompatible
    'Jinja2>=3, <4',    # UI related, but also dev-dep of `pandas` but required for testing
    'certifi>=2022.12.7',  # SEC safe version
]

requirements = [
    'requests>=2.27, <2.29',
    'requests-futures>=1.0.0, <1.1',
    'pandas>=1.1.5, <1.6',
    'numpy>=1.24, <1.25',
    'tqdm>=4.41, <4.70',
    'packaging>=21.3, <22',
    'stringcase>=1.2, <1.3'
] + peer_force_version

# Add dependencies for connector-jupyter if connector-jupyter folder is added
if find_in_file('graft connector-jupyter', MANIFEST_FILE):
    requirements += [
        # direct dependencies
        'jupyter-contrib-nbextensions>=0.5.1, <0.6',
        'ipywidgets>=8.0.2, <9',

        # peer, UI related, force version for SEC
        'notebook>=6.4.12',
        'jupyter_core>=4.11.2',
        'lxml>=4.9.1',
        'ipython>=8.4.0, <9',
        'nbconvert>=7, <8',
        'mistune>=2.0.4',
        'setuptools>=65.5.1'
    ]

setup(
    name=__title__,
    python_requires='>=3.10',
    version=dist_version,
    license=__license__,
    description=__description__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/MicroStrategy/mstrio-py',
    author=__author__,
    author_email=__author_email__,
    project_urls={
        'Bug Tracker': 'https://github.com/MicroStrategy/mstrio-py/issues',
        'Documentation': 'http://www2.microstrategy.com/producthelp/Current/mstrio-py/',
        'Source Code': 'https://github.com/MicroStrategy/mstrio-py',
        'Quick Manual': 'https://www2.microstrategy.com/producthelp/current/MSTR-for-Jupyter/Content/mstr_for_jupyter.htm',  # noqa
    },
    install_requires=requirements,
    extras_require={
        'dev': [
            'flake8', 'mypy', 'yapf', 'nose', 'coverage', 'pytest', 'pytest-cov', 'isort',
            'pre-commit', 'flaky', 'python-decouple'
        ],  # noqa
    },
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: JavaScript',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3 :: Only',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Libraries',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development',
    ],
)
