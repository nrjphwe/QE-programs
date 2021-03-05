import serial, pynmea2, string
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
