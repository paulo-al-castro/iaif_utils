# This file is part of the iaif_utils package
#  mt5se home: https://github.com/paulo-al-castro/iaif_utils
# Author: Paulo Al Castro
# Date: 2026-03-02

##########################################


"""
Backtest Module 
"""

from datetime import datetime
from datetime import timedelta
import pandas as pd 
import numpy as np
import os.path

historical=False
historical_dbars=dict()

def set_historical(assets,dbars,prestart,start,end,period,capital,file='backtest_file',verbose=False):
    global historical,historical_dbars
    historical=True
    historical_dbars=dbars
    return set(assets,prestart,start,end,period,capital,file,verbose)

def set(assets,prestart,start,end,period,capital,file='backtest_file',verbose=False):

    bts=dict()  #backtest setup
    if type(verbose)==bool:
        bts['verbose']=verbose
    else:
        print('verbose should be bool')
        return None
    if type(prestart)==datetime:
        bts['prestart']=prestart
    else:
        print('prestart should be datetime')
        return None
    if type(start)==datetime:
        bts['start']=start
    else:
        print('start should be datetime')
        return None
    if type(end)==datetime:
        bts['end']=end
    else:
        print('end should be datetime')
        return None
    if period==se.DAILY or period==se.INTRADAY or period==se.H1:
        bts['type']=period
    else:
        print('type should be daily or intraday or H1')
        return None
    if type(file)==str:
        bts['file']=file
    else:
        print('file should be str')
        return None
    if type(assets)==list:
        bts['assets']=assets
    else:
        print('assets should be list')
        return None
    if type(capital)==float or type(capital)==int:
        bts['capital']=float(capital)
    else:
        print('capital should be float')
        return None
    return bts

def get_shares(bts,asset):
    return bts['shares_'+asset]

def get_balance(bts):
    return bts['capital']

#######################################
# Funções para carregar dados do backtest online ou historico

def get_bars(asset,b_start,b_end,b_type=1):
    if historical:
        if type(b_end).__name__=='int':
            start=b_start.strftime("%Y-%m-%d")
            end=b_end
            return historical_dbars[asset][(historical_dbars[asset]['time']>=start)].head(end)            
        else:
            start=b_start.strftime("%Y-%m-%d")
            end=b_end.strftime("%Y-%m-%d")
            return historical_dbars[asset][(historical_dbars[asset]['time']>=start)&((historical_dbars[asset]['time']<=end))]
    else:
        return se.get_bars(asset,b_start,b_end,b_type)

def get_last_prices(assets):
    if historical:
        return se.get_last_prices(assets,historical_dbars)
    else:
        return se.get_last_prices(assets)

##########################################

## assume-se que todos os ativos tem o mesmo numero de barras do ativo indice zero assets[0] no periodo de backtest
sim_dates=[]

def startBckt(bts): 
    global sim_dates
    assets=bts['assets']
    dbars=dict()
    for asset in assets:
        dbars[asset]=get_bars(asset,bts['prestart'],bts['start'],bts['type'])
        bts['shares_'+asset]=0.0
    bars=get_bars(assets[0],bts['start'],bts['end'],bts['type'])
    
    sim_dates=list(bars['time'])
   
    bts['curr']=0 # guarda a data simulada corrente como indice de sim_dates
    
    #balanceHist.append(bts['capital'])
    #equityHist.append(bts['capital'])
    #datesHist.append(sim_dates[bts['curr']])
    return dbars

def endedBckt(bts):
    if bts['verbose']:
        print('Ended?? time =', bts['curr'], ' of ',len(sim_dates))
    if bts['curr']==None or bts['end']==None:
        return True
    elif bts['curr']<len(sim_dates):
        return False
    else:
        return True


balanceHist=[]
equityHist=[]
datesHist=[]
ordersHist=[]

def checkOrder(req,bts,bars):
    if req==None:
        return False
    money=bts['capital']
    asset=req['symbol']
    volume=req['volume']
    price=se.get_last(bars)
    sell=se.isSellOrder(req)

    if sell:
        if bts['shares_'+asset]>=volume:
            return True
        else:
            return False
    else:
        if money>=volume*price : # checa se não ficaria negativo com a execução
            return True
        else:
            se.setLastError('Trade would make the balance negative! Therefore, it does not check!')
        return False


