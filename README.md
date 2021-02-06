# QE-Programs
Connect to your Raspberry Pi via SSH the Clone this repo: git clone https://github.com/nrjphwe/QE-Programs

Then do: CD QE-programs and ./QE-install

Need to update the config.ini file to your mysql password.

The i2c connection uses pin 3 for SDA, and pin 5 for SCL

The shut down uses GPIO4, which is Pin 7 and pin 9 (ground)

- Pin 2 5V power
- Pin 3 i2c SDA (GPIO2)
- Pin 5 i2c SCL (GPIO3)
- Pin 6 Ground, Ground used for shutdown (could maybe use 6 GND as well?)
- Pin 7 GPIO4 used for shutdown
- Pin 8 GPIO14 used for speed pulses


To get into phpmyadmin: http://192.xxx.x.xxx/phpmyadmin/
