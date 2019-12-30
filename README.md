eprint-iacr-notifier
====================

Daily email reminders with the newest [Cryptology ePrint Archive](https://eprint.iacr.org/eprint-bin/search.pl?last=365&title=1) papers.

Just install the Python script as a cronjob and forget about it.

## TODO

 - https://eprint.iacr.org/2019/1172 has a ``<`` sign in the abstract that throws off our parser
 - For now, the script uses a throwaway Gmail account to send emails, because it was the easiest way to get this running. This should be made more flexible.
 - Better logging library

## Installation (as a cron job)

This works both in Ubuntu Linux (via /etc/cron.d/) and on OS X (via launchctl).
First, install dependencies:

    ./install-deps.sh

Then, [create a dummy Gmail account](https://gmail.com) that you do not care about.
Importantly, activate ["less secure apps" mode](https://myaccount.google.com/lesssecureapps), so it can be used by the script to send emails.
**WARNING:** The password of this account will show up in your syslog, so don't use your actual Gmail account.

Second, run the following:

    ./add-cron-job.sh

The script will ask you which paper you've read last, what email address you want to be notified at and the credentials of the dummy Gmail account used to send the notifications.

### OS X

Useful commands:

    launchctl list | grep eprint

## Pull requests

...that fix bugs are very welcome.

## Other IACR ePrint tools

Check out my labmate's Zack Newman [`iacr-dl` Python tool](https://github.com/znewman01/iacr-dl) also which provides a nice Python API for downloading eprint papers.