def compute_order(order,volume,price):
    lastOrderResult=dict()
    lastOrderResult['symbol']=order['symbol'] 
    lastOrderResult['isSellOrder']=se.isSellOrder(order)
    lastOrderResult['shares']=volume
    lastOrderResult['price']=price
    return lastOrderResult





def computeOrders(orders,bts,dbars):
    assets=bts['assets']
    total_in_shares=0.0
    executedOrdersList=[]
    if orders==None:
        equityHist.append(equityHist[-1])
        balanceHist.append(balanceHist[-1])
        datesHist.append(sim_dates[bts['curr']])
        for asset in assets:
            bar=dbars[asset]
            price=se.get_last(bar)
            total_in_shares=total_in_shares+bts['shares_'+asset]*price # counts the value in asset with no order
        if bts['verbose']:
            print( 'No orders in time(',bts['curr'],') = ',sim_dates[bts['curr']],' capital=',bts['capital'], 'total in shares=',total_in_shares)
        return True
    
    if bts['verbose']:
        print('List of ',len(orders),'orders in time(',bts['curr'],') :')
    for asset in assets:
        bar=dbars[asset]
        if bar is None:
            print('Error accesing bar to compute order')
            return False
        price=se.get_last(bar)
        order=getOrder(orders,asset)
        if order==None: # if no order for that asset, go to the next
            total_in_shares=total_in_shares+bts['shares_'+asset]*price # counts the value in asset with no order
            continue
        volume=order['volume']
        if se.isSellOrder(order):
            bts['shares_'+asset]=bts['shares_'+asset]-volume
            bts['capital']=bts['capital']+volume*price
            if bts['verbose']:
                print("Order for selling ",volume,"shares of asset=",asset, " at price=",price)
        else:
            bts['shares_'+asset]=bts['shares_'+asset]+volume
            bts['capital']=bts['capital']-volume*price
            if bts['verbose']:
                print("Order for buying ",volume,"shares of asset=",asset, " at price=",price)
        ord_result=compute_order(order,volume,price)
        executedOrdersList.append(ord_result)
        total_in_shares=total_in_shares+float(bts['shares_'+asset])*price # counts the value in asset with order
    if bts['verbose']:
        print( len(orders),' order(s) in time(',bts['curr'],') = ',sim_dates[bts['curr']],' capital=',bts['capital'], 'total in shares=',total_in_shares, 'equity=',bts['capital']+total_in_shares)
    equityHist.append(bts['capital']+total_in_shares)
    balanceHist.append(bts['capital'])
    datesHist.append(sim_dates[bts['curr']])
    #detalhamento das ordens
    prices=se.get_last_prices(assets)
    ordersHist.append(se.operations.orders_to_txt(assets,orders,prices))
    return executedOrdersList
    

def getOrder(orders,asset):
    for order in orders:
        if order['symbol']==asset:
            return order
    return None


def getCurrBars(bts,dbars):
    assets=bts['assets']
    #dbars=dict()
    for asset in assets:
        dbar=dbars[asset]
        #pega nova barra    
        aux=get_bars(asset,sim_dates[bts['curr']],1,bts['type']) # pega uma barra! daily or intraday
        if not aux is None and not aux.empty:
            dbar=dbar.iloc[1:,] #remove barra mais antiga
            #adiciona nova barra
            #dbar=dbar.append(aux)
            dbar=pd.concat([dbar, aux], ignore_index=True)
            dbar.index=range(len(dbar))# corrige indices
            dbars[asset]=dbar
       
    return dbars 

def checkBTS(bts):
    try:
        if type(bts['verbose'])!=bool:
            print('verbose should be bool')
            return False
        if type( bts['prestart'])!=datetime:
            print('prestart should be datetime')
            return False
        if type(bts['start'] )!=datetime:
            print('start should be datetime')
            return False
        if type(bts['end'])!=datetime:
            print('end should be datetime')
            return False
        if bts['type']!=se.DAILY and bts['type']!=se.INTRADAY and bts['type']!=se.H1:
            print('type should be daily or intraday or H1')
            return False
        if type(bts['file'])!=str:
            print('file should be str')
            return False
        if type(bts['assets'])!=list:
            print('assets should be list')
            return False
        if type(bts['capital'])!=float and type(bts['capital'])!=int:
            print('capital should be float')
            return False
        return True
    except:
        print("An exception occurred")
        return False

