from setuptools import setup, find_packages
import os
import sys

install_requires = [
    "zmq",
    "numpy",
    # "matplotlib",
    "pyyaml",
    "click",
    # "mysqlclient",
    "jinja2",
    "google-api-python-client",
    "google-auth-httplib2",
    "google-auth-oauthlib",
    'Sphinx',
]

#
from shutil import copyfile, rmtree

if not os.path.exists("tmps"):
    os.makedirs("tmps")
copyfile("crundb/version.py", "tmps/version.py")
__import__("tmps.version")
package = sys.modules["tmps"]
package.version.update_release_version("crundb")

setup(
    name="CHECRunPage",
    version=package.version.get_version(pep440=True),
    description="",
    author="Samuel Flis",
    author_email="samuel.flis@desy.de",
    url="https://github.com/sflis/crundb",
    packages=find_packages(),
    provides=["crundb"],
    license="GNU Lesser General Public License v3 or later",
    install_requires=install_requires,
    extras_requires={
        #'encryption': ['cryptography']
    },
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={
        "console_scripts": ["chec-runpage-submit=crundb.bin.local_submit:run_local"]
    },
)


rmtree("tmps")
