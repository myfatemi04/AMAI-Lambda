import pandas as pd
import pymongo
import datetime
import os
import sys

client = pymongo.MongoClient(os.environ['MONGO_URI'])
db = client['test']
interactions = db['interactions']
tokens = db['tokens']

# Assume EST
# Format: MM/DD/YYYY or MM/DD/YYYY HH:MM [AM|PM]
# Return: datetime.datetime object
def parse_datetime(date_str: str):
    if ' ' in date_str:
        date_str, time_str, ampm = date_str.split(' ')
        hour, minute = time_str.split(':')
        hour = int(hour)
        if hour == 12:
            hour = 0
        minute = int(minute)
        if ampm == 'PM':
            hour += 12
        return datetime.datetime.strptime(date_str, '%m/%d/%Y') + datetime.timedelta(hours=hour, minutes=minute)
    else:
        return datetime.datetime.strptime(date_str, '%m/%d/%Y')

def upsert_tokens(df):
    for i, row in df.iterrows():
        start_date = parse_datetime(row['Start Date'])
        name = row['Name']
        token = row['Token']
        # print(start_date, parse_datetime(start_date))
        tokens.update_one({
            "token": token
        }, {
            "$set": {
                "start_date": start_date,
                "name": name,
                "token": token
            }
        }, upsert=True)

def print_tokens():
    for token in tokens.find():
        print(token)

def manual_upsert(token: str, name: str):
    tokens.update_one({
        "token": token
    }, {
        "$set": {
            "name": name,
            "token": token
        }
    }, upsert=True)

def help():
    print("Usage: python3 log.py [file <filename>|upsert <token> <name>|list|set-method <token> <method>]")

def set_method(token: str, method: str):
    tokens.update_one({
        "token": token
    }, {
        "$set": {
            "method": method,
            "token": token
        }
    }, upsert=True)

if __name__ == '__main__':
    if len(sys.argv) == 0:
        help()

    if sys.argv[1] == 'file':
        if len(sys.argv) != 3:
            help()
        df = pd.read_csv(sys.argv[2], delimiter='\t')
        upsert_tokens(df)
    elif sys.argv[1] == 'upsert':
        print(sys.argv)
        if len(sys.argv) != 4:
            help()
        manual_upsert(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'list':
        print_tokens()
    elif sys.argv[1] == 'set-method':
        if len(sys.argv) != 4:
            help()
        set_method(sys.argv[2], sys.argv[3])
    else:
        help()
