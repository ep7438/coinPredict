# imports
import datetime
# import schedule                             
import time
from coinbase.wallet.client import Client   
import cbpro                                
import coinmarketcapapi
import pandas as pd                         
import os
import csv
import numpy as np
import sklearn
from sklearn.tree import DecisionTreeRegressor # Import Decision Tree Classifier
from sklearn import tree
from sklearn.model_selection import train_test_split
from matplotlib import pyplot as plt

counter = 0 # num iterations
#print(MutableMapping)

# connect to cb, cmc
# api.dat stores cb api key with wallet:accounts:read permission
#   on first two lines and cmc api key on third
# required to execute script 
handshake = open('api.dat', 'r').read().splitlines()
client = Client(handshake[0], handshake[1])
cmc = coinmarketcapapi.CoinMarketCapAPI(handshake[2])
cbp = cbpro.PublicClient() # for granular trading data
pd.set_option('display.max_rows', 500) # pandas toggle all data
pd.set_option('display.max_columns', 50)    


#######################
###### BEGIN RUN ######
#######################

def run():
    start_time = time.time() # start timer

    global counter # necessary for schedule mode
    print("") # OUTPUT CONSOLE
    print(str(counter)) 

    # remove temp files from previous runs
    # perhaps keep them, ie separate folder & timestamp names 
    if (os.path.exists("tmp-cb_CurrentPrice.csv")):
        os.remove("tmp-cb_CurrentPrice.csv")
    if (os.path.exists("tmp-cmc_LatestQuotes.csv")):
        os.remove("tmp-cmc_LatestQuotes.csv")
    if (os.path.exists("tmp-the_Wire.csv")):
        os.remove("tmp-the_Wire.csv")
    if (os.path.exists("tmp-cmc_Data.csv")):
        os.remove("tmp-cmc_Data.csv")
    
    cmcfile = open("tmp-cmc_Data.csv", "w") # data from cmc
    wirefile = open("tmp-the_Wire.csv", "w") # data from cb
    wirefile.write("name,price,volatility,rsi\n") # columns
    outfile = open("output.csv", "a") # final output, append because it is not temporary

    # read from input file to create dictionary { name : cmcid }
    with open("inp-cmc_id.csv", mode="r") as infile:
        reader = csv.reader(infile)
        mydict = dict((rows[0], rows[1]) for rows in reader) 
    mydict_swap = {v: k for k, v in mydict.items()} # reverse -> { cmcid : name }

    next = None # variables
    names = []
    numbers = []
    cmcOrder = []
    cbDict = {}

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
                
                # means info must be added to inp-cmc_id.csv
                if nameStr.replace("-USD","") not in mydict:
                    print(nameStr)
                    print("New Crypto")
                
                names.append(nameStr) # add to list
                
                # 86400 = 1 day, 3600 = 1 hour, 900 = 15 min, 300 = 5 min, 60 = 1 min
                # returns 300 rows
                # 86400 = 300 days, 3600 = 12.5 days, 900 = 3.125 days, 300 = 1.04 days, 60 = 5 hours
                raw = cbp.get_product_historic_rates(product_id = nameStr, granularity = 60)
                
                nameStr = nameStr.replace("-USD","") # remove -USD
                numbers.append(mydict.get(nameStr)) # save to ordered list
                
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
                currentPrice = dataFrame["Close"].iloc[-1]

                ### BEGIN RSI ###
                close_delta = dataFrame['Close'].diff()

                # Make two series: one for lower closes and one for higher closes
                up = close_delta.clip(lower=0)
                down = -1 * close_delta.clip(upper=0)
                
                # Use simple moving average
                ma_up = up.rolling(window = 14).mean()
                ma_down = down.rolling(window = 14).mean()
                    
                rsi = ma_up / ma_down
                rsi = 100 - (100/(1 + rsi))
                ###  END RSI  ###

                # insert log return column to dataFrame, needed for volatility
                dataFrame.insert(6, "Log Return", np.log(dataFrame['Close']/dataFrame['Close'].shift()))
                dataFrame.insert(7, "RSI", rsi)

                # calculate
                volatilityOut = (dataFrame['Log Return'].std()*252**.5)*100
                volatilityOut = round(volatilityOut, 2)
                rsiOut = dataFrame['RSI'].iloc[-1] # pull last, most immediate rsi value
                rsiOut = round(rsiOut, 2)

                # output to the wire
                wirefile.write(nameStr + "," + str(currentPrice) + "," + str(volatilityOut) + "," + str(rsiOut) + "\n")
                cbDict[nameStr] = str(currentPrice) + "," + str(volatilityOut) + "," + str(rsiOut)

        # escape loop            
        if accounts.pagination.next_uri == None:
            break            

    ### BEGIN CMC ###
    cmcOrder = [] # order of cryptos  
    data = []       # for text parsing
    num = ""        #
    dataStr = ""    #
    temp = ""       #

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
                        cmcOrder.insert(0, num[::-1]) # insert front, LIFO
                        num = "" # reset val
                    num += char            
                
            elif i == 13: # 14th line, save bulk data
                start = len(line) - 4 # ignore the first }}
                
                for j in range(start, 0, -1): # splice rows
                    if line[j] == "}" and line[j-1] == "}": 
                        data.insert(0, dataStr[::-1]) # insert front
                        dataStr = "" # reset val
                    dataStr += line[j]
                data.insert(0, dataStr[::-1]) # don't forget first value, added last
              
    # splice column values
    matrix = [[]]
    cmcDict = {}
    for index, lineStr in enumerate(data):
        count = 0
        for c in lineStr:
            if c == "'":
                count += 1

            # DECIDE which values to utilize    

            if count == 30: # percent_change_1hr 
                if c.isdigit() or c == "-" or c == ".":
                    temp += c 
        
        # OUTPUT
        builder1 = mydict_swap.get(cmcOrder[index])
        builder2 = temp
        matrix.append((builder1,builder2))
        cmcfile.write(builder1 + "," + builder2 + "\n")
        cmcDict[builder1] = builder2
        temp = "" # reset

    # determine top 10 1hr%change performers
    df = pd.DataFrame(matrix, columns =['name','percent_change_1hr'])
    df = df.sort_values('percent_change_1hr', ascending=False)
    df = df[:-1] # drop last row
    
    # OUTPUT
    result = df.head(10)
    
    # add names to top10 list
    strBuild = ""
    top10 = []
    orderedPrice = [] 
    for i in range(0,10): # why 0-10?, this is weird but works, change iteration method
        strBuild = str(result['name'].iloc[i])
        top10.append(strBuild +"-USD") 
        orderedPrice.append(float(result['percent_change_1hr'].iloc[i]))
        outfile.write(strBuild + "," + str(cbDict.get(strBuild)) + "," + str(cmcDict.get(strBuild)) + "\n")
    print(orderedPrice) # OUTPUT 
    ### END CMC ###
 
    wirefile.close() # end files
    cmcfile.close()
    outfile.close()

    end_time = time.time() # OUTPUT console rutime
    print("--- %s seconds ---" % (end_time - start_time))
    print("--- %s minutes ---" % ((end_time - start_time) / 60))

