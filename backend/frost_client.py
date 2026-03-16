import requests
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

endpoint = os.getenv('FROST_API_ENDPOINT')
station_id = 'SN50540' # ID for Bergen - Florida
element = 'sum(precipitation_amount P1D)' # Døgnnedbør

end_date = datetime.now()
start_date = end_date - timedelta(days=14)
time_period = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"


params = {
    'sources': station_id,
    'elements': element,
    'referencetime': time_period,
}


r = requests.get(endpoint, params, auth=(client_id, client_secret))
json_data = r.json()


if r.status_code == 200:
    data = json_data['data']
    print(f"Hentet data for {station_id}:")
    for row in data:
        tid = row['referenceTime']
        verdi = row['observations'][0]['value']
        enhet = row['observations'][0]['unit']
        print(f"Dato: {tid[:10]} | Nedbør: {verdi} {enhet}")
else:
    print(f"Feil oppsto: {r.status_code}")
    print(json_data['error'])