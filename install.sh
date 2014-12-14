#!/bin/bash

# Current script dir
cd "$(dirname "$0")"

# Install required python packages for setup and packages that are comlicated to compile
sudo apt-get update
sudo apt-get install python-numpy python-scipy python-psycopg2 python-pip -y
sudo pip install virtualenv pybuilder

# Create and activate virtualenv for all other packages
virtualenv --system-site-packages venv
source venv/bin/activate

# Use PyBuilder to install deps from requirements.txt and requirements_dev.txt
pyb install_dependencies

# Copy sample configuration
cp sample_config.ini config.ini

# Prompt user for EOSDMDBOne details and replace in config.ini
read -p 'Enter EOSDMDBOne host and port (e.g. localhost:5432): ' host
sed -i -e "s/\(DB_HOST\s*=\s*\).*$/\1$host/g" config.ini

read -p 'Enter EOSDMDBOne database name: ' dbname
sed -i -e "s/\(DB_NAME\s*=\s*\).*$/\1$dbname/g" config.ini

read -p 'Enter EOSDMDBOne database username: ' dbuser
sed -i -e "s/\(DB_USER\s*=\s*\).*$/\1$dbuser/g" config.ini

read -p "Enter $dbuser's password: " dbpassword
sed -i -e "s/\(DB_PASSWORD\s*=\s*\).*$/\1$dbpassword/g" config.ini

# Start Flasks integrated webserver on all interfaces if chosen by the user
read -p 'Do you want to start the backend in dev mode on 0.0.0.0:5000 now? [Y/n] ' -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
    sed -i -e "s/\(CONFIG_TYPE\s*=\s*\).*$/\1development/g" config.ini
    python manager.py dev_listenall
fi
