from setuptools import setup
setup(
      name='subtitle_search',
      scripts=['subtitle_search.py'],
      entry_points = {
              'console_scripts':
                  ['subtitle-search=subtitle_search:main']             
      }
)
