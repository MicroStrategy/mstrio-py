from setuptools import setup


setup(name='mstrio-py',
      version='10.11',
      packages=['mstrio', 'mstrio.api', 'mstrio.utils'],
      description='Python interface for the MicroStrategy REST API',
      license='Apache License 2.0',
      author=[
          'Scott Rigney',
          'Peter Ott',
          'Sergio Sainz Palacios',
          'Alex Fernandes'
      ],
      author_email=[
          'srigney@microstrategy.com',
          'pott@microstrategy.com',
          'ssainz@microstrategy.com',
          'afernandes@microstrategy.com'
      ],
      install_requires=[
          'requests',
          'pandas'
      ]
      )
