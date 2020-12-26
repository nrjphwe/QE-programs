#!/usr/bin/python3
import RPi.GPIO as GPIO
from time import sleep
import time, math
import mariadb
from mysql.connector import MySQLConnection, Error
from python_mysql_dbconfig import read_db_config

def connect():
    """ Connect to MySQL database """
    dbconfig = read_db_config()
    conn = None
    try:
		conn = mariadb.connect(**dbconfig)
		cursor = conn.cursor()

    except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform:{e}")
    sys.exit(1)

try:
    # def Add data
    def add_data(cursor,rpm,nmh,dist_meas):
    """Adds the given data to the power table"""
    sql_insert_query = (f'INSERT INTO knots ( rpm, nmh, dist_meas) VALUES ({rpm:},{nmh:.3f},{dist_meas:.4f})')
    cursor.execute(sql_insert_query)
    conn.commit()

except mariadb.Error as e:
    print(f"Error adding data to Maridb: {e}")
    sys.exit(1)


dist_meas = 0.00
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
    elapse = time.time() - start_timer      # elapse for every 1 complete rotation made!
    start_timer = time.time()           # let current time equals to start_timer

def calculate_speed(r_cm):
    global pulse,elapse,rpm,dist_nm,dist_meas,nm_per_sec,nm_per_hour
    if elapse !=0:                  # to avoid DivisionByZero error
        rpm = 1/elapse * 60
        circ_cm = (2*math.pi)*r_cm      # calculate wheel circumference in CM
        #dist_km = circ_cm/100000       # convert cm to km
        dist_nm = circ_cm/185200        # convert cm to km
        #km_per_sec = dist_km / elapse      # calculate Km/sec
        nm_per_sec = dist_nm / elapse       # calculate Nm/sec
        #km_per_hour = km_per_sec * 3600    # calculate Km/h
        nmh = nm_per_sec * 3600     # calculate knots (Nn/h)
        #dist_meas = (dist_km*pulse)*1000   # measure distance traverse in meter
        dist_meas = (dist_nm*pulse)*1000    # measure distance traverse in meter
        return nmp
#       return nm_per_hour

def init_interrupt():
    GPIO.add_event_detect(sensor, GPIO.FALLING, callback = calculate_elapse, bouncetime = 20)

if __name__ == '__main__':
    init_GPIO()
    init_interrupt()
    while True:
        calculate_speed(5)  # call this function with wheel radius as parameter
        print('rpm:{0:.0f}-RPM Nmh:{1:.2f}-NMH dist_meas:{2:.2f}m pulse:{3}'.format(rpm,nm_per_hour,dist_meas,pulse))
        try:
            add_data(cursor,rpm, nmh, dist_meas)
        except mariadb.Error as e:
            print(f"Error inserting to db: {e}")
            sys.exit(1)
        time.sleep(0.1)
        print(f"Last Inserted ID: {cursor.lastrowid}")
        time.sleep(5)
        cursor.close()
        conn.close()
