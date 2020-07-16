import numpy as np

from capi.com_types import *
from report.fieldConfigure import FrequencyDict


class ReportDetail(object):
    def __init__(self, runSet, position, profit, test_day, fund_record, trade_time_info, orders, trade_info, beginDate, endDate):
        self._runSet = runSet
        self._position = position
        self._profit = profit
        self._test_day = test_day
        self._fund_record = fund_record
        self._trade_time_info = trade_time_info
        self._orders = orders
        self._trade_info = trade_info
        self._beginDate = beginDate
        self._endDate = endDate

    @property
    def initial_fund(self):  # 资金
        return self._runSet['StartFund']

    @property
    def contract(self):  # 合约信息
        return [p for p in self._position]

    @property
    def period(self):  # 周期
        klineType = FrequencyDict[self._runSet['KLineType']]
        kLineSlice = str(self._runSet['KLineSlice'])
        return kLineSlice + klineType

    @property
    def start_time(self):  # 计算开始时间
        return self._beginDate

    @property
    def end_time(self):  # 计算结束时间
        return self._endDate

    @property
    def test_day(self):  # 测试天数
        return self._test_day

    @property
    def final_equity(self):  # 最终权益
        if not self._fund_record:
            return self.initial_fund
        return self._fund_record[-1]['DynamicEquity']

    @property
    def empty_period(self):  # 空仓周期数
        return self._trade_info['EmptyPeriod']

    @property
    def max_continue_empty(self):  # 最长连续空仓周期
        return self._trade_info['MaxContinuousEmptyPeriod']

    @property
    def max_trade_period(self):  # 最长交易周期（先不计算）
        return np.nan

    @property
    def std_dev(self):  # 标准离差
        # np.std()
        d, N = 0, 0
        for eo in self._orders:
            if (eo['Order']['Direct'] == dBuy and eo['Order']['Offset'] == oCover) \
                    or (eo['Order']['Direct'] == dSell and eo['Order']['Offset'] == oCover) \
                    or (eo['Order']['Direct'] == dBuy and eo['Order']['Offset'] == oCoverT) \
                    or (eo['Order']['Direct'] == dBuy and eo['Order']['Offset'] == oCoverT):
                # 这里的eo['Profit']会多算手续费的吧，如果既有开仓又有平仓的话
                d += np.square(eo['Profit'] - self.mean_profit)
                N += 1
        if N == 0:
            return 0
        else:
            return np.sqrt(d / N)

    @property
    def std_dev_rate(self):  # 标准离差率
        if self._profit['TradeTimes']:
            return self.std_dev / self.mean_profit
        return float('inf')

    @property
    def sharpe(self):  # 夏普比率
        return (self.annualized_simple - 0.03) * np.sqrt(self._test_day / 365) / self.std_dev_rate

    @property
    def plm_lm(self):  # 盈亏总平均/亏损平均
        if self.trade_times and self.total_lose:
            return (self.total_win - self.total_lose) * self.lose_times / (self.total_lose * self.trade_times)
        return float('inf')

    @property
    def max_retrace(self):  # 权益最大回撤
        # 当有一个资金记录的时候，该怎么确定权益最大回撤呢
        if len(self._fund_record) <= 1:
            return 0.0
        return self._profit['MaxRetracement']

    @property
    def max_retrace_start_time(self):  # 权益最大回撤开始时间
        if len(self._fund_record) < 1 or (self._profit['MaxRetracementStartTm'] >= self._profit['MaxRetracementEndTm']):
            return '-'
        return self._profit['MaxRetracementStartTm']

    @property
    def max_retrace_end_time(self):  # 权益最大回撤结束时间
        if len(self._fund_record) < 1 or (self._profit['MaxRetracementStartTm'] >= self._profit['MaxRetracementEndTm']):
            return '-'
        return self._profit['MaxRetracementEndTm']

    @property
    def max_retrace_rate(self):  # 权益最大回撤比
        return self._profit['MaxRetracementRate']

    @property
    def max_retrace_rate_start_time(self):  # 权益最大回测比开始时间
        if len(self._fund_record) < 1 or (
                self._profit['MaxRetracementRateStartTm'] >= self._profit['MaxRetracementRateEndTm']):
            print("111111: ", self._profit["MaxRetracementRateStartTm"])
            print("222222: ", self._profit["MaxRetracementRateEndTm"])
            return '-'
        return self._profit['MaxRetracementRateStartTm']

    @property
    def max_retrace_rate_end_time(self):  # 权益最大回测比结束时间
        if len(self._fund_record) < 1 or (
                self._profit['MaxRetracementRateStartTm'] >= self._profit['MaxRetracementRateEndTm']):
            return '-'
        return self._profit['MaxRetracementRateEndTm']

    @property
    def risky(self):  # 风险率
        return self._profit['Risky']

    @property
    def rate_of_return_risk(self):  # 收益率/风险率
        if self.risky:
            return self._profit["YieldRate"] / self.risky
            # return self.annualized_simple / self.risky
        return float('inf')

    @property
    def returns(self):  # 盈利率
        # if self._runSet['StartFund']:
        #     return self._profit['TotalProfit'] / int(self._runSet['StartFund'])
        # return np.nan
        return self._profit["Returns"]

    @property
    def real_returns(self):  # 实际盈利率（这个不会计算）
        return self.returns

    @property
    def annualized_simple(self):  # 年化单利收益率
        return self.returns * 365 /self._test_day

    @property
    def monthly_simple(self):  # 月化单利收益率
        return self.returns * 30 / self._test_day

    @property
    def annualized_compound(self):  # 年化复利收益率
        if self.final_equity < 0:
            if self._runSet['StartFund'] == 0:
                return float('inf')
            else:
                return '--'
        return (self.final_equity / int(self._runSet['StartFund'])) ** (365 / self._test_day) - 1

    @property
    def monthly_compound(self):  # 月化复利收益率
        if self.final_equity < 0:
            if self._runSet['StartFund'] == 0:
                return float('inf')
            else:
                return '--'
        return (self.final_equity / int(self._runSet['StartFund'])) ** (30 / self._test_day) - 1

    @property
    def win_rate(self):  # 胜率
        # if self._profit['TradeTimes']:
        #     return (self._profit['TradeTimes'] - self._profit['LoseTimes']) / self._profit['TradeTimes']
        try:
            return self._profit["WinRate"]
        except:
            return 0.0

    @property
    def mean_win_lose(self):  # 平均盈利/平均亏损（按照全平交易次数计算）
        if self.win_times and self.lose_times:
            return (self._profit['TotalWin'] * self.lose_times)/(self._profit['TotalLose'] * self.win_times)
        elif self.win_times and not self.lose_times:
            return float('inf')
        else:
            return 0

    @property
    def mean_win_lose_rate(self):  # 平均盈利率/平均亏损率
        if self._profit['SumSingleLoseReturns'] == 0:
            return float('inf')
        elif self._profit['SumSingleWinReturns'] == 0:
            return 0
        else:
            mean_win_returns = self._profit['SumSingleWinReturns'] / self._trade_time_info['TradeWins']
            mean_lose_returns = self._profit['SumSingleLoseReturns'] / self._trade_time_info['TradeLoses']
            return mean_win_returns / mean_lose_returns

    @property
    def net_profit(self):  # 净利润
        return self.total_win - self.total_lose

    @property
    def total_win(self):  # 总盈利
        return self._profit['TotalWin']

    @property
    def total_lose(self):  # 总亏损
        return self._profit['TotalLose']

    @property
    def ratio_of_win_lose(self):  # 总盈利/总亏损
       if self.total_lose:
           return self.total_win / self.total_lose
       else:
           return float('inf')

    @property
    def hold_profit(self):  # 其中持仓浮盈
        return self._profit['HoldProfit']

    @property
    def trade_times(self):  # 交易次数
        return self._trade_time_info['TradeTimes']

    @property
    def win_percentage(self):  # 盈利比率
        if self.trade_times:
            return self.win_times / self.trade_times
        return 0

    @property
    def win_times(self):  # 盈利次数
        return self._trade_time_info['TradeWins']

    @property
    def lose_times(self):  # 亏损次数
        return self._trade_time_info['TradeLoses']

    @property
    def event_times(self):  # 持平次数
        return self._trade_time_info['TradeEvents']

    # @property
    # def mean_trade_period(self):  # 平均交易周期（先不计算）（平均交易周期应该怎么算呢）
    #     return self._
    #
    # @property
    # def(self):  # 平均盈利交易周期（先不计算）
    #     return
    #
    # @property
    # def(self):  # 平均亏损交易周期（先不计算）
    #     return

    @property
    def mean_profit(self):  # 平均盈亏
        if self._profit['TradeTimes']:
            return (self._profit['TotalWin'] - self._profit['TotalLose']) / self._profit['TradeTimes']
        return 0

    @property
    def mean_win(self):  # 平均盈利
        if self._profit['WinTimes']:
            return self._profit['TotalWin'] / self._profit['WinTimes']
        return 0

    @property
    def mean_lose(self):  # 平均亏损
        if self._profit['LoseTimes']:
            return self._profit['TotalLose'] / self._profit['LoseTimes']
        return 0

    @property
    def max_win_continue_days(self):  # 盈利持续最大天数
        return self._trade_info['MaxWinContinueDays']

    @property
    def max_win_continue_days_time(self):  # 盈利持续最大天数出现时间
        return self._trade_info['MaxWinContinueDaysTime']

    @property
    def max_lose_continue_days(self):  # 亏损持续最大天数
        return self._trade_info['MaxLoseContinueDays']

    @property
    def max_lose_continue_days_time(self):  # 亏损持续最大天数出现时间
        return self._trade_info['MaxLoseContinueDaysTime']

    @property
    def max_win_compared_increase_continue_days(self):  # 盈利环比增加持续最大天数
        return self._trade_info['MaxWinComparedIncreaseContinueDays']

    @property
    def max_win_compared_increase_continue_days_time(self):  # 盈利环比增加持续最大天数出现时间
        return self._trade_info['MaxWinComparedIncreaseContinueDaysTime']

    @property
    def max_lose_compared_increase_continue_days(self):  # 亏损环比增加持续最大天数
        return self._trade_info['MaxLoseComparedIncreaseContinueDays']

    @property
    def max_lose_compared_increase_continue_days_time(self):  # 亏损环比增加持续最大天数出现时间
        return self._trade_info['MaxLoseComparedIncreaseContinueDaysTime']

    @property
    def max_equity(self):  # 期间最大权益
        return self._profit['MaxAssets']

    @property
    def min_equity(self):  # 期间最小权益
        return self._profit['MinAssets']

    @property
    def cost(self):  # 手续费
        return self._profit['Cost']

    @property
    def slippage_cost(self):  # 滑点损耗（还没算）
        return self._profit["SlippageLoss"]

    @property
    def turnover(self):  # 成交额
        return self._profit['Turnover']

    def all(self):
        result = {
            'InitialFund': self.initial_fund,
            'Contract': self.contract,
            'Period': self.period,
            'StartTime': self.start_time,
            'EndTime': self.end_time,
            'TestDay': self.test_day,
            'FinalEquity': self.final_equity,
            # 'EmptyPeriod': self.empty_period,
            # 'MaxContinueEmpty': self.max_continue_empty,
            # 'MaxTradePeriod': self.max_trade_period,
            'StdDev': self.std_dev,
            'StdDevRate': self.std_dev_rate,
            'Sharpe': self.sharpe,
            'PlmLm': self.plm_lm,
            'MaxRetrace': self.max_retrace,
            'MaxRetraceStartTime': self.max_retrace_start_time,
            'MaxRetraceTime': self.max_retrace_end_time,
            'MaxRetraceRate': self.max_retrace_rate,
            'MaxRetraceRateStartTime': self.max_retrace_rate_start_time,
            'MaxRetraceRateTime': self.max_retrace_rate_end_time,
            'Risky': self.risky,
            'RateofReturnRisk': self.rate_of_return_risk,
            'Returns': self.returns,
            'RealReturns': self.real_returns,
            'AnnualizedSimple': self.annualized_simple,
            'MonthlySimple': self.monthly_simple,
            'AnnualizedCompound': self.annualized_compound,
            'MonthlyCompound': self.monthly_compound,
            'WinRate':self.win_rate,
            'MeanWinLose': self.mean_win_lose,
            'MeanWinLoseRate': self.mean_win_lose_rate,
            'NetProfit': self.net_profit,
            'TotalWin': self.total_win,
            'TotalLose': self.total_lose,
            'RatioofWinLose': self.ratio_of_win_lose,
            'HoldProfit': self.hold_profit,
            'TradeTimes': self.trade_times,
            'WinPercentage': self.win_percentage,
            'WinTimes': self.win_times,
            'LoseTimes': self.lose_times,
            'EventTimes': self.event_times,
            'MeanProfit': self.mean_profit,
            'MeanWin': self.mean_win,
            'MeanLose': self.mean_lose,
            'MaxWinContinueDays': self.max_win_continue_days,
            'MaxWinContinueDaysTime': self.max_win_continue_days_time,
            'MaxLoseContinueDays': self.max_lose_continue_days,
            'MaxLoseContinueDaysTime': self.max_lose_continue_days_time,
            'MaxWinComparedIncreaseContinueDays': self.max_win_compared_increase_continue_days,
            'MaxWinComparedIncreaseContinueDaysTime': self.max_win_compared_increase_continue_days_time,
            'MaxLoseComparedIncreaseContinueDays': self.max_lose_compared_increase_continue_days,
            'MaxLoseComparedIncreaseContinueDaysTime': self.max_lose_compared_increase_continue_days_time,
            'MaxEquity': self.max_equity,
            'MinEquity': self.min_equity,
            'Cost': self.cost,
            'SlippageCost': self.slippage_cost,
            'Turnover': self.turnover
        }

        return result