def run(trader,bts):
    se.mt5se.inbacktest=True
    se.mt5se.bts=bts
    balanceHist.clear()
    equityHist.clear()
    datesHist.clear()
    if trader==None: # or type(trader)!=se.Trader:
        print("Error! Trader should be an object of class mt5se.Trader or its subclass")
        return False
    if not checkBTS(bts):
        print("The Backtest setup (bts) is not valid!")
        return False
    dbars=startBckt(bts)
    trader.setup(dbars)
    bts['curr']=0
    if bts['verbose']:
        print("Starting at simulated date=",sim_dates[0]," len=",len(sim_dates))
    while not endedBckt(bts):
        #orders=trader.getNewInfo(dbars)
        orders=trader.trade(dbars)
        dbars=getCurrBars(bts,dbars)
        ex_orders_list=computeOrders(orders,bts,dbars)
        trader.orders_result(ex_orders_list)
        if bts['verbose']:
            print("Advancing simulated date from ",bts['curr']," = ",sim_dates[bts['curr']])
        bts['curr']=bts['curr']+1 # advances simulated time
    print('End of backtest with ',bts['curr'],' bars,  saving equity file in ',bts['file'])
    trader.ending(dbars)
    df=saveEquityFile(bts)
    se.mt5se.inbacktest=False
    return df


def saveEquityFile(bts):
    """
    print('csv format, columns: <DATE>		<BALANCE>	<EQUITY>	<DEPOSIT LOAD>')
<DATE>	            <BALANCE>	<EQUITY>	<DEPOSIT LOAD> <orders>
2019.07.01 00:00	100000.00	100000.00	0.0000
2019.07.01 12:00	99980.00	99999.00	0.0000
2019.07.01 12:59	99980.00	100002.00	0.1847
2019.07.01 12:59	99980.00	99980.00	0.0000
2019.07.02 14:59	99960.00	99960.00	0.0000
2019.07.03 13:00	99940.00	99959.00	0.0000
2019.07.03 13:59	99940.00	99940.00	0.0000
2019.07.08 15:59	99920.00	99936.00	0.0000
2019.07.08 16:59	99920.00	99978.00	0.1965
2019.07.10 10:00	99920.00	99920.00	0.0000
2019.07.10 10:59	99900.00	99937.00	0.1988
Formato gerado pelo metatrader,
ao fazer backtest com o Strategy Tester, clicar na tab 'Graphs' e botao direto 'Export to CSV (text file)'
    """
    #print('write report....')
    if len(equityHist)!=len(balanceHist) or len(balanceHist)!=len(datesHist):
        print("Erro!! Diferentes tamanhos de historia, de equity, balance e dates")
        return False
    df=pd.DataFrame()
    df['date']=[]
    df['balance']=[]
    df['equity']=[]
    df['load']=[]
    df['orders']=[]

    for i in range(len(equityHist)):
        df.loc[i]=[datesHist[i],balanceHist[i],equityHist[i],0.0,ordersHist[i]]

    if os.path.isfile(bts['file']+'.csv'):
        df.to_csv(bts['file']+'.csv',mode='a',header=False) # file already exists, so it appends
    else:
        df.to_csv(bts['file']+'.csv') 
    return df 


def evaluate(df):
   #rreturns=__calcReturns(df['equity'])
   """ print('---rreturns------')
   print(rreturns)
   for r in rreturns:
       print(r)
   print('---rreturns------') """
   #if df==None:
   #    print('Error!! df should be a DataFrame with a equity column')
   evaluateEquitySerie(df['equity'])



#using Distributions
#using CSV
#using StringEncodings
from math import sqrt
from scipy.stats import norm
from scipy.stats import kurtosis
from scipy.stats import skew

import pandas as pd 
import numpy as np 
import statistics 




"""
   return the probability of the performance greater than the given threshold (annual return)
"""
def ProbReturnGreaterThanThreshold(returns,threshold):
   numberOfDays=len(returns)
   if numberOfDays<30:
      print("In order to perform STSE evaluation, you should have at least 30 daily data points, but you got only ",numberOfDays)
      return False
   prob=__estimateProb(returns,(threshold+1)**(1/252)-1)
   return 1-prob
