# easybackups

## Config file

    [DEFAULT]
    ; Base directory to store backups in.
    ; CAUTION: the clean command looks inside this directory and removes 
    ; outdated files from there, so be sure that this points to the right place.
    backup_storage_dir: ~/easybackups
    dir:
    db:

    ; Settings for default shipper. Can be overridden per group. 
    shipper_ssh_port: 222
    shipper_user: rsync_user
    shipper_host: rsync_host
    shipper_dir: /path/to/rsync/target/dir

    ; Settings for cleaner. Can be overridden per group.
    cleaner_days_to_keep: 7
    cleaner_weeks_to_keep: 4
    cleaner_months_to_keep: 12
    cleaner_day_of_week_to_keep: 4
    cleaner_day_of_month_to_keep: 15
    
    [test1]
    ; Each section is treated as a backup group. Backups for groups are 
    ; namespaced in a folder named after the section, e.g. <base_dir>/test1/
    
    ; Multiple directories separated by comma (,).
    dir: ~/foo/bar, ~/baz
    
    ; Multiple databases separated by comma (,).
    db: postgres:db_name:db_user, postgres:db_another_name:db_user
    
    [test2]
    dir: ~/testconf2
    
    [test3]
    db: postgres:db_name:db_user

## Usage examples

    # Help
    $ esbckp
    $ esbckp --help
    
    # Help for subcommand
    $ esbckp [command] --help
    
    # Backups
    $ esbckp start --conf=~/myconf.ini  # Run all backups in conf
    $ esbckp start --conf=~/myconf.ini --groups=test1  # Run all backups in group [test1]
    $ esbckp start --conf=~/myconf.ini --routines=dir  # Run only filesystem backups.
    
    # Shipping
    $ esbckp ship --conf=~/myconf.ini  # Rsync all backups to remote location.
    
    # Cleaning
    $ esbckp clean --conf=~/myconf.ini # Prints paths of backups to be deleted to stdout
    $ esbckp clean --conf=~/myconf.ini --dryrun=False # Removes backups marked for deletion
    
    
    
## Installation

    $ virtualenv ./pyvenv
    $ source ./pyvenv/bin/activate
    $ cd /dir/with/setup.py/
    $ pip install .
    
    
## Example crons

    # Start backups daily at 3.30 a.m.
    30 3 * * * source /path/to/pyvenv/bin/activate && esbckp start --conf=/path/to/easybackups_conf.ini >> /path/to/logs/easybackups_start.log 2>&1
    # Ship backups daily at 4.30 a.m.
    30 4 * * * source /path/to/pyvenv/bin/activate && esbckp ship --conf=/path/toeasybackups_conf.ini >> /path/to/logs/easybackups_ship.log 2>&1
    # Remove outdated backups daily at 5.30 a.m.
    30 5 * * * source /path/to/pyvenv/bin/activate && esbckp clean --dryrun=False --conf=/path/toeasybackups_conf.ini >> /path/to/logs/easybackups_ship.log 2>&1
    

## About authentication

To run the scripts automated the host machine needs to be able to access the 
remote machine without a password prompt, e.g. by authorizing the public key 
of the host in the remote machine's authorized_keys.

To create the database backups (currently postgres) the cron user needs to 
be able to access the database, e.g. by using a .pgpass file or by running 
the cron as an appropriate user.


## Dependencies

Created with Click, support colorama.

* [Click](http://click.pocoo.org/3/)
* [colorama](https://github.com/tartley/colorama)