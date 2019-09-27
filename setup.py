from setuptools import setup


setup(name='mstrio-py',
      version='10.11.1',
      packages=['mstrio', 'mstrio.api', 'mstrio.utils'],
      description='Python interface for the MicroStrategy REST API',
      license='Apache License 2.0',
      url='https://github.com/MicroStrategy/mstrio-py',
      author='Scott Rigney, Sergio Sainz Palacios',
      author_email='srigney@microstrategy.com, ssainz@microstrategy.com',
      python_requires='>=3.6',
      install_requires=[
          'requests>=2.19.1',
          'pandas>=0.23.3'
      ]
      )
