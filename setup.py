import os
from setuptools import setup


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


setup(
    name='nws-wwa',
    version='0.0.2',
    description="Download watch, warning and advisory data from the National Weather Service",
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    author='Ben Welsh',
    author_email='b@palewi.re',
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
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: MIT License'
    ],
    project_urls={
        'Maintainer': 'https://github.com/palewire',
        'Source': 'https://github.com/palewire/nws-wwa',
        'Tracker': 'https://github.com/palewire/nws-wwa/issues',
    },
)