"""
   https://www.google.com/search?q=how+to+obtain+a+distribution+from+another+distribution&oq=how+to+obtain+a+distribution+from+another+distribution&aqs=chrome..69i57.71322j0j4&sourceid=chrome&ie=UTF-8#kpvalbx=_q39vX-3TA9ix5OUPl9Sg4AI30

   y=g(x)= (1+x)^252-1

   Fy(y)=P(Y<=y)
   Y<=y
   g(x)=(1+x)^252-1<=y
   x<=(y+1)^(1/252)-1=expr
   3.Fy(y)=P(Y<=y)=P(x<expr)
   Logo,
   Probabilidade de retorno maior que y=1-Fy(y)=1-P(X<(y+1)^(1/252)-1)
"""

def __estimateProb(returns,limit):
   numberOfDays=len(returns)
   if numberOfDays<30:
      print("In order to perform evaluation, you should have at least 30 daily data points, but you got only ",numberOfDays)
      return False
   if returns==None or len(returns)==0:
      return 0
   smaller=0
   for i in returns:
      if i<=limit:
         smaller=smaller+1
   return smaller/numberOfDays



"""
    calcGeoAvgReturn(returns::Array{Float64}) 
    returns the geometric average of the given serie of returns. 
"""
def calcGeoAvgReturn(returns):
   ret=1
   s=len(returns)
   for  i in range(s):
      ret*=(1+returns[i])
   return ret**(1.0/s)-1

"""
    calcStdDev(x::Array{Float64}) 
    return the standard deviation of a sample
"""
def calcStdDev(x):
   return statistics.stdev(x)


"""
    calculates a serie of return given a serie of prices as argument
    return[i]=price[i]/price[i-1]-1
    the serie of returns has length equal to the price serie lenth minus 1.
"""
def calcReturnsFromPrice(serie):
   x=[]
   if type(serie)==pd.Series:
      for i,valor in serie.iteritems(): # calculates the serie of returns
         x.append(valor)
      y=[]
      for i in range(len(x)-1): # calculates the serie of returns
        y.append(x[i+1]/x[i]-1)
      return y   
   else:
    for i in range(len(serie)-1): # calculates the serie of returns
        x.append(serie[i+1]/serie[i]-1)
    return x


def __calcReturns(serie):
    x=[]
    #print('calcRetursn')
    for i in range(len(serie)-1): # calculates the serie of returns
        x.append(serie[i+1]/serie[i]-1)
        #print(x[i])
    return x


"""
    evaluateEquitySerie(serie,threshold=0.5,riskFree=0.0)
    evaluates a trader performance given its serie of historical equity value 
"""
def evaluateEquitySerie(serie,threshold=0.5,riskFree=0.0):
    if serie is None:
        print("serie should be a list of observed market values of the portfolio, given daily")
        return None
    serie=__calcReturns(serie)
    numberOfDays=len(serie)
    if numberOfDays<30:
        print("In order to perform evaluation, you should have at least 30 data points, but you got only ",numberOfDays)
        return False
    print("\n -----------------------   Backtest Report  ------------------------------- \n")
    print("Total Return (%)={:.2f} in {} bars ".format(calcTotalReturn(serie)*100,numberOfDays))
    print("Average Bar Return (%)={:.2f}  ".format(np.average(serie)*100))
    #print("Annualized Return (%)={:.2f}".format(calcAnnualReturn(serie,numberOfDays)*100))
    print("Std Deviation of returns (%) ={:.4f}".format(calcStdDev(serie)*100))
    #print("Sharpe Ratio={:.4f} ".format(calcSharpeRatio(serie,riskFree)))
    #print("Annualized Sharpe Ratio={:.4f} ".format(calcAnnualSharpeRatio(serie,riskFree,numberOfDays ))),
    """ l1=0
   p1=ProbReturnGreaterThanThreshold(serie,l1)
   l2=0.1
   p2=ProbReturnGreaterThanThreshold(serie,l2)
   l3=0.2
   p3=ProbReturnGreaterThanThreshold(serie,l3)
   
   print("Probability that Annual Return is greater than ({:.1f}%) ={:.2f}%".format(100*l1, 100*p1))
   print("Probability that Annual Return is greater than ({:.1f}%) ={:.2f}%".format(100*l2, 100*p2))
   print("Probability that Annual Return is greater than ({:.1f}%) ={:.2f}%".format(100*l3, 100*p3))"""

    print("\n ----------------------        End of Report     -------------------------------- \n")