#########################
######   END RUN   ######
#########################


######################
### BEGIN CLASSIFY ###
######################

def classify():

    #print('The scikit-learn version is {}.'.format(sklearn.__version__))

    with open("inp-cmc_id.csv", mode="r") as infile:
        reader = csv.reader(infile)
        mydict = dict((rows[0], rows[1]) for rows in reader) 
    mydict_swap = {v: k for k, v in mydict.items()} # reverse -> { cmcid : name }

    with open("output.csv") as csv_file:
        for row in csv.reader(csv_file, delimiter=','):
            print(row[0])

    df = pd.read_csv('output.csv')
    # print(df.columns)
    # print(df) 

    # store x and y variables
    # y is the class result, x for the other four
    x = pd.DataFrame(df.drop(['percent_change_1hr'],axis=1))
    y = pd.DataFrame(df['percent_change_1hr'])

    # train test split
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.22, random_state=22, shuffle=True)

    # do machine learning
    regr = DecisionTreeRegressor(max_depth=4, random_state=2222)
    model = regr.fit(x_train, y_train)
    trScore = model.score(x_train, y_train)
    print("\nDecision Tree Train Score ->")
    print(trScore)

    # print out text of tree path-
    # tree_rules = export_text(model, feature_names=list(X_train.columns))
    text_representation = tree.export_text(model, feature_names=list(x_train.columns))
    print(text_representation)

    # generate tree image
    fig = plt.figure(figsize=(25,20))
    _ = tree.plot_tree(model, feature_names=x.columns, class_names=y.columns, filled=True)
    fig.savefig("decision_tree.png")

######################
###  END CLASSIFY  ###
######################


######################
### BEGIN SCHEDULE ###
######################

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


#################
### VOID MAIN ###
#################

# run once
# run()
classify()

'''
BEGIN Fast stochastic calculation
    %K = (Current Close - Lowest Low)/
    (Highest High - Lowest Low) * 100
    %D = 3-day SMA of %K

    Slow stochastic calculation
    %K = %D of fast stochastic
    %D = 3-day SMA of %K

    When %K crosses above %D, buy signal 
    When the %K crosses below %D, sell signal
    """

    df = dataframe.copy()

    # Set minimum low and maximum high of the k stoch
    low_min  = df[low].rolling( window = k ).min()
    high_max = df[high].rolling( window = k ).max()

    # Fast Stochastic
    df['k_fast'] = 100 * (df[close] - low_min)/(high_max - low_min)
    df['k_fast'].ffill(inplace=True)
    df['d_fast'] = df['k_fast'].rolling(window = d).mean()

    # Slow Stochastic
    df['k_slow'] = df["d_fast"]
    df['d_slow'] = df['k_slow'].rolling(window = d).mean()

    return df

stochs = stochastics( df, 'Low', 'High', 'Close', 14, 3 )
slow_k = stochs['k_slow'].values
fast_k = stochs['k_fast'].values
### END FAST STOCHASTIC CALCULATION

# example cmc output
# "{u'USD': {u'percent_change_60d': -46.9785509, u'market_cap_dominance': 0.0244, u'percent_change_7d': -17.47625752, u'price': 3.1982419442751278, u'volume_change_24h': 14.9018, u'percent_change_90d': -39.65488546, u'percent_change_24h': -7.39091959, u'tvl': 3323604703.28227, u'market_cap': 249490627.3795067, u'volume_24h': 6477255.6591379, u'percent_change_30d': -31.81212781, u'last_updated': u'2023-06-15T05:04:00.000Z', u'percent_change_1h': -0.03585149, u'fully_diluted_market_cap': 319824194.43}}"
'''