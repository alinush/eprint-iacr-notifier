#!/bin/bash

set -e
#set -x

scriptdir=$(cd $(dirname $0); pwd -P)

. $scriptdir/os.sh

logdir=/var/log/eprint
logfile=$logdir/out+err.log

if [ "$OS" = "OSX" ]; then
    name=org.iacr.eprint.notifier
    cronfile=$HOME/Library/LaunchAgents/$name.plist

    echo "Cronfile at '$cronfile':"
    echo "========================"
    if [ -f "$cronfile" ]; then
        cat $cronfile
    else
        echo "ERROR: No launchd .plist file at '$cronfile'"
    fi
    echo

    echo "Last run in logfile at '$logfile':"
    echo "=================================="
    if [ -f $logfile ]; then
        last_run_line=`grep -n ^Time: /var/log/eprint/out+err.log | tail -n 1 | cut -f 1 -d:`

        if [ -n "$last_run_line" ]; then
            tail -n +$last_run_line $logfile
        fi
    else
        echo "ERROR: No $logfile in $logdir. List of files in $logdir is:"
        ls -l $logdir
    fi
    echo

    echo "Status in 'launchctl list':"
    echo "==========================="
    list=`launchctl list`
    echo "$list" | head -n 1
    echo "$list" | grep $name
    echo
    echo "(If status is 0, then all went well the last time the script was run!)"
fi
