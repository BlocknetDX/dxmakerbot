#!/usr/bin/env python3
import time
import random
import argparse
import sys
import logging
from utils import dxbottools
from utils import trexbot
from utils import dxsettings



logging.basicConfig(filename='botdebug.log', 
                    level=logging.INFO, 
                    format='%(asctime)s %(levelname)s - %(message)s',
                    datefmt='[%Y-%m-%d:%H:%M:%S]')

# TODO: Implementing CLI based arg's
parser = argparse.ArgumentParser()
parser.add_argument('--maker', help='maker chain', default='BLOCK')
parser.add_argument('--taker', help='taker chain', default='LTC')
parser.add_argument('--slidemin', help='price slide adjustment', default=0.999887)
parser.add_argument('--slidemax', help='price slide adjustment', default=1.015999)
parser.add_argument('--cancelall', help='cancel all orders and exist', action="store_true")
parser.add_argument('--sellmin', help='maker sell min order size', default=0.001)
parser.add_argument('--sellmax', help='maker sell max order size', default=1)
args = parser.parse_args()

BOTsellmarket = args.maker.upper()
BOTbuymarket = args.taker.upper()
BOTslidemin = float(args.slidemin)
BOTslidemax = float(args.slidemax)

if args.cancelall:
  results = dxbottools.cancelallorders()
  print (results)
  sys.exit(0)

time.sleep(1.5) # wait for cancel orders
print ('start bot')
print (BOTsellmarket, BOTbuymarket)
print (' - checking trex api ...')
print ('makers market price: %s' %(trexbot.getpricedata(BOTsellmarket, BOTbuymarket)))
# init values
maxloopcount = 30 # 1 loop per minute, then cancel all orders, start over
loopcount = 0
maxordercount = 10
ordercount = 0

# order loop
print (BOTsellmarket, BOTbuymarket)
makeraddress = dxsettings.tradingaddress[BOTsellmarket]
takeraddress = dxsettings.tradingaddress[BOTbuymarket]

print (makeraddress)
print (takeraddress)
if __name__ == "__main__":
  while 1:  # loop forever
    #print('.', end='')
    mybalances = dxbottools.rpc_connection.dxGetTokenBalances()
    blockbalance = float(mybalances[BOTsellmarket]) 
    print('pre-start balances: %s' % blockbalance)
    while blockbalance > 0:
      print ('balance ok')
      makermarketprice = trexbot.getpricedata(BOTsellmarket, BOTbuymarket)
      print ('marketprice: {0}'.format(makermarketprice))
      mybalances = dxbottools.rpc_connection.dxGetTokenBalances()
      blockbalance = float(mybalances[BOTsellmarket])
      print ('Balances', blockbalance)
      #generate random sell amount of block
      sellamount = random.uniform(float(args.sellmin), float(args.sellmax))
      sellamount = '%.6f' % sellamount

      #adjust block ltc price
      print('block: ', makermarketprice)
      print('slidemin: ', BOTslidemin)
      print('sldiemax: ', BOTslidemax)
      makermarketpriceslide = float(makermarketprice) * float(random.uniform(BOTslidemin, BOTslidemax))
      
      print ('blockprice: ', makermarketpriceslide)
      print ('sell amount', str(sellamount))

      buyamount = (float(sellamount) * float(makermarketpriceslide)) 
      buyamountclean = '%.6f' % buyamount
      print ('buyamount {0}'.format(buyamountclean))
      currentopenorders = len(dxbottools.getopenordersbymaker(BOTsellmarket))
      print('currentopenorders: {0} maker: {1}'.format(currentopenorders, BOTsellmarket))
      if (ordercount < maxordercount) and (currentopenorders < (maxordercount)):
        try:
          print('placing order...')
          results = {}
          results = dxbottools.makeorder(BOTsellmarket, str(sellamount), makeraddress, BOTbuymarket, str(buyamountclean), takeraddress)
          print ('order placed, id: {0} maker_size: {1} taker_size: {2}'.format(results['id'], results['maker_size'],results['taker_size']))
          logging.info('order placed, id: {0} maker_size: {1} taker_size: {2}'.format(results['id'], results['maker_size'],results['taker_size']))
        except Exception as err:
          print ('error: %s' % err)
        print('completed')
      else:
        print('##### too many orders open, open order count: {0}, loopcount: {1}'.format(currentopenorders, loopcount))
      loopcount += 1
      ordercount += 1
      print ('sleep')
      time.sleep(3)
      if loopcount > maxloopcount:
        results = dxbottools.canceloldestorder()
        logging.info('cancelled order1 ID:{0} '.format(results))
        print ('canceled oldest: {0}'.format(results))
        loopcount = 0
        ordercount = 0
        time.sleep(3.5)
    if blockbalance <= 10:
      loopcount += 1
    if loopcount > maxloopcount:
      results = dxbottools.canceloldestorder()
      logging.info('cancelled order1 ID:{0} '.format(results))
      print ('canceled oldest: {0}'.format(results))
      loopcount = 0
      ordercount = 0
      time.sleep(3.5)
      print ('canceled oldest sleeping...')
      time.sleep(120)


# vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2