"""
    processFile(fileName,numberOfDays)
    process the  "tick-returns CSV file" pointed by fileName and provide several information about the strategy performance. The numberOfDays informs the number of working days in the serie, and it
    can have more or less than a year. One year is assumed to have 252 [working] days. 
"""
def evaluateFile(fileName,threshold=0.5,riskFree=0.0):
  
  # assetSR=calcSharpeRatio(areturns,0)
   cv=pd.read_csv(fileName)

   #rreturns=__calcReturns(cv['equity'])
   #evaluateEquitySerie expectes the equity serie
   evaluateEquitySerie(cv['equity'],threshold,riskFree)


#returns the Total return of a series of returns given of the n first returns
def calcTotalReturn(returns):
   ret=1
   s=len(returns)
   for  i in range(s):
      ret*=(1+returns[i])
   return ret-1


#returns the arithmetic average return of the series of returns given of the n first returns
def calcAvgReturn(returns): 
   sum=float(0)
   s=len(returns)
   for  i in range(s):
      sum+=returns[i]
   return sum/s


def calcAnnualReturn(returns, numberOfDays):
   gReturn=calcTotalReturn(returns)
   return (1+gReturn)**(252.0/numberOfDays)-1



def calcAnnualSharpeRatio(returns, riskfree, numberOfDays):
   # annRet=calcAnnualReturn(returns,numberOfDays)
   # sigma=calcDesvPad(returns) # we suppose sigma stable
   #if(sigma==0) 
   #   print("ERROR! standard deviation equals to zero. In calc Annual SR")
   #   return (annRet-riskfree)
   #end
   #return (annRet-riskfree)/sigma
   # implemented according to paper Andrew W Lo},The Statistics of Sharpe Ratios, journal = {Financial Analysts Journal}, 2003

   return sqrt(252)*calcSharpeRatio(returns,riskfree)


def calcSharpeRatioFromPrice(prices, riskfree): 
   returns=calcReturnsFromPrice(prices)
   return calcSharpeRatio(returns,riskfree)

def calcSharpeRatio(returns, riskfree): 
   avg=calcAvgReturn(returns)
   sigma=calcStdDev(returns)
   if sigma!=0:
       return (avg-riskfree)/sigma
   print("Error!! standard deviation of returns is not suposed to be zero, but it is!!")
   return -1

#### operations

# This file is part of the mt5se package
#  mt5se home: https://github.com/paulo-al-castro/mt5se
# Author: Paulo Al Castro
# Date: 2020-11-17

"""
Operations Module - Disponibiliza funções para facilitar a criação, execução e avaliação de backtests
"""

from mt5se.mt5se import date
import mt5se as se
from datetime import datetime
from datetime import timedelta
import pandas as pd 
import time
import os.path

"""
    Returns the time to the given time in the same day in seconds
"""
def secondsToTime(endHour=18, endMin=0):
    refTime=datetime.now()
    endTime=datetime.now()
    endTime=endTime.replace(hour=endHour, minute=endMin)
    d=endTime-refTime
    return d.total_seconds()

"""
    Returns the datetime expected to end today's session. For default, 17:00 (hour=17 minute=0) 
"""
def sessionEnd(hourSessionEnd=17,minSessionEnd=0):
    endTime=datetime.now()
    endTime=endTime.replace(hour=hourSessionEnd,minute=minSessionEnd,second=0)
    return endTime


