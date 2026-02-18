from setuptools import setup, find_packages

setup(
    name = 'topas_tools',
    version= '1.0.0',
    packages= find_packages(where='src'),
    package_dir = {'': 'src'},
    install_requires = [
        # List package dependencies here
        'pymatgen',
        'tqdm',
        'plotly',
        'texttable',
        'numpy',
        'fabio',

    ],
    entry_points = {
        'console_scripts': [
            # Define command-line scripts here
        ],
    },
    author= 'Dario C. Lewczyk',
    author_email='darlewczyk@gmail.com',
    description='A complete suite of tools for automating runtime of TOPAS Rietveld Refinements and analyzing outputs',
    long_description=open('README.md').read(),
    long_description_content_type = 'text/markdown',
    url= 'https://github.com/DarioLewczyk/topas_tools',
    classifiers= [
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires = '>=3.6',

)
