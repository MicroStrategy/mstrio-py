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
    'notebook>=6.4.10',  # Jupyter Notebook - ver required for SEC
    'ipython>=8.1.1, <9',  # dep of dep - higher ver required for SEC
    'requests>=2.27, <2.28',
    'urllib3>=1.26.0',  # dep of dep (but ver 1.25.x is incompatible)
    'requests_futures>=1.0.0, <1.1',
    'pandas>=1.1.5, <=1.5',
    'numpy>=1.22.3, <1.23',
    'tqdm>=4.41, <4.70',
    'packaging>=21.3, <22',
    'dictdiffer>=0.8.1, <0.10',
    'stringcase>=1.2, <1.3',
    'Jinja2>=3.0, <4.0',
]

# Add dependencies for connector-jupyter if connector-jupyter folder is added
if find_in_file('graft connector-jupyter', MANIFEST_FILE):
    requirements.extend([
        'lxml>=4.7.1',  # dep of dep but prev vers are considered vulnerable
        'jupyter_contrib_nbextensions>=0.5.1, <0.6',
        'ipywidgets>=7.5.1, <8'
    ])
setup(
    name=__title__,
    python_requires='>=3.9',
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
                'isort', 'pre-commit'],  # noqa
    },
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: JavaScript',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
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