"""
 Returns a specification to operations session. Parameters:
    assets,
    capital,
    endTime,
    mem,
    timeframe=se.DAILY,
    file='operation_file',
    verbose=False,
    delay=1,
    waitForOpen=False

"""
def set(assets,capital,endTime,mem,timeframe=se.DAILY,file='operation_file',verbose=False,delay=1,waitForOpen=False):
    ops=dict()  #backtest setup
    if type(waitForOpen)==bool:
        ops['waitForOpen']=waitForOpen
    else:
        print('waitForOpen should be bool')
    if type(verbose)==bool:
        ops['verbose']=verbose
    else:
        print('verbose should be bool')
        return None
    if type(delay)==float or type(delay)==int:
        ops['delay']=delay
    else:
        print('delay should be float')
        return None
    
    if type(mem)==int:
        ops['mem']=mem
    else:
        print('mem should be int')
        return None

    if type(endTime)==datetime:
        ops['end']=endTime
    else:
        print('endTime should be datetime')
        return None
    if timeframe==se.DAILY or timeframe==se.INTRADAY:
        ops['type']=timeframe
    else:
        print('type should be daily or intraday')
        return None
    if type(file)==str:
        ops['file']=file
    else:
        print('file should be str')
        return None
    if type(assets)==list:
        ops['assets']=assets
    else:
        print('assets should be list')
        return None
    if type(capital)==float or type(capital)==int:
        ops['capital']=float(capital)
    else:
        print('capital should be float')
        return None
    return ops

"""
Returns True if the given operation setup is Ok
"""
def checkOps(ops):
    try:
        if type(ops['waitForOpen'])!=bool:
            print('waitForOpen should be bool')
            return False
        if type(ops['verbose'])!=bool:
            print('verbose should be bool')
            return False
        if type( ops['mem'])!=int:
            print('mem should be int')
            return False
        if type( ops['delay'])!=int and type( ops['delay'])!=float:
            print('delay should be int or float. (seconds of delay, between to calls to trade)')
            return False
        if type(ops['start'] )!=datetime:
            print('start should be datetime')
            return False
        if type(ops['end'])!=datetime:
            print('end should be datetime')
            return False
        if ops['type']!=se.DAILY and ops['type']!=se.INTRADAY:
            print('type should be daily or intraday')
            return False
        if type(ops['file'])!=str:
            print('file should be str')
            return False
        if type(ops['assets'])!=list:
            print('assets should be list')
            return False
        if type(ops['capital'])!=float and type(ops['capital'])!=int:
            print('capital should be float')
            return False
        return True
    except:
        print("An exception occurred")
        return False



## assume-se que todos os ativos tem o mesmo numero de barras do ativo indice zero assets[0] no periodo de backtest
sim_dates=[]
balanceHist=[]
equityHist=[]
datesHist=[]
ordersHist=[]
averagePrices=dict()


"""
Returns the current time in a given operation setup
"""
def getCurrTime(ops):
    assets=ops['assets']
    bars=se.get_bars(assets[0],1,timeFrame=se.INTRADAY)
    return bars['time'][0]
    
def startOps(ops): 
    global sim_dates
    assets=ops['assets']
    dbars=dict()
    
    sim_dates.append(getCurrTime(ops))
    mem=ops['mem']
    for asset in assets:
        averagePrices[asset]=0.0
        dbar=se.get_bars(asset,mem,timeFrame=se.INTRADAY)
        if not dbar is None and not dbar.empty:
            dbars[asset]=dbar
        else:
            print("Error asset ",asset, " without information!!!")
    balanceHist.append(ops['capital'])
    equityHist.append(ops['capital'])
    datesHist.append(sim_dates[0])
    ordersHist.append(' ')
    return dbars

def getDeltaOrder(req):
    vol=req['volume']

    if se.isSellOrder(req):
        vol=-vol    
    #elif req['type']==mt5.ORDER_TYPE_BUY_LIMIT or req['type']==mt5.ORDER_TYPE_BUY:
    #    return False
    return vol

""" 
 Returns the Equity in the default currency of the stock
"""
def get_equity():
    return se.account_info().equity


