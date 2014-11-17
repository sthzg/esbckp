from setuptools import setup, find_packages

setup(
    name='esbckp',
    version='0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'colorama',
    ],
    entry_points='''
        [console_scripts]
        esbckp=esbckp.backups:cli
    ''',
)