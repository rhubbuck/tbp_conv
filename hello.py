'''
README: This file must be executed from 10.10.1.3 from the Windows Powershell being run as administrator.
Save, copy, and paste onto the remote 10.10.1.3 desktop.
If you encounter connection issues with SQLServer, the password as of 4/23/24 is KP.....rys.
'''
import itertools
import csv
import pymssql, os, datetime, sys, json

print("Ready...")

conn = pymssql.connect(
    host=r'10.10.1.3',
    user=r'tbp\bdickson',
    password=sys.argv[1],
    database='Convention',
    as_dict=True
)

print("Connected to database...")

SQL_QUERY_ALL = """
SELECT 
[RoomNumber]
	  ,[Email]
      ,[LastName]
      ,[FirstName]
      ,[ConvRole]
      ,[Age]
      ,[Chap]
      ,[Dis]
      ,[Stat]
      ,[C/I]
      ,[R/S]
      ,[K/D]
      ,[M/F]
      ,[S/N]
      ,[Occupancy]
      ,[Roommate]
      ,[GeneralComments]
      ,[Gender]
      ,[DietaryNeeds]
      ,[F/D]
      ,[Arrive]
      ,[Depart]
      ,[None]
      ,[RN]
      ,[TP]
      ,[Hotel]
      ,[Confirm]
      ,[RC]
      ,[RoomMFC]
	  ,[RoomSerialNumb]
      ,[RoomStatus]
      ,[Code]
FROM Conv_RoomingData
WHERE Roommate IS NOT NULL
ORDER BY Dis, Age, Arrive
"""
SQL_QUERY_NO_OCCUPANCY = """
SELECT * FROM Conv_RoomingData
WHERE Occupancy = ''
ORDER BY Age, Arrive
"""

cursor = conn.cursor()

cursor.execute(SQL_QUERY_ALL)
records = cursor.fetchall()

cursor.execute(SQL_QUERY_NO_OCCUPANCY)
others = cursor.fetchall()

singles = []
doubles = []
doubleRooms = []
rn = 1
memberSet = {"filler"} # member set will keep track of all registered members to make sure all are assigned

# Iterate through each record and add a new field for fullName
for r in records:
    x = r['FirstName'] + r['LastName']
    y = ''.join(filter(str.isalpha, x))
    z = y.lower()
    r['fullName'] = z
    memberSet.add(z)
    if r['Occupancy'] == 'Single': # filter out single rooms and remove them from the memberSet
        singles.append(r)
        memberSet.remove(r['fullName'])
    if r['Occupancy'] == 'Double': # make the roommate field uniform for people selecting a double room
        roommate = r['Roommate']
        roommateStripped = ''.join(filter(str.isalpha, roommate))
        r['roommateUniform'] = roommateStripped.lower()
        doubleRooms.append(r)

memberSet.remove("filler")

for s in singles:
    s['RoomNumber'] = rn;
    rn += 1

perfectMatch = []
noPair = []
# iterate through members requesting double rooms and check for exact matches (where each member requested to room with eachother)
for i, d in enumerate(doubleRooms):
    match = False
    for l, j in enumerate(doubleRooms[:]):
        if d['fullName'] == j['roommateUniform'] and d['roommateUniform'] == j['fullName'] and d['fullName'] :
            match = True
            memberSet.remove(d['fullName'])  
            if j['fullName'] in memberSet:
                d['roomNumber'] = rn
                j['roomNumber'] = rn
                print("match: ", i,  d['fullName'], " - ", i,  d['roommateUniform'], rn)
                perfectMatch.append(d)
                perfectMatch.append(j)
                doubles.append(d)
                doubles.append(j)
                rn += 1
            
    if match == False: # add members without exact matches to pass along for next check
        noPair.append(d)


nonbinary = []
finalToPair = []
partialMatch = []

