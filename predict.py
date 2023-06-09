# imports
import datetime
import schedule
import time

# print time function
def run():
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S.%f')
    print(formatted_time[:-3])    

# schedules
schedule.every().minute.at(":00").do(run)
# schedule.every().hour.at(":42").do(run)

# keep running  
while True:
    schedule.run_pending()
    time.sleep(1)