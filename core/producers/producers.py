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
from abc import ABCMeta
from typing import List

from core.consumer import Consumer
from tools import get_logger
from trading.exchanges.exchange_manager import ExchangeManager


class Producer:
    __metaclass__ = ABCMeta

    def __init__(self, config):
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

        # List of consumer queues to be fill
        self.consumer_queues: List[Consumer] = []

        self.should_stop = False

    def send(self, data):
        """
        Send to each consumer data though its queue
        :param data:
        :return:
        """
        for consumer in self.consumer_queues:
            consumer.queue.put(data)

    def receive(self, data):
        """
        Receive notification that new data should be sent implementation
        When nothing should be done on data : self.send(data)
        :param data:
        :return:
        """
        pass

    def start(self):
        """
        Should be implemented for producer's non-triggered tasks
        :return:
        """
        pass

    def perform(self):
        """
        Should implement producer's non-triggered tasks
        Can be use to force producer to perform tasks
        :return:
        """
        pass

    def stop(self):
        """
        Stops non-triggered tasks management
        :return:
        """
        self.should_stop = True


class ExchangeProducer(Producer):
    __metaclass__ = ABCMeta

    def __init__(self, config, exchange: ExchangeManager):
        super().__init__(config)
        self.exchange: ExchangeManager = exchange


class NotificationProducer(Producer):  # TODO TO BE IMPLEMENTED
    __metaclass__ = ABCMeta

    def __init__(self, config):
        super().__init__(config)
