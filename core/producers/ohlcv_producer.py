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
import asyncio
import time
from asyncio import CancelledError
from collections import defaultdict

from backtesting import backtesting_enabled, BacktestingEndedException
from config import TimeFramesMinutes, MINUTE_TO_SECONDS, UPDATER_MAX_SLEEPING_TIME
from core.producers.producers import ExchangeProducer
from tools.time_frame_manager import TimeFrameManager


class OHLCVProducer(ExchangeProducer):
    def __init__(self, config, exchange):
        super().__init__(config, exchange)

        self.symbols = self.exchange.traded_pairs
        self.time_frames = []
        self.refreshed_times = {}
        self.time_frame_last_update = {}

        self.in_backtesting = False

    def start(self):
        self.time_frames = self.evaluator_task_manager_by_time_frame_by_symbol.keys()

        # sort time frames to update them in order of accuracy
        self.time_frames = TimeFrameManager.sort_time_frames(self.time_frames)

        if self.time_frames and self.symbols:
            self.in_backtesting = self._init_backtesting_if_necessary()

            # init refreshed_times at 0 for each time frame
            self.refreshed_times = {key: defaultdict(lambda: 0) for key in self.time_frames}

            # init last refresh times at 0 for each time frame
            self.time_frame_last_update = {key: defaultdict(lambda: 0) for key in self.time_frames}
        else:
            self.should_stop = True
            self.logger.warning("No time frames to monitor, going to sleep. "
                                "This is normal if you did not activate any technical analysis evaluator.")

    def perform(self):
        while not self.should_stop:
            try:
                await self._trigger_update()
            except CancelledError:
                self.logger.info("Update tasks cancelled.")
            except Exception as e:
                self.logger.error(f"exception when triggering update: {e}")
                self.logger.exception(e)

    def receive(self, time_frame):
        pass

    def _init_backtesting_if_necessary(self):
        # figure out from an evaluator if back testing is running for this symbol
        evaluator_task_manager = \
            self.evaluator_task_manager_by_time_frame_by_symbol[self.time_frames[0]][self.symbols[0]]

        # test if we need to initialize backtesting features
        is_backtesting_enabled = backtesting_enabled(evaluator_task_manager.get_evaluator().get_config())
        if is_backtesting_enabled:
            for symbol in self.symbols:
                self.exchange.get_exchange().init_candles_offset(self.time_frames, symbol)

        return is_backtesting_enabled

    async def _trigger_update(self):
        now = time.time()
        update_tasks = []

        for time_frame in self.time_frames:
            for symbol in self.symbols:
                # backtesting doesn't need to wait a specific time frame to end to refresh data
                if self.in_backtesting:
                    update_tasks.append(self._refresh_backtesting_time_frame_data(time_frame, symbol))

                # if data from this time frame needs an update
                elif now - self.time_frame_last_update[time_frame][symbol] \
                        >= TimeFramesMinutes[time_frame] * MINUTE_TO_SECONDS:
                    update_tasks.append(self._refresh_time_frame_data(time_frame, symbol))

        await asyncio.gather(*update_tasks)

        if update_tasks:
            await self.trigger_symbols_finalize()

        if self.in_backtesting:
            await self.update_backtesting_order_status()

        if self.should_stop:
            await self._update_pause(now)

    async def trigger_symbols_finalize(self):
        sort_symbol_evaluators = sorted(self.symbol_evaluators,
                                        key=lambda s: abs(s.get_average_strategy_eval(self.exchange)),
                                        reverse=True)
        for symbol_evaluator in sort_symbol_evaluators:
            await symbol_evaluator.finalize(self.exchange)

    # calculate task sleep time between each refresh
    async def _update_pause(self, now):
        sleeping_time = 0
        if not self.in_backtesting:
            sleeping_time = UPDATER_MAX_SLEEPING_TIME - (time.time() - now)
        if sleeping_time > 0:
            await asyncio.sleep(sleeping_time)

    async def _refresh_backtesting_time_frame_data(self, time_frame, symbol):
        try:
            if self.exchange.get_exchange().should_update_data(time_frame, symbol):
                await self._refresh_data(time_frame, symbol)
        except BacktestingEndedException as e:
            self.logger.info(e)
            self.keep_running = False
            await self.exchange.get_exchange().end_backtesting(symbol)

    # currently used only during backtesting, will force refresh of each supervised task
    async def update_backtesting_order_status(self):
        order_manager = self.exchange.get_trader().get_order_manager()
        await order_manager.force_update_order_status(simulated_time=True)

    async def _refresh_time_frame_data(self, time_frame, symbol, notify=True):
        try:
            await self._refresh_data(time_frame, symbol, notify=notify)
            self.time_frame_last_update[time_frame][symbol] = time.time()
        except CancelledError as e:
            raise e
        except Exception as e:
            self.logger.error(f" Error when refreshing data for time frame {time_frame}: {e}")
            self.logger.exception(e)

    # notify the time frame's evaluator task manager to refresh its data
    async def _refresh_data(self, time_frame, symbol, limit=None, notify=True):
        evaluator_task_manager_to_notify = self.evaluator_task_manager_by_time_frame_by_symbol[time_frame][symbol]

        numpy_candle_data = copy.deepcopy(await evaluator_task_manager_to_notify.exchange.get_symbol_prices(
            evaluator_task_manager_to_notify.symbol,
            evaluator_task_manager_to_notify.time_frame,
            limit=limit,
            return_list=False))

        evaluator_task_manager_to_notify.evaluator.set_data(numpy_candle_data)
        self.refreshed_times[time_frame][symbol] += 1
        if notify:
            await evaluator_task_manager_to_notify.notify(self.__class__.__name__)
