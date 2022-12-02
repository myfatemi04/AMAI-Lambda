import pandas as pd
import pymongo
import datetime
import os

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

def upsert_tokens():
    df = pd.read_csv("tokens.csv", delimiter='\t')
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

if __name__ == '__main__':
    upsert_tokens()
    print_tokens()
