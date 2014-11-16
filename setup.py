from setuptools import setup, find_packages

setup(
    name='easybackup',
    version='0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'colorama',
    ],
    entry_points='''
        [console_scripts]
        easybackups_start=easybackup.backups:start
        easybackups_ship=easybackup.backups:ship
        easybackups_clean=easybackup.backups:clean
    ''',
)