def executeOrders(orders,ops,dbars):
    assets=ops['assets']
    total_in_shares=0.0
    sim_dates.append(getCurrTime(ops))
    executedOrders=[]
    txt=''
    balance=se.get_balance() 
    equity=get_equity()
    for asset in assets:
        shares=se.get_shares(asset)
        order=getOrder(orders,asset)
        # send order
        if order!=None:
            if se.checkOrder(order) and se.sendOrder(order): 
                    print('order sent to se')
                    result=se.getLastOrderResult()
                    executedOrders.append(result)
            else:
                    print('Error  : ',se.getLastError())
            txt=txt+' '+asset+', '+ str(shares)+', '+str(getDeltaOrder(order))+';'
        else:
            txt=txt+' '+asset+','+ str(shares)+', 0;'
            continue
    total_in_shares=se.get_position_value()
    if ops['verbose']==True:
        msg=str(len(orders))+' order(s) in time('+str(sim_dates[-1])+' equity={:,.2f} balance={:,.2f} '+txt
        print(msg.format(equity,balance))
    else:
        msg=str(len(orders))+' order(s) in time('+str(sim_dates[-1])+' equity={:,.2f} balance={:,.2f}. Use verbose=True for more information'
        print(msg.format(equity,balance))
    equityHist.append(equity)  # equity in operations 
    balanceHist.append(balance)
    datesHist.append(sim_dates[-1])
    prices=se.get_last_prices(assets)
    ordersHist.append(orders_to_txt(assets,orders,prices))
    return executedOrders

  
    
def orders_to_txt(assets,orders,prices):
    assets.sort()
    txt=''
    for asset in assets:
        order=getOrder(orders,asset)
        if order is not None:
            if se.isSellOrder(order):
                sinal='-'
            else:
                sinal='+'
            volume=order['volume']
        else:  # sem ordem para o ativo
            sinal=' '
            volume=0
        txt=txt+asset+'/'+sinal+str(volume)+'/'+str(prices[asset])+'/ '
    return txt

def txt_to_orders(txt):
    orders=[]
    lst=txt.split('/')
    if len(lst)%3!=1 or len(lst)<3:
        return None
    i=0
    while i<len(lst)-3:
        order=0
        symbol=lst[i].strip()
        shares=float(lst[i+1])
        price=float(lst[i+2])
        if shares>0:
            order=se.buyOrder(symbol,int(abs(shares)),price)
        elif shares<0:
            order=se.sellOrder(symbol,int(abs(shares)),price)
        else:
            order=None        
        i=i+3
        if order is not None:
            orders.append(order)
    return orders



def getOrder(orders,asset):
    for order in orders:
        if order['symbol']==asset:
            return order
    return None


def getCurrBars(ops,dbars):
    assets=ops['assets']
    #dbars=dict()
    for asset in assets:
        dbar=dbars[asset]
        #pega nova barra    
        aux=se.get_bars(asset,1,timeFrame=se.INTRADAY) # pega uma barra!
        if not aux is None and not aux.empty:
            dbar=dbar.iloc[1:,] #remove barra mais antiga
            #adiciona nova barra
            dbar=dbar.append(aux)
            dbar.index=range(len(dbar))# corrige indices
            dbars[asset]=dbar
       
    return dbars 

def getLastTime(ops):
    assets=ops['assets']
    bars=se.get_bars(assets[0],1,timeFrame=se.INTRADAY)
    return bars['time'][0]
   

def endedOps(ops):
    assets=ops['assets']
    if not se.is_market_open(assets[0]):
        print('Market is NOT open at the moment!!')
        return True
    
    if ops['verbose']:
        print('Ended?? time =',getCurrTime(ops), ' of ',len(sim_dates))
    if ops['end']==None:
        return True
    elif ops['end']<getLastTime(ops):
        return 
    else:
        return False




"""
    Start the execution of the given trader according to the operation setup given
"""
def run(trader,ops):
    se.mt5se.inbacktest=False

    if trader==None: # or type(trader)!=se.Trader:
        print("Error! Trader should be an object of class mt5se.Trader or its subclass")
        return False
    dbars=startOps(ops)
    assets=ops['assets']
    trader.setup(dbars)
    if 'delay' in ops.keys():
        delay=ops['delay']
    else:
        delay=0
    if ops['verbose']:
        print("Starting Operation at date/time=",sim_dates[0]," len=",len(sim_dates))
    if ops['waitForOpen']:
        while not se.is_market_open(assets[0]):
            print('Market is NOT open! we will wait until it is open...')
            time.sleep(1)
    while not endedOps(ops):
        orders=trader.trade(dbars)
        ex_order_list=executeOrders(orders,ops,dbars)
        trader.orders_result(ex_order_list)
        dbars=getCurrBars(ops,dbars)
        saveTick(ops)
        time.sleep(delay)
    print('End of operation saving equity file in ',ops['file'])
    trader.ending(dbars)
    df=saveEquityFile(ops)
    return df


