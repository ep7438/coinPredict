# imports
import datetime
import schedule                             
import time
from coinbase.wallet.client import Client   
import cbpro                                
import coinmarketcapapi
import pandas as pd                         
import os
import csv
import numpy as np

start_time = time.time() # start timer

# connect to cb, cmc
# api.dat stores cb api key with wallet:accounts:read permission
# on first two lines and cmc api key on third
# required to execute script 
handshake = open('api.dat', 'r').read().splitlines()
client = Client(handshake[0], handshake[1])
cmc = coinmarketcapapi.CoinMarketCapAPI(handshake[2])

# for cb trading data
cbp = cbpro.PublicClient() 

# pandas toggle all data
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 50)
# pd.set_option('display.width', None) # None errors out in python 2.7.18
# pd.set_option('display.max_colwidth', None)


#######################
###### BEGIN RUN ######
#######################

def run():
    
    # remove temp files from previous runs
    if (os.path.exists("tmp-cb_CurrentPrice.csv")):
        os.remove("tmp-cb_CurrentPrice.csv")
    if (os.path.exists("tmp-cmc_LatestQuotes.csv")):
        os.remove("tmp-cmc_LatestQuotes.csv")
    if (os.path.exists("tmp-the_Wire.csv")):
        os.remove("tmp-the_Wire.csv")
    if (os.path.exists("tmp-cb_TradeData.txt")):
        os.remove("tmp-cb_TradeData.txt")

    # create temp files
    cbfile = open("tmp-cb_CurrentPrice.csv", "w") # name,price
    wirefile = open("tmp-the_Wire.csv", "w") # name,%change_1hr
    tradefile = open("tmp-cb_TradeData.txt", "w") # dataframe outputs

    # read from file to create dictionary { name : cmcid }
    with open("inp-cmc_id.csv", mode="r") as infile:
        reader = csv.reader(infile)
        mydict = dict((rows[0], rows[1]) for rows in reader) # cmcid : name
    mydict_swap = {v: k for k, v in mydict.items()}

    next = None # variables
    names = []
    numbers = []
    cmcOrder = []

    # runs until the next_uri parameter is none
    while True:
        accounts = client.get_accounts(starting_after = next)
        next = accounts.pagination.next_starting_after

        # iterate each wallet name
        for wallet in accounts.data:        
            
            # change crypto name to cbpro historic rates product ticker name
            nameStr = wallet['name']
            nameStr = nameStr.replace(" Wallet", "")
            nameStr = nameStr + "-USD" 

            # if program errors out, the cause is likely here
            # filter out staked, delisted, stable, etc.               
            exclude = ["Staked SOL-USD","Staked ATOM-USD","Staked XTZ-USD","Staked ADA-USD","ETH2-USD","REPV2-USD","USDC-USD","Cash (USD)-USD","GNT-USD","RGT-USD","TRIBE-USD","UST-USD","WLUNA-USD","MUSD-USD","UPI-USD","RGT-USD","XRP-USD","USDT-USD","DAI-USD","BUSD-USD","GUSD-USD","RLY-USD","KEEP-USD","NU-USD","MIR-USD","OMG-USD","REP-USD","LOOM-USD","YFII-USD","GALA-USD","STG-USD","PAX-USD"]
            
            if nameStr not in exclude:    
                
                names.append(nameStr) # add to list
                nameStr = nameStr.replace("-USD","") # remove -USD
                numbers.append(mydict.get(nameStr)) # save to numbers ordered list    
                
                # means info must be added to inp-cmc_id.csv
                # print(nameStr) # debug if new crypto
                if nameStr not in mydict:
                    print("New Crypto")
                    wirefile.write("New Crypto\n")

        # escape loop            
        if accounts.pagination.next_uri == None:
            break            

    # OUTSIDE loop activity starts here
    cmcOrder = [] # cmc variables 
    data = []
    num = ""
    dataStr = ""
    temp = ""

    # make string list all cmc ids
    idBuild = ""
    for i in numbers:
        idBuild += str(i)
        idBuild += ","
    idBuild = idBuild[:-1] # remove last ',' char
    data_quote = cmc.cryptocurrency_quotes_latest(id=idBuild, convert='USD')
    df = pd.DataFrame.from_records(data_quote.data)
    df.to_csv("tmp-cmc_LatestQuotes.csv") # OUTPUT to file
    
    with open("tmp-cmc_LatestQuotes.csv", mode='r') as fp: # read from cmc file
        for i, line in enumerate(fp):
            line = line[:-1] # remove newline
            
            if i == 0: # first line, determine cmcid order
                for char in reversed(line): # reverse iterate
                    if char == ",":
                        num = num.replace(",", "")
                        cmcOrder.insert(0, num[::-1]) # insert front, num reverse order
                        num = "" # reset num
                    num += char
                
                # for debug
                # wirefile.write(str((len(cmcOrder))) + "\n") # OUTPUT
                # wirefile.write(str(cmcOrder) + "\n")

            elif i == 13: # 14th line, save bulk data
                start = len(line) - 4 # ignore the first }}
                
                for i in range(start, 0, -1): # splice rows
                    if line[i] == "}" and line[i-1] == "}": 
                        data.insert(0, dataStr[::-1]) 
                        dataStr = ""
                    dataStr += line[i]
                data.insert(0, dataStr[::-1]) # don't forget first value, added last
              
                # for debug
                # wirefile.write("\n")
                # wirefile.write(str((len(data))) + "\n") 
                # wirefile.write(str(data[0]) + "\n")  # print first and last examples            
                # wirefile.write(str(data[len(data) - 1]) + "\n")

    # splice column value
    matrix = [[]]
    for index, lineStr in enumerate(data):
        count = 0
        for c in lineStr:
            if c == "'":
                count += 1

            if count == 30: # percent_change_1hr 
                if c.isdigit() or c == "-" or c == ".":
                    temp += c 
        
        # OUTPUT
        builder1 = mydict_swap.get(cmcOrder[index])
        builder2 = temp
        matrix.append((builder1,builder2))
        temp = "" # reset

    # determine top 10 1hr%change performers
    df = pd.DataFrame(matrix, columns =['name','percent_change_1hr'])
    df = df.sort_values('percent_change_1hr', ascending=False)
    df = df[:-1] # drop last row
    
    # OUTPUT
    print(df)
    result = df.head(10)
    print(result)
    
    # add names to top10 list
    strBuild = ""
    top10 = []
    orderedPrice = [] 
    for i in range(0,10):
        strBuild = str(result['name'].iloc[i])
        top10.append(strBuild +"-USD") 
        orderedPrice.append(float(result['percent_change_1hr'].iloc[-1]))
    print(orderedPrice)

    # machine learning happens here
    wirefile.write("name,price,volatility\n")
    print(top10) # this will go to cb historical data
    for i, line in enumerate(top10):
        # correct number of tabs applied if want to run once for every crypto
        # historic rates 
        # 86400 = 1 day, 3600 = 1 hour, 900 = 15 min, 300 = 5 min, 60 = 1 min
        # returns 300 rows
        # 86400 = 300 days, 3600 = 12.5 days, 900 = 3.125 days, 300 = 1.04 days, 60 = 5 hours

        # get cb data
        raw = cbp.get_product_historic_rates(product_id = line, granularity = 60)
        
        # change line
        line = line.replace("-USD","")

        # put in chronological order
        raw.reverse()

        # pause so cbpro calls don't error out
        # sometimes required on high performance environments
        # time.sleep(0.10)
        
        # send to pandas dataframe
        dataFrame = pd.DataFrame(raw, columns = ["Date", "Open", "High", "Low", "Close", "Volume"]) 

        # convert date from unix timestamp to readable format
        dataFrame['Date'] = pd.to_datetime(dataFrame['Date'].astype(str), unit='s')

        # save most recent price
        current = dataFrame["Close"].iloc[-1]
        current = float(current)

        # insert log return column to dataFrame, needed for volatility
        dataFrame.insert(6, "Log Return", np.log(dataFrame['Close']/dataFrame['Close'].shift()))
        
        # calculate volatility
        volatility = (dataFrame['Log Return'].std()*252**.5)*100
        volatility = round(volatility, 2)
        print(volatility)

        # output last values to the wire
        wirefile.write(line + "," + str(current) + "," + str(volatility) + "\n")

        # OUTPUT
        tradefile.write("\n" + line + "\n")              # tmp-cb_TradeData.txt
        tradefile.write(str(dataFrame) + "\n")
        tradefile.write("\n\n")
        # cbfile.write(line + "," + str(current) + "\n")   # tmp-cb_CurrentPrice.csv
        #   this only outputs the top 10    

    # end files
    cbfile.close() 
    wirefile.close()
    tradefile.close() 

