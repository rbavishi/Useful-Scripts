from setuptools import setup
setup(
      name='subtitle-search',
      description='A command-line utility to download subtitles from Subscene.com',
      author='Rohan Bavishi',
      author_email='rohan.bavishi95@gmail.com',
      scripts=['subtitle_search.py'],
      install_requires=['fuzzywuzzy', 'python-Levenshtein', 'beautifulsoup4 >= 4.5.0'],
      entry_points = {
              'console_scripts':
                  ['subtitle-search=subtitle_search:main']             
      }
)
