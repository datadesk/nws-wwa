import os

from setuptools import setup


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


def version_scheme(version):
    """
    Version scheme hack for setuptools_scm.
    Appears to be necessary to due to the bug documented here: https://github.com/pypa/setuptools_scm/issues/342
    If that issue is resolved, this method can be removed.
    """
    import time

    from setuptools_scm.version import guess_next_version

    if version.exact:
        return version.format_with("{tag}")
    else:
        _super_value = version.format_next_version(guess_next_version)
        now = int(time.time())
        return _super_value + str(now)


def local_version(version):
    """
    Local version scheme hack for setuptools_scm.
    Appears to be necessary to due to the bug documented here: https://github.com/pypa/setuptools_scm/issues/342
    If that issue is resolved, this method can be removed.
    """
    return ""


setup(
    name="nws-wwa",
    description="Download watch, warning and advisory data from the National Weather Service",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Ben Welsh",
    author_email="b@palewi.re",
    url="http://www.github.com/datadesk/nws-wwa",
    license="MIT",
    packages=("nws_wwa",),
    install_requires=["requests", "fiona", "geojson", "click", "exceptiongroup"],
    entry_points="""
        [console_scripts]
        nwswwa=nws_wwa.cli:cmd
    """,
    use_scm_version={"version_scheme": version_scheme, "local_scheme": local_version},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
    ],
    project_urls={
        "Maintainer": "https://github.com/datadesk",
        "Source": "https://github.com/datadesk/nws-wwa",
        "Tracker": "https://github.com/datadesk/nws-wwa/issues",
    },
)
