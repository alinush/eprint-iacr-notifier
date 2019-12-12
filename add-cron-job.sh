#!/bin/sh

set -e

scriptdir=$(cd $(dirname $0); pwd -P)

. $scriptdir/os.sh

logdir=/var/log
logfile=$logdir/eprint.log
crondir=/etc/cron.d
cronfile=$crondir/eprint-iacr-notifier
name=eprint-iacr-notifier.py
bin=/usr/local/bin/$name
conf=/etc/eprint-iacr-notifier.conf

if [ "$OS" = "OSX" ]; then
    user_group=staff
    root_group=wheel
else
    user_group=`whoami`
    root_group=root
fi

# symlink script in /usr/bin
sudo ln -sf $scriptdir/$name $bin
sudo chmod +x $bin

if [ ! -f "$conf" ]; then
    # write year and latest paper ID to conf file
    conf_tmp=`mktemp`
    year=`date +%Y`
    read -p "What is the last paper ID you have read? " ID
    echo $year >$conf_tmp
    echo $ID >>$conf_tmp
    sudo mv $conf_tmp $conf
else
    echo "WARNING: Already detected config file at: $conf. Leaving intact."
fi

if [ ! -f "$logfile" ]; then
    # create log file in /var/log/eprint.log
    [ -d $logdir ] || { echo "ERROR: Log directory $logdir does NOT exist."; exit 1; }
    sudo touch "$logfile"
    sudo chown `whoami`:$user_group "$logfile"
else
    echo "WARNING: Already detected log file at: $logfile. Leaving intact."
fi

if [ ! -f "$cronfile" ]; then
    # get details about the Gmail account used to send emails
    read -p "What is the email address that should receive new paper notifications? " NOTIF_EMAIL
    read -p "Gmail account username that should send out the emails: " GMAIL_USER
    read -p "Gmail account password: " GMAIL_PASSWD
    GMAIL_ADDR="$GMAIL_USER@gmail.com"

    # configure cron job in /etc/cron.d/
    # For help, see: https://crontab.guru/#0_5_*_*_1-7
    time="5"        # the hour of the day to run the script: from 0 to 23 (military format)
    days="1-7"      # the days of the week to run the script: any range from 1 to 7
    cron_tmp=`mktemp`
    echo "0 $time * * $days `whoami` $bin $NOTIF_EMAIL $GMAIL_ADDR $GMAIL_PASSWD $conf >>$logfile 2>&1" >$cron_tmp
    # if you want to test the cron job is installing correctly, use this 'every 1-minute' template instead
    #echo "* * * * * `whoami` $bin $NOTIF_EMAIL $GMAIL_ADDR $GMAIL_PASSWD $conf >>$logfile 2>&1" >$cron_tmp
    sudo mkdir -p $crondir
    sudo mv $cron_tmp $cronfile
    sudo chmod 0644 $cronfile
    sudo chown root:$root_group $cronfile
else
    echo "WARNING: Already detected cron file at: $cronfile. Leaving intact."
fi
