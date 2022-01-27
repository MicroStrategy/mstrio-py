import os

from setuptools import dist, find_packages, setup
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
dist.pkg_resources.safe_version = lambda v: v


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

requirements = [
    'notebook>=6.4.5',  # Jupyter Notebook - ver required by WS
    'requests>=2.25, <2.26',
    'urllib3>=1.26.0',  # dep of dep (but ver 1.25.x is incompatible)
    'requests_futures>=1.0.0, <1.1',
    'pandas>=1.1.5, <1.3',
    'numpy>=1.18.1, <1.22',
    'tqdm>=4.41, <4.70',
    'packaging>=20.9, <21',
    'dictdiffer>=0.8.1, <0.9',
    'stringcase>=1.2, <1.3',
    'Jinja2>=2.11, <3.0',
]

# Add dependencies for connector-jupyter if connector-jupyter folder is added
# Else add workstation_demo_scripts folder
if find_in_file('graft connector-jupyter', MANIFEST_FILE):
    requirements.extend([
        'lxml>=4.7.1',  # dep of dep but prev vers are considered vulnerable
        'jupyter_contrib_nbextensions>=0.5.1, <0.6',
        'ipywidgets>=7.5.1, <8'
    ])
elif find_in_file('prune connector-jupyter', MANIFEST_FILE):
    with open(MANIFEST_FILE, "a+") as f:
        f.write('graft workstation_demo_scripts')

setup(
    name=__title__,
    python_requires='>=3.6',
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
        'dev': ['flake8', 'mypy', 'yapf', 'nose', 'coverage', 'pytest', 'pytest-cov',
                'isort'],  # noqa
    },
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: JavaScript',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
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
