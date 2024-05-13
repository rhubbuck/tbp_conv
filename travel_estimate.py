print('test')
import itertools
import pymssql, os, datetime, sys, json
import csv

'''
Records have been sources from https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FHK&QO_fu146_anzr=b4vtv0%20n0q%20Qr56v0n6v10%20f748rB
This data can be updated every quarter. Only include ORIGIN_AIRPORT_ID, ORIGIN, DEST_AIRPORT_ID, DEST, & MARKET_FARE in the download.
'''

flights = []
uniqueFlights = {}

# Open the flight_data csv and read in data
with open("flight_data.csv", 'r') as file:
    csvreader = csv.reader(file)
    header = next(csvreader)
    for row in csvreader:
        if float(row[4]) > 75.0: # Only keep the rows with prices over $75 to exclude outliers or records only contianing taxes or fees
            flights.append({'orig_id': row[0], 'origin': row[1], 
                        'dest_id': row[2], 'destination': row[3], 
                        'unique_id': row[1] + "-" + row[3], 
                        'fare': float(row[4]), 'average': float(row[4])})
# print(header)
# print(flights[0])
# print(flights[1])

for f in flights:
    if f['unique_id'] not in uniqueFlights: # if this is a new unique flight path
        uniqueFlights[f['unique_id']] = f
        count = 1
        total = f['fare']
    else:
        count += 1
        total += f['fare']
        uniqueFlights[f['unique_id']]['average'] = round(total / count, 2)

print(uniqueFlights['TYS-ATL'])