#!/usr/bin/python3
import RPi.GPIO as GPIO
from time import sleep
import time, math
import mariadb
#from mysql.connector import MySQLConnection, Error
from python_mysql_dbconfig import read_db_config

dist_meas = 0
nmh = 0
nm_per_hour = 0
rpm = 0
elapse = 0
sensor = 18
pulse = 0
start_timer = time.time()

def init_GPIO():                    # initialize GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(sensor,GPIO.IN,GPIO.PUD_UP)

def calculate_elapse(channel):              # callback function
    global pulse, start_timer, elapse
    pulse+=1                    # increase pulse by 1 whenever interrupt occurred
    elapse = time.time() - start_timer  # elapse for every 1 complete rotation made!
    start_timer = time.time()           # let current time equals to start_timer

def calculate_speed(r_cm):
    global pulse,elapse,rpm,dist_nm,dist_meas,nm_per_sec,nm_per_hour
    if elapse !=0:                  # to avoid DivisionByZero error
        rpm = 1/elapse * 60
        circ_cm = (2*math.pi)*r_cm      # calculate wheel circumference in CM
        #dist_km = circ_cm/100000       # convert cm to km
        dist_nm = circ_cm/185200        # convert cm to km
        nm_per_sec = dist_nm / elapse       # calculate Nm/sec
        nm_per_hour = nm_per_sec * 3600     # calculate knots (Nn/h)
        dist_meas = (dist_nm*pulse) * 1000    # measure distance traverse in meter
        #print(nm_per_hour)
        return nm_per_hour

def init_interrupt():
    # add falling edge detection on "sensor" channel, ignoring further edges for 10ms 
    GPIO.add_event_detect(sensor, GPIO.FALLING, callback = calculate_elapse, bouncetime = 10)
# startt 
init_GPIO()
init_interrupt()
dbconfig = read_db_config()
conn = None
try:
    print('connecting to Mysql DB..')
    conn = mariadb.connect(**dbconfig)
    cursor = conn.cursor()
except mariadb.Error as e:
    print(f"line 29 Error connecting to MariaDB Platform:{e}")
    sys.exit(1)
    
while True:
    calculate_speed(5)  # call this function with wheel radius as parameter
    print('rpm:{0:.0f}-RPM mh:{1:.2f}-NMH dist_meas:{2:.2f}m pulse:{3}'.format(rpm,nm_per_hour,dist_meas,pulse))
    try:
        sql_insert_query = (f'INSERT INTO knots (rpm, nmh, dist_meas) VALUES ({rpm:},{nmh:.3f},{dist_meas:.4f})')
        cursor.execute(sql_insert_query)
        conn.commit()
    except mariadb.Error as e:
        print(f"line 81 Error inserting to db: {e}")
        sys.exit(1)
    time.sleep(0.1)
print(f"Last Inserted ID: {cursor.lastrowid}")
#time.sleep(5)
cursor.close()
conn.close()
