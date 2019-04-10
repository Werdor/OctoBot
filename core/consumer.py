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
from abc import ABCMeta, abstractmethod
from asyncio import Queue

from evaluator.abstract_evaluator import AbstractEvaluator
from evaluator.evaluator_task_manager import EvaluatorTaskManager
from tools import get_logger


class Consumer:
    __metaclass__ = ABCMeta

    def __init__(self, config):
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

        self.queue: Queue = Queue()

        self.should_close = False

    @abstractmethod
    def consume(self):
        """
        Should implement self.queue.get() in a while loop

        while not self.should_close:
            await self.queue.get()

        :return:
        """
        raise NotImplementedError("consume not implemented")


class EvaluatorConsumer(Consumer):
    def __init__(self, config, evaluator: AbstractEvaluator):
        super().__init__(config)
        self.evaluator: AbstractEvaluator = evaluator

    async def consume(self):
        while not self.should_close:
            await self.evaluator.eval(eval_trigger_tag=(await self.queue.get()))


class EvaluatorTaskManagerConsumer(Consumer):
    def __init__(self, config, evaluator_task_manager: EvaluatorTaskManager):
        super().__init__(config)
        self.evaluator_task_manager: EvaluatorTaskManager = evaluator_task_manager

    async def consume(self):
        while not self.should_close:
            await self.evaluator_task_manager.notify(notifier_name=(await self.queue.get()))  # TODO
