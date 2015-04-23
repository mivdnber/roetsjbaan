from setuptools import setup
from os.path import join, dirname

with open(join(dirname(__file__), 'requirements.txt')) as f:
    requirements = list(f)

setup(
    name='roetsjbaan',
    version='0.1.1',
    description='A minimal, lightweight migration system',
    url='https://github.com/mivdnber/roetsjbaan',
    download_url='https://github.com/mivdnber/roetsjbaan/tarball/0.1.1',
    author='Michiel Van den Berghe',
    author_email='michiel.vdb@gmail.com',
    license='MIT',
    packages=['roetsjbaan'],
    keywords=['migration', 'database'],
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'roetsj=roetsjbaan.main:main'
        ]
    },
    install_requires=requirements
)
