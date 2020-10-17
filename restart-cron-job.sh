#!/bin/sh

set -e

scriptdir=$(cd $(dirname $0); pwd -P)

. $scriptdir/os.sh

if [ "$OS" = "OSX" ]; then
    cronfile=$HOME/Library/LaunchAgents/org.iacr.eprint.notifier.plist

    if [ -f $cronfile ]; then
        echo "Unloading $cronfile..."
        launchctl unload $cronfile

        echo "Realoading..."
        launchctl load -w $cronfile
    else
        echo "$cronfile does not exist."
        echo "Did you add it using $scriptdir/add-cron-job.sh?"
        exit 1
    fi
else
    echo "ERROR: Not implemented yet."
    exit 1
fi
