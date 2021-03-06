#!/usr/bin/env python

from ethereum.tools import tester
from ethereum.tools.tester import TransactionFailed
from pytest import raises, fixture
from utils import bytesToLong, longTo32Bytes, longToHexString, bytesToHexString, fix, unfix, captureFilteredLogs
from uuid import uuid4
from constants import BID, ASK, YES, NO

tester.STARTGAS = long(6.7 * 10**6)

ATTOSHARES = 0
DISPLAY_PRICE = 1
OWNER = 2
TOKENS_ESCROWED = 3
SHARES_ESCROWED = 4
BETTER_ORDER_ID = 5
WORSE_ORDER_ID = 6
GAS_PRICE = 7

def test_publicCreateOrder_bid(contractsFixture):
    createOrder = contractsFixture.contracts['CreateOrder']
    cash = contractsFixture.cash
    market = contractsFixture.binaryMarket
    ordersFetcher = contractsFixture.contracts['OrdersFetcher']
    createOrder = contractsFixture.contracts['CreateOrder']

    orderID = createOrder.publicCreateOrder(BID, 1, 10**17, market.address, 1, longTo32Bytes(0), longTo32Bytes(0), 7, value = 10**17)
    assert orderID

    amount, displayPrice, owner, tokensEscrowed, sharesEscrowed, betterOrderId, worseOrderId, gasPrice = ordersFetcher.getOrder(orderID)
    assert amount == 1
    assert displayPrice == 10**17
    assert owner == bytesToHexString(tester.a0)
    assert tokensEscrowed == 10**17
    assert sharesEscrowed == 0
    assert betterOrderId == bytearray(32)
    assert worseOrderId == bytearray(32)

def test_publicCreateOrder_ask(contractsFixture):
    cash = contractsFixture.cash
    market = contractsFixture.binaryMarket
    ordersFetcher = contractsFixture.contracts['OrdersFetcher']
    createOrder = contractsFixture.contracts['CreateOrder']

    orderID = createOrder.publicCreateOrder(ASK, 1, 10**17, market.address, 0, longTo32Bytes(0), longTo32Bytes(0), 7, value = 10**18)

    amount, displayPrice, owner, tokensEscrowed, sharesEscrowed, betterOrderId, worseOrderId, gasPrice = ordersFetcher.getOrder(orderID)
    assert amount == 1
    assert displayPrice == 10**17
    assert owner == bytesToHexString(tester.a0)
    assert tokensEscrowed == 10**18 - 10**17
    assert sharesEscrowed == 0
    assert betterOrderId == bytearray(32)
    assert worseOrderId == bytearray(32)
    assert cash.balanceOf(market.address) == 10**18 - 10**17

def test_publicCreateOrder_bid2(contractsFixture):
    cash = contractsFixture.cash
    market = contractsFixture.binaryMarket
    orders = contractsFixture.contracts['Orders']
    ordersFetcher = contractsFixture.contracts['OrdersFetcher']
    createOrder = contractsFixture.contracts['CreateOrder']
    logs = []

    orderType = BID
    amount = 1
    fxpPrice = fix('0.6')
    outcome = 0
    tradeGroupID = 42

    marketInitialCash = cash.balanceOf(market.address)
    captureFilteredLogs(contractsFixture.chain.head_state, orders, logs)
    creatorInitialETH = contractsFixture.utils.getETHBalance(tester.a1)
    orderID = createOrder.publicCreateOrder(orderType, amount, fxpPrice, market.address, outcome, longTo32Bytes(0), longTo32Bytes(0), tradeGroupID, sender=tester.k1, value = fix('10'))
    assert orderID != bytearray(32), "Order ID should be non-zero"

    retAmount, displayPrice, owner, tokensEscrowed, sharesEscrowed, betterOrderId, worseOrderId, gasPrice = ordersFetcher.getOrder(orderID)
    assert retAmount == amount
    assert displayPrice == fxpPrice
    assert owner == bytesToHexString(tester.a1)
    assert tokensEscrowed == 0.6 * 10**18
    assert sharesEscrowed == 0
    assert cash.balanceOf(tester.a1) == 0
    assert contractsFixture.utils.getETHBalance(tester.a1) == creatorInitialETH - long(0.6 * 10**18)
    assert cash.balanceOf(market.address) - marketInitialCash == 0.6 * 10**18
    assert logs == [
        {
            "_event_type": "CreateOrder",
            "tradeGroupId": tradeGroupID,
            "amount": amount,
            "price": displayPrice,
            "moneyEscrowed": tokensEscrowed,
            "sharesEscrowed": sharesEscrowed,
            "orderId": orderID,
            "outcome": outcome,
            "market": market.address,
            "sender": bytesToHexString(tester.a1),
            "orderType": BID,
        }
    ]

