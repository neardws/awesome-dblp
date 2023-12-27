from setuptools import setup
from codecs import open
from os import path
here = path.abspath(path.dirname(__file__))
setup(
    name='awesome-dblp',
    version='1.1',
    description='A simple python package to search dblp by keywords and venues',
    # The project's main homepage.
    url='https://github.com/neardws/awesome-dblp',
    # Author details
    author='neardws',
    author_email='neard.ws@gmail.com',
    # Choose your license
    license='GPLv3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Education',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    py_modules=["dblp"],
    install_requires=['tqdm', 'lxml', 'requests', 'thefuzz', 'fake_useragent']
)