def saveTick(ops):
    """
    print('csv format, columns: <DATE>		<BALANCE>	<EQUITY>	<DEPOSIT LOAD>')
<DATE>	            <BALANCE>	<EQUITY>	<DEPOSIT LOAD>
2019.07.01 00:00	100000.00	100000.00	0.0000
2019.07.01 12:00	99980.00	99999.00	0.0000
2019.07.01 12:59	99980.00	100002.00	0.1847
2019.07.01 12:59	99980.00	99980.00	0.0000
2019.07.02 14:59	99960.00	99960.00	0.0000
2019.07.03 13:00	99940.00	99959.00	0.0000
2019.07.03 13:59	99940.00	99940.00	0.0000
2019.07.08 15:59	99920.00	99936.00	0.0000
2019.07.08 16:59	99920.00	99978.00	0.1965
2019.07.10 10:00	99920.00	99920.00	0.0000
2019.07.10 10:59	99900.00	99937.00	0.1988
Formato gerado pelo metatrader,
ao fazer backtest com o Strategy Tester, clicar na tab 'Graphs' e botao direto 'Export to CSV (text file)'
    """
    #print('write report....')
    if len(equityHist)!=len(balanceHist) or len(balanceHist)!=len(datesHist) or len(datesHist)!=len(ordersHist):
        print("Erro!! Diferentes tamanhos de historia, de equity, balance e dates")
        print('bH=',len(balanceHist),' dH=',len(datesHist),' orderHist=',len(ordersHist))
        return False
    if len(equityHist)<=0:
        return False
    df=pd.DataFrame()
    df['date']=[]
    df['balance']=[]
    df['equity']=[]
    df['load']=[]
    df['orders']=[]
    # Salva apenas o ultimo tick
    #for i in range(len(equityHist)):
    
    i=len(equityHist)-1
    idx=len(df)
    df.loc[idx]=[datesHist[i],balanceHist[i],equityHist[i],0.0,ordersHist[i]]

    if os.path.isfile(ops['file']+'.csv'):
        df.to_csv(ops['file']+'.csv',mode='a',header=False) # file already exists, so it appends
    else:
        df.to_csv(ops['file']+'.csv')
    return df 





def saveEquityFile(ops):
    """
    print('csv format, columns: <DATE>		<BALANCE>	<EQUITY>	<DEPOSIT LOAD>')
<DATE>	            <BALANCE>	<EQUITY>	<DEPOSIT LOAD>
2019.07.01 00:00	100000.00	100000.00	0.0000
2019.07.01 12:00	99980.00	99999.00	0.0000
2019.07.01 12:59	99980.00	100002.00	0.1847
2019.07.01 12:59	99980.00	99980.00	0.0000
2019.07.02 14:59	99960.00	99960.00	0.0000
2019.07.03 13:00	99940.00	99959.00	0.0000
2019.07.03 13:59	99940.00	99940.00	0.0000
2019.07.08 15:59	99920.00	99936.00	0.0000
2019.07.08 16:59	99920.00	99978.00	0.1965
2019.07.10 10:00	99920.00	99920.00	0.0000
2019.07.10 10:59	99900.00	99937.00	0.1988
Formato gerado pelo metatrader,
ao fazer backtest com o Strategy Tester, clicar na tab 'Graphs' e botao direto 'Export to CSV (text file)'
    """
    #print('write report....')
    if len(equityHist)!=len(balanceHist) or len(balanceHist)!=len(datesHist):
        print("Erro!! Diferentes tamanhos de historia, de equity, balance e dates")
        return False
    df=pd.DataFrame()
    df['date']=[]
    df['balance']=[]
    df['equity']=[]
    df['load']=[]
    df['orders']=[]

    for i in range(len(equityHist)):
        df.loc[i]=[datesHist[i],balanceHist[i],equityHist[i],0.0,ordersHist[i]]

    if not os.path.isfile(ops['file']+'.csv'): # salva apenas se nao existir!!
       # df.to_csv(ops['file']+'.csv',mode='a',header=False) # file already exists, so it appends
        #else:
        df.to_csv(ops['file']+'.csv')
    return df 



