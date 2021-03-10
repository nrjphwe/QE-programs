#!/usr/bin/python3
import RPi.GPIO as GPIO
from time import sleep
import sys, time, math
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)
# Create the ADC object using the I2C bus
ads = ADS.ADS1015(i2c)
ads.gain = 2/3
# Create differential input between channel 0 and 1
chan_diff = AnalogIn(ads, ADS.P0, ADS.P1)

# setup db
import mariadb
from python_mysql_dbconfig import read_db_config
dbconfig = read_db_config()
conn = None
try:
    print('connecting to Mysql DB..')
    conn = mariadb.connect(**dbconfig)
    cursor = conn.cursor()
except mariadb.Error as e:
    print(f"line 29 Error connecting to MariaDB Platform:{e}")
    sys.exit(1)

def add_data(cursor, wind_dir, lat, lon, speed, true_course,wmg):
   try: # def Add data to Mariadb
      """Adds the given data to the tables"""
      sql_insert_query = (f'INSERT INTO gps (wind_dir, lat, lon, speed, true_course, wmg) VALUES ({wind_dir:.1f},{lat:.11},{lon:.11},{speed:.6},{true_course:.1f},{wmg:.2f})')
      cursor.execute(sql_insert_query)
      conn.commit()
   except mariadb.Error as e:
      print(f"Error inserting to db: {e}")
      sys.exit(1)
      
# calculate average wind direct
def get_average(angles):
    sin_sum = 0.0
    cos_sum = 0.0
    for angle in angles:
        r = math.radians(angle)
        sin_sum += math.sin(r)
        cos_sum += math.cos(r)
    flen = float(len(angles))
    s = sin_sum / flen
    c = cos_sum / flen
    arc = math.degrees(math.atan(s / c))
    average = 0.0
    if s > 0 and c > 0:
        average = arc
    elif c < 0:
        average = arc + 180
    elif s < 0 and c > 0:
        average = arc + 360
    return 0.0 if average == 360 else average
# Wind
count = 0
values = []
def get_value(length=5):
    data = []
    print("Measuring wind direction for %d seconds..." % length)
    start_time = time.time()
    while time.time() - start_time <= length:
        wind_volt =round(chan_diff.voltage,2)
        if (wind_volt > 4.55 ): angle = 270;    # W
        elif (wind_volt > 4.30): angle = 315;   # NW
        elif (wind_volt > 4.00): angle = 292.5; # WNW
        elif (wind_volt > 3.81): angle = 0;     # N
        elif (wind_volt > 3.40): angle = 337.5; # NNW
        elif (wind_volt > 3.02): angle = 225;   # SW
        elif (wind_volt > 2.85): angle = 247.5; # WSW
        elif (wind_volt > 2.20): angle = 45;    # NE
        elif (wind_volt > 1.94): angle = 22.5;  # NNE
        elif (wind_volt > 1.40): angle = 180;   # S
        elif (wind_volt > 1.19): angle = 202.5; # SSW
        elif (wind_volt > 0.95): angle = 135;   # SE
        elif (wind_volt > 0.62): angle = 157.5; # SSE
        elif (wind_volt > 0.52): angle = 90; # E
        elif (wind_volt > 0.48): angle = 67.5; # ENE
        elif (wind_volt > 0.38): angle = 112.5 # ESE
        else: angle = 400; # Err
        if not wind_volt in values: # keep only good measurements
            print('unknown value ' + str(angle) + ' ' + str(wind_volt))
            values.append(wind_volt)
        data.append(angle)
    return get_average(data)

if __name__ == "__main__":
#    obj = wind_direction(0, "wind_direction.json")
     while True:
          print (get_value())
          wind_dir = round(get_value(),1)
          print('wind_dir = '+ str(wind_dir))
          try:
              add_data(cursor, wind_dir)
          except mariadb.Error as e:
              print(f"line 81 Error inserting to db: {e}")
              sys.exit(1)
print(f"Last Inserted ID: {cursor.lastrowid}")
cursor.close()
conn.close()
