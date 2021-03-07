import serial, pynmea2, string

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
   GPIO.setup(sensor,GPIO.IN,GPIO.PUD_UP) #### question

def add_data(cursor, rpm, nm_per_hour, dist_meas):
   try: # def Add data to Mariadb
      """Adds the given data to the tables"""
      sql_insert_query = (f'INSERT INTO gps (lat, lon, speed, true_course) VALUES ({lat:10f},{lon:.10f},{speed:.2f},{true_course:.2f})')
      cursor.execute(sql_insert_query)
      conn.commit()
   except mariadb.Error as e:
      print(f"Error inserting to db: {e}")
      sys.exit(1)

list_of_valid_statuses = ['A','V']
with serial.Serial('/dev/ttyAMA0', baudrate=4800, timeout=1) as ser:
    # read 10 lines from the serial output
    for i in range(5):
        line = ser.readline().decode('ascii', errors='replace')
#        print (line)
        decoded_line = (line.strip(string.punctuation))
#        print (decoded_line)
    while True:
        line = ser.readline().decode('ascii', errors='replace')
#        print (line)
        decoded_line = line.strip()
        if decoded_line[0:6] == '$GPVTG':
            print ("VTG line")
            msg = pynmea2.parse(str(decoded_line))
            print ('Speed over ground = ' + str(msg.spd_over_grnd_kts) + ' True track made good = ' +str(msg.true_track))
            #for i in range(len(msg.fields)):
            #    print (msg.fields[i], msg.data[i])
        if decoded_line[0:6] == '$GPRMC':
            msg = pynmea2.parse(str(decoded_line))
            if str(msg.status) in list_of_valid_statuses:
                print ("RMC line")
                #print (msg.datetime,msg.latitude, msg.longitude)
                #for i in range(len(msg.fields)):
                #    print (msg.fields[i], msg.data[i])
                lat = ("%02d°%07.4f'" % (msg.latitude, msg.latitude_minutes))
                lon = ("%02d°%07.4f'" % (msg.longitude, msg.longitude_minutes))
                gps = "Latitude=" + str(lat) + "and Longitude=" + str(lon)
                print(gps)
                speed = msg.spd_over_grnd
                print ('Speed over ground = ' + str(speed))
                true_course = msg.true_course
                print ('True Course = '+ str(true_course))
                try:
                    add_data(cursor,lat, lon, speed, true_course)
                except mariadb.Error as e:
                    print(f"Error inserting to db: {e}")
                    sys.exit(1)      
