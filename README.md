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
    
    [test1]
    base_name: eb_testconf1
    dir: ~/foo/bar, /foo/bar/bam, ~/baz
    db: postgres:db_name:db_user, postgres:db_another_name:db_user
    
    [test2]
    base_name: eb_testconf2
    dir: ~/testconf2

## Usage examples

    # Backups
    $ easybackups_start --conf=~/myconf.ini  # Run all backups in conf
    $ easybackups_start --conf=~/myconf.ini --groups=test1  # Run all backups in group [test1]
    $ easybackups_start --conf=~/myconf.ini --routines=dir  # Run only filesystem backups.
    
    # Shipping
    $ easybackups_ship --conf=~/myconf.ini  # Rsync all backups to remote location.
    
    
## Installation

    $ virtualenv ./pyvenv
    $ source ./pyvenv/bin/activate
    $ cd /dir/with/setup.py/
    $ pip install .
    
    
## Example crons

    # Start backups daily at 3.30 a.m.
    30 3 * * * source /path/to/pyvenv/bin/activate && easybackups_start --conf=/path/to/easybackups_conf.ini >> /path/to/logs/easybackups_start.log 2>&1
    # Ship backups daily at 4.30 a.m.
    30 4 * * * source /path/to/pyvenv/bin/activate && easybackups_ship --conf=/path/toeasybackups_conf.ini >> /path/to/logs/easybackups_ship.log 2>&1
    

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