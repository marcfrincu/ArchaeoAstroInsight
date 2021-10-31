from math import sin, cos, asin, degrees, radians
import os

#check computed declination against declinations of the sun and moon
def checkDeclinationSunMoon(calculatedDeclination):
    if calculatedDeclination < -0.5:
        winter_solistice = 23.5 - abs(calculatedDeclination)
        north_minor_lunar_standstill = 18.1 - abs(calculatedDeclination)
        north_major_lunar_standstill = 28.7 - abs(calculatedDeclination)

        if abs(winter_solistice) <= 0.5:
            print("Winter solistice")
            return "Winter solstice"
        elif abs(north_minor_lunar_standstill) <= 0.5:
            print("North minor lunar standstill")
            return "North minor lunar standstill"
        elif abs(north_major_lunar_standstill) <= 0.5:
            print("North major lunar standstill")
            return "North major lunar standstill"

    elif calculatedDeclination > 0.5:
        summer_solistice = 23.5 - calculatedDeclination
        south_minor_lunar_standstill = 18.1 - calculatedDeclination
        south_major_lunar_standstill = 28.7 - calculatedDeclination

        if abs(summer_solistice) <= 0.5:
            print("Summer solistice")
            return "Summer solstice"
        elif abs(south_minor_lunar_standstill) <= 0.5:
            print("South minor lunar standstill")
            return "South minor lunar standstill"
        elif abs(south_major_lunar_standstill) <= 0.5:
            print("South major lunar standstill")
            return "South major lunar standstill"
    else:
        print("Equinox")
        return "Equinox"

    return "None"


#check computed declination against declinations of starts from the  Bright Star Catalogue, 5th Revised Ed. (Hoffleit+, 1991)
def checkDeclinationBSC5(calculatedDeclination, path):
    file_path = os.path.join(path, "bsc5.dat")
    with open(file_path, "rt") as f:
        stars = []
        for line in f:
            if (len(line) < 100) or (line[0] == '#'):
                continue
            try:
                # Read the declination of this star (J2000)
                dec_neg = (line[83] == '-')
                dec_deg = float(line[84:86])
                dec_min = float(line[86:88])
                dec_sec = float(line[88:90])

                declination = dec_deg + dec_min/60 + dec_sec/3600
                if dec_neg:
                    declination = -declination

                #read the visible magnitude of this star
                mag = float(line[102:107])

                #read the name of this star
                name = line[4:14]

                if calculatedDeclination < 0:
                    error_margin = calculatedDeclination + abs(declination)

                    if abs(error_margin) <= 0.5:
                        if mag <= 2:
                            print(name)
                            stars.append(name)
                else:
                    error_margin = declination - abs(calculatedDeclination)

                    if abs(error_margin) <= 0.5:
                        if mag <= 2:
                            print(name)
                            stars.append(name)
            except ValueError:
                continue
    return stars

def computeAzimuth(points):
    az = points[0].azimuth(points[1])
    if az < 0:
        az += 360
    print("Azimuth is: {}".format(az))
    return az


def computeDeclination(altitude, azimuth, points):
    dec_sin = sin(radians(altitude))*sin(radians(points[0].y())) + cos(radians(altitude))*cos(radians(points[0].y()))*cos(radians(azimuth))
    #print(dec_sin)
    declination = asin(dec_sin)
    #print(declination)
    print("Declination in degrees is {}".format(degrees(declination)))
    print("Relevant celestial bodies:")
    return degrees(declination)