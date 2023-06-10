# imports
import datetime
import schedule
import time
from coinbase.wallet.client import Client
import cbpro

# connect to coinbase
handshake = open('api.dat', 'r').read().splitlines()
client = Client(handshake[0], handshake[1])

# for price data
# c = cbpro.PublicClient() 


##############################
### BEGIN GET CRYPTO NAMES ###
##############################

# connect to coinbase api and generate list of crypto names
# only part of the program which accesses the coinbase api key

def names():
    # initialize next wallet id and declare empty list
    next = None
    names = []

    # this loop will run until the next_uri parameter is none
    while True:
        accounts = client.get_accounts(starting_after = next)
        next = accounts.pagination.next_starting_after
        
        for wallet in accounts.data:
                
            # change crypto name to cbpro historic rates product ticker name
            tempStr = wallet['name']
            tempStr = tempStr.replace(" Wallet", "")
            tempStr = tempStr + "-USD"
            
            # filter out cryptos cbpro can't pull up, delisted, also stable coins

            # if tempStr not in "ETH2-USD" and tempStr not in "REPV2-USD" and 
            # tempStr not in "USDC-USD" and tempStr not in "XRP-USD" and tempStr 
            # not in "Cash (USD)-USD" and tempStr not in "GNT-USD" and tempStr not in 
            # "UST-USD" and tempStr not in "WLUNA-USD" and tempStr not in "MNDE-USD" and 
            # tempStr not in "USDT-USD" and tempStr not in "MSOL-USD" and tempStr not in 
            # "GUSD-USD" and tempStr not in "Staked ATOM-USD" and tempStr not in "Staked XTZ-USD" 
            # and tempStr not in "Staked ADA-USD" and tempStr not in "RGT-USD" and tempStr not in "NU-USD" 
            # and tempStr not in "TRIBE-USD" and tempStr not in "BUSD-USD" and tempStr not in "MUSD-USD" and tempStr 
            # not in "UPI-USD" and tempStr not in "STG-USD" and tempStr not in "Staked SOL-USD":
                
            # this is tabbed over 1 more when running if condition on 48-56
            # add to names list 
            names.append(tempStr)
            
            print(tempStr) # TESTING

        # escape loop            
        if accounts.pagination.next_uri == None:
            break            

##############################
###  END GET CRYPTO NAMES  ###
##############################


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
names()

# keep running 
# while True:
    # schedule.run_pending()
    # time.sleep(1) # pause one second

######################
###  END SCHEDULE  ###
######################