# iterate through remaining members seeking double rooms. Filter out non-binary members for human review and then check for partial matches (one member requested the other)
for i, d in enumerate(noPair):
    match = False
    if d['Gender'] == 'Non-Binary':
        nonbinary.append(d)
        memberSet.remove(d['fullName'])
        match = True
    for l, j in enumerate(noPair[:]): # check if either member requested eachother
        if d['fullName'] == j['roommateUniform'] or j['fullName'] == d['roommateUniform']:
            match = True
            if d['fullName'] in memberSet and j['fullName'] in memberSet: # if neither member has been assigned yet, assign them to the set
                d['roomNumber'] = rn
                j['roomNumber'] = rn
                print(d['fullName'], " --------- " ,j['fullName'], rn)
                partialMatch.append(d)
                partialMatch.append(j)
                doubles.append(d)
                doubles.append(j)
                memberSet.remove(d['fullName'])
                memberSet.remove(j['fullName'])
                rn += 1
                
            elif d['fullName'] in memberSet and j['fullName'] not in memberSet: # if a member not assigned requested a member already assigned, pass them along
                match = False
    if match == False:
        finalToPair.append(d)
        

print(len(finalToPair), " still left to pair")

# Final removal of members free to pair with anyone from member set to validate that all members have been assigned
for i in finalToPair:
    memberSet.remove(i['fullName'])

humanReview = []
finalPair = []

# Filter out members with general comments and push them to human review
for f in finalToPair:
    if f['GeneralComments'] != '':
        humanReview.append(f)
    else:
        finalPair.append(f)

print(len(finalPair), " can be paired")

# add non-binary members to list needing human review
for n in nonbinary:
    humanReview.append(n)

# add 'others' to list needing human review
for o in others:
    humanReview.append(o)

male = []
female = []
maleOff = []
femaleOff = []
# Filter through remaining members and seperate members assigned a district from HQ/nat. off.
# This keeps districts together for the most part, and the list is already sorted by age. 
for i, r in enumerate(finalPair):
    if r['Dis'] == None or r['Dis'] == 0:
        if r['Gender'] == 'Male':
            maleOff.append(r)
        else:
            femaleOff.append(r)
    elif r['Dis'] > 0:
        if r['Gender'] == 'Male':
            male.append(r)
        else:
            female.append(r)
# Add non-district members back into list before pairing up
for m in maleOff:
    male.append(m)
for f in femaleOff:
    female.append(f)

# Go through male list and pair up roommates in consecutive order. If there is a leftover, a single room will be assigned
# m_pairs = [(i, j) if j is not None else (i,) for i, j in itertools.zip_longest(male[::2], male[1::2])]
# print(m_pairs)
print(len(male), " males")

# Go through male list and pair up roommates in consecutive order. If there is a leftover, a single room will be assigned
# f_pairs = [(i, j) if j is not None else (i,) for i, j in itertools.zip_longest(female[::2], female[1::2])]
# print(f_pairs)

print(len(female), "females to pair")
print("+++++++++++++++++++++++++++++++++++++++++++++")
print(1 % 2)
for i, m in enumerate(male):
    m['roomNumber'] = rn
    # print(m['roomNumber'], m['fullName'])
    doubles.append(m)
    if i % 2 != 0:
        rn += 1
rn += 1
for i, m in enumerate(female):
    m['roomNumber'] = rn
    # print(m['roomNumber'], m['fullName'])
    doubles.append(m)
    if i % 2 != 0:
        rn += 1

print(len(records), " records in All Records (not including 5 from others)")
print(len(others), " others")
print(len(singles), " Single rooms")
print(len(perfectMatch), " perfect matches")
print(len(partialMatch), " partial matches")
print(len(humanReview), " need human review - Includes Non-B, which is", len(nonbinary))
print(len(female) + len(male), "  -Total leftover males and females paired up")
print(len(memberSet), " left in member set")
print(len(doubles))
try:
    with open('single_rooms.csv', mode='w') as csvfile:
        fieldnames = singles[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in singles:
            writer.writerow(row)    
    with open('needs_review.csv', mode='w') as csvfile:
        fieldnames = humanReview[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in humanReview:
            writer.writerow(row)    
    with open('double_rooms.csv', mode='w') as csvfile:
        fieldnames = doubles[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in doubles:
            writer.writerow(row)    

except IOError:
    print("I/O error")