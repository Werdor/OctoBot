#  Drakkar-Software OctoBot
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
from core.producers.balance_producer import BalanceProducer
from core.producers.ohlcv_producer import OHLCVProducer
from core.producers.order_book_producer import OrderBookProducer
from core.producers.orders_producer import OrdersProducer
from core.producers.recent_trade_producer import RecentTradeProducer
from core.producers.ticker_producer import TickerProducer
from tools import get_logger


class ExchangeProducersManager:
    def __init__(self, exchange):
        self.logger = get_logger(self.__class__.__name__)

        # user data producers
        self.orders_producer: OrdersProducer = OrdersProducer(exchange)
        self.balance_producer: BalanceProducer = BalanceProducer(exchange)

        # exchange data producers
        self.ohlcv_producer: OHLCVProducer = OHLCVProducer(exchange)
        self.order_book_producer: OrderBookProducer = OrderBookProducer(exchange)
        self.ticker_producer: TickerProducer = TickerProducer(exchange)
        self.recent_trade_producer: RecentTradeProducer = RecentTradeProducer(exchange)