def test_createOrder_failure(contractsFixture):
    universe = contractsFixture.universe
    cash = contractsFixture.cash
    market = contractsFixture.binaryMarket
    orders = contractsFixture.contracts['Orders']
    createOrder = contractsFixture.contracts['CreateOrder']
    fillOrder = contractsFixture.contracts['FillOrder']
    completeSets = contractsFixture.contracts['CompleteSets']
    yesShareToken = contractsFixture.applySignature('ShareToken', market.getShareToken(YES))
    noShareToken = contractsFixture.applySignature('ShareToken', market.getShareToken(NO))

    with raises(TransactionFailed):
        createOrder.createOrder(tester.a1, ASK, 1, fix('0.6'), market.address, YES, longTo32Bytes(0), longTo32Bytes(0), 42, sender=tester.k1)

    # createOrder exceptions (pre-escrowFunds)
    with raises(TransactionFailed):
        createOrder.publicCreateOrder(3, 1, fix('0.6'), market.address, YES, longTo32Bytes(0), longTo32Bytes(0), 42, sender=tester.k1)

    # escrowFundsForBid exceptions
    with raises(TransactionFailed):
        createOrder.publicCreateOrder(BID, 1, fix('3'), market.address, YES, longTo32Bytes(0), longTo32Bytes(0), 42, sender=tester.k1)
    with raises(TransactionFailed):
        createOrder.publicCreateOrder(BID, 1, fix('0.6'), market.address, YES, longTo32Bytes(0), longTo32Bytes(0), 42, sender=tester.k1)

    # escrowFundsForAsk exceptions
    with raises(TransactionFailed):
        createOrder.publicCreateOrder(ASK, 1, 1, market.address, YES, longTo32Bytes(0), longTo32Bytes(0), 42, sender=tester.k1)
    with raises(TransactionFailed):
        createOrder.publicCreateOrder(ASK, 1, fix('0.6'), market.address, YES, longTo32Bytes(0), longTo32Bytes(0), 42, sender=tester.k1)
    assert completeSets.publicBuyCompleteSets(market.address, 2, sender=tester.k1, value=fix('2'))
    with raises(TransactionFailed):
        createOrder.publicCreateOrder(ASK, 1, fix('3'), market.address, YES, longTo32Bytes(0), longTo32Bytes(0), 42, sender=tester.k1)
    with raises(TransactionFailed):
        createOrder.publicCreateOrder(ASK, 1, fix('0.6'), market.address, YES, longTo32Bytes(0), longTo32Bytes(0), 42, sender=tester.k1)

    assert yesShareToken.approve(createOrder.address, 12, sender=tester.k1) == 1, "Approve createOrder contract to spend shares from the user's account (account 1)"
    assert yesShareToken.allowance(tester.a1, createOrder.address) == 12, "CreateOrder contract's allowance should be equal to the amount approved"

    with raises(TransactionFailed):
        createOrder.publicCreateOrder(ASK, 1, fix('0.6'), tester.a1, YES, longTo32Bytes(0), longTo32Bytes(0), 42, sender=tester.k1)

    assert createOrder.publicCreateOrder(ASK, 1, fix('0.6'), market.address, YES, longTo32Bytes(0), longTo32Bytes(0), 42, sender=tester.k1) != 0, "Order ID should be non-zero"

    # createOrder exceptions (post-escrowFunds)
    with raises(TransactionFailed):
        createOrder.publicCreateOrder(ASK, 1, fix('0.6'), market.address, YES, longTo32Bytes(0), longTo32Bytes(0), 42, sender=tester.k1)

def test_ask_withPartialShares(contractsFixture):
    universe = contractsFixture.universe
    cash = contractsFixture.cash
    market = contractsFixture.binaryMarket
    orders = contractsFixture.contracts['Orders']
    ordersFetcher = contractsFixture.contracts['OrdersFetcher']
    createOrder = contractsFixture.contracts['CreateOrder']
    fillOrder = contractsFixture.contracts['FillOrder']
    completeSets = contractsFixture.contracts['CompleteSets']
    yesShareToken = contractsFixture.applySignature('ShareToken', market.getShareToken(YES))
    noShareToken = contractsFixture.applySignature('ShareToken', market.getShareToken(NO))
    logs = []

    # buy 2 complete sets
    assert completeSets.publicBuyCompleteSets(market.address, 2, sender = tester.k1, value=fix('2'))
    assert cash.balanceOf(tester.a1) == fix('0')
    assert yesShareToken.balanceOf(tester.a1) == 2
    assert noShareToken.balanceOf(tester.a1) == 2

    # create ASK order for 3 shares with a mix of shares and cash
    assert yesShareToken.approve(createOrder.address, fix('2'), sender = tester.k1)
    captureFilteredLogs(contractsFixture.chain.head_state, orders, logs)
    orderID = createOrder.publicCreateOrder(ASK, 3, fix('0.6'), market.address, YES, longTo32Bytes(0), longTo32Bytes(0), 42, sender=tester.k1, value=fix('0.4'))
    assert cash.balanceOf(tester.a1) == fix('0')
    assert yesShareToken.balanceOf(tester.a1) == 0
    assert noShareToken.balanceOf(tester.a1) == 2

    # validate the order contains expected results
    assert orderID != bytearray(32), "Order ID should be non-zero"
    amount, displayPrice, owner, tokensEscrowed, sharesEscrowed, betterOrderId, worseOrderId, gasPrice = ordersFetcher.getOrder(orderID)
    assert amount == 3
    assert displayPrice == fix('0.6')
    assert owner == bytesToHexString(tester.a1)
    assert tokensEscrowed == fix('0.4')
    assert sharesEscrowed == 2
    # validate the log output of the order
    assert logs == [
        {
            "_event_type": "CreateOrder",
            "tradeGroupId": 42,
            "amount": amount,
            "price": displayPrice,
            "moneyEscrowed": tokensEscrowed,
            "sharesEscrowed": sharesEscrowed,
            "orderId": orderID,
            "orderType": ASK,
            "outcome": YES,
            "market": market.address,
            "sender": bytesToHexString(tester.a1),
            "orderType": ASK,
        }
    ]
