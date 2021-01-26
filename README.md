# QEPprograms
Connect to your Raspberry Pi via SSH the Clone this repo: git clone https://github.com/nrjphwe/QE-Programs

Then do: CD QE-programs and ./QE-install

Need to update the config.ini file to your mysql password.


The i2c connection uses pin 3 for SDA, and pin 5 for SCL
The shut down uses GPIO4, which is Pin 7.

Pin 2 5V power
Pin 3 i2c SDA
Pin 5 i2c SCL
Pin 6 Ground
Pin 7 GPIO4 used for shutdown
Pin 9 Ground used for shutdown
pin 12 used for speed pulses
