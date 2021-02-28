#!/usr/bin/python3
import os
import sys,time, math
from time import sleep
import mariadb
import datetime #new
import board
import busio
import RPi.GPIO as GPIO
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

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
   print(f"Error connecting to MariaDB Platform: {e}")
   sys.exit(1)

# initialize GPIO
def init_GPIO():           # initialize GPIO
   GPIO.setmode(GPIO.BCM)
   GPIO.setwarnings(False)
   GPIO.setup(sensor,GPIO.IN,GPIO.PUD_UP)

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)
# Create the ADC object using the I2C bus
ads = ADS.ADS1015(i2c)
chan1_diff = AnalogIn(ads, ADS.P0, ADS.P1) # Create differential input between channel 0 and 1
chan2_diff = AnalogIn(ads, ADS.P2, ADS.P3) # Create differential input between channel 2 and 3

#To boost small signals, the gain can be adjusted on the ADS1x15 chips in the following steps:
#GAIN_TWOTHIRDS (for an input range of +/- 6.144V)
#// ads1015.setGain(GAIN_TWOTHIRDS); // 2/3x gain +/- 6.144V 1 bit = 3mV (default)
#// ads1015.setGain(GAIN_ONE);     // 1x gain   +/- 4.096V  1 bit = 2mV
#// ads1015.setGain(GAIN_TWO);     // 2x gain   +/- 2.048V  1 bit = 1mV
#// ads1015.setGain(GAIN_FOUR);    // 4x gain   +/- 1.024V  1 bit = 0.5mV
#// ads1015.setGain(GAIN_EIGHT);   // 8x gain   +/- 0.512V  1 bit = 0.25mV
#// ads1015.setGain(GAIN_SIXTEEN); // 16x gain  +/- 0.256V  1 bit = 0.125mV
ads.gain = 2/3

# Wind
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

#speed -- params to set:
sleeptime= 1  #secs between reporting loop
secsnoread= 6 #number of seconds rotor is stationary before a 'no read' is declared and set result to zero - depends on inertia of your rotor in light >no wind
errortime= 90 #number of seconds of no activity before error/stationary warning is shown - set high after debugging
loopcount= 0  #a 'nothing is happening' counter
r_cm = 2.5    #cm wheel radius as parameter (assumed centre of cups)
sensor = 14   #BCM
magnets = 1   #how many magnets in your rotor? (code assumes one sensor though)

# startup numbers
adjustment = 1
dist_meas = 0
olddist_meas = 0
circ_cm = (2*math.pi) * r_cm  # calculate wheel circumference in CM
dist_nm = circ_cm/185200/magnets
nm_per_hour = 0
rpm = 0
elapse = 0
pulse = 0
start_timer = time.time()
avg_timer = time.time() #start of this average timing

def calculate_elapse(channel):              # callback function
    global pulse, start_timer, elapse
    pulse+=1                    # increase pulse by 1 whenever interrupt occurred
    elapse = time.time() - start_timer  # elapse for every 1 complete rotation made!
    start_timer = time.time()           # let current time equals to start_timer

def calculate_speed():
    global elapse,rpm,dist_meas,oldist_meas,nm_per_hour
    try:
        rpm = 1/elapse * 60    # 1 interupt per rotation, 1 magnet out of 4 paddels
        dist_nm = circ_cm/185200        # convert cm to nm
        nm_per_hour = dist_nm / elapse * 3600     # calculate knots (Nm/h)
        nmh = nm_per_hour
        dist_meas = dist_nm * pulse * 1852  # measure distance traverse in meter
        if dist_meas == olddist_meas:
            nm_per_hour = 0
            rpm = 0
        return nm_per_hour
    except ZeroDivisionError:
        pass

def report(mode):
        if mode=='realtime': #comment this mode if you want a quieter report, or use
            knots=nm_per_hour
            print(datetime.now().ctime(),'{0:.0f} RPM, {1:.1f} knots'.format(rpm,knots))
        elif mode=='average':
            print(datetime.now().ctime(),'{0:.1f} Gust, {1:.1f} Average (both Knots)'.format(gust/1.852,avg/1.852))
        elif mode=='error':
            print(datetime.now().ctime(),'dead calm or connection fault') #report rotor still stationary
        else:
            print('bad report mode')

def init_interrupt():
    # add falling edge detection on "sensor" channel, ignoring further edges for 10ms
    GPIO.add_event_detect(sensor, GPIO.FALLING, callback = calculate_elapse, bouncetime = 10)
   
# Wind Get Value
count = 0
values = []
def get_value(length=5):      # Def wind Get Value
    data = []
    print("Measuring wind direction for %d seconds..." % length)
    start_time = time.time()
    while time.time() - start_time <= length:
        wind_volt =round(chan1_diff.voltage,2)
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

try: # def Add data to Mariadb
   def add_data(cursor, rpm, nm_per_hour, dist_meas, angle):
      """Adds the given data to the tables"""
      sql_insert_query = (f'INSERT INTO knots (rpm, nmh, dist_meas) VALUES ({rpm:2f},{nm_per_hour:.3f},{dist_meas:.2f})')
      sql_insert_query = (f'INSERT INTO wind (angle) VALUES ({angle:.1f})')
      cursor.execute(sql_insert_query)
      conn.commit()

except mariadb.Error as e:
   print(f"Error adding data to Maridb: {e}")
   sys.exit(1)

# startt
init_GPIO()
init_interrupt()
if __name__ == "__main__":
#    obj = wind_direction(0, "wind_direction.json")    
    while True:
        olddist_meas = dist_meas
        calculate_speed()
        if olddist_meas!=dist_meas:
            loopcount=0
            report('realtime')
        else:
            loopcount+=1
            if loopcount==secsnoread/sleeptime: #its stopped, force show a zero as it might be 'between magnets' and show last value
                report('realtime')
            if loopcount==20/sleeptime: #after each 60 secs
                loopcount=secsnoread/sleeptime+1 #reset loopcount
                report('error')
            sleep(sleeptime)
        print (get_value())
        angle = round(get_value(),1)
        print('angle ' + ' ' + str(angle))
        print('rpm:{0:.2f}-RPM, nmh:{1:.3f}-knots, dist_meas:{2:.2f}m pulse:{3} elapse:{4:.3f},start_timer:{5:.3f}'.format(rpm,nm_per_hour,dist_meas,pulse, elapse, start_timer))
        try:
            add_data(cursor,rpm, nm_per_hour, dist_meas, angle)
        except mariadb.Error as e:
            print(f"Error inserting to db: {e}")
            sys.exit(1)
        time.sleep(5)
print(f"Last Inserted ID: {cursor.lastrowid}")
cursor.close()
conn.close()
