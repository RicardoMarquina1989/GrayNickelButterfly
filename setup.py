from setuptools import setup, find_packages

setup(
    name='orca_whirlpools_py',
    version='0.1',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/RicardoM11/orca_whirlpools_py',
    author='Ricardo Andres Marquina Molina',
    author_email='paolasuxobravo@gmail.com',
    description='Python Library for handling ORCA CLAMM. Easy and vast',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)