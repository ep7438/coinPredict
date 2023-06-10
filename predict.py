# imports
import datetime
import schedule
import time
from coinbase.wallet.client import Client
import cbpro
import pandas as pd

# connect to coinbase
handshake = open('api.dat', 'r').read().splitlines()
client = Client(handshake[0], handshake[1])

# for price data
cbp = cbpro.PublicClient() 

# display dataframe row truncate 
pd.set_option('display.max_rows', 20)


################################
###### BEGIN NAMES&PRICES ######
################################

# connect to coinbase api and generate list of crypto names
# only part of the program which accesses the coinbase api key

def namesPrices():
    # counter var
    c = 1
    
    # output to file
    outfile = open("output.txt", "w")
    
    # initialize next wallet id and declare empty list
    next = None
    names = []

    # coinbase loop
    # runs until the next_uri parameter is none
    while True:
        accounts = client.get_accounts(starting_after = next)
        next = accounts.pagination.next_starting_after
        
        # iterate each wallet name
        for wallet in accounts.data:        
            
            # change crypto name to cbpro historic rates product ticker name
            tempStr = wallet['name']
            tempStr = tempStr.replace(" Wallet", "")
            tempStr = tempStr + "-USD" 

            # filter out staked, delisted, stable, etc.            
            if tempStr not in "Staked SOL-USD" and tempStr not in "Staked ATOM-USD" and tempStr not in "Staked XTZ-USD" and tempStr not in "Staked ADA-USD" and tempStr not in "ETH2-USD" and tempStr not in "REPV2-USD" and tempStr not in "USDC-USD" and tempStr not in "Cash (USD)-USD" and tempStr not in "GNT-USD" and tempStr not in "RGT-USD" and tempStr not in "TRIBE-USD" and tempStr not in "UST-USD" and tempStr not in "WLUNA-USD" and tempStr not in "MUSD-USD" and tempStr not in "UPI-USD" and tempStr not in "RGT-USD" and tempStr not in "XRP-USD" and tempStr not in "USDT-USD" and tempStr not in "DAI-USD" and tempStr not in "BUSD-USD" and tempStr not in "GUSD-USD" and tempStr not in "RLY-USD" and tempStr not in "KEEP-USD" and tempStr not in "NU-USD" and tempStr not in "MIR-USD" and tempStr not in "OMG-USD" and tempStr not in "REP-USD" and tempStr not in "LOOM-USD" and tempStr not in "YFII-USD" and tempStr not in "GALA-USD" and tempStr not in "STG-USD":
                
                names.append(tempStr) # add to list

                # pull historic rates for crypto: 86400 = 1 day, 3600 = 1 hour, 900 = 15 min, 300 = 5 min, 60 = 1 min
                # get historic rates function returns 300 data points
                # 86400 = 300 days, 3600 = 12.5 days, 900 = 3.125 days, 300 = 1.04 days, 60 = 5 hours
                # this program focuses on short term data

                raw = cbp.get_product_historic_rates(product_id = tempStr, granularity = 60)
                
                # put in chronological order
                raw.reverse()

                # short pause so cbpro calls don't error out
                # time.sleep(0.10)
                
                # send to pandas dataframe
                df = pd.DataFrame(raw, columns = [ "Date", "Open", "High", "Low", "Close", "Volume" ]) 

                # convert date to readable format
                df['Date'] = pd.to_datetime(df['Date'].astype(str), unit='s')

                # OUTPUT
                outfile.write("\n\n")
                outfile.write(str(c))
                outfile.write(". ")
                outfile.write(tempStr)
                outfile.write("\n")
                outfile.write(str(df))
                outfile.write("\n")

                # increment counter
                c += 1

        # escape loop            
        if accounts.pagination.next_uri == None:
            break            
    
    outfile.close() # close file


################################
######  END NAMES&PRICES  ######
################################


######################
### BEGIN SCHEDULE ###
######################

# def run():
    # print current time
    # current_time = datetime.datetime.now()
    # formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S.%f')
    # print(formatted_time[:-3])     

# set schedule
# schedule.every().minute.at(":00").do(run) # every minute at 00 seconds
# schedule.every().hour.at(":42").do(run) # every hour at 42 minutes

# void main()
namesPrices()

# keep running 
# while True:
    # schedule.run_pending()
    # time.sleep(1) # pause one second

######################
###  END SCHEDULE  ###
######################