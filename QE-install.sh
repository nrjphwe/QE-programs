#!/bin/bash
#trap 'read -p "run: $BASH_COMMAND "' DEBUG

#set -e
set -x

cd "$(dirname "$0")/.."

# We start the power_check script on boot by using systemd file 
sudo cp -v script/power_check.service /lib/systemd/system
sudo chmod u+x /lib/systemd/system/power_check.service
sudo systemctl daemon-reload
sudo systemctl enable power_check.service
sudo systemctl start power_check.service
systemctl status power_check.service

echo "=> Installing power check php files at /var/www/html/...\n"
sudo cp -v w3.css /var/www/html
sudo chmod -R 755 /var/www/html/
sudo chown -R www-data:www-data /var/www/html

echo "=> setup for ADS1115 ...\n"
sudo apt-get -y install python3-pip
sudo pip3 install adafruit-circuitpython-ads1x15

echo "=> setup SQL-Mariadb:...\n"
sudo apt -y install mariadb-server mariadb-client
echo "sudo mysql_secure_installation"
sudo mysql_secure_installation

echo " === Now some manual steps, copy the lines and paste into mysql                  ==="
echo " === after sudo mysql -u root then                                               ==="
echo " === UPDATE mysql.user SET plugin = 'mysql_native_password' WHERE User = 'root'; ==="
echo " === create user pi@localhost identified by "password";                          ==="
echo " === grant all privileges on regattastart.* TO pi@localhost;                     ==="
echo " === FLUSH PRIVILEGES;                                                           ==="
echo " === now mysql -u root                                                           ==="
sudo mysql -u root

echo "now comes: sudo systemctl stop mariadb"
sudo systemctl stop mariadb
#sudo mysqld_safe --skip-grant-tables --skip-networking &
#sudo systemctl start mysql.service
#sudo systemctl start mariadb

echo "python integration to MYSQL"
sudo pip3 install mariadb
sudo apt install python3-mysql.connector
sudo apt-get install phpmyadmin -y
sudo systemctl start mysql.service
sleep 5
systemctl status mariadb.service

# import/add sql data to db
mysql -h localhost -u pi -p < mysql.txt

# install Grafana
sudo apt-get install -y adduser libfontconfig1
wget https://dl.grafana.com/oss/release/grafana_7.3.1_armhf.deb
sudo dpkg -i grafana_7.3.1_armhf.deb
sudo /bin/systemctl daemon-reload
sudo /bin/systemctl enable grafana-server
### You can start grafana-server by executing
sudo /bin/systemctl start grafana-server
systemctl status grafana-server

# Create a credential file for mysql
# by nano ~/.bash_profile and add this text
# export SQL_HOST=‘localhost’
# export SQL_USER=‘pi’
# export SQL_PWD=‘password’
# export SQL_DB=‘regattastart'
# 
# then do source ~/.bash_profile
