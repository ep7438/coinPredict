# imports
import datetime
import schedule                             
import time
from coinbase.wallet.client import Client   
import cbpro                                
import coinmarketcapapi
import pandas as pd                         
import os

# start timer
start_time = time.time()

# connect to cb, cmc
# api.dat stores cb api key with wallet:accounts:read permission
# on first two lines and cmc api key on third 
handshake = open('api.dat', 'r').read().splitlines()
client = Client(handshake[0], handshake[1])
cmc = coinmarketcapapi.CoinMarketCapAPI(handshake[2])

# for cb trading data
cbp = cbpro.PublicClient() 

# truncate rows
# df has max 300 rows 
pd.set_option('display.max_rows', 500)


#####################
### BEGIN CLEANUP ###
#####################

# remove temp files from previous runs

def cleanup():
    if (os.path.exists("tmp-cb_CurrentPrice.csv")):
        os.remove("tmp-cb_CurrentPrice.csv")

    if (os.path.exists("tmp-cmc_LatestQuotes.csv")):
        os.remove("tmp-cmc_LatestQuotes.csv")

    if (os.path.exists("tmp-the_Wire.txt")):
        os.remove("tmp-the_Wire.txt")

    if (os.path.exists("tmp-cb_TradeData.txt")):
        os.remove("tmp-cb_TradeData.txt")

#####################
###  END CLEANUP  ###
#####################


################################
###### BEGIN NAMES&PRICES ######
################################

# connect to coinbase and cmc 
# make names and price dataframe

def namesPrices():

    # OUTPUT files
    cbfile = open("tmp-cb_CurrentPrice.csv", "w") # name,price
    wirefile = open("tmp-the_Wire.txt", "w") # what's happeninng
    wirefile.write("Get trade data from coinbase -> \n")
    tradefile = open("tmp-cb_TradeData.txt", "w") # dataframe

    # pull information from cmc
    # snapshot of global trading data
    # need ordered list of all (233) cmc id numbers  
    # id="1,2" are bitcoin and litecoin for example
    data_quote = cmc.cryptocurrency_quotes_latest(id="1,2", convert='USD')
    df = pd.DataFrame.from_records(data_quote.data)
    df.to_csv("tmp-cmc_LatestQuotes.csv") # OUTPUT

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
            # if program errors out, the cause is likely here
            # example scenario -> cb adds a new staked wallet, 
            #                     no price data to pull,
            #                     error at raw.reverse()
            #                     print(tempStr) to debug               
            if tempStr not in "Staked SOL-USD" and tempStr not in "Staked ATOM-USD" and tempStr not in "Staked XTZ-USD" and tempStr not in "Staked ADA-USD" and tempStr not in "ETH2-USD" and tempStr not in "REPV2-USD" and tempStr not in "USDC-USD" and tempStr not in "Cash (USD)-USD" and tempStr not in "GNT-USD" and tempStr not in "RGT-USD" and tempStr not in "TRIBE-USD" and tempStr not in "UST-USD" and tempStr not in "WLUNA-USD" and tempStr not in "MUSD-USD" and tempStr not in "UPI-USD" and tempStr not in "RGT-USD" and tempStr not in "XRP-USD" and tempStr not in "USDT-USD" and tempStr not in "DAI-USD" and tempStr not in "BUSD-USD" and tempStr not in "GUSD-USD" and tempStr not in "RLY-USD" and tempStr not in "KEEP-USD" and tempStr not in "NU-USD" and tempStr not in "MIR-USD" and tempStr not in "OMG-USD" and tempStr not in "REP-USD" and tempStr not in "LOOM-USD" and tempStr not in "YFII-USD" and tempStr not in "GALA-USD" and tempStr not in "STG-USD":
                
                names.append(tempStr) # add to list

                # pull historic rates for crypto: 86400 = 1 day, 3600 = 1 hour, 900 = 15 min, 300 = 5 min, 60 = 1 min
                # get historic rates function returns 300 rows
                # 86400 = 300 days, 3600 = 12.5 days, 900 = 3.125 days, 300 = 1.04 days, 60 = 5 hours
                # this program focuses on short term data

                # snapshot of local trading data
                # now minus 5 hours -> from cb perspective
                # date, open, high, low, close, volume
                raw = cbp.get_product_historic_rates(product_id = tempStr, granularity = 60)
                
                # put in chronological order
                raw.reverse()

                # pause so cbpro calls don't error out
                # sometimes required on high performance environments
                # time.sleep(0.10)
                
                # send to pandas dataframe
                df = pd.DataFrame(raw, columns = ["Date", "Open", "High", "Low", "Close", "Volume"]) 

                # convert date to readable format
                df['Date'] = pd.to_datetime(df['Date'].astype(str), unit='s')

                # last price
                current = df["Close"].iloc[-1]
                current = float(current)

                # remove -USD
                tempStr = tempStr.replace("-USD","")
                
                # OUTPUT
                wirefile.write("    " + tempStr + "\n")             # tmp-the_Wire.txt         
                cbfile.write(tempStr + "," + str(current) + "\n")   # tmp-cb_CurrentPrice.csv
                tradefile.write("\n" + tempStr + "\n")              # tmp-cb_TradeData.txt
                tradefile.write(str(df))
                tradefile.write("\n\n")
        
        # escape loop            
        if accounts.pagination.next_uri == None:
            break            
    
    # end files
    cbfile.close() 
    wirefile.close()
    tradefile.close() 

################################
######  END NAMES&PRICES  ######
################################


######################
### BEGIN SCHEDULE ###
######################

# this framework allows program to keep running
# with scheduled function calls

# def run():
    # print current time
    # current_time = datetime.datetime.now()
    # formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S.%f')
    # print(formatted_time[:-3])     

# set schedule
# schedule.every().minute.at(":00").do(run) # every minute at 00 seconds
# schedule.every().hour.at(":42").do(run) # every hour at 42 minutes

# void main

# keep running 
# while True:
    # schedule.run_pending()
    # time.sleep(1) # pause one second

######################
###  END SCHEDULE  ###
######################


#################
### VOID MAIN ###
#################

cleanup()
namesPrices()

# OUTPUT console rutime
# avg 1.6 min so far
# lubuntu linux on toshiba satellite l755d
end_time = time.time()
print("--- %s seconds ---" % (end_time - start_time))
print("--- %s minutes ---" % ((end_time - start_time) / 60))