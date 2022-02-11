#
# 02/10/2022
# Chris Auron  <chris.auron@gmail.com>
# https://github.com/imaplt/gopro-highlights
#

import sys
import os
import gopro2gpx.config as config
import gopro2gpx.gopro2gpx as gopro2gpx
import gopro2gpx.gpmf as gpmf
import gopro2gpx.fourCC as fourCC
import gopro2gpx.gpshelper as gpshelper
import argparse
from datetime import datetime
import time
import highlights


def parseArgs():

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="count")
    parser.add_argument("-b", "--binary", help="read data from bin file", action="store_true")
    parser.add_argument("-s", "--skip", help="Skip bad points (GPSFIX=0)", action="store_true", default=False)
    parser.add_argument("file", help="Video file or binary metadata dump")
    parser.add_argument("outputfile", help="output file. builds KML and GPX")
    args = parser.parse_args()

    return args


# def BuildGPSPoints(data, skip=False):
#     """
#     Data comes UNSCALED so we have to do: Data / Scale.
#     Do a finite state machine to process the labels.
#     GET
#      - SCAL     Scale value
#      - GPSF     GPS Fix
#      - GPSU     GPS Time
#      - GPS5     GPS Data
#     """
#
#     points = []
#     SCAL = fourCC.XYZData(1.0, 1.0, 1.0)
#     GPSU = None
#     SYST = fourCC.SYSTData(0, 0)
#
#     stats = {
#         'ok': 0,
#         'badfix': 0,
#         'badfixskip': 0,
#         'empty': 0
#     }
#
#     GPSFIX = 0  # no lock.
#     for d in data:
#
#         if d.fourCC == 'SCAL':
#             SCAL = d.data
#         elif d.fourCC == 'GPSU':
#             GPSU = d.data
#         elif d.fourCC == 'GPSF':
#             if d.data != GPSFIX:
#                 print("GPSFIX change to %s [%s]" % (d.data, fourCC.LabelGPSF.xlate[d.data]))
#             GPSFIX = d.data
#         elif d.fourCC == 'GPS5':
#             # we have to use the REPEAT value.
#
#             for item in d.data:
#
#                 if item.lon == item.lat == item.alt == 0:
#                     print("Warning: Skipping empty point")
#                     stats['empty'] += 1
#                     continue
#
#                 if GPSFIX == 0:
#                     stats['badfix'] += 1
#                     if skip:
#                         print("Warning: Skipping point due GPSFIX==0")
#                         stats['badfixskip'] += 1
#                         continue
#
#                 retdata = [float(x) / float(y) for x, y in zip(item._asdict().values(), list(SCAL))]
#
#                 gpsdata = fourCC.GPSData._make(retdata)
#                 p = gpshelper.GPSPoint(gpsdata.lat, gpsdata.lon, gpsdata.alt, datetime.fromtimestamp(time.mktime(GPSU)),
#                                        gpsdata.speed)
#                 points.append(p)
#                 stats['ok'] += 1
#
#         elif d.fourCC == 'SYST':
#             data = [float(x) / float(y) for x, y in zip(d.data._asdict().values(), list(SCAL))]
#             if data[0] != 0 and data[1] != 0:
#                 SYST = fourCC.SYSTData._make(data)
#
#         elif d.fourCC == 'GPRI':
#             # KARMA GPRI info
#
#             if d.data.lon == d.data.lat == d.data.alt == 0:
#                 print("Warning: Skipping empty point")
#                 stats['empty'] += 1
#                 continue
#
#             if GPSFIX == 0:
#                 stats['badfix'] += 1
#                 if skip:
#                     print("Warning: Skipping point due GPSFIX==0")
#                     stats['badfixskip'] += 1
#                     continue
#
#             data = [float(x) / float(y) for x, y in zip(d.data._asdict().values(), list(SCAL))]
#             gpsdata = fourCC.KARMAGPSData._make(data)
#
#             if SYST.seconds != 0 and SYST.miliseconds != 0:
#                 p = gpshelper.GPSPoint(gpsdata.lat, gpsdata.lon, gpsdata.alt, datetime.fromtimestamp(SYST.miliseconds),
#                                        gpsdata.speed)
#                 points.append(p)
#                 stats['ok'] += 1
#
#     print("-- stats -----------------")
#     total_points = 0
#     for i in stats.keys():
#         total_points += stats[i]
#     print("- Ok:              %5d" % stats['ok'])
#     print("- GPSFIX=0 (bad):  %5d (skipped: %d)" % (stats['badfix'], stats['badfixskip']))
#     print("- Empty (No data): %5d" % stats['empty'])
#     print("Total points:      %5d" % total_points)
#     print("--------------------------")
#     return (points)


if __name__ == "__main__":

    args = parseArgs()

    _config = config.setup_environment(args)
    parser = gpmf.Parser(_config)

    if not args.binary:
        data = parser.readFromMP4()
    else:
        data = parser.readFromBinary()

    # //////////////
    # You can enter a custom filename here instead of 'None'. Otherwise, just drag and drop a file on this script
    filename = args.file
    # //////////////

    if filename is None:
        fNames = []
        try:
            counter = 1
            while True:
                try:
                    fNames.append(sys.argv[counter])
                except IndexError:
                    if counter > 1:  # at least one file found
                        break
                    else:
                        _ = sys.argv[counter]  # no file found => create IndexError
                counter += 1
        except IndexError:
            # Print error and exit after next userinput
            print(
                ("\nERROR: No file selected. Please drag the chosen file onto this script to parse for highlights.\n" +
                 "\tOr change \"filename = None\" with the filename in the sourcecode."))
            os.system("pause")
            exit()
    else:
        fNames = [filename]
    str2insert = ""

    for fName in fNames:
        str2insert += fName + "\n"
        highlights = highlights.examine_mp4(fName)  # examine each file
        for highlight in highlights:
            str2insert += ''.join(map(str, highlight)) + '\n'

    # Create document
    stripPath, _ = os.path.splitext(fNames[0])
    outpFold, newFName = os.path.split(stripPath)

    newPath = os.path.join(outpFold, 'GP-Highlights_' + newFName + '.txt')

    with open(newPath, "w") as f:
        f.write(str2insert)

    print("Saved Highlights under: \"" + newPath + "\"")

    points = gopro2gpx.BuildGPSPoints(data, skip=args.skip)

    if len(points) == 0:
        print("Can't create file. No GPS info in %s. Exiting" % args.file)
        sys.exit(0)

    kml = gpshelper.generate_KML(points, highlights)
    with open("%s.kml" % args.outputfile, "w+") as fd:
        fd.write(kml)

    gpx = gpshelper.generate_GPX(points, highlights, trk_name="gopro7-track")
    with open("%s.gpx" % args.outputfile, "w+") as fd:
        fd.write(gpx)


