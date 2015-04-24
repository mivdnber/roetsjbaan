from setuptools import setup

setup(
    name='roetsjbaan',
    version='0.1.4',
    description='A minimal, lightweight migration system',
    url='https://github.com/mivdnber/roetsjbaan',
    download_url='https://github.com/mivdnber/roetsjbaan/tarball/0.1.4',
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
    install_requires=[
        'slugify==0.0.1',
        'tabulate==0.7.5'
    ]
)
