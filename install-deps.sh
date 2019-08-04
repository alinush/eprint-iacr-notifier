set -e

scriptdir=$(cd $(dirname $0); pwd -P)

. $scriptdir/os.sh

if [ "$OS" = "Linux" ]; then
    sudo apt-get install python-bs4
elif [ "$OS" = "OSX" ]; then
    pip2.7 install lxml
    pip2.7 install beautifulsoup4
fi
