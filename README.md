# easybackups

## Config file

    [DEFAULT]
    backup_storage_dir: ~/easybackups
    dir:
    db:
    shipper_ssh_port: 222
    shipper_user: rsync_user
    shipper_host: rsync_host
    shipper_dir: /path/to/rsync/target/dir
    cleaner_days_to_keep: 7
    cleaner_weeks_to_keep: 4
    cleaner_months_to_keep: 12
    cleaner_day_of_week_to_keep: 4
    cleaner_day_of_month_to_keep: 15
    
    [test1]
    base_name: eb_testconf1
    dir: ~/foo/bar, /foo/bar/bam, ~/baz
    db: postgres:db_name:db_user, postgres:db_another_name:db_user
    
    [test2]
    base_name: eb_testconf2
    dir: ~/testconf2

## Usage examples

    # Help
    $ esbck
    $ esbck --help
    
    # Help for subcommand
    $ esbck [command] --help
    
    # Backups
    $ esbck start --conf=~/myconf.ini  # Run all backups in conf
    $ esbck start --conf=~/myconf.ini --groups=test1  # Run all backups in group [test1]
    $ esbck start --conf=~/myconf.ini --routines=dir  # Run only filesystem backups.
    
    # Shipping
    $ esbck ship --conf=~/myconf.ini  # Rsync all backups to remote location.
    
    # Cleaning
    $ esbck clean --conf=~/myconf.ini # Prints paths of backups to be deleted to stdout
    $ esbck clean --conf=~/myconf.ini --dryrun=False # Removes backups marked for deletion
    
    
    
## Installation

    $ virtualenv ./pyvenv
    $ source ./pyvenv/bin/activate
    $ cd /dir/with/setup.py/
    $ pip install .
    
    
## Example crons

    # Start backups daily at 3.30 a.m.
    30 3 * * * source /path/to/pyvenv/bin/activate && esbck start --conf=/path/to/easybackups_conf.ini >> /path/to/logs/easybackups_start.log 2>&1
    # Ship backups daily at 4.30 a.m.
    30 4 * * * source /path/to/pyvenv/bin/activate && esbck ship --conf=/path/toeasybackups_conf.ini >> /path/to/logs/easybackups_ship.log 2>&1
    # Remove outdated backups daily at 5.30 a.m.
    30 4 * * * source /path/to/pyvenv/bin/activate && esbck clean --dryrun=False --conf=/path/toeasybackups_conf.ini >> /path/to/logs/easybackups_ship.log 2>&1
    

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