import os
from setuptools import setup


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


setup(
    name='nws-wwa',
    version='0.0.1',
    description="Download watch, warning and advisory data from the National Weather Service",
    long_description=read('README.rst'),
    author='Los Angeles Times Data and Graphics Department',
    author_email='datagraphics@latimes.com',
    url='http://www.github.com/datadesk/nws-wwa',
    license="MIT",
    packages=("nws_wwa",),
    install_requires=[
        "requests",
        "fiona",
        "geojson",
        "click"
    ],
    entry_points="""
        [console_scripts]
        nwswwa=nws_wwa.cli:cmd
    """,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License'
    ],
    project_urls={
        'Maintainer': 'https://github.com/datadesk',
        'Source': 'https://github.com/datadesk/nws-wwa',
        'Tracker': 'https://github.com/datadesk/nws-wwa/issues',
        'CI': 'https://travis-ci.org/datadesk/nws-wwa/'
    },
)