#########################
######   END RUN   ######
#########################


#######################
### BEGIN DATAFRAME ###
#######################

                # correct number of tabs applied if want to run once for every crypto
                # historic rates 
                # 86400 = 1 day, 3600 = 1 hour, 900 = 15 min, 300 = 5 min, 60 = 1 min
                # returns 300 rows
                # 86400 = 300 days, 3600 = 12.5 days, 900 = 3.125 days, 300 = 1.04 days, 60 = 5 hours

                # get cb data
                # raw = cbp.get_product_historic_rates(product_id = nameStr, granularity = 60)
                
                # put in chronological order
                # raw.reverse()

                # pause so cbpro calls don't error out
                # sometimes required on high performance environments
                # time.sleep(0.10)
                
                # send to pandas dataframe
                # df = pd.DataFrame(raw, columns = ["Date", "Open", "High", "Low", "Close", "Volume"]) 

                # convert date from unix timestamp to readable format
                # df['Date'] = pd.to_datetime(df['Date'].astype(str), unit='s')

                # save most recent price
                # current = df["Close"].iloc[-1]
                # current = float(current)

                # tradefile.write("\n" + nameStr + "\n")              # tmp-cb_TradeData.txt
                # tradefile.write(nameStr + "\n")# str(df))
                # tradefile.write("\n\n")

#######################
###  END DATAFRAME  ###
#######################


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
# schedule.every().hour.at(":00").do(run) # every hour at 00 minutes

# void main

# keep running 
# while True:
    # schedule.run_pending()
    # time.sleep(1) # pause one second

######################
###  END SCHEDULE  ###
######################


###################
### BEGIN OTHER ###
###################

def other():
    print("other()")

###################
###  END OTHER  ###
###################


#################
### VOID MAIN ###
#################

# run once
run()
# other()

# OUTPUT console rutime
end_time = time.time()
print("--- %s seconds ---" % (end_time - start_time))
print("--- %s minutes ---" % ((end_time - start_time) / 60))