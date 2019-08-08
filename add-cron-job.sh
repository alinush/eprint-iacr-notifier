#!/bin/sh

set -e

scriptdir=$(cd $(dirname $0); pwd -P)

logdir=/var/log
logfile=$logdir/eprint.log
cronfile=/etc/cron.d/eprint-iacr-notifier
name=eprint-iacr-notifier.py
bin=/usr/bin/$name
conf=/etc/eprint-iacr-notifier.conf

if [ -f "$cronfile" ]; then
    echo "Cronfile has already been set up in $cronfile. Nothing to do. Exiting..."
    exit 0
fi

# symlink script in /usr/bin
sudo ln -s $scriptdir/$name $bin
sudo chmod +x $bin

# write year and latest paper ID to conf file
conf_tmp=`mktemp`
year=`date +%Y`
read -p "What is the last paper ID you have read? " ID
echo $year >$conf_tmp
echo $ID >>$conf_tmp
sudo mv $conf_tmp $conf

# get details about the Gmail account used to send emails
read -p "What is the email address that should receive new paper notifications? " NOTIF_EMAIL
read -p "Gmail account username that should send out the emails: " GMAIL_USER
read -p "Gmail account password: " GMAIL_PASSWD
GMAIL_ADDR="$GMAIL_USER@gmail.com"

# create log file in /var/log/eprint.log
sudo touch "$logfile"
sudo chown `whoami`:`whoami` "$logfile"

# configure cron job in /etc/cron.d/
# For help, see: https://crontab.guru/#0_5_*_*_1-7
time="5"        # the hour of the day to run the script: from 0 to 23 (military format)
days="1-7"      # the days of the week to run the script: any range from 1 to 7
cron_tmp=`mktemp`
echo "0 $time * * $days `whoami` $bin $NOTIF_EMAIL $GMAIL_ADDR $GMAIL_PASSWD $conf >>$logfile 2>&1" >$cron_tmp
# if you want to test the cron job is installing correctly, use this 'every 1-minute' template instead
#echo "* * * * * `whoami` $bin $NOTIF_EMAIL $GMAIL_ADDR $GMAIL_PASSWD $conf >>$logfile 2>&1" >$cron_tmp
sudo mv $cron_tmp $cronfile
sudo chmod 0644 $cronfile
sudo chown root:root $cronfile
