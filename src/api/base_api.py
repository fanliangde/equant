

#BaseApi类定义
class BaseApi(object):
    # 单例模式
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
            #print("create singleton instance of BaseAPI ", cls._instance)
        else:
            #print("BaseAPI instance has existed")
            pass
        return cls._instance

    def __init__(self, strategy = None, dataModel = None):
        self.updateData(strategy, dataModel)

    def updateData(self, strategy, dataModel):
        # 关联的策略
        self._strategy = strategy
        # 子进程数据模型
        self._dataModel = dataModel

    #/////////////////////////K线数据/////////////////////////////
    def Date(self, contractNo, kLineType, kLineValue):
        '''
        【说明】
              当前Bar的日期

        【语法】
              int Date(string contractNo='', char kLineType='', int kLineValue=0)

        【参数】
              contractNo 合约编号, 默认基准合约
              kLineType K线类型，可选值请参阅周期类型枚举函数
              kLineValue K线周期

        【备注】
              简写D,返回格式为YYYYMMDD的整数

        【示例】
              当前Bar对应的日期为2019-03-25，则Date返回值为20190325
        '''
        return self._dataModel.getBarDate(contractNo, kLineType, kLineValue)

    def Time(self, contractNo, kLineType, kLineValue):
        '''
        【说明】
              当前Bar的时间

        【语法】
              float Time(string contractNo='', char kLineType='', int kLineValue=0)

        【参数】
              contractNo 合约编号, 默认基准合约
              kLineType K线类型，可选值请参阅周期类型枚举函数
              kLineValue K线周期

        【备注】
              简写T, 返回格式为0.HHMMSS的浮点数

        【示例】
              当前Bar对应的时间为11:34:21，Time返回值为0.113421
              当前Bar对应的时间为09:34:00，Time返回值为0.0934
              当前Bar对应的时间为11:34:00，Time返回值为0.1134
        '''
        return self._dataModel.getBarTime(contractNo, kLineType, kLineValue)

    def Open(self, contractNo, kLineType, kLineValue):
        '''
        【说明】
              指定合约指定周期的开盘价

        【语法】
              array Open(string contractNo='', char kLineType='', int kLineValue=0)

        【参数】
              contractNo 合约编号, 默认基准合约
              kLineType K线类型，可选值请参阅周期类型枚举函数
              kLineValue K线周期

        【备注】
              简写O, 返回值numpy数组包含截止当前Bar的所有开盘价
              Open()[-1] 表示当前Bar开盘价，Open()[-2]表示上一个Bar开盘价，以此类推

        【示例】
              Open() 获取基准合约的所有开盘价列表
              Open('ZCE|F|SR|905', 'M', 1) 获取白糖905合约1分钟K线的所有开盘价列表
        '''
        return self._dataModel.getBarOpen(contractNo, kLineType, kLineValue)

    def High(self, contractNo, kLineType, kLineValue):
        '''
        【说明】
              指定合约指定周期的最高价

        【语法】
              array High(string contractNo='', char kLineType='', int kLineValue=0)

        【参数】
              contractNo 合约编号,默认基准合约
              kLineType K线类型，可选值请参阅周期类型枚举函数
              kLineValue K线周期

        【备注】
              简写H, Tick时为当时的委托卖价
              返回numpy数组，包括截止当前Bar的所有最高价
              High('ZCE|F|SR|905', 'M', 1)[-1] 表示当前Bar最高价，High('ZCE|F|SR|905', 'M', 1)[-2]表示上一个Bar最高价，以此类推

        【示例】
              无
        '''
        return self._dataModel.getBarHigh(contractNo, kLineType, kLineValue)

    def Low(self, contractNo, kLineType, kLineValue):
        '''
        【说明】
              指定合约指定周期的最低价

        【语法】
              array Low(string contractNo='', char klineType='', int kLineValue=0)

        【参数】
              contractNo 合约编号, 默认基准合约
              kLineType K线类型，可选值请参阅周期类型枚举函数
              kLineValue K线周期

        【备注】
              简写H, Tick时为当时的委托卖价
              返回numpy数组，包括截止当前Bar的所有最低价
              Low()[-1] 表示当前Bar最低价，Low()[-2]表示上一个Bar最低价，以此类推

        【示例】
              无
        '''
        return self._dataModel.getBarLow(contractNo, kLineType, kLineValue)

    def Close(self, contractNo, kLineType, kLineValue):
        '''
        【说明】
              指定合约指定周期的收盘价

        【语法】
              array Close(string contractNo='', char kLineType='', int kLineValue=0)

        【参数】
              contractNo 合约编号, 默认基准合约
              kLineType K线类型，可选值请参阅周期类型枚举函数
              kLineValue K线周期

        【备注】
              简写C, 返回numpy数组，包括截止当前Bar的所有收盘价
              Close()[-1] 表示当前Bar收盘价，Close()[-2]表示上一个Bar收盘价，以此类推

        【示例】
              无
        '''
        return self._dataModel.getBarClose(contractNo, kLineType, kLineValue)

    def OpenD(self, daysAgo, contractNo):
        '''
        【说明】
              指定合约指定周期N天前的开盘价

        【语法】
              float OpenD(int daysAgo=0, string contractNo='')

        【参数】
              daysAgo 第几天前，默认值为0，即当天
              contractNo 合约编号, 默认基准合约

        【备注】
              使用该函数前请确保在策略的initial方法中使用SetBarInterval(contractNo, 'D', 1)方法订阅contractNo合约的日线信息；
              若daysAgo超过了订阅合约contractNo日线数据的样本数量，则返回为-1。

        【示例】
              OpenD(3，'ZCE|F|SR|905') 获取白糖905合约3天前的开盘价
        '''
        return self._dataModel.getOpenD(daysAgo, contractNo)

    def CloseD(self, daysAgo, contractNo):
        '''
        【说明】
              指定合约指定周期N天前的收盘价

        【语法】
              float CloseD(int daysAgo=0, string contractNo='')

        【参数】
              daysAgo 第几天前，默认值为0，即当天
              contractNo 合约编号, 默认基准合约

        【备注】
              使用该函数前请确保在策略的initial方法中使用SetBarInterval(contractNo, 'D', 1)方法订阅contractNo合约的日线信息；
              若daysAgo超过了订阅合约contractNo日线数据的样本数量，则返回为-1。

        【示例】
              CloseD(3，'ZCE|F|SR|905') 获取白糖905合约3天前的收盘价
        '''
        return self._dataModel.getCloseD(daysAgo, contractNo)

    def HighD(self, daysAgo, contractNo):
        '''
        【说明】
              指定合约指定周期N天前的最高价

        【语法】
              float HighD(int daysAgo=0, string contractNo='')

        【参数】
              daysAgo 第几天前，默认值为0，即当天
              contractNo 合约编号, 默认基准合约

        【备注】
              使用该函数前请确保在策略的initial方法中使用SetBarInterval(contractNo, 'D', 1)方法订阅contractNo合约的日线信息；
              若daysAgo超过了订阅合约contractNo日线数据的样本数量，则返回为-1。

        【示例】
              HighD(3，'ZCE|F|SR|905') 获取白糖905合约3天前的最高价
        '''
        return self._dataModel.getHighD(daysAgo, contractNo)

    def LowD(self, daysAgo, contractNo):
        '''
        【说明】
              指定合约指定周期N天前的最低价

        【语法】
              float LowD(int daysAgo=0, string contractNo='')

        【参数】
              daysAgo 第几天前，默认值为0，即当天
              contractNo 合约编号, 默认基准合约

        【备注】
              使用该函数前请确保在策略的initial方法中使用SetBarInterval(contractNo, 'D', 1)方法订阅contractNo合约的日线信息；
              若daysAgo超过了订阅合约contractNo日线数据的样本数量，则返回为-1。

        【示例】
              LowD(3，'ZCE|F|SR|905') 获取白糖905合约3天前的最低价
        '''
        return self._dataModel.getLowD(daysAgo, contractNo)

    def Vol(self, contractNo, kLineType, kLineValue):
        '''
        【说明】
              指定合约指定周期的成交量

        【语法】
              array Vol(string contractNo='', char kLineType='', int kLineValue=0)

        【参数】
              contractNo 合约编号, 默认基准合约
              kLineType K线类型，可选值请参阅周期类型枚举函数
              kLineValue K线周期

        【备注】
              简写V, 返回numpy数组，包括截止当前Bar的所有成交量
              Vol()[-1] 表示当前Bar成交量，Vol()[-2]表示上一个Bar成交量，以此类推

        【示例】
              无
        '''
        return self._dataModel.getBarVol(contractNo, kLineType, kLineValue)

    def OpenInt(self, contractNo, kLineType, kLineValue):
        '''
        【说明】
              指定合约指定周期的持仓量

        【语法】
              numpy.array OpenInt(string contractNo='', char kLineType='', int kLineValue=0)

        【参数】
              contractNo 合约编号, 默认基准合约
              kLineType K线类型，可选值请参阅周期类型枚举函数
              kLineValue K线周期

        【备注】
              返回numpy数组，包括截止当前Bar的所有持仓量
              OpenInt()[-1] 表示当前Bar持仓量，OpenInt()[-2]表示上一个Bar持仓量，以此类推

        【示例】
              无
        '''
        return self._dataModel.getBarOpenInt(contractNo, kLineType, kLineValue)

    def TradeDate(self, contractNo, kLineType, kLineValue):
        '''
        【说明】
              指定合约当前Bar的交易日

        【语法】
              int TradeDate(string contractNo='', char kLineType='', int kLineValue=0)

        【参数】
              contractNo 合约编号, 默认基准合约
              kLineType K线类型，可选值请参阅周期类型枚举函数
              kLineValue K线周期

        【备注】
              返回格式为YYYYMMDD的整数

        【示例】
              当前Bar对应的交易日为2019-03-25，则TradeDate返回值为20190325
        '''
        return self._dataModel.getBarTradeDate(contractNo, kLineType, kLineValue)

    def BarCount(self, contractNo, kLineType, kLineValue):
        '''
        【说明】
              指定合约Bar的总数

        【语法】
              int BarCount(string contractNo='', char kLineType='', int kLineValue=0)

        【参数】
              contractNo 合约编号, 默认基准合约
              kLineType K线类型，可选值请参阅周期类型枚举函数
              kLineValue K线周期

        【备注】
              返回值为整型

        【示例】
              无
        '''
        return self._dataModel.getBarCount(contractNo, kLineType, kLineValue)

    def CurrentBar(self, contractNo, kLineType, kLineValue):
        '''
        【说明】
              指定合约当前Bar的索引值

        【语法】
              int CurrentBar(string contractNo='', char kLineType='', int kLineValue=0)

        【参数】
              contractNo 合约编号, 默认基准合约
              kLineType K线类型，可选值请参阅周期类型枚举函数
              kLineValue K线周期

        【备注】
              第一个Bar返回值为0，其他Bar递增
              当无数据时，不存在当前Bar，返回-1

        【示例】
              无
        '''
        return self._dataModel.getCurrentBar(contractNo, kLineType, kLineValue)

    def CurrentBarEntity(self, contractNo, kLineType, kLineValue):
        return self._dataModel.getCurrentBarEntity(contractNo, kLineType, kLineValue)

    def BarStatus(self, contractNo, kLineType, kLineValue):
        '''
        【说明】
              指定合约当前Bar的状态值

        【语法】
              int BarStatus(string contractNo='', char kLineType='', int kLineValue=0)

        【参数】
              contractNo 合约编号, 默认基准合约
              kLineType K线类型，可选值请参阅周期类型枚举函数
              kLineValue K线周期

        【备注】
              返回值整型, 0表示第一个Bar,1表示中间普通Bar,2表示最后一个Bar

        【示例】
              无
        '''
        return self._dataModel.getBarStatus(contractNo, kLineType, kLineValue)

    def HistoryDataExist(self, contractNo, kLineType, kLineValue):
        '''
        【说明】
              指定合约的历史数据是否有效

        【语法】
              bool HistoryDataExist(string contractNo='', char kLineType='', int kLineValue=0)

        【参数】
              contractNo 合约编号, 默认基准合约
              kLineType K线类型，可选值请参阅周期类型枚举函数
              kLineValue K线周期

        【备注】
              返回Bool值，有效返回True，否则返回False

        【示例】
              无
        '''
        return self._dataModel.isHistoryDataExist(contractNo, kLineType, kLineValue)

    def HisData(self, dataType, kLineType, kLineValue, contractNo, maxLength):
        '''
        【说明】
              获取各种历史数据数组

        【语法】
               numpy.array HisData(enum dataType, enum kLineType='', int kLineValue=0, string contractNo='', int maxLength=100)

        【参数】
              dataType 指定历史数据的种类，可选的枚举函数和相应含义为：
                Enum_Data_Close         : 收盘价
                Enum_Data_Open          : 开盘价
                Enum_Data_High          : 最高价
                Enum_Data_Low           : 最低价
                Enum_Data_Median        : 中间价
                Enum_Data_Typical       : 标准价
                Enum_Data_Weighted      : 加权收盘价
                Enum_Data_Vol           : 成交量
                Enum_Data_Opi           : 持仓量
                Enum_Data_Time          : K线时间
                
              kLineType 指定周期类型，可选的枚举函数和相应含义为：
                Enum_Period_Tick        : 周期类型_分笔
                Enum_Period_Min         : 周期类型_分钟
                Enum_Period_Day         : 周期类型_日线
                
              kLineValue 周期数， 如：5分钟线，周期数就是5；50秒线，周期数为50
                                  要订阅秒线，周期类型选择Enum_Period_tick, 周期数选择大于等于1的整数
              contractNo 合约编号, 为空时取当前合约
              maxLength 定返回历史数据数组的最大长度，默认值为100

        【备注】
              1. 获取前要使用SetBarInterval订阅指定合约，指定周期，指定数量的历史数据，否则HisData取不到数据
              2. 返回numpy数组，获取订阅的maxLength个指定的种类的历史数据
              

        【示例】
              closeList = HisData(Enum_Data_Close(), Enum_Period_Min(), 5, "ZCE|F|SR|906", 1000) # 获取合约ZCE|F|SR|906包含当前Bar在内的之前1000个5分钟线的收盘价
              closeList[-1] # 当前Bar的收盘价
              closeList[-2] # 上一个Bar的收盘价
        '''
        return self._dataModel.getHisData(dataType, kLineType, kLineValue, contractNo, maxLength)

    def HisBarsInfo(self, contractNo, kLineType, kLineValue, maxLength):
        '''
        【说明】
              获取最多maxLength根指定类型的历史K线详细数据

        【语法】
               list HisBarsInfo(string contractNo='', char kLineType='', int kLineValue=0, int maxLength=None)

        【参数】
              contractNo 合约编号, 为空时取当前合约
              kLineType K线类型，可选值请参阅周期类型枚举函数
              kLineValue K线周期
              maxLength 返回历史数据数组的最大长度，默认值为所有K线数据
              若contractNo, kLineType, kLineValue同时不填，则取用于展示的合约及相应的K线类型和周期

        【备注】
              返回列表，包括截止当前Bar的最多maxLength个K线的历史数据
              列表中以字典的形式保存每个K线的数据，字典中每个键值的含义如下:
                ContractNo 合约编号，如'NYMEX|F|CL|1907'
                DateTimeStamp 更新时间，如20190521130800000
                KLineIndex K线索引，如1
                KLineQty K线成交量，如18
                TotalQty 总成交量，如41401
                KLineSlice K线周期， 如1
                KLineType K线类型，如'M'
                OpeningPrice 开盘价， 如63.5
                LastPrice 收盘价，如63.49
                SettlePrice 结算价，如63.21
                HighPrice 最高价，如63.5
                LowPrice 最低价， 如63.49
                PositionQty 总持仓，如460816
                TradeDate 交易日期，如20190521

        【示例】
              barList = HisBarsInfo("ZCE|F|SR|906", Enum_Period_Min(), 5, 1000) # 获取合约ZCE|F|SR|906包含当前Bar在内的之前1000个历史5分钟K线的数据
              barInfo = barList[-1] # 当前Bar的详细信息
        '''
        return self._dataModel.getHisBarsInfo(contractNo, kLineType, kLineValue, maxLength)

    #/////////////////////////即时行情/////////////////////////////
    def Q_UpdateTime(self, contractNo):
        '''
        【说明】
              获取指定合约即时行情的更新时间

        【语法】
              string Q_UpdateTime(string contractNo='')

        【参数】
              contractNo 合约编号, 默认当前合约

        【备注】
              返回格式为"YYYYMMDDHHMMSSmmm"的字符串，
              若指定合约即时行情的更新时间为2019-05-21 10:07:46.000，则该函数放回为20190521100746000

        【示例】
              无
        '''
        return self._dataModel.getQUpdateTime(contractNo)

    def Q_AskPrice(self, contractNo='', level=1):
        '''
        【说明】
              合约最优卖价

        【语法】
              float Q_AskPrice(string contractNo='', int level=1)

        【参数】
              contractNo 合约编号, 默认当前合约;level 档位数,默认1档

        【备注】
              返回浮点数, 可获取指定合约,指定深度的最优卖价

        【示例】
              无
        '''
        return self._dataModel.getQAskPrice(contractNo, level)

    def Q_AskPriceFlag(self, contractNo=''):
        '''
        【说明】
              卖盘价格变化标志

        【语法】
              int Q_AskPriceFlag(string contractNo='')

        【参数】
              contractNo 合约编号, 默认当前合约

        【备注】
              返回整型，1为上涨，-1为下跌，0为不变

        【示例】
              无
        '''
        return self._dataModel.getQAskPriceFlag(contractNo)

    def Q_AskVol(self, contractNo='', level=1):
        '''
        【说明】
              合约最优卖量

        【语法】
              float Q_AskVol(string contractNo='', int level=1)

        【参数】
              contractNo 合约编号, 默认当前合约;level 档位数,默认1档

        【备注】
              返回浮点数, 可获取指定合约,指定深度的最优卖量

        【示例】
              无
        '''
        return self._dataModel.getQAskVol(contractNo, level)

    def Q_AvgPrice(self, contractNo=''):
        '''
        【说明】
              当前合约的实时均价

        【语法】
              float Q_AvgPrice(string contractNo='')

        【参数】
              contractNo 合约编号, 默认当前合约

        【备注】
              返回浮点数，返回实时均价即结算价

        【示例】
              无
        '''
        return self._dataModel.getQAvgPrice(contractNo)

    def Q_BidPrice(self, contractNo='', level=1):
        '''
        【说明】
              合约最优买价

        【语法】
              float Q_BidPrice(string contractNo='', int level=1)

        【参数】
              contractNo 合约编号, 默认当前合约;level 档位数,默认1档

        【备注】
              返回浮点数, 可获取指定合约,指定深度的最优买价

        【示例】
              无
        '''
        return self._dataModel.getQBidPrice(contractNo, level)

    def Q_BidPriceFlag(self, contractNo=''):
        '''
        【说明】
              买盘价格变化标志

        【语法】
              int Q_AskPriceFlag(string contractNo='')

        【参数】
              contractNo 合约编号,  默认当前合约

        【备注】
              返回整型，1为上涨，-1为下跌，0为不变

        【示例】
              无
        '''
        return self._dataModel.getQBidPriceFlag(contractNo)


    def Q_BidVol(self, contractNo='', level=1):
        '''
        【说明】
              合约最优买量

        【语法】
              float Q_BidVol(string contractNo='', int level=1)

        【参数】
              contractNo 合约编号, 默认当前合约;level 档位数,默认1档

        【备注】
              返回浮点数, 可获取指定合约,指定深度的最优买量

        【示例】
              无
        '''
        return self._dataModel.getQBidVol(contractNo, level)

    def Q_Close(self, contractNo=''):
        '''
        【说明】
              当日收盘价，未收盘则取昨收盘

        【语法】
              float Q_Close(string contractNo='')

        【参数】
              contractNo 合约编号,默认当前合约

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getQClose(contractNo)

    def Q_High(self, contractNo=''):
        '''
        【说明】
              当日最高价

        【语法】
              float Q_High(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getQHigh(contractNo)

    def Q_HisHigh(self, contractNo=''):
        '''
        【说明】
              历史最高价

        【语法】
              float Q_HisHigh(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getQHisHigh(contractNo)

    def Q_HisLow(self, contractNo=''):
        '''
        【说明】
              历史最低价

        【语法】
              float Q_HisLow(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getQHisLow(contractNo)

    def Q_InsideVol(self, contractNo=''):
        '''
        【说明】
              内盘量

        【语法】
              float Q_InsideVol(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数, 买入价成交为内盘

        【示例】
              无
        '''
        return self._dataModel.getQInsideVol(contractNo)

    def Q_Last(self, contractNo=''):
        '''
        【说明】
              最新价

        【语法】
              float Q_Last(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getQLast(contractNo)

    def Q_LastDate(self, contractNo=''):
        '''
        【说明】
              最新成交日期

        【语法】
              int Q_LastDate(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回当前公式应用商品的最新成交日期，格式为YYYYMMDD整数表示的日期。

        【示例】
              无
        '''
        return self._dataModel.getQLastDate(contractNo)

    def Q_LastTime(self, contractNo=''):
        '''
        【说明】
              最新成交时间

        【语法】
              float Q_LastTime(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回当前公式应用商品的最新成交时间，以格式为0.HHMMSSmmm浮点数表示的时间。


        【示例】
              无
        '''
        return self._dataModel.getQLastTime(contractNo)

    def Q_LastVol(self, contractNo=''):
        '''
        【说明】
              现手

        【语法】
              float Q_LastVol(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数，单位为手

        【示例】
              无
        '''
        return self._dataModel.getQLastVol(contractNo)

    def Q_Low(self, contractNo=''):
        '''
        【说明】
              当日最低价

        【语法】
              float Q_Low(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getQLow(contractNo)

    def Q_LowLimit(self, contractNo=''):
        '''
        【说明】
              当日跌停板价

        【语法】
              float Q_LowLimit(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getQLowLimit(contractNo)

    def Q_Open(self, contractNo=''):
        '''
        【说明】
              当日开盘价

        【语法】
              float Q_Open(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getQOpen(contractNo)

    def Q_OpenInt(self, contractNo=''):
        '''
        【说明】
              持仓量

        【语法】
              float Q_OpenInt(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数, 单位为手

        【示例】
              无
        '''
        return self._dataModel.getQOpenInt(contractNo)

    def Q_OpenIntFlag(self, contractNo=''):
        '''
        【说明】
              持仓量变化标志

        【语法】
              int  Q_OpenIntFlag(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回整型, 1为增加，-1为下降，0为不变

        【示例】
              无
        '''
        return self._dataModel.getQOpenIntFlag(contractNo)

    def Q_OutsideVol(self, contractNo=''):
        '''
        【说明】
              外盘量

        【语法】
              float Q_OutsideVol(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数，卖出价成交为外盘

        【示例】
              无
        '''
        return self._dataModel.getQOutsideVol(contractNo)

    def Q_PreOpenInt(self, contractNo=''):
        '''
        【说明】
              昨持仓量

        【语法】
              float Q_PreOpenInt(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getQPreOpenInt(contractNo)

    def Q_PreSettlePrice(self, contractNo=''):
        '''
        【说明】
              昨结算

        【语法】
              float Q_PreSettlePrice(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getQPreSettlePrice(contractNo)

    def Q_PriceChg(self, contractNo=''):
        '''
        【说明】
              当日涨跌

        【语法】
              float Q_PriceChg(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getQPriceChg(contractNo)


    def Q_PriceChgRadio(self, contractNo=''):
        '''
        【说明】
              当日涨跌幅

        【语法】
              float Q_PriceChgRadio(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getQPriceChgRadio(contractNo)

    def Q_TodayEntryVol(self, contractNo=''):
        '''
        【说明】
              当日开仓量

        【语法】
              float Q_TodayEntryVol(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getQTodayEntryVol(contractNo)

    def Q_TodayExitVol(self, contractNo=''):
        '''
        【说明】
              当日平仓量

        【语法】
              float Q_TodayExitVol(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getQTodayExitVol(contractNo)

    def Q_TotalVol(self, contractNo=''):
        '''
        【说明】
              当日成交量

        【语法】
              float Q_TotalVol(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getQTotalVol(contractNo)

    def Q_TurnOver(self, contractNo=''):
        '''
        【说明】
              当日成交额

        【语法】
              float Q_TurnOver(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getQTurnOver(contractNo)

    def Q_UpperLimit(self, contractNo=''):
        '''
        【说明】
              当日涨停板价

        【语法】
              float Q_UpperLimit(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getQUpperLimit(contractNo)
        
    def Q_TheoryPrice(self, contractNo=''):
        '''
        【说明】
              当日期权理论价

        【语法】
              float Q_TheoryPrice(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数, 不存在时返回None

        【示例】
              无
        '''
        return self._dataModel.getQTheoryPrice(contractNo)
        
    def Q_Sigma(self, contractNo=''):
        '''
        【说明】
              当日期权波动率

        【语法】
              float Q_Sigma(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数, 不存在时返回None

        【示例】
              无
        '''
        return self._dataModel.getQSigma(contractNo)
        
    def Q_Delta(self, contractNo=''):
        '''
        【说明】
              当日期权Delta

        【语法】
              float Q_Delta(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数, 不存在时返回None

        【示例】
              无
        '''
        return self._dataModel.getQDelta(contractNo)
        
    def Q_Gamma(self, contractNo=''):
        '''
        【说明】
              当日期权Gamma

        【语法】
              float Q_Gamma(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数, 不存在时返回None

        【示例】
              无
        '''
        return self._dataModel.getQGamma(contractNo)
        
    def Q_Vega(self, contractNo=''):
        '''
        【说明】
              当日期权Vega

        【语法】
              float Q_Vega(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数, 不存在时返回None

        【示例】
              无
        '''
        return self._dataModel.getQVega(contractNo)
        
    def Q_Theta(self, contractNo=''):
        '''
        【说明】
              当日期权Theta

        【语法】
              float Q_Theta(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数, 不存在时返回None

        【示例】
              无
        '''
        return self._dataModel.getQTheta(contractNo)
        
    def Q_Rho(self, contractNo=''):
        '''
        【说明】
              当日期权Rho

        【语法】
              float Q_Rho(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回浮点数, 不存在时返回None

        【示例】
              无
        '''
        return self._dataModel.getQRho(contractNo)

    def QuoteDataExist(self, contractNo=''):
        '''
        【说明】
              行情数据是否有效

        【语法】
              Bool QuoteDataExist(string contractNo='')

        【参数】
              contractNo 合约编号

        【备注】
              返回Bool值，数据有效返回True，否则False

        【示例】
              无
        '''
        return self._dataModel.getQuoteDataExist(contractNo)
        
    def CalcTradeDate(self, contractNo='', dateTimeStamp=0):
        '''
        【说明】
              计算指定合约，指定时间戳所属的交易日

        【语法】
              int CalcTradeDate(string contractNo='', int dateTimeStamp=0)

        【参数】
              contractNo 合约编号，默认基准合约
              dateTimeStamp  时间戳，默认0

        【备注】
              正常情况，返回指定合约指定时间戳所属的交易日
              当返回值为-1时，表示合约参数有误
              当返回值为-2时，表示时间戳参数有误，比如传入非交易时段时间戳

        【示例】
              CalcTradeDate(dateTimeStamp=20190830110000000)
              CalcTradeDate('ZCE|F|SR|001', 20190830110000000)
        '''
        return self._dataModel.getTradeDate(contractNo, dateTimeStamp)

    #/////////////////////////策略交易/////////////////////////////
    def Buy(self, orderQty, orderPrice, contractNo, needCover, userNo):
        '''
        【说明】
              产生一个多头建仓操作

        【语法】
              void Buy(int orderQty=0, float orderPrice=0, string contractNo=None, bool needCover = True, string userNo='')

        【参数】
              orderQty 买入数量，为整型值，默认为0；
              orderPrice 买入价格，为浮点数，默认为0；
              contract 合约代码，为字符串，默认使用基准合约；
              needCover 是否先清掉方向持仓，默认为True；
              userNo 用户编号，为字符串，默认使用界面选定用户编号。

        【备注】
              产生一个多头建仓操作，无返回值。
              该函数仅用于多头建仓，其处理规则如下：
              如果当前持仓状态为持平，该函数按照参数进行多头建仓。
              如果当前持仓状态为空仓，该函数平掉所有空仓，同时按照参数进行多头建仓，两个动作同时发出。
              如果当前持仓状态为多仓，该函数将继续建仓，但具体是否能够成功建仓要取决于系统中关于连续建仓的设置，以及资金，最大持仓量等限制。
              当委托价格超出k线的有效范围，在历史数据上，将会取最接近的有效价格发单；在实盘中，将会按照实际委托价格发单。
              例如：当前k线有效价格为50-100，用buy(1,10)发单，委托价将以50发单。

        【示例】
              在当前没有持仓或者持有多头仓位的情况下：
              Buy(50,10.2) 表示用10.2的价格买入50张合约。
              Buy(10,Close) 表示用当前Bar收盘价买入10张合约，马上发送委托。
              Buy(5,0) 表示用现价买入5张合约，马上发送委托。
              Buy(0,0) 表示用现价按交易设置中设置的手数,马上发送委托。

              在当前持有空头仓位的情况下：
              Buy(10,Close) 表示平掉所有空仓，并用当前Bar收盘价买入10张合约，马上发送委托。
        '''
        return self._dataModel.setBuy(userNo, contractNo, orderQty, orderPrice, needCover)

    def BuyToCover(self, orderQty, orderPrice, contractNo, userNo, coverFlag):
        '''
        【说明】
              产生一个空头平仓操作

        【语法】
              void BuyToCover(int orderQty=0, float orderPrice=0, string contractNo=None, string userNo='', char coverFlag = 'A')

        【参数】
              orderQty 买入数量，为整型值，默认为0；
              orderPrice 买入价格，为浮点数，默认为0；
              contract 合约代码，为字符串，默认使用基准合约；
              userNo 用户编号，为字符串，默认使用界面选定用户编号。
              coverFlag 平今平昨标志（此参数仅对SHFE和INE有效）
                        默认设置为'A'自适应(先平昨再平今)
                        若平昨，则需设置为'C'
                        若平今，则需设置为'T'

        【备注】
              产生一个空头平仓操作，无返回值。
              该函数仅用于空头平仓，其处理规则如下：
              如果当前持仓状态为持平，该函数不执行任何操作。
              如果当前持仓状态为多仓，该函数不执行任何操作。
              如果当前持仓状态为空仓，如果此时Share使用默认值，该函数将平掉所有空仓，达到持平的状态，否则只平掉参数Share的空仓。
              当委托价格超出k线的有效范围，在历史数据上，将会取最接近的有效价格发单；在实盘中，将会按照实际委托价格发单。
              例如：当前k线有效价格为50-100，用BuyToCover(1,10)发单，委托价将以50发单。

        【示例】
              在持有空头仓位的情况下：
              BuyToCover(50,10.2) 表示用10.2的价格空头买入50张合约。
              BuyToCover(10,Close) 表示用当前Bar收盘价空头买入10张合约，马上发送委托。
              BuyToCover(5,0) 表示用现价空头买入5张合约)，马上发送委托。
              BuyToCover(0,0) 表示用现价按交易设置中的设置,马上发送委托。
        '''
        return self._dataModel.setBuyToCover(userNo, contractNo, orderQty, orderPrice, coverFlag)

    def Sell(self, orderQty, orderPrice, contractNo, userNo, coverFlag):
        '''
        【说明】
              产生一个多头平仓操作

        【语法】
              void Sell(int orderQty=0, float orderPrice=0, string contractNo=None, string userNo='', char coverFlag = 'A')

        【参数】
              orderQty 买入数量，为整型值，默认为0；
              orderPrice 买入价格，为浮点数，默认为0；
              contract 合约代码，为字符串，默认使用基准合约；
              userNo 用户编号，为字符串，默认使用界面选定用户编号。
              coverFlag 平今平昨标志（此参数仅对SHFE和INE有效）
                        默认设置为'A'自适应(先平昨再平今)
                        若平昨，则需设置为'C'
                        若平今，则需设置为'T'

        【备注】
              产生一个多头平仓操作，无返回值。
              该函数仅用于多头平仓，其处理规则如下：
              如果当前持仓状态为持平，该函数不执行任何操作。
              如果当前持仓状态为空仓，该函数不执行任何操作。
              如果当前持仓状态为多仓，如果此时Share使用默认值，该函数将平掉所有多仓，达到持平的状态，否则只平掉参数Share的多仓。
              当委托价格超出k线的有效范围，在历史数据上，将会取最接近的有效价格发单；在实盘中，将会按照实际委托价格发单。
              例如：当前k线有效价格为50-100，用sell(1,10)发单，委托价将以50发单。

        【示例】
              在持有多头仓位的情况下：
              Sell(50,10.2) 表示用10.2的价格卖出50张合约。
              Sell(10,Close) 表示用当前Bar收盘价卖出10张合约，马上发送委托。
              Sell(5,0) 表示用现价卖出5张合约，马上发送委托。
              Sell(0,0) 表示用现价按交易设置中的设置,马上发送委托。
        '''
        return self._dataModel.setSell(userNo, contractNo, orderQty, orderPrice, coverFlag)

    def SellShort(self, orderQty, orderPrice, contractNo, needCover, userNo):
        '''
        【说明】
              产生一个空头建仓操作

        【语法】
              void SellShort(int orderQty=0, float orderPrice=0, string contractNo=None, bool needCover = True, string userNo='')

        【参数】
              orderQty 买入数量，为整型值，默认为0；
              orderPrice 买入价格，为浮点数，默认为0；
              contract 合约代码，为字符串，默认使用基准合约；
              needCover 是否先清掉方向持仓，默认为True；
              userNo 用户编号，为字符串，默认使用界面选定用户编号。

        【备注】
              产生一个空头建仓操作，无返回值。
              该函数仅用于空头建仓，其处理规则如下：
              如果当前持仓状态为持平，该函数按照参数进行空头建仓。
              如果当前持仓状态为多仓，该函数平掉所有多仓，同时按照参数进行空头建仓，两个动作同时发出
              如果当前持仓状态为空仓，该函数将继续建仓，但具体是否能够成功建仓要取决于系统中关于连续建仓的设置，以及资金，最大持仓量等限制。
              当委托价格超出k线的有效范围，在历史数据上，将会取最接近的有效价格发单；在实盘中，将会按照实际委托价格发单。
              例如：当前k线有效价格为50-100，用SellShort(1,10)发单，委托价将以50发单。

        【示例】
              在没有持仓或者持有空头持仓的情况下：
              SellShort(50,10.2) 表示用10.2的价格空头卖出50张合约。
              SellShort(10,Close) 表示用当前Bar收盘价空头卖出10张合约，马上发送委托。
              SellShort(5,0) 表示用现价空头卖出5张合约，马上发送委托。
              SellShort(0,0) 表示用现价按交易设置中设置的手数,马上发送委托。
              在MarketPosition=1的情况下：（当前持有多头持仓）
              SellShort(10,Close) 表示平掉所有多头仓位，并用当前Bar收盘价空头卖出10张合约，马上发送委托。

        '''
        return self._dataModel.setSellShort(userNo, contractNo, orderQty, orderPrice, needCover)

    def StartTrade(self):
        '''
        【说明】
              开启实盘交易。

        【语法】
              void StartTrade()

        【参数】
              无

        【备注】
              在策略运行时，使用StopTrade可以暂时停止策略向实盘发单，通过该方法可以开启策略向实盘发单的功能。

        【示例】
              无

        '''
        return self._dataModel.setStartTrade()

    def StopTrade(self):
        '''
        【说明】
              暂停实盘交易。

        【语法】
              void StopTrade()

        【参数】
              无

        【备注】
              在策略运行时，使用StopTrade可以暂时停止策略向实盘发单。

        【示例】
              无

        '''
        return self._dataModel.setStopTrade()

    def IsTradeAllowed(self):
        '''
        【说明】
              是否允许实盘交易。

        【语法】
              bool IsTradeAllowed()

        【参数】
              无

        【备注】
              获取策略是否可以向实盘发单的布尔值，策略实盘运行时并且允许向实盘发单返回True，否则返回False。

        【示例】
              无

        '''
        return self._dataModel.isTradeAllowed()

    #/////////////////////////属性函数/////////////////////////////
    def BarInterval(self):
        '''
        【说明】
              返回界面合约图表K线周期数值

        【语法】
              int BarInterval()

        【参数】
              无

        【备注】
              返回界面图表K线周期数值，通常和BarType一起使用进行数据周期的判别

        【示例】
              当前数据周期为1日线，BarInterval等于1；
              当前数据周期为22日线，BarInterval等于22；
              当前数据周期为60分钟线，BarInterval等于60；
              当前数据周期为1TICK线，BarInterval等于1；br> 当前数据周期为5000量线，BarInterval等于5000。
        '''
        return self._dataModel.getBarInterval()
        
    def BarType(self):
        '''
        【说明】
              返回界面合约K线图表周期类型字符

        【语法】
              char BarType()

        【参数】
              无

        【备注】
              返回值为字符，通常和BarInterval一起使用进行数据周期的判别
              返回值如下定义：
              T 分笔
              S 秒线
              M 分钟
              D 日线

        【示例】
              当前数据周期为22日线，BarType等于D；
              当前数据周期为60分钟线，BarType等于M；
              当前数据周期为1TICK线，BarType等于T。
        '''
        return self._dataModel.getBarType()
        
    def BidAskSize(self, contractNo):
        '''
        【说明】
              买卖盘个数

        【语法】
              int BidAskSize(string contractNo='')

        【参数】
              contractNo: 合约编号，为空时，取基准合约。

        【备注】
              返回整型

        【示例】
              郑商所白糖的买卖盘个数为5个，因此其BidAskSize等于5；
              郑商所棉花的买卖盘个数为1个，因此其BidAskSize等于1。 
        '''
        return self._dataModel.getBidAskSize(contractNo)

    def CanTrade(self, contractNo):
        '''
        【说明】
              合约是否支持交易

        【语法】
              Bool CanTrade(string contractNo='')

        【参数】
              contractNo: 合约编号，为空时，取基准合约。

        【备注】
              返回Bool值，支持返回True，否则返回False

        【示例】
              无 
        '''
        return self._dataModel.getCanTrade(contractNo)
        
    def ContractUnit(self, contractNo):
        '''
        【说明】
              每张合约包含的基本单位数量, 即每手乘数

        【语法】
              int ContractUnit(string contractNo='')

        【参数】
              contractNo: 合约编号，为空时，取基准合约。

        【备注】
              返回整型，1张合约包含多少标的物。

        【示例】
              无 
        '''
        return self._dataModel.getContractUnit(contractNo)
        
    def ExchangeName(self, contractNo):
        '''
        【说明】
              合约对应交易所名称代码

        【语法】
              string ExchangeName(string contractNo='')

        【参数】
              contractNo: 合约编号，为空时，取基准合约。

        【备注】
              返回字符串

        【示例】
              # 郑商所下各合约的交易所名称为："ZCE"
              ExchangeName("ZCE|Z|TA|MAIN")
        '''
        return self._dataModel.getExchangeName(contractNo)
        
    def ExchangeTime(self, exchangeNo):
        '''
        【说明】
              交易所时间

        【语法】
              string ExchangeTime(string exchangeNo)

        【参数】
              exchangeNo: 交易所编号，例如"ZCE","DCE","SHFE","CFFEX","INE"

        【备注】
              返回字符串 "2019-07-05 22:11:00"
              当交易所编号为无效编号时，返回空字符串
              该函数返回的时间是系统时间

        【示例】
              ExchangeTime('ZCE')
        '''
        return self._dataModel.getExchangeTime(exchangeNo)
        
    def ExchangeStatus(self, exchangeNo):
        '''
        【说明】
              交易所状态

        【语法】
              string ExchangeStatus(string exchangeNo)

        【参数】
              exchangeNo: 交易所编号，例如"ZCE","DCE","SHFE","CFFEX","INE"

        【备注】
              返回字符
              'N'   未知状态
              'I'   正初始化
              'R'   准备就绪
              '0'   交易日切换
              '1'   竞价申报
              '2'   竞价撮合
              '3'   连续交易
              '4'   交易暂停
              '5'   交易闭市  
              '6'   竞价暂停
              '7'   报盘未连
              '8'   交易未连
              '9'   闭市处理

              该方法仅适用于内盘交易所，对外盘交易所返回值为空字符串。

        【示例】
              ExchangeStatus('ZCE')
        '''
        return self._dataModel.getExchangeStatus(exchangeNo)
        
    def CommodityStatus(self, commodityNo):
        '''
        【说明】
              品种或合约交易状态

        【语法】
              string CommodityStatus(string commodityNo|string contractNo)

        【参数】
              commodityNo: 品种编号，例如"ZCE|F|SR", "DCE|F|I"
                或者
              contractNo: 合约编号，例如"ZCE|F|SR|001", "DCE|F|I|2001"
        【备注】
              返回字符
              'N'   未知状态
              'I'   正初始化
              'R'   准备就绪
              '0'   交易日切换
              '1'   竞价申报
              '2'   竞价撮合
              '3'   连续交易
              '4'   交易暂停
              '5'   交易闭市  
              '6'   竞价暂停
              '7'   报盘未连
              '8'   交易未连
              '9'   闭市处理

              该方法仅适用于内盘品种，对外盘品种返回值为空字符串。

        【示例】
              CommodityStatus('ZCE|F|SR')
        '''
        return self._dataModel.getCommodityStatus(commodityNo)
        
        
    def ExpiredDate(self, contractNo):
        '''
        【说明】
              合约最后交易日

        【语法】
              string ExpiredDate(string contractNo='')

        【参数】
              contractNo: 合约编号，为空时，取基准合约。

        【备注】
              返回字符串

        【示例】
              无
        '''
        return self._dataModel.getExpiredDate()
        
    def GetSessionCount(self, contractNo):
        '''
        【说明】
              获取交易时间段的个数

        【语法】
              int GetSessionCount(string contractNo='')

        【参数】
              contractNo: 合约编号，为空时，取基准合约。

        【备注】
              返回整型

        【示例】
              无
        '''
        return self._dataModel.getGetSessionCount(contractNo)

    def GetSessionEndTime(self, contractNo, index):
        '''
        【说明】
              获取指定交易时间段的结束时间。

        【语法】
              float GetSessionEndTime(string contractNo='', int index=0)

        【参数】
              contractNo 合约编号，为空时，取基准合约。
              index 交易时间段的索引值, 从0开始。

        【备注】
              返回指定合约的交易时间段结束时间，格式为0.HHMMSS的浮点数。

        【示例】
              contractNo = "ZCE|F|SR|905"
              sessionCount = GetSessionCount(contractNo)
              for i in range(0, sessionCount-1):
                sessionEndTime = GetSessionEndTime(contractNo, i)

              由于合约ZCE|F|TA|908的第三段交易结束时间为11:30:00，
              所以GetSessionEndTime("ZCE|F|TA|908", 2)的返回值为0.113
        '''
        return self._dataModel.getSessionEndTime(contractNo, index)

    def GetSessionStartTime(self, contractNo, index):
        '''
        【说明】
              获取合约指定交易时间段的开始时间。

        【语法】
              float GetSessionStartTime(string contractNo='', int index=0)

        【参数】
              contractNo 合约编号，为空时，取基准合约。
              index 交易时间段的索引值, 从0开始。

        【备注】
              返回指定合约的交易时间段开始时间，格式为0.HHMMSS的浮点数。

        【示例】
              无
        '''
        return self._dataModel.getGetSessionStartTime(contractNo, index)

    def GetNextTimeInfo(self, contractNo, timeStamp):
        '''
        【说明】
              获取指定合约指定时间点的下一个时间点及交易状态。

        【语法】
              dict GetNextTimeInfo(string contractNo, float timeStamp)

        【参数】
              contractNo 合约编号。
              timeStr 指定的时间点，格式为0.HHMMSS。

        【备注】
              返回时间字典，结构如下：
              {
                'Time' : 0.21,
                'TradeState' : 3
              }
              其中Time对应的值表示指定时间timeStamp的下一个时间点，返回指定合约的交易时间段开始时间，格式为0.HHMMSS的浮点数。
              TradeState表示对应时间点的交易状态，数据类型为字符，可能出现的值及相应的状态含义如下：
                1 : 集合竞价
                2 : 集合竞价撮合
                3 : 连续交易
                4 : 暂停
                5 : 闭市
                6 : 闭市处理时间
                0 : 交易日切换时间
                N : 未知状态
                I : 正初始化
                R : 准备就绪
              异常情况返回为空字典：{}

        【示例】
              GetNextTimeInfo('SHFE|F|CU|1907', 0.22) # 获取22:00:00后下一个时间点的时间和交易状态
              获取当前时间下一个时间点的时间和交易状态
              import time # 需要在策略头部添加time库
              curTime = time.strftime('0.%H%M%S',time.localtime(time.time()))
              timeInfoDict = GetNextTimeInfo("SHFE|F|CU|1907", curTime)
        '''
        return self._dataModel.getNextTimeInfo(contractNo, timeStamp)

    def TradeSessionBeginTime(self, contractNo, tradeDate, index):
        '''
        【说明】
              获取指定合约指定交易日的指定交易时间段的开始时间戳。

        【语法】
              int TradeSessionBeginTime(string contractNo='', int tradeDate=0, int index=0)

        【参数】
              contractNo 合约编号，为空时，取基准合约。
              tradeDate  指定的交易日, 默认0
              index 交易时间段的索引值, 从0开始，默认取第一个交易时段。

        【备注】
              返回时间戳类型, 如20190904213000000

        【示例】
              无
        '''
        return self._dataModel.getTradeSessionBeginTime(contractNo, tradeDate, index)
        
    def TradeSessionEndTime(self, contractNo, tradeDate, index):
        '''
        【说明】
              获取指定合约指定交易日的指定交易时间段的结束时间戳。

        【语法】
              int TradeSessionEndTime(string contractNo='', int tradeDate=0, int index=-1)

        【参数】
              contractNo 合约编号，为空时，取基准合约。
              tradeDate  指定的交易日, 默认0
              index 交易时间段的索引值, 从0开始，默认取最后一个交易时段。

        【备注】
              返回时间戳类型, 如20190904213000000

        【示例】
              无
        '''
        return self._dataModel.getTradeSessionEndTime(contractNo, tradeDate, index)

    def CurrentDate(self):
        '''
        【说明】
              公式处于历史阶段时，返回历史K线当时的日期。处于实时阶段时，返回客户端所在操作系统的日期

        【语法】
              int CurrentDate()

        【参数】
              无

        【备注】
              格式为YYMMDD的整数。

        【示例】
              如果当前日期为2019-7-13，CurrentDate返回值为20190713
        '''
        return self._dataModel.getCurrentDate()
        
    def CurrentTime(self):
        '''
        【说明】
              公式处于历史阶段时，返回历史K线当时的时间。处于实时阶段时，返回客户端所在操作系统的时间

        【语法】
              float CurrentTime()

        【参数】
              无

        【备注】
              格式为0.HHMMSS的浮点数。

        【示例】
              如果当前时间为11:34:21，CurrentTime返回值为0.113421。
        '''
        return self._dataModel.getCurrentTime()
        
    def TimeDiff(self, datetime1, datetime2):
        '''
        【说明】
              返回两个时间之间的间隔秒数，忽略日期差异

        【语法】
              int TimeDiff(self, float datetime1, float datetime2)

        【参数】
              datetime1 输入较早时间
              datetime2 输入较晚个时间

        【备注】
              该函数只计算两个时间之间的差值，不考虑两个参数的日期
              若输入参数不为float类型，则函数返回值为0

        【示例】
              TimeDiff(20190404.104110,20110404.104120);返回两时间相差10秒；
              TimeDiff(20190404.1041,20110404.1043);返回两时间相差2分钟，即120秒
        '''
        return self._dataModel.getTimeDiff(datetime1, datetime2)

    def IsInSession(self, contractNo):
        '''
        【说明】
              操作系统的当前时间是否为指定合约的交易时间。

        【语法】
              bool IsInSession(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基础合约。

        【备注】
              获取操作系统的当前时间，是否为指定合约的交易时间。

        【示例】
              如果当前时间为11:34:21，IsInSession("ZCE|F|TA|909")返回值为False。
        '''
        return self._dataModel.isInSession(contractNo)

    def MarginRatio(self, contractNo):
        '''
        【说明】
              获取合约默认保证金比率

        【语法】
              float MarginRatio(string contractNo='')

        【参数】
              contractNo 合约编号，为空时，取基准合约。

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getMarginRatio(contractNo)
        
    def MaxBarsBack(self):
        '''
        【说明】
              最大回溯Bar数

        【语法】
              float  MaxBarsBack()

        【参数】
              无

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getMaxBarsBack()
        
    def MaxSingleTradeSize(self):
        '''
        【说明】
              单笔交易限量

        【语法】
              int MaxSingleTradeSize()

        【参数】
              无

        【备注】
              返回整型，单笔交易限量，对于不能交易的商品，返回-1，对于无限量的商品，返回0

        【示例】
              无
        '''
        return self._dataModel.getMaxSingleTradeSize()

    def PriceTick(self, contractNo):
        '''
        【说明】
              合约最小变动价

        【语法】
              int PriceTick(string contractNo='')

        【参数】
              contractNo 合约编号，为空时，取基准合约。

        【备注】
              无

        【示例】
              沪铝的最小变动价为5，因此其PriceTick等于5
        '''
        return self._dataModel.getPriceTick(contractNo)
        
    def OptionStyle(self, contractNo):
        '''
        【说明】
              期权类型，欧式还是美式

        【语法】
              int OptionStyle(string contractNo='')

        【参数】
              contractNo 合约编号，为空时，取基准合约。

        【备注】
              返回整型，0为欧式，1为美式

        【示例】
              无
        '''
        return self._dataModel.getOptionStyle(contractNo)
        
    def OptionType(self, contractNo):
        '''
        【说明】
              返回期权的类型，是看涨还是看跌期权

        【语法】
              int OptionType(string contractNo='')

        【参数】
              contractNo 合约编号，为空时，取基准合约。

        【备注】
              返回整型，0为看涨，1为看跌， -1为异常。

        【示例】
              无
        '''
        return self._dataModel.getOptionType(contractNo)
        
    def PriceScale(self, contractNo):
        '''
        【说明】
              合约价格精度

        【语法】
              float PriceScale(string contractNo='')

        【参数】
              contractNo 合约编号，为空时，取基准合约。

        【备注】
              返回浮点数

        【示例】
              上期沪金的报价精确到小数点2位，则PriceScale为1/100，PriceScale的返回值为0.01
        '''
        return self._dataModel.getPriceScale(contractNo)
        
    def RelativeSymbol(self):
        '''
        【说明】
              关联合约

        【语法】
              string RelativeSymbol()

        【参数】
              无

        【备注】
              返回字符串
              主连或者近月合约，返回具体的某个月份的合约
              期权返回标的合约
              套利返回单腿合约，以逗号分隔
              其他，返回空字符串

        【示例】
              "ZCE|O|SR|905C5000"白糖期权的关联合约为"ZCE|F|SR|905"
              "SPD|m|OI/Y|001|001"菜油豆油价比的关联合约为"ZCE|F|OI|001,DCE|F|Y|001"
        '''
        return self._dataModel.getRelativeSymbol()
        
    def StrikePrice(self):
        '''
        【说明】
              获取期权行权价

        【语法】
              float StrikePrice()

        【参数】
              无

        【备注】
              返回浮点数

        【示例】
              无
        '''
        return self._dataModel.getStrikePrice()
        
    def Symbol(self):
        '''
        【说明】
              获取展示合约，即基准合约的编号

        【语法】
              string Symbol()

        【参数】
              无

        【备注】
              期货、现货、指数: <EXG>|<TYPE>|<ROOT>|<YEAR><MONTH>[DAY]
              
              期权            : <EXG>|<TYPE>|<ROOT>|<YEAR><MONTH>[DAY]<CP><STRIKE>
              
              跨期套利        : <EXG>|<TYPE>|<ROOT>|<YEAR><MONTH>[DAY]|<YEAR><MONTH>[DAY]
              
              跨品种套利      : <EXG>|<TYPE>|<ROOT&ROOT>|<YEAR><MONTH>[DAY]
              
              极星跨期套利    : <EXG>|s|<ROOT>|<YEAR><MONTH>[DAY]|<YEAR><MONTH>[DAY]
              
              极星跨品种套利  : <EXG>|m|<ROOT-ROOT>|<YEAR><MONTH>|<YEAR><MONTH>
              
              极星现货期货套利: <EXG>|p|<ROOT-ROOT>||<YEAR><MONTH>

        【示例】
              "ZCE|F|SR|001", "ZCE|O|SR|001C5000"
        '''
        return self._dataModel.getSymbol()
        
    def SymbolName(self, contractNo):
        '''
        【说明】
              获取合约名称

        【语法】
              string SymbolName(string contractNo='')

        【参数】
              contractNo 合约编号，为空时，取基准合约。

        【备注】
              返回字符串

        【示例】
              "ZCE|F|SR|001"的合约名称为"白糖001"
        '''
        return self._dataModel.getSymbolName(contractNo)
        
    def SymbolType(self, contractNo):
        '''
        【说明】
              获取合约所属的品种编号

        【语法】
              string SymbolType(string contractNo='')

        【参数】
              contractNo 合约编号，为空时，取基准合约。

        【备注】
              返回字符串

        【示例】
              "ZCE|F|SR|001"的品种编号为"ZCE|F|SR"
        '''
        return self._dataModel.getSymbolType(contractNo)

    def GetTrendContract(self, contractNo):
        '''
        【说明】
              获取商品主连/近月对应的合约

        【语法】
              string GetTrendContract(string contractNo="")

        【参数】
              contractNo 取商品主连/近月编号，为空时，取基准合约。

        【备注】
              返回字符串

        【示例】
              GetTrendContract('DCE|Z|I|MAIN') 的返回为"DCE|F|I|1909"
              GetTrendContract('DCE|Z|I|NEARBY') 的返回为"DCE|F|I|1907"
        '''
        return self._dataModel.getIndexMap(contractNo)

    # //////////////////////策略状态////////////////////
    def AvgEntryPrice(self, contractNo):
        '''
        【说明】
              获得当前持仓指定合约的平均建仓价格。

        【语法】
              float AvgEntryPrice(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              无

        【示例】
              无
        '''
        return self._dataModel.getAvgEntryPrice(contractNo)

    def BarsSinceEntry(self, contractNo):
        '''
        【说明】
              获得当前持仓中指定合约的第一个建仓位置到当前位置的Bar计数。

        【语法】
              int BarsSinceEntry(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前持仓指定合约的第一个建仓位置到当前位置的Bar计数，返回值为整型。
              只有当MarketPosition != 0时，即有持仓的状况下，该函数才有意义，否则返回-1。
              注意：在开仓Bar上为0。

        【示例】
              无
        '''
        return self._dataModel.getBarsSinceEntry(contractNo)

    def BarsSinceExit(self, contractNo):
        '''
        【说明】
              获得当前持仓中指定合约的最近平仓位置到当前位置的Bar计数。

        【语法】
              int BarsSinceExit(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前持仓指定合约的最近平仓位置到当前位置的Bar计数，返回值为整型。
              若从未平过仓，则返回-1。
              注意：在平仓Bar上为0。

        【示例】
              无
        '''
        return self._dataModel.getBarsSinceExit(contractNo)

    def BarsSinceLastEntry(self, contractNo):
        '''
        【说明】
              获得当前持仓的最后一个建仓位置到当前位置的Bar计数。

        【语法】
              int BarsSinceLastEntry(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前持仓指定合约的最后一个建仓位置到当前位置的Bar计数，返回值为整型。
              若当前策略持仓为0，则返回-1。
              注意：在建仓Bar上为0。

        【示例】
              无
        '''
        return self._dataModel.getBarsSinceLastEntry(contractNo)

    def BarsSinceLastBuyEntry(self, contractNo):
        '''
        【说明】
              获得当前持仓的最后一个Buy建仓位置到当前位置的Bar计数。

        【语法】
              int BarsSinceLastBuyEntry(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前持仓指定合约的最后一个Buy建仓位置到当前位置的Bar计数，返回值为整型。
              若当前策略持仓为0，则返回-1。
              注意：在建仓Bar上为0。

        【示例】
              无
        '''
        return self._dataModel.getBarsSinceLastBuyEntry(contractNo)

    def BarsSinceLastSellEntry(self, contractNo):
        '''
        【说明】
              获得当前持仓的最后一个Sell建仓位置到当前位置的Bar计数。

        【语法】
              int BarsSinceLastSellEntry(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前持仓指定合约的最后一个Sell建仓位置到当前位置的Bar计数，返回值为整型。
              若当前策略持仓为0，则返回-1。
              注意：在建仓Bar上为0。

        【示例】
              无
        '''
        return self._dataModel.getBarsSinceLastSellEntry(contractNo)

    def BarsSinceToday(self, contractNo, kLineType, kLineValue):
        '''
        【说明】
              获得当天的第一根Bar到当前的Bar个数。

        【语法】
              int BarsSinceToday(string contractNo='', char kLineType='', int kLineValue='')

        【参数】
              contractNo 合约编号，默认为基准合约
              kLineType K线类型
              kLineValue K线周期

        【备注】
              无。

        【示例】
              无
        '''
        return self._dataModel.getBarsSinceToday(contractNo, kLineType, kLineValue)

    def ContractProfit(self, contractNo):
        '''
        【说明】
              获得当前持仓的每手浮动盈亏。

        【语法】
              float ContractProfit(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前持仓位置的每手浮动盈亏，返回值为浮点数。

        【示例】
              无
        '''
        return self._dataModel.getContractProfit(contractNo)

    def CurrentContracts(self, contractNo):
        '''
        【说明】
              获得策略当前的持仓合约数(净持仓)。

        【语法】
              int CurrentContracts(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得策略当前的持仓合约数，返回值为整数。
              该函数返回策略当前的净持仓数量，多仓为正值，空仓为负值，持平返回0。

        【示例】
              无
        '''
        return self._dataModel.getCurrentContracts(contractNo)

    def BuyPosition(self, contractNo):
        '''
        【说明】
              获得当前持仓的买入方向的持仓量。
         【语法】
              int BuyPosition(string contractNo='')
         【参数】
              contractNo 合约编号，默认为基准合约。
         【备注】
              获得策略当前持仓的买入方向的持仓量，返回值为整数。
         【示例】
              无
        '''
        return self._dataModel.getBuyPositionInStrategy(contractNo)

    def SellPosition(self, contractNo):
        '''
        【说明】
              获得当前持仓的卖出方向的持仓量。
         【语法】
              int SellPosition(string contractNo='')
         【参数】
              contractNo 合约编号，默认为基准合约。
         【备注】
              获得策略当前持仓的卖出持仓量，返回值为整数。
         【示例】
              无
        '''
        return self._dataModel.getSellPositionInStrategy(contractNo)

    def EntryDate(self, contractNo):
        '''
        【说明】
              获得当前持仓的第一个建仓位置的日期。

        【语法】
              int EntryDate(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              若策略当前持仓为0，则返回无效日期:19700101，否则返回YYYYMMDD格式的日期。

        【示例】
              无
        '''
        return self._dataModel.getEntryDate(contractNo)

    def EntryPrice(self, contractNo):
        '''
        【说明】
              获得当前持仓的第一次建仓的委托价格。

        【语法】
              float EntryPrice(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前持仓的第一个建仓价格，返回值为浮点数。
              若策略当前持仓为0，则返回0。

        【示例】
              无
        '''
        return self._dataModel.getEntryPrice(contractNo)

    def EntryTime(self, contractNo):
        '''
        【说明】
              获得当前持仓的第一个建仓位置的时间。

        【语法】
              float EntryTime(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前持仓的第一个建仓时间，返回值为0.HHMMSSmmm格式的时间。
              若策略当前持仓为0，则返回0。

        【示例】
              无
        '''
        return self._dataModel.getEntryTime(contractNo)

    def ExitDate(self, contractNo):
        '''
        【说明】
              获得最近平仓位置Bar日期。

        【语法】
              int ExitDate(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前持仓的最近平仓时间，返回值为YYYYMMDD格式的日期。
              若从未平过仓，则返回无效日期:19700101。

        【示例】
              无
        '''
        return self._dataModel.getExitDate(contractNo)

    def ExitPrice(self, contractNo):
        '''
        【说明】
              获得合约最近一次平仓的委托价格。

        【语法】
              float ExitPrice(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得最近平仓位置的平仓价格，返回值为浮点数。
              若合约从未被平仓,则返回0，否则返回合约最近一次平仓时的委托价格。

        【示例】
              无
        '''
        return self._dataModel.getExitPrice(contractNo)

    def ExitTime(self, contractNo):
        '''
        【说明】
              获得最近平仓位置Bar时间。

        【语法】
              float ExitTime(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得最近平仓位置Bar时间，返回值为0.HHMMSSmmm格式的时间。
              若合约从未平过仓，则返回0。

        【示例】
              无
        '''
        return self._dataModel.getExitTime(contractNo)

    def LastEntryDate(self, contractNo):
        '''
        【说明】
              获得当前持仓的最后一个建仓位置的日期。

        【语法】
              int LastEntryDate(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前持仓的最后一个建仓位置的日期，返回值为YYYYMMDD格式的日期。
              若策略当前持仓为0，则返回无效日期:19700101。

        【示例】
              无
        '''
        return self._dataModel.getLastEntryDate(contractNo)

    def LastEntryPrice(self, contractNo):
        '''
        【说明】
              获得当前持仓的最后一次建仓的委托价格。

        【语法】
              float LastEntryPrice(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前持仓的最后一个建仓价格，返回值为浮点数。
              若策略当前持仓为0，则返回0。

        【示例】
              无
        '''
        return self._dataModel.getLastEntryPrice(contractNo)

    def LastBuyEntryPrice(self, contractNo):
        '''
        【说明】
              获得当前Buy持仓的最后一次建仓的委托价格。

        【语法】
              float LastBuyEntryPrice(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前Buy持仓的最后一个建仓价格，返回值为浮点数。
              若策略当前Buy持仓为0，则返回0。

        【示例】
              无
        '''
        return self._dataModel.getLastBuyEntryPrice(contractNo)

    def LastSellEntryPrice(self, contractNo):
        '''
        【说明】
              获得当前Sell持仓的最后一次建仓的委托价格。

        【语法】
              float LastSellEntryPrice(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前Sell持仓的最后一个建仓价格，返回值为浮点数。
              若策略当前Sell持仓为0，则返回0。

        【示例】
              无
        '''
        return self._dataModel.getLastSellEntryPrice(contractNo)
        
    def HighestSinceLastBuyEntry(self, contractNo):
        '''
        【说明】
              获得当前Buy持仓的最后一次建仓以来的最高价。

        【语法】
              float HighestSinceLastBuyEntry(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前Buy持仓的最后一个建仓以来的最高价，返回值为浮点数。
              若策略当前Buy持仓为0，则返回0。

        【示例】
              无
        '''
        return self._dataModel.getHighestSinceLastBuyEntry(contractNo)
        
    def LowestSinceLastBuyEntry(self, contractNo):
        '''
        【说明】
              获得当前Buy持仓的最后一次建仓以来的最低价。

        【语法】
              float LowestSinceLastBuyEntry(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前Buy持仓的最后一个建仓以来的最低价，返回值为浮点数。
              若策略当前Buy持仓为0，则返回0。

        【示例】
              无
        '''
        return self._dataModel.getLowestSinceLastBuyEntry(contractNo)

    def HighestSinceLastSellEntry(self, contractNo):
        '''
        【说明】
              获得当前Sell持仓的最后一次建仓以来的最高价。

        【语法】
              float HighestSinceLastSellEntry(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前Sell持仓的最后一个建仓以来的最高价，返回值为浮点数。
              若策略当前Sell持仓为0，则返回0。

        【示例】
              无
        '''
        return self._dataModel.getHighestSinceLastSellEntry(contractNo)
        
    def LowestSinceLastSellEntry(self, contractNo):
        '''
        【说明】
              获得当前Sell持仓的最后一次建仓以来的最低价。

        【语法】
              float LowestSinceLastSellEntry(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前Sell持仓的最后一个建仓以来的最低价，返回值为浮点数。
              若策略当前Sell持仓为0，则返回0。

        【示例】
              无
        '''
        return self._dataModel.getLowestSinceLastSellEntry(contractNo)

    def LastEntryTime(self, contractNo):
        '''
        【说明】
              获得当前持仓的最后一个建仓位置的时间。

        【语法】
              float LastEntryTime(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前持仓的最后一个建仓位置的时间，返回值为0.HHMMSSmmm格式的时间。
              若策略当前持仓为0，则返回0。

        【示例】
              无
        '''
        return self._dataModel.getLastEntryTime(contractNo)

    def MarketPosition(self, contractNo):
        '''
        【说明】
               获得当前持仓状态 。

        【语法】
              int MarketPosition(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              获得当前持仓状态，返回值为整型。
              返回值定义如下：
                -1 当前位置为持空仓
                0 当前位置为持平
                1 当前位置为持多仓

        【示例】
              if(MarketPosition("ZCE|F|SR|905")==1)判断合约ZCE|F|SR|905当前是否持多仓
              if(MarketPosition("ZCE|F|SR|905")!=0)判断合约ZCE|F|SR|905当前是否有持仓，无论持空仓或多仓
        '''
        return self._dataModel.getMarketPosition(contractNo)

    def PositionProfit(self, contractNo):
        '''
        【说明】
               获得当前持仓的浮动盈亏 。

        【语法】
              float PositionProfit(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              若策略当前持仓为0，则返回0

        【示例】
              无
        '''
        return self._dataModel.getPositionProfit(contractNo)

    def BarsLast(self, condition):
        '''
        【说明】
              返回最后一次满足条件时距离当前的bar数

        【语法】
               int BarsLast(bool condition)

        【参数】
              condition  传入的条件表达式

        【备注】
              返回最后一次满足条件时距离当前的bar数。

        【示例】
              BarsLast(Close > Open); 从当前Bar开始，最近出现Close>Open的Bar到当前Bar的偏移值。如果为0，即当前Bar为最近的满足条件的Bar。

        '''
        return self._dataModel.getBarsLast(condition)

    #////////////////////////////策略性能/////////////////
    def Available(self):
        '''
        【说明】
              返回策略当前可用虚拟资金。

        【语法】
              float Available()

        【参数】
              无

        【备注】
              无

        【示例】
              无
        '''
        return self._dataModel.getAvailable()

    def CurrentEquity(self):
        '''
        【说明】
              返回策略的当前账户权益。

        【语法】
              float CurrentEquity()

        【参数】
              无

        【备注】
              无

        【示例】
              无
        '''
        return self._dataModel.getEquity()

    def FloatProfit(self, contractNo):
        '''
        【说明】
              返回指定合约的浮动盈亏。

        【语法】
              float FloatProfit(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              无

        【示例】
              无
        '''
        return self._dataModel.getFloatProfit(contractNo)

    def GrossLoss(self):
        '''
        【说明】
              返回累计总亏损。

        【语法】
              float GrossLoss()

        【参数】
              无

        【备注】
              无

        【示例】
              无
        '''
        return self._dataModel.getGrossLoss()

    def GrossProfit(self):
        '''
        【说明】
              返回累计总利润。

        【语法】
              float GrossProfit()

        【参数】
              无

        【备注】
              无

        【示例】
              无
        '''
        return self._dataModel.getGrossProfit()

    def Margin(self, contractNo):
        '''
        【说明】
              返回指定合约的持仓保证金。

        【语法】
              float Margin(string contractNo='')

        【参数】
              contractNo 合约编号，默认为基准合约。

        【备注】
              无

        【示例】
              无
        '''
        return self._dataModel.getMargin(contractNo)

    def NetProfit(self):
        '''
        【说明】
              返回该账户下的平仓盈亏。

        【语法】
              float NetProfit()

        【参数】
              无

        【备注】
              无

        【示例】
              无
        '''
        return self._dataModel.getNetProfit()

    def NumEvenTrades(self):
        '''
        【说明】
              返回该账户下保本交易的总手数。

        【语法】
              int NumEvenTrades()

        【参数】
              无

        【备注】
              无

        【示例】
              无
        '''
        return self._dataModel.getNumEvenTrades()

    def NumLosTrades(self):
        '''
        【说明】
              返回该账户下亏损交易的总手数。

        【语法】
              int NumLosTrades()

        【参数】
              无

        【备注】
              无

        【示例】
              无
        '''
        return self._dataModel.getNumLosTrades()

    def NumWinTrades(self):
        '''
        【说明】
              返回该账户下盈利交易的总手数。

        【语法】
              int NumWinTrades()

        【参数】
              无

        【备注】
              无

        【示例】
              无
        '''
        return self._dataModel.getNumWinTrades()

    def NumAllTimes(self):
        '''
        【说明】
              返回该账户的开仓次数。

        【语法】
              int NumAllTimes()

        【参数】
              无

        【备注】
              无

        【示例】
              无
        '''
        return self._dataModel.getNumAllTimes()

    def NumWinTimes(self):
        '''
        【说明】
              返回该账户的盈利次数。

        【语法】
              int NumWinTimes()

        【参数】
              无

        【备注】
              无

        【示例】
              无
        '''
        return self._dataModel.getNumWinTimes()

    def NumLoseTimes(self):
        '''
        【说明】
              返回该账户的亏损次数。

        【语法】
              int NumLoseTimes()

        【参数】
              无

        【备注】
              无

        【示例】
              无
        '''
        return self._dataModel.getNumLoseTimes()

    def NumEventTimes(self):
        '''
        【说明】
              返回该账户的保本次数。

        【语法】
              int NumEventTimes()

        【参数】
              无

        【备注】
              无

        【示例】
              无
        '''
        return self._dataModel.getNumEventTimes()

    def PercentProfit(self):
        '''
        【说明】
              返回该账户的盈利成功率。

        【语法】
              float PercentProfit()

        【参数】
              无

        【备注】
              无

        【示例】
              无
        '''
        return self._dataModel.getPercentProfit()

    def TradeCost(self):
        '''
        【说明】
              返回该账户交易产生的手续费。

        【语法】
              float TradeCost()

        【参数】
              无

        【备注】
              无

        【示例】
              无
        '''
        return self._dataModel.getTradeCost()

    def TotalTrades(self, contractNo):
        '''
        【说明】
              返回该账户的交易总开仓手数。

        【语法】
              int TotalTrades()

        【参数】
              无

        【备注】
              无

        【示例】
              无
        '''
        buyPos  = self._dataModel.getBuyPositionInStrategy(contractNo)
        sellPos = self._dataModel.getSellPositionInStrategy(contractNo)
        return buyPos + sellPos
        #return self._dataModel.getTotalTrades()


    #////////////////////////////账户函数/////////////////
    def A_AccountID(self):
        '''
        【说明】
              返回当前公式应用的交易帐户ID。

        【语法】
              string A_AccountID()

        【参数】
              无

        【备注】
              返回当前公式应用的交易帐户ID，返回值为字符串，无效时返回空串。
              注：不能用于历史测试，仅适用于实时行情交易。

        【示例】
              无
        '''
        return self._dataModel.getAccountId()
        
    def A_AllAccountID(self):
        '''
        【说明】
              返回所有已登录交易帐户ID。

        【语法】
              list A_AllAccountID()

        【参数】
              无

        【备注】
              没有账号登录时，返回空列表
              注：不能用于历史测试，仅适用于实时行情交易。

        【示例】
              无
        '''
        return self._dataModel.getAllAccountId()

    def A_GetAllPositionSymbol(self, userNo):
        '''
        【说明】
              获得指定账户所有持仓合约。

        【语法】
              list A_GetAllPositionSymbol(string userNo='')

        【参数】
              userNo  指定的交易账户，默认当前账户

        【备注】
              该参数返回类型为字符串列表，列表内容为账户所有持仓合约列表。

        【示例】
              无
        '''
        return self._dataModel.getAllPositionSymbol(userNo)

    def A_Cost(self, userNo):
        '''
        【说明】
              返回指定交易帐户的手续费。

        【语法】
              string A_Cost(string userNo='')

        【参数】
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定交易帐户的手续费，返回值为浮点数。

        【示例】
              无
        '''
        return self._dataModel.getCost(userNo)

    def A_Assets(self, userNo):
        '''
        【说明】
              返回指定交易帐户的动态权益。

        【语法】
              float A_Assets(string userNo='')

        【参数】
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定交易帐户的动态权益，返回值为浮点数。

        【示例】
              无
        '''
        return self._dataModel.getCurrentEquity(userNo)

    def A_Available(self, userNo):
        '''
        【说明】
              返回指定交易帐户的可用资金。

        【语法】
              float A_Available(string userNo='')

        【参数】
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定交易帐户的可用资金，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
        '''
        return self._dataModel.getFreeMargin(userNo)

    def A_Margin(self, userNo):
        '''
        【说明】
              返回指定交易帐户的持仓保证金。

        【语法】
              float A_Margin(string userNo='')

        【参数】
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定交易帐户的持仓保证金，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
        '''
        return self._dataModel.getAMargin(userNo)

    def A_ProfitLoss(self, userNo):
        '''
        【说明】
              返回指定交易帐户的浮动盈亏。

        【语法】
              float A_ProfitLoss(string userNo='')

        【参数】
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定交易帐户的浮动盈亏，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
        '''
        return self._dataModel.getProfitLoss(userNo)

    def A_CoverProfit(self, userNo):
        '''
        【说明】
              返回当前账户的平仓盈亏。

        【语法】
              float A_CoverProfit(string userNo='')

        【参数】
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定交易帐户的平仓盈亏，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
        '''
        return self._dataModel.getCoverProfit(userNo)

    def A_TotalFreeze(self, userNo):
        '''
        【说明】
              返回指定交易帐户的冻结资金。

        【语法】
              float A_TotalFreeze(string userNo='')

        【参数】
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定交易帐户的冻结资金，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
        '''
        return self._dataModel.getTotalFreeze(userNo)

    def A_BuyAvgPrice(self, contractNo, userNo):
        '''
        【说明】
              返回指定帐户下当前商品的买入持仓均价。

        【语法】
              float A_BuyAvgPrice(string contractNo='', string userNo='')

        【参数】
              contractNo，指定商品的合约编号，为空时采用基准合约编号。
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定帐户下当前商品的买入持仓均价，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
         '''
        return self._dataModel.getBuyAvgPrice(userNo, contractNo)

    def A_BuyPosition(self, contractNo, userNo):
        '''
        【说明】
              返回指定帐户下当前商品的买入持仓。

        【语法】
              float A_BuyPosition(string contractNo='', string userNo='')

        【参数】
              contractNo，指定商品的合约编号，为空时采用基准合约编号。
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定帐户下当前商品的买入持仓，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              当前持多仓2手，A_BuyPosition返回2。
         '''
        return self._dataModel.getBuyPosition(userNo, contractNo)

    def A_BuyPositionCanCover(self, contractNo, userNo):
        '''
        【说明】
              返回指定帐户下买仓可平数量。

        【语法】
              int A_BuyPositionCanCover(string contractNo='', string userNo='')

        【参数】
              contractNo，指定商品的合约编号，为空时采用基准合约编号。
              userNo  指定的交易账户，默认当前账户

        【备注】
              可平仓数量=持仓数量-已排队的挂单数量

        【示例】
              无
         '''
        return self._dataModel.getBuyPositionCanCover(userNo, contractNo)

    def A_BuyProfitLoss(self, contractNo, userNo):
        '''
        【说明】
              返回指定帐户下当前商品的买入持仓盈亏。

        【语法】
              float A_BuyProfitLoss(string contractNo='', string userNo='')

        【参数】
              contractNo，指定商品的合约编号，为空时采用基准合约编号。
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定帐户下当前商品的买入持仓盈亏，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
         '''
        return self._dataModel.getBuyProfitLoss(userNo, contractNo)

    def A_SellAvgPrice(self, contractNo, userNo):
        '''
        【说明】
              返回指定帐户下当前商品的卖出持仓均价。

        【语法】
              float A_SellAvgPrice(string contractNo='', string userNo='')

        【参数】
              contractNo，指定商品的合约编号，为空时采用基准合约编号。
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定帐户下当前商品的卖出持仓均价，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
         '''
        return self._dataModel.getSellAvgPrice(userNo, contractNo)

    def A_SellPosition(self, contractNo, userNo):
        '''
        【说明】
              返回指定帐户下当前商品的卖出持仓。

        【语法】
              float A_SellPosition(string contractNo='', string userNo='')

        【参数】
              contractNo，指定商品的合约编号，为空时采用基准合约编号。
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定帐户下当前商品的卖出持仓，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              当前持空仓3手，A_SellPosition返回3。
         '''
        return self._dataModel.getSellPosition(userNo, contractNo)

    def A_SellPositionCanCover(self, contractNo, userNo):
        '''
        【说明】
              返回指定帐户下卖仓可平数量。

        【语法】
              int A_SellPositionCanCover(string contractNo='', string userNo='')

        【参数】
              contractNo，指定商品的合约编号，为空时采用基准合约编号。
              userNo  指定的交易账户，默认当前账户

        【备注】
              可平仓数量=持仓数量-已排队的挂单数量

        【示例】
              无
         '''
        return self._dataModel.getSellPositionCanCover(userNo, contractNo)

    def A_SellProfitLoss(self, contractNo, userNo):
        '''
        【说明】
              返回指定帐户下当前商品的卖出持仓盈亏。

        【语法】
              float A_SellProfitLoss(string contractNo='', string userNo='')

        【参数】
              contractNo，指定商品的合约编号，为空时采用基准合约编号。
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定帐户下当前商品的卖出持仓盈亏，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
         '''
        return self._dataModel.getSellProfitLoss(userNo, contractNo)

    def A_TotalAvgPrice(self, contractNo, userNo):
        '''
        【说明】
              返回指定帐户下当前商品的持仓均价。

        【语法】
              float A_TotalAvgPrice(string contractNo='', string userNo='')

        【参数】
              contractNo，指定商品的合约编号，为空时采用基准合约编号。
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定帐户下当前商品的持仓均价，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
         '''
        return self._dataModel.getTotalAvgPrice(userNo, contractNo)

    def A_TotalPosition(self, contractNo, userNo):
        '''
        【说明】
              返回指定帐户下当前商品的总持仓。

        【语法】
              int A_TotalPosition(string contractNo='', string userNo='')

        【参数】
              contractNo，指定商品的合约编号，为空时采用基准合约编号。
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定帐户下当前商品的总持仓，返回值为浮点数。
              该持仓为所有持仓的合计值，正数表示多仓，负数表示空仓，零为无持仓。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
         '''
        return self._dataModel.getTotalPosition(userNo, contractNo)

    def A_TotalProfitLoss(self, contractNo, userNo):
        '''
        【说明】
              返回指定帐户下当前商品的总持仓盈亏。

        【语法】
              float A_TotalProfitLoss(string contractNo='', string userNo='')

        【参数】
              contractNo，指定商品的合约编号，为空时采用基准合约编号。
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定帐户下当前商品的总持仓盈亏，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
         '''
        return self._dataModel.getTotalProfitLoss(userNo, contractNo)

    def A_TodayBuyPosition(self, contractNo, userNo):
        '''
        【说明】
              返回指定帐户下当前商品的当日买入持仓。

        【语法】
              float A_TodayBuyPosition(string contractNo='', string userNo='')

        【参数】
              contractNo，指定商品的合约编号，为空时采用基准合约编号。
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定帐户下当前商品的当日买入持仓，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
         '''
        return self._dataModel.getTodayBuyPosition(userNo, contractNo)

    def A_TodaySellPosition(self, contractNo, userNo):
        '''
        【说明】
              返回指定帐户下当前商品的当日卖出持仓。

        【语法】
              float A_TodaySellPosition(string contractNo='', string userNo='')

        【参数】
              contractNo，指定商品的合约编号，为空时采用基准合约编号。
              userNo  指定的交易账户，默认当前账户

        【备注】
              返回指定帐户下当前商品的当日卖出持仓，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
         '''
        return self._dataModel.getTodaySellPosition(userNo, contractNo)

    def A_OrderBuyOrSell(self, userNo, localOrderId):
        '''
        【说明】
              返回指定帐户下当前商品的某个委托单的买卖类型。

        【语法】
              char A_OrderBuyOrSell(int|string localOrderId='')

        【参数】
              localOrderId 定单号，或者使用A_SendOrder返回的下单编号。

        【备注】
              返回指定帐户下当前商品的某个委托单的买卖类型，返回值为：
              B : 买入
              S : 卖出
              A : 双边
              该函数返回值可以与Enum_Buy、Enum_Sell等买卖状态枚举值进行比较，根据类型不同分别处理。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              nBorS = A_OrderBuyOrSell('1-1')
              if nBorS == Enum_Buy():
                ...
         '''
        return self._dataModel.getOrderBuyOrSell(userNo, localOrderId)

    def A_OrderEntryOrExit(self, userNo, localOrderId):
        '''
        【说明】
              返回指定帐户下当前商品的某个委托单的开平仓状态。

        【语法】
              char A_OrderEntryOrExit(int|string localOrderId='')

        【参数】
              localOrderId 定单号，或者使用A_SendOrder返回的下单编号。

        【备注】
              返回指定帐户下当前商品的某个委托单的开平仓状态，返回值：
              N : 无
              O : 开仓
              C : 平仓
              T : 平今
              1 : 开平，应价时有效, 本地套利也可以
              2 : 平开，应价时有效, 本地套利也可以
              该函数返回值可以与Enum_Entry、Enum_Exit等开平仓状态枚举值进行比较，根据类型不同分别处理。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              orderFlag = A_OrderEntryOrExit('1-1')
              if orderFlag == Enum_Exit():
                ...
         '''
        return self._dataModel.getOrderEntryOrExit(userNo, localOrderId)

    def A_OrderFilledLot(self, userNo, localOrderId):
        '''
        【说明】
              返回指定帐户下当前商品的某个委托单的成交数量。

        【语法】
              float A_OrderFilledLot(int|string localOrderId='')

        【参数】
              localOrderId 定单号，或者使用A_SendOrder返回的下单编号。

        【备注】
              返回指定帐户下当前商品的某个委托单的成交数量，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
         '''
        return self._dataModel.getOrderFilledLot(userNo, localOrderId)

    def A_OrderFilledPrice(self, userNo, localOrderId):
        '''
        【说明】
              返回指定帐户下当前商品的某个委托单的成交价格。

        【语法】
              float A_OrderFilledPrice(int|string localOrderId='')

        【参数】
              localOrderId 定单号，或者使用A_SendOrder返回的下单编号。

        【备注】
              返回指定帐户下当前商品的某个委托单的成交价格，返回值为浮点数。
              该成交价格可能为多个成交价格的平均值。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
         '''
        return self._dataModel.getOrderFilledPrice(userNo, localOrderId)

    def A_OrderLot(self, userNo, localOrderId):
        '''
        【说明】
              返回指定帐户下当前商品的某个委托单的委托数量。

        【语法】
              float A_OrderLot(int|string localOrderId='')

        【参数】
              localOrderId 定单号，或者使用A_SendOrder返回的下单编号。

        【备注】
              返回指定帐户下当前商品的某个委托单的委托数量，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
         '''
        return self._dataModel.getOrderLot(userNo, localOrderId)

    def A_OrderPrice(self, userNo, localOrderId):
        '''
        【说明】
              返回指定帐户下当前商品的某个委托单的委托价格。

        【语法】
              float A_OrderPrice(int|string localOrderId='')

        【参数】
              localOrderId 定单号，或者使用A_SendOrder返回的下单编号。

        【备注】
              返回指定帐户下当前商品的某个委托单的委托价格，返回值为浮点数。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
         '''
        return self._dataModel.getOrderPrice(userNo, localOrderId)

    def A_OrderStatus(self, userNo, localOrderId):
        '''
        【说明】
              返回指定帐户下当前商品的某个委托单的状态。

        【语法】
              char A_OrderStatus(int|string localOrderId='')

        【参数】
              localOrderId 定单号，或者使用A_SendOrder返回的下单编号。

        【备注】
              返回指定帐户下当前商品的某个委托单的状态，返回值：
              N : 无
              0 : 已发送
              1 : 已受理
              2 : 待触发
              3 : 已生效
              4 : 已排队
              5 : 部分成交
              6 : 完全成交
              7 : 待撤
              8 : 待改
              9 : 已撤单
              A : 已撤余单
              B : 指令失败
              C : 待审核
              D : 已挂起
              E : 已申请
              F : 无效单
              G : 部分触发
              H : 完全触发
              I : 余单失败
              该函数返回值可以与委托状态枚举函数Enum_Sended、Enum_Accept等函数进行比较，根据类型不同分别处理。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
         '''
        return self._dataModel.getOrderStatus(userNo, localOrderId)

    def A_OrderIsClose(self, userNo, localOrderId):
        '''
        【说明】
              判断某个委托单是否完结。

        【语法】
              bool A_OrderIsClose(int|string localOrderId='')

        【参数】
              localOrderId 定单号，或者使用A_SendOrder返回的下单编号。

        【备注】
              当委托单是完结状态，返回True，否则返回False。
              
        【示例】
              无
         '''
        return self._dataModel.getOrderIsClose(userNo, localOrderId)

    def A_OrderTime(self, userNo, localOrderId):
        '''
        【说明】
              返回指定公式应用的帐户下当前商品的某个委托单的委托时间。

        【语法】
              struct_time A_OrderTime(int|string localOrderId='')

        【参数】
              localOrderId 定单号，或者使用A_SendOrder返回的下单编号。

        【备注】
              返回指定帐户下当前商品的某个委托单的委托时间，返回格式为YYYYMMDD.hhmmss的数值。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
         '''
        return self._dataModel.getOrderTime(userNo, localOrderId)

    def A_FirstOrderNo(self, contractNo1, contractNo2, userNo):
        '''
        【说明】
              返回指定账户第一个订单号。

        【语法】
              int A_FirstOrderNo(string contractNo1='', string contractNo2='', string userNo='')

        【参数】
              contractNo1 合约代码，默认为遍历所有合约。
              contractNo2 合约代码，默认为遍历所有合约。
              userNo  指定的交易账户，默认当前账户

        【备注】
              若返回值为-1，表示没有任何订单，否则，返回第一个订单的索引值，
              该函数经常和A_NextOrderNo函数合用，用于遍历所有的订单。

        【示例】
              无
         '''
        return self._dataModel.getFirstOrderNo(userNo, contractNo1, contractNo2)

    def A_NextOrderNo(self, localOrderId, contractNo1, contractNo2, userNo):
        '''
        【说明】
              返回指定账户下一个订单号。

        【语法】
              int A_NextOrderNo(int localOrderId=0, string contractNo1='', string contractNo2='', string userNo='')

        【参数】
              localOrderId 定单号，默认为0，
              contractNo1 合约代码，默认为遍历所有合约。
              contractNo2 合约代码，默认为遍历所有合约。
              userNo  指定的交易账户，默认当前账户

        【备注】
              若返回值为-1，表示没有任何订单，否则，返回处在OrderNo后面的订单索引值，
              该函数常和A_FirstOrderNo联合使用。

        【示例】
              无
         '''
        return self._dataModel.getNextOrderNo(userNo, localOrderId, contractNo1, contractNo2)

    def A_LastOrderNo(self, contractNo1, contractNo2, userNo):
        '''
        【说明】
              返回指定账户最近发送的订单号。

        【语法】
              int A_LastOrderNo(string contractNo1='', string contractNo2='', string userNo='')

        【参数】
              contractNo1 合约代码，默认为遍历所有合约。
              contractNo2 合约代码，默认为遍历所有合约。
              userNo  指定的交易账户，默认当前账户

        【备注】
              若返回值为-1，表示没有任何订单，否则，返回最后一个订单的索引值。

        【示例】
              无
         '''
        return self._dataModel.getLastOrderNo(userNo, contractNo1, contractNo2)

    def A_FirstQueueOrderNo(self, contractNo1, contractNo2, userNo):
        '''
        【说明】
              返回指定账户第一个排队(可撤)订单号。

        【语法】
              int A_FirstQueueOrderNo(string contractNo1='', string contractNo2='', string userNo='')

        【参数】
              contractNo1 合约代码，默认为遍历所有合约。
              contractNo2 合约代码，默认为遍历所有合约。
              userNo  指定的交易账户，默认当前账户

        【备注】
              若返回值为-1，表示没有任何可撤排队订单，否则，返回第一个订单的索引值。，
              该函数经常和A_NextQueueOrderNo函数合用，用于遍历排队中的订单。

        【示例】
              无
         '''
        return self._dataModel.getFirstQueueOrderNo(userNo, contractNo1, contractNo2)

    def A_NextQueueOrderNo(self, localOrderId, contractNo1, contractNo2, userNo):
        '''
        【说明】
              返回指定账户下一个排队(可撤)订单号。

        【语法】
              int A_NextQueueOrderNo(int localOrderId=0, string contractNo1='', string contractNo2='', string userNo='')

        【参数】
              localOrderId 定单号，默认为0，
              contractNo1 合约代码，默认为遍历所有合约。
              contractNo2 合约代码，默认为遍历所有合约。
              userNo  指定的交易账户，默认当前账户

        【备注】
              若返回值为-1，表示没有任何排队订单，否则，返回处在OrderNo后面的订单索引值，
              该函数常和A_FirstQueueOrderNo联合使用。

        【示例】
              无
         '''
        return self._dataModel.getNextQueueOrderNo(userNo, localOrderId, contractNo1, contractNo2)

    def A_AllQueueOrderNo(self, contractNo, userNo):
        '''
        【说明】
              返回指定账户所有排队(可撤)订单号。

        【语法】
              list A_AllQueueOrderNo(string contractNo='', string userNo='')

        【参数】
              contractNo 合约代码，默认为遍历所有合约，指定后只遍历指定合约。
              userNo  指定的交易账户，默认当前账户

        【备注】
              若返回值为空列表，表示没有任何排队订单，否则，返回包含处于排队中的委托定单号的列表。

        【示例】
              无
         '''
        return self._dataModel.getAllQueueOrderNo(userNo, contractNo)

    def A_LatestFilledTime(self, contractNo, userNo):
        '''
        【说明】
              返回指定账户最新一笔完全成交委托单对应的时间。

        【语法】
              float A_LatestFilledTime(string contractNo='', string userNo='')

        【参数】
              contractNo 合约代码，默认为遍历所有合约，指定后只遍历指定合约。
              userNo  指定的交易账户，默认当前账户

        【备注】
              若返回值为-1，表示没有对应的完全成交的委托，否则，返回最新一笔完全成交委托单对应的时间，返回格式为YYYYMMDD.hhmmss的数值。

        【示例】
              无
         '''
        return self._dataModel.getALatestFilledTime(userNo, contractNo)
        
    def A_AllOrderNo(self, contractNo, userNo):
        '''
        【说明】
              返回包含指定合约指定账户所有订单号的列表。

        【语法】
              list A_AllOrderNo(string contractNo='', string userNo='')

        【参数】
              contractNo 合约代码，默认为遍历所有合约，指定后只遍历指定合约。
              userNo  指定的交易账户，默认当前账户

        【备注】
              无

        【示例】
              无
         '''
        return self._dataModel.getAllOrderNo(userNo, contractNo)

    def A_OrderContractNo(self, userNo, localOrderId):
        '''
        【说明】
              返回订单的合约号。

        【语法】
              string A_OrderContractNo(int|string localOrderId=0)

        【参数】
              localOrderId 定单号，或者使用A_SendOrder返回的下单编号。

        【备注】
              返回结果如："ZCE|F|TA|305"等，
              如果localOrderId没有对应的委托单，则返回结果为字符串。

        【示例】
              无
         '''
        return self._dataModel.getOrderContractNo(userNo, localOrderId)

    def A_SendOrder(self, userNo, contractNo, orderDirct, entryOrExit, orderQty, orderPrice, orderType, validType, hedge, triggerType, triggerMode, triggerCondition, triggerPrice):
        '''
        【说明】
              针对指定的帐户、商品发送委托单。

        【语法】
              int. string A_SendOrder(char orderDirct, char entryOrExit, int orderQty, float orderPrice, string contractNo='', string userNo='', char orderType='2', char validType='0', char hedge='T', char triggerType='N', char triggerMode='N', char triggerCondition='N', float triggerPrice=0)

        【参数】
              orderDirct 发送委托单的买卖类型，取值为Enum_Buy或Enum_Sell之一，
              entryOrExit 发送委托单的开平仓类型，取值为Enum_Entry,Enum_Exit,Enum_ExitToday之一，
              orderQty 委托单的交易数量，
              orderPrice 委托单的交易价格，
              contractNo 商品合约编号，默认值为基准合约，
              userNo 指定的账户名称，默认为界面选定的账户名称，
              orderType 订单类型，字符类型，默认值为'2'，可选值为：
                '1' : 市价单
                '2' : 限价单
                '3' : 市价止损
                '4' : 限价止损
                '5' : 行权
                '6' : 弃权
                '7' : 询价
                '8' : 应价
                '9' : 冰山单
                'A' : 影子单
                'B' : 互换
                'C' : 套利申请
                'D' : 套保申请
                'F' : 行权前期权自对冲申请
                'G' : 履约期货自对冲申请
                'H' : 做市商留仓
                可使用如Enum_Order_Market、Enum_Order_Limit等订单类型枚举函数获取相应的类型，
              validType 订单有效类型，字符类型，默认值为'0'， 可选值为：
                '0' : 当日有效
                '1' : 长期有效
                '2' : 限期有效
                '3' : 即时部分
                '4' : 即时全部
                可使用如Enum_GFD、Enum_GTC等订单有效类型枚举函数获取相应的类型，
              hedge 投保标记，字符类型，默认值为'T'，可选值为：
                'T' : 投机
                'B' : 套保
                'S' : 套利
                'M' : 做市
                可使用如Enum_Speculate、Enum_Hedge等订单投保标记枚举函数获取相应的类型，
              triggerType 触发委托类型，默认值为'N'，可用的值为：
                'N' : 普通单
                'P' : 预备单(埋单)
                'A' : 自动单
                'C' : 条件单
              triggerMode 触发模式，默认值为'N'，可用的值为：
                'N' : 普通单
                'L' : 最新价
                'B' : 买价
                'A' : 卖价
              triggerCondition 触发条件，默认值为'N'，可用的值为：
                'N' : 无
                'g' : 大于
                'G' : 大于等于
                'l' : 小于
                'L' : 小于等于
              triggerPrice 触发价格，默认价格为0。

        【备注】
              针对当前公式指定的帐户、商品发送委托单，发送成功返回如"1-2"的下单编号，发送失败返回空字符串""。
              返回结果形式未：retCode, retMsg，retCode的数据类型为可以为负的整数, retMsg的数据类型为字符串。
              其中发送成功时retCode为0，retMsg为返回的下单编号localOrderId，其组成规则为：策略id-该策略中发送委托单的次数，所以下单编号"1-2"表示在策略id为1的策略中的第2次发送委托单返回的下单编号。
              当发送失败时retCode为负数，retMsg为返回的发送失败的原因，retCode可能返回的值及含义如下：
                -1 : 未选择实盘运行，请在设置界面勾选"实盘运行"，或者在策略代码中调用SetActual()方法选择实盘运行；
                -2 : 策略当前状态不是实盘运行状态，请勿在历史回测阶段调用该函数；
                -3 : 未指定下单账户信息；
                -4 : 输入的账户没有在极星客户端登录；
                -5 : 请调用StartTrade方法开启实盘下单功能。
              该函数直接发单，不经过任何确认，并会在每次公式计算时发送，一般需要配合着仓位头寸进行条件处理，在不清楚运行机制的情况下，请慎用。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              retCode, retMsg = A_SendOrder(Enum_Buy(), Enum_Exit(), 1, Q_AskPrice())
              当retCode为0时表明发送订单信息成功，retMsg为返回的下单编号localOrderId。
         '''
        return self._dataModel.sendOrder(userNo, contractNo, orderType, validType, orderDirct, entryOrExit, hedge, orderPrice, orderQty, \
                                                      triggerType, triggerMode, triggerCondition, triggerPrice, aFunc=True)


    def A_ModifyOrder(self, userNo, localOrderId, contractNo, orderDirct, entryOrExit, orderQty, orderPrice, orderType, validType, hedge, triggerType, triggerMode, triggerCondition, triggerPrice):
        '''
        【说明】
              发送改单指令。

        【语法】
              bool A_ModifyOrder(string localOrderId, char orderDirct, char entryOrExit, int orderQty, float orderPrice, string contractNo='', string userNo='', char orderType='2', char validType='0', char hedge='T', char triggerType='N', char triggerMode='N', char triggerCondition='N', float triggerPrice=0)

        【参数】
              localOrderId 定单号，或者使用A_SendOrder返回的下单编号，
              orderDirct 发送委托单的买卖类型，取值为Enum_Buy或Enum_Sell之一，
              entryOrExit 发送委托单的开平仓类型，取值为Enum_Entry,Enum_Exit,Enum_ExitToday之一，
              orderQty 委托单的交易数量，
              orderPrice 委托单的交易价格，
              contractNo 商品合约编号，默认值为基准合约，
              userNo 指定的账户名称，默认为界面选定的账户名称，
              orderType 订单类型，字符类型，默认值为'2'，可选值为：
                '1' : 市价单
                '2' : 限价单
                '3' : 市价止损
                '4' : 限价止损
                '5' : 行权
                '6' : 弃权
                '7' : 询价
                '8' : 应价
                '9' : 冰山单
                'A' : 影子单
                'B' : 互换
                'C' : 套利申请
                'D' : 套保申请
                'F' : 行权前期权自对冲申请
                'G' : 履约期货自对冲申请
                'H' : 做市商留仓
                可使用如Enum_Order_Market、Enum_Order_Limit等订单类型枚举函数获取相应的类型，
              validType 订单有效类型，字符类型，默认值为'0'， 可选值为：
                '0' : 当日有效
                '1' : 长期有效
                '2' : 限期有效
                '3' : 即时部分
                '4' : 即时全部
                可使用如Enum_GFD、Enum_GTC等订单有效类型枚举函数获取相应的类型，
              hedge 投保标记，字符类型，默认值为'T'，可选值为：
                'T' : 投机
                'B' : 套保
                'S' : 套利
                'M' : 做市
                可使用如Enum_Speculate、Enum_Hedge等订单投保标记枚举函数获取相应的类型，
              triggerType 触发委托类型，默认值为'N'，可用的值为：
                'N' : 普通单
                'P' : 预备单(埋单)
                'A' : 自动单
                'C' : 条件单
              triggerMode 触发模式，默认值为'N'，可用的值为：
                'N' : 普通单
                'L' : 最新价
                'B' : 买价
                'A' : 卖价
              triggerCondition 触发条件，默认值为'N'，可用的值为：
                'N' : 无
                'g' : 大于
                'G' : 大于等于
                'l' : 小于
                'L' : 小于等于
              triggerPrice 触发价格，默认价格为0。

        【备注】
              针对指定帐户、订单发送改单指令，发送成功返回True, 发送失败返回False。
              该函数直接发单，不经过任何确认，并会在每次公式计算时发送，一般需要配合着仓位头寸进行条件处理，在不清楚运行机制的情况下，请慎用。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
 
         '''
         
        return self._dataModel.modifyOrder(userNo, localOrderId, contractNo, orderType, validType, orderDirct, entryOrExit, \
                                            hedge, orderPrice, orderQty, triggerType, triggerMode, triggerCondition, triggerPrice)
                                            

    def A_DeleteOrder(self, userNo, localOrderId):
        '''
        【说明】
              针对指定帐户、商品发送撤单指令。

        【语法】
              bool A_DeleteOrder(int|string localOrderId)

        【参数】
              localOrderId 定单号，或者使用A_SendOrder返回的下单编号。

        【备注】
              针对指定帐户、商品发送撤单指令，发送成功返回True, 发送失败返回False。
              该函数直接发单，不经过任何确认，并会在每次公式计算时发送，一般需要配合着仓位头寸进行条件处理，在不清楚运行机制的情况下，请慎用。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              无
         '''
        return self._dataModel.deleteOrder(userNo, localOrderId)

    def A_GetOrderNo(self, localOrderId):
        '''
        【说明】
              获取下单编号对应的定单号和委托号。

        【语法】
              string, string A_GetOrderNo(string localOrderId)

        【参数】
              localOrderId 使用A_SendOrder返回的下单编号。

        【备注】
              针对当前策略使用A_SendOrder返回的下单编号，可以使用A_GetOrderNo获取下单编号对应的定单号和委托号。
              由于使用A_SendOrder返回的下单编号localOrderId与策略相关，所以在策略重启后localOrderId会发生变化。
              由于委托单对应的定单号与客户端有关，所以在客户端重启后，委托单对应的定单号可能会发生变化。
              由于委托号是服务器生成的，所以在使用A_SendOrder得到下单编号后，如果服务器还没有返回相应的委托单信息，可能获取不到相应的定单号和委托号。
              当localOrderId对应的定单号和委托号还没有从服务器返回，则对应的值为空字符串。
              注：不能使用于历史测试，仅适用于实时行情交易。

        【示例】
              retCode, retMsg = A_SendOrder(.....)
              time.sleep(5)
              if retCode == 0:
                sessionId, orderNo =  A_GetOrderNo(retMsg)
         '''
        return self._dataModel.getAOrderNo(localOrderId)

    def DeleteAllOrders(self, contractNo, userNo):
        '''
        【说明】
              批量撤单函数。

        【语法】
              bool DeleteAllOrders(string contractNo='', string userNo='')

        【参数】
              contractNo 合约代码，默认为所有合约，指定后只撤指定合约。
              userNo  指定的交易账户，默认当前账户

        【备注】
              本函数将检查指定账户下所有处于排队状态的订单，并依次发送撤单指令

        【示例】
              无
         '''
        return self._dataModel.deleteAllOrders(userNo, contractNo)

    #/////////////////////////////枚举函数/////////////////
    def Enum_Buy(self):
        '''
        【说明】
              返回买卖状态的买入枚举值

        【语法】
              char Enum_Buy()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumBuy()

    def Enum_Sell(self):
        '''
        【说明】
              返回买卖状态的卖出枚举值

        【语法】
              char Enum_Sell()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumSell()

    def Enum_Entry(self):
        '''
        【说明】
              返回开平状态的开仓枚举值

        【语法】
              char Enum_Entry()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumEntry()

    def Enum_Exit(self):
        '''
        【说明】
              返回开平状态的平仓枚举值

        【语法】
              char Enum_Exit()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumExit()

    def Enum_ExitToday(self):
        '''
        【说明】
              返回开平状态的平今枚举值

        【语法】
              char Enum_ExitToday()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumExitToday()

    def Enum_EntryExitIgnore(self):
        '''
        【说明】
              返回开平状态不区分开平的枚举值

        【语法】
              char Enum_EntryExitIgnore()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumEntryExitIgnore()

    def Enum_Sended(self):
        '''
        【说明】
              返回委托状态为已发送的枚举值

        【语法】
              char Enum_Sended()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumSended()

    def Enum_Accept(self):
        '''
        【说明】
              返回委托状态为已受理的枚举值

        【语法】
              char Enum_Accept()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumAccept()

    def Enum_Triggering(self):
        '''
        【说明】
              返回委托状态为待触发的枚举值

        【语法】
              char Enum_Triggering()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumTriggering()

    def Enum_Active(self):
        '''
        【说明】
              返回委托状态为已生效的枚举值

        【语法】
              char Enum_Active()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumActive()

    def Enum_Queued(self):
        '''
        【说明】
              返回委托状态为已排队的枚举值

        【语法】
              char Enum_Queued()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumQueued()

    def Enum_FillPart(self):
        '''
        【说明】
              返回委托状态为部分成交的枚举值

        【语法】
              char Enum_FillPart()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumFillPart()

    def Enum_Filled(self):
        '''
        【说明】
              返回委托状态为全部成交的枚举值

        【语法】
              char Enum_Filled()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumFilled()

    def Enum_Canceling(self):
        '''
        【说明】
              返回委托状态为待撤的枚举值

        【语法】
              char Enum_Canceling()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumCanceling()

    def Enum_Modifying(self):
        '''
        【说明】
              返回委托状态为待改的枚举值

        【语法】
              char Enum_Modifying()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumModifying()

    def Enum_Canceled(self):
        '''
        【说明】
              返回委托状态为已撤单的枚举值

        【语法】
              char Enum_Canceled()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumCanceled()

    def Enum_PartCanceled(self):
        '''
        【说明】
              返回委托状态为已撤余单的枚举值

        【语法】
              char Enum_PartCanceled()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumPartCanceled()

    def Enum_Fail(self):
        '''
        【说明】
              返回委托状态为指令失败的枚举值

        【语法】
              char Enum_Fail()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumFail()

    def Enum_Suspended(self):
        '''
        【说明】
              返回委托状态为已挂起的枚举值

        【语法】
              char Enum_Suspended()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumSuspended()

    def Enum_Apply(self):
        '''
        【说明】
              返回委托状态为已申请的枚举值

        【语法】
              char Enum_Apply()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumApply()

    def Enum_Period_Tick(self):
        '''
        【说明】
              返回周期类型成交明细的枚举值

        【语法】
              char Enum_Period_Tick()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumPeriodTick()
        
    def Enum_Period_Dyna(self):
        '''
        【说明】
              返回周期类型分时图枚举值

        【语法】
              char Enum_Period_Dyna()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumPeriodDyna() 
        
    def Enum_Period_Second(self):
        '''
        【说明】
              返回周期类型秒线的枚举值

        【语法】
              char Enum_Period_Second()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumPeriodSecond() 
        
    def Enum_Period_Min(self):
        '''
        【说明】
              返回周期类型分钟线的枚举值

        【语法】
              char Enum_Period_Min()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumPeriodMin() 
        
    def Enum_Period_Hour(self):
        '''
        【说明】
              返回周期类型小时线的枚举值

        【语法】
              char Enum_Period_Hour()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumPeriodHour() 
        
    def Enum_Period_Day(self):
        '''
        【说明】
              返回周期类型日线的枚举值

        【语法】
              char Enum_Period_Day()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumPeriodDay() 
        
    def Enum_Period_Week(self):
        '''
        【说明】
              返回周期类型周线的枚举值

        【语法】
              char Enum_Period_Week()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumPeriodWeek()

    def Enum_Period_Month(self):
        '''
        【说明】
              返回周期类型月线的枚举值

        【语法】
              char Enum_Period_Month()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumPeriodMonth() 
    
    def Enum_Period_Year(self):
        '''
        【说明】
              返回周期类型年线的枚举值

        【语法】
              char Enum_Period_Year()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumPeriodYear() 

    def Enum_Period_DayX(self):
        '''
        【说明】
              返回周期类型多日线的枚举值

        【语法】
              char Enum_Period_DayX()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumPeriodDayX()

    def RGB_Red(self):
        '''
        【说明】
             返回颜色类型红色的枚举值

        【语法】
              int RGB_Red()

        【参数】
              无

        【备注】
              返回16进制颜色代码

        【示例】
              无
        '''
        return self._dataModel.getRed()

    def RGB_Green(self):
        '''
        【说明】
              返回颜色类型绿色的枚举值

        【语法】
              int RGB_Green()

        【参数】
              无

        【备注】
              返回16进制颜色代码

        【示例】
              无
        '''
        return self._dataModel.getGreen()

    def RGB_Blue(self):
        '''
        【说明】
              返回颜色类型蓝色的枚举值

        【语法】
              int RGB_Blue()

        【参数】
              无

        【备注】
              返回16进制颜色代码

        【示例】
              无
        '''
        return self._dataModel.getBlue()

    def RGB_Yellow(self):
        '''
        【说明】
              返回颜色类型黄色的枚举值

        【语法】
              int RGB_Yellow()

        【参数】
              无

        【备注】
              返回16进制颜色代码

        【示例】
              无
        '''
        return self._dataModel.getYellow()

    def RGB_Purple(self):
        '''
        【说明】
              返回颜色类型紫色的枚举值

        【语法】
              int RGB_Purple()

        【参数】
              无

        【备注】
              返回16进制颜色代码

        【示例】
              无
        '''
        return self._dataModel.getPurple()

    def RGB_Gray(self):
        '''
        【说明】
              返回颜色类型灰色的枚举值

        【语法】
              int RGB_Gray()

        【参数】
              无

        【备注】
              返回16进制颜色代码

        【示例】
              无
        '''
        return self._dataModel.getGray()

    def RGB_Brown(self):
        '''
        【说明】
              返回颜色类型褐色的枚举值

        【语法】
              int RGB_Brown()

        【参数】
              无

        【备注】
              返回16进制颜色代码

        【示例】
              无
        '''
        return self._dataModel.getBrown()

    def Enum_Order_Market(self):
        '''
        【说明】
              返回订单类型市价单的枚举值

        【语法】
              char Enum_Order_Market()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOrderMarket()

    def Enum_Order_Limit(self):
        '''
        【说明】
              返回订单类型限价单的枚举值

        【语法】
              char Enum_Order_Limit()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOrderLimit()

    def Enum_Order_MarketStop(self):
        '''
        【说明】
              返回订单类型市价止损单的枚举值

        【语法】
              char Enum_Order_MarketStop()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOrderMarketStop()

    def Enum_Order_LimitStop(self):
        '''
        【说明】
              返回订单类型限价止损单的枚举值

        【语法】
              char Enum_Order_LimitStop()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOrderLimitStop()

    def Enum_Order_Execute(self):
        '''
        【说明】
              返回订单类型行权单的枚举值

        【语法】
              char Enum_Order_Execute()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOrderExecute()

    def Enum_Order_Abandon(self):
        '''
        【说明】
              返回订单类型弃权单的枚举值

        【语法】
              char Enum_Order_Abandon()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOrderAbandon()

    def Enum_Order_Enquiry(self):
        '''
        【说明】
              返回订单类型询价单的枚举值

        【语法】
              char Enum_Order_Enquiry()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOrderEnquiry()

    def Enum_Order_Offer(self):
        '''
        【说明】
              返回订单类型应价单的枚举值

        【语法】
              char Enum_Order_Offer()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOrderOffer()

    def Enum_Order_Iceberg(self):
        '''
        【说明】
              返回订单类型冰山单的枚举值

        【语法】
              char Enum_Order_Iceberg()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOrderIceberg()

    def Enum_Order_Ghost(self):
        '''
        【说明】
              返回订单类型影子单的枚举值

        【语法】
              char Enum_Order_Ghost()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOrderGhost()

    def Enum_Order_Swap(self):
        '''
        【说明】
              返回订单类型互换单的枚举值

        【语法】
              char Enum_Order_Swap()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOrderSwap()

    def Enum_Order_SpreadApply(self):
        '''
        【说明】
              返回订单类型套利申请的枚举值

        【语法】
              char Enum_Order_SpreadApply()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOrderSpreadApply()

    def Enum_Order_HedgApply(self):
        '''
        【说明】
              返回订单类型套保申请的枚举值

        【语法】
              char Enum_Order_HedgApply()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOrderHedgApply()

    def Enum_Order_OptionAutoClose(self):
        '''
        【说明】
              返回订单类型行权前期权自对冲申请的枚举值

        【语法】
              char Enum_Order_OptionAutoClose()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOrderOptionAutoClose()

    def Enum_Order_FutureAutoClose(self):
        '''
        【说明】
              返回订单类型履约期货自对冲申请的枚举值

        【语法】
              char Enum_Order_FutureAutoClose()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOrderFutureAutoClose()

    def Enum_Order_MarketOptionKeep(self):
        '''
        【说明】
              返回订单类型做市商留仓的枚举值

        【语法】
              char Enum_Order_MarketOptionKeep()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOrderMarketOptionKeep()

    def Enum_GFD(self):
        '''
        【说明】
              返回订单有效类型当日有效的枚举值

        【语法】
              char Enum_GFD()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumGFD()

    def Enum_GTC(self):
        '''
        【说明】
              返回订单有效类型当日有效的枚举值

        【语法】
              char Enum_GTC()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumGTC()

    def Enum_GTD(self):
        '''
        【说明】
              返回订单有效类型限期有效的枚举值

        【语法】
              char Enum_GTD()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumGTD()

    def Enum_IOC(self):
        '''
        【说明】
              返回订单有效类型即时部分有效的枚举值

        【语法】
              char Enum_IOC()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumIOC()

    def Enum_FOK(self):
        '''
        【说明】
              返回订单有效类型即时全部有效的枚举值

        【语法】
              char Enum_FOK()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumFOK()

    def Enum_Speculate(self):
        '''
        【说明】
              返回订单投保标记投机的枚举值

        【语法】
              char Enum_Speculate()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumSpeculate()

    def Enum_Hedge(self):
        '''
        【说明】
              返回订单投保标记套保的枚举值

        【语法】
              char Enum_Hedge()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumHedge()

    def Enum_Spread(self):
        '''
        【说明】
              返回订单投保标记套利的枚举值

        【语法】
              char Enum_Spread()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumSpread()

    def Enum_Market(self):
        '''
        【说明】
              返回订单投保标记做市的枚举值

        【语法】
              char Enum_Market()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumMarket()

    def Enum_Data_Close(self):
        '''
        【说明】
              返回收盘价的枚举值

        【语法】
              char Enum_Data_Close()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumClose()

    def Enum_Data_Open(self):
        '''
        【说明】
              返回开盘价的枚举值

        【语法】
              char Enum_Data_Open()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOpen()

    def Enum_Data_High(self):
        '''
        【说明】
              返回最高价的枚举值

        【语法】
              char Enum_Data_High()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumHigh()

    def Enum_Data_Low(self):
        '''
        【说明】
              返回最低价的枚举值

        【语法】
              char Enum_Data_Low()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumLow()

    def Enum_Data_Median(self):
        '''
        【说明】
              返回中间价的枚举值，中间价=（最高价+最低价）/ 2

        【语法】
              char Enum_Data_Median()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumMedian()

    def Enum_Data_Typical(self):
        '''
        【说明】
              返回标准价的枚举值，标准价=（最高价+最低价+收盘价）/ 3

        【语法】
              char Enum_Data_Typical()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumTypical()

    def Enum_Data_Weighted(self):
        '''
        【说明】
              返回加权收盘价的枚举值，加权收盘价=（最高价+最低价+开盘价+收盘价）/ 4

        【语法】
              char Enum_Data_Weighted()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumWeighted()

    def Enum_Data_Vol(self):
        '''
        【说明】
              返回成交量的枚举值

        【语法】
              char Enum_Data_Vol()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumVol()

    def Enum_Data_Opi(self):
        '''
        【说明】
              返回持仓量的枚举值

        【语法】
              char Enum_Data_Opi()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumOpi()

    def Enum_Data_Time(self):
        '''
        【说明】
              返回K线时间的枚举值

        【语法】
              char Enum_Data_Time()

        【参数】
              无

        【备注】
              返回字符

        【示例】
              无
        '''
        return self._dataModel.getEnumTime()

    #//////////////////////设置函数////////////////////
    def GetConfig(self):
        return self._dataModel.getConfig()

    def SetUserNo(self, userNo):
        '''
        【说明】
              设置实盘交易账户

        【语法】
              int SetUserNo(string userNo)

        【参数】
              userNo 实盘交易账户，不能为空字符串

        【备注】
              返回整型, 0成功，-1失败
              若需要添加多个不同的交易账号，则可多次调用该账户

        【示例】
              SetUserNo('ET001')
        '''
        return self._dataModel.setUserNo(userNo)

    def SetBarInterval(self, contractNo, barType, barInterval, sampleConfig):
        '''
        【说明】
              设置指定合约的K线类型和K线周期，以及策略历史回测的起始点信息

        【语法】
              int SetBarInterval(string contractNo, char barType, int barInterval, int|string|char sampleConfig=2000)

        【参数】
              contractNo 合约编号
              barType K线类型 T分笔，M分钟，D日线
              barInterval K线周期
              sampleConfig 策略历史回测的起始点信息，可选的值为：
                字符A : 使用所有K线
                字符N : 不执行历史K线
                整数 : 历史回测使用的K线根数
                字符串 : 用于历史回测样本的起始日期，格式为YYYYMMDD，精确到日，例如2019-04-30的日期格式为'20190430'
                默认为使用2000根K线进行回测

        【备注】
              返回整型, 0成功，-1失败
              通过该方法系统会订阅指定合约的K线数据，
              对于相同的合约，如果使用该函数设置不同的K线类型(barType)和周期(barInterval)，则系统会同时订阅指定的K线类型和周期的行情数据
              如果使用该方法订阅了多个合约，则第一条合约为基准合约
              如果在策略中使用SetBarInterval方法订阅了合约，则在设置界面选中的基准合约便不再订阅
              若要订阅秒线数据，可以设置K线类型为'T'，K线类型为n(n>0)，则表示订阅n秒的K线。

        【示例】
              # 订阅合约ZCE|F|SR|906的3分钟K线数据，并使用所有K线样本进行历史回测
              SetBarInterval('ZCE|F|SR|906', 'M', 3, 'A')
              # 订阅合约ZCE|F|SR|906的3分钟K线数据，并不使用K线样本进行历史回测
              SetBarInterval('ZCE|F|SR|906', 'M', 3, 'N')
              # 订阅合约ZCE|F|SR|906的3分钟K线数据，并使用2000根K线样本进行历史回测
              SetBarInterval('ZCE|F|SR|906', 'M', 3, 2000)
              # 订阅合约ZCE|F|SR|906的3分钟K线数据，由于sampleConfig的默认值为2000，所以使用2000根K线样本进行历史回测
              SetBarInterval('ZCE|F|SR|906', 'M', 3)
              # 订阅合约ZCE|F|SR|906的3分钟K线数据，并使用2019-04-30起的K线进行历史回测
              SetBarInterval('ZCE|F|SR|906', 'M', 3, '20190430')
              # 订阅合约ZCE|Z|SR|MAIN的1秒钟K线数据，并使用2000根K线样本进行历史回测
              SetBarInterval(' ZCE|Z|SR|MAIN', 'T', 1, 2000)

        '''
        return self._dataModel.setBarInterval(contractNo, barType, barInterval, sampleConfig)

    def SetSample(self, sampleType, sampleValue):
        '''
        【说明】
              设置策略历史回测的样本数量，默认为使用2000根K线进行回测。

        【语法】
              int SetSample(char sampleType, int|string sampleValue)

        【参数】
              sampleType 历史回测起始点类型
                A : 使用所有K线
                D : 指定日期开始触发
                C : 使用固定根数
                N : 不执行历史K线
              sampleValue 可选，设置历史回测起始点使用的数值
                当sampleType为A或N时，sampleValue的值不设置；
                当sampleType为D时，sampleValue为形如'20190430'的string型触发指定日期；
                当sampleType为C时，sampleValue为int型历史回测使用的K线根数。

        【备注】
              返回整型，0成功，-1失败

        【示例】
              无
        '''
        return self._dataModel.setSample(sampleType, sampleValue)
        
    def SetInitCapital(self, capital):
        '''
        【说明】
              设置初始资金，不设置默认100万

        【语法】
              int SetInitCapital(float capital=10000000)

        【参数】
              capital 初始资金，默认为10000000

        【备注】
              返回整型，0成功，-1失败

        【示例】
              SetInitCapital(200*10000), 设置初始资金为200万
        '''
        return self._dataModel.setInitCapital(capital)
        
    def SetMargin(self, type, value, contractNo):
        '''
        【说明】
              设置保证金参数，不设置或设置失败取界面设置的保证金比例

        【语法】
              int SetMargin(float type, float value=0, string contractNo='')

        【参数】
              type 0：按比例收取保证金， 1：按定额收取保证金，
              value 按比例收取保证金时的比例， 或者按定额收取保证金时的额度，
              contractNo 合约编号，默认为基础合约。

        【备注】
              返回整型，0成功，-1失败

        【示例】
              SetMargin(0, 0.08) 设置基础合约的保证金按比例收取8%
              SetMargin(1, 80000, 'ZCE|F|SR|906') 设置合约ZCE|F|SR|906的保证金按额度收取80000
        '''
        return self._dataModel.setMargin(type, value, contractNo)
        
    def SetTradeFee(self, type, feeType, feeValue, contractNo):
        '''
        【说明】
              设置手续费收取方式

        【语法】
              int SetTradeFee(string type, int feeType, float feeValue, string contractNo='')

        【参数】
              type 手续费类型，A-全部，O-开仓，C-平仓，T-平今
              feeType 手续费收取方式，1-按比例收取，2-按定额收取
              feeValue 按比例收取手续费时，feeValue为收取比例；按定额收取手续费时，feeValue为收取额度
              contractNo 合约编号，默认为基础合约
        【备注】
              返回整型，0成功，-1失败

        【示例】
              SetTradeFee('O', 2, 5) 设置基础合约的开仓手续费为5元/手
              SetTradeFee('O', 1, 0.02) 设置基础合约的开仓手续费为每笔2%
              SetTradeFee('T', 2, 5, "ZCE|F|SR|906") 设置合约ZCE|F|SR|906的平今手续费为5元/手
        '''
        return self._dataModel.setTradeFee(type, feeType, feeValue, contractNo)

    def SetActual(self):
        '''
        【说明】
             设置策略在实盘上运行

        【语法】
              int SetActual()

        【参数】
              无

        【备注】
              返回整型，0成功，-1失败

        【示例】
              无
        '''
        return self._dataModel.setActual()

    def SetOrderWay(self, type):
        '''
        【说明】
             设置发单方式

        【语法】
              int SetOrderWay(int type)

        【参数】
              type 在实盘上的发单方式，1 表示实时发单,2 表示K线完成后发单

        【备注】
              返回整型，0成功，-1失败

        【示例】
              SetOrderWay(1)    # 在实盘上使用实时数据运行策略，实时发单
              SetOrderWay(2)     # 在实盘上使用实时数据运行策略，在K线稳定后发单
        '''
        return self._dataModel.setOrderWay(type)

    def SetTradeDirection(self, tradeDirection):
        '''
        【说明】
             设置交易方向

        【语法】
              int SetTradeDirection(int tradeDirection)

        【参数】
              tradeDirection 设置交易方向
              0 : 双向交易
              1 : 仅多头
              2 : 仅空头

        【备注】
              返回整型，0成功，-1失败

        【示例】
              SetTradeDirection(0)    # 双向交易
        '''
        return self._dataModel.setTradeDirection(tradeDirection)

    def SetMinTradeQuantity(self, tradeQty):
        '''
        【说明】
             设置最小下单量，单位为手，默认值为1手。

        【语法】
              int SetMinTradeQuantity(int tradeQty=1)

        【参数】
              tradeQty 最小下单量，默认为1，不超过1000

        【备注】
              返回整型，0成功，-1失败

        【示例】
              无
        '''
        return self._dataModel.setMinTradeQuantity(tradeQty)

    def SetHedge(self, hedge):
        '''
        【说明】
             设置投保标志

        【语法】
              int SetHedge(char hedge)

        【参数】
              hedge 投保标志
              T : 投机
              B : 套保
              S : 套利
              M : 做市

        【备注】
              返回整型，0成功，-1失败

        【示例】
              SetHedge('T') # 设置基础合约的投保标志为投机
        '''
        return self._dataModel.setHedge(hedge)

    def SetSlippage(self, slippage):
        '''
        【说明】
             设置滑点损耗

        【语法】
              int SetSlippage(float slippage)

        【参数】
              slippage 滑点损耗

        【备注】
              返回整型，0成功，-1失败

        【示例】
              无
        '''
        return self._dataModel.setSlippage(slippage)

    def SetTriggerType(self, type, value):
        '''
        【说明】
             设置触发方式

        【语法】
              int SetTriggerType(int type, int|list value=None)

        【参数】
              type 触发方式，可使用的值为：
                1 : 即时行情触发
                2 : 交易数据触发
                3 : 每隔固定时间触发
                4 : 指定时刻触发
                5 : K线触发
              value 当触发方式是为每隔固定时间触发(type=3)时，value为触发间隔，单位为毫秒，必须为100的整数倍，
              当触发方式为指定时刻触发(type=4)时，value为触发时刻列表，时间的格式为'20190511121314'
              当type为其他值时，该值无效，可以不填

        【备注】
              返回整型，0成功，-1失败

        【示例】
              SetTriggerType(3, 1000) # 每隔1000毫秒触发一次
              SetTriggerType(4, ['084000', '084030', '084100']) # 指定时刻触发
        '''
        return self._dataModel.setTriggerMode(type, value)

    def SetWinPoint(self, winPoint, nPriceType, nAddTick, contractNo):
        '''
        【说明】
             设置止盈点

        【语法】
              void SetWinPoint(int winPoint, int nPriceType = 0, int nAddTick = 0, string contractNo = "")

        【参数】
              winPoint 赢利点数值，若当前价格相对于最近一次开仓价格的盈利点数达到或超过该值，就进行止盈；
              nPriceType 平仓下单价格类型 0:最新价 1：对盘价 2：挂单价 3：市价 4：停板价，默认值为0；
              nAddTick 超价点数 仅当nPrice为0，1，2时有效，默认为0；
              contractNo 合约代码，默认为基准合约。

        【备注】
              止损止盈只对用Buy、Sell函数下单的方式有效，A_SendOrder函数因为在历史阶段下单调用的是Buy、Sell函数，因此止损止盈对A_SendOrder函数在历史阶段下单也生效

        【示例】
              SetWinPoint(10) # 当价格相对于最近一次开仓价格超过10个点，进行止盈平仓。如郑棉合约多头：开仓价格为15000，当前价格大于或等于5*10=50时，即达到15050，则进行平仓。
        '''
        return self._dataModel.setWinPoint(winPoint, nPriceType, nAddTick, contractNo)

    def SetStopPoint(self, stopPoint, nPriceType, nAddTick, contractNo):
        '''
        【说明】
             设置止损点

        【语法】
              void SetStopPoint(int stopPoint, int nPriceType = 0, int nAddTick = 0, string contractNo = "")

        【参数】
              stopPoint 止损点数，若当前价格相对于最近一次开仓价格亏损点数达到或跌破该值，就进行止损；
              nPriceType 平仓下单价格类型 0:最新价 1：对盘价 2：挂单价 3：市价 4：停板价，默认值为0；
              nAddTick 超价点数 仅当nPrice为0，1，2时有效，默认为0；
              contractNo 合约代码，默认为基准合约。

        【备注】
              止损止盈只对用Buy、Sell函数下单的方式有效，A_SendOrder函数因为在历史阶段下单调用的是Buy、Sell函数，因此止损止盈对A_SendOrder函数在历史阶段下单也生效

        【示例】
              SetStopPoint(10) # 当价格跌破10个点，进行止损平仓。 如：如郑棉合约多头：开仓价格为15000，当前价格小于或等于5*10=50时，即达到14950，则进行平仓。
        '''
        return self._dataModel.setStopPoint(stopPoint, nPriceType, nAddTick, contractNo)

    def SetFloatStopPoint(self, startPoint, stopPoint, nPriceType, nAddTick, contractNo):
        '''
        【说明】
             设置浮动止损点

        【语法】
              int SetFloatStopPoint(int startPoint, int stopPoint, int nPriceType = 0, int nAddTick = 0, string contractNo = "")

        【参数】
              startPoint 启动点数，当前价格相对于最后一次开仓价格盈利点数超过该值后启动浮动止损监控；
              stopPoint 止损点数，若当前价格相对于最近一次开仓价格亏损点数达到或跌破该值，就进行止损；
              nPriceType 平仓下单价格类型 0:最新价 1：对盘价 2：挂单价 3：市价 4：停板价，默认为0；
              nAddTick 超价点数 仅当nPrice为0，1，2时有效，默认为0；
              contractNo 合约代码，默认为基准合约。

        【备注】
              止损止盈只对用Buy、Sell函数下单的方式有效，A_SendOrder函数因为在历史阶段下单调用的是Buy、Sell函数，因此止损止盈对A_SendOrder函数在历史阶段下单也生效

        【示例】
              SetFloatStopPoint(20,10)
              举例：郑棉合约，多头方向。开仓价格为15000，当前价格突破15100后开启浮动止损，若此，止损点会随着价格上升而不断上升。假如价格上涨到15300，则此时的止损价格为(15300-50),即15250，若价格从15300回落到15250，则进行自动平仓。
        '''
        return self._dataModel.setFloatStopPoint(startPoint, stopPoint, nPriceType, nAddTick, contractNo)

    def SetStopWinKtBlack(self, op, kt):
        '''
        【说明】
             设置不触发止损止盈和浮动止损的K线类型

        【语法】
              int SetStopWinKtBlack(op, kt)

        【参数】
              op  操作类型必须为 0: 取消设置, 1: 增加设置，中的一个
              kt  K线类型必须为 'D', 'M', 'T'   ，中的一个

        【备注】
              返回整型，0成功，-1失败
              止损止盈只对用Buy、Sell函数下单的方式有效，A_SendOrder函数因为在历史阶段下单调用的是Buy、Sell函数，因此止损止盈对A_SendOrder函数在历史阶段下单也生效

        【示例】
              无
        '''
        return self._dataModel.setStopWinKtBlack(op, kt)

    def GetStopWinKtBlack(self):
        '''
        【说明】
             获取不触发止损止盈和浮动止损的K线类型列表

        【语法】
              list GetStopWinKtBlack()

        【参数】


        【备注】
              返回不触发止损/止盈/浮动止损的K线类型列表

        【示例】
              无
        '''
        return self._dataModel.getStopWinKtBlack()

    def SubQuote(self, contNoTuple):
        '''
        【说明】
             订阅指定合约的即时行情。

        【语法】
              bool SubQuote(string contractNo1, string contractNo2, string contractNo3, ...)

        【参数】
              contractNo 合约编号，为空不做任何操作

        【备注】
              该方法可用在策略的initialize(context)方法中订阅指定合约的即时行情，也可在handle_data(context)方法中动态的订阅指定合约的即时行情。

        【示例】
              SubQuote("ZCE|F|TA|909") 订阅合约TA909的即时行情；
              SubQuote("ZCE|F|TA|909", "ZCE|F|TA|910") 订阅合约TA909和TA910的即时行情；
              SubQuote("ZCE|F|TA") 订阅TA品种下所有合约的即时行情
        '''
        return self._dataModel.subscribeQuote(contNoTuple)

    def UnsubQuote(self, contNoTuple):
        '''
        【说明】
             退订指定合约的即时行情。

        【语法】
              bool UnsubQuote(string contractNo1, string contractNo2, string contractNo3, ...)

        【参数】
              contractNo 合约编号

        【备注】
              该方法可用在策略的initialize(context)方法中退订指定合约的即时行情，也可在handle_data(context)方法中动态的退订指定合约的即时行情。

        【示例】
              UnsubQuote('ZCE|F|SR|909') 退订合约'ZCE|F|SR|909'的即时行情；
              UnsubQuote('ZCE|F|SR|909', 'ZCE|F|SR|910') 退订合约'ZCE|F|SR|909'和'ZCE|F|SR|910'的即时行情；
              UnsubQuote('ZCE|F|SR') 退订合约商品'ZCE|F|SR'对应的所有合约的即时行情。
        '''
        return self._dataModel.unsubscribeQuote(contNoTuple)

    # //////////////////////其他函数////////////////////

    def PlotNumeric(self, name, value, color, main, axis, barsback):
        '''
        【说明】
            在当前Bar输出一个数值

        【语法】
            void PlotNumeric(string name,float value,int color,bool main, char axis, int barsback=0)

        【参数】
            name  输出值的名称，不区分大小写；
            value 输出的数值；
            color 输出值的显示颜色，默认表示使用属性设置框中的颜色；
            main  指标是否加载到主图，True-主图，False-幅图，默认主图
            axis  指标是否使用独立坐标，True-独立坐标，False-非独立坐标，默认非独立坐标
            barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。

        【备注】
            在当前Bar输出一个数值，输出的值用于在上层调用模块显示

        【示例】
            例1：PlotNumeric ("MA1",Ma1Value)
            输出MA1的值。
        '''
        return self._dataModel.setPlotNumeric(name, value, color, main, axis, 1, barsback)
        
    def PlotIcon(self, value, icon, main, barsback):
        '''
        【说明】
            在当前Bar输出一个图标

        【语法】
            void PlotIcon(float value,int icon, bool main, int barsback=0)

        【参数】
            value 输出的值
            icon 图标类型，0-默认图标，1-笑脸，2-哭脸，3-上箭头，4-下箭头，5-上箭头2, 6-下箭头2
                           7-喇叭，8-加锁，9-解锁，10-货币+，11-货币-，12-加号，13-减号，14-叹号，15-叉号
            main  指标是否加载到主图，True-主图，False-幅图，默认主图
            barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。

        【备注】
            在当前Bar输出一个图标，输出的值用于在上层调用模块显示

        【示例】
            例1：PlotIcon(10,14)
            输出MA1的值。
        '''
        return self._dataModel.setPlotIcon(value, icon, main, barsback)

    def PlotDot(self, name, value, icon, color, main, barsback):
        '''
        【说明】
            在当前Bar输出一个点

        【语法】
            void PlotDot(string name, float value, int icon, int color, bool main, int barsback=0)

        【参数】
            value 输出的值
            icon  图标类型0-14，共15种样式，包括箭头，圆点，三角等
            color 输出值的显示颜色，默认表示使用属性设置框中的颜色；
            main  指标是否加载到主图，True-主图，False-幅图，默认主图
            barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。

        【备注】
            在当前Bar输出一个点，输出的值用于在上层调用模块显示。

        【示例】
            PlotDot(name="Dot", value=Close()[-1], main=True)
        '''
        return self._dataModel.setPlotDot(name, value, icon, color, main, barsback)

    def PlotBar(self, name, vol1, vol2, color, main, filled, barsback):
        '''
        【说明】
            绘制一根Bar

        【语法】
            void PlotBar(string name, float vol1, float vol2, int color, bool main, bool filled, int barsback=0)

        【参数】
            name  bar名称
            vol1  柱子起始点
            vol2  柱子结束点
            color 输出值的显示颜色，默认表示使用属性设置框中的颜色；
            main  指标是否加载到主图，True-主图，False-幅图，默认主图
            filled 是否填充, 默认填充
            barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。

        【备注】
            在当前Bar输出一个Bar，输出的值用于在上层调用模块显示。

        【示例】
            PlotBar("BarExample1", Vol()[-1], 0, RGB_Red())
        '''
        return self._dataModel.setPlotBar(name, vol1, vol2, color, main, filled, barsback)

    def PlotText(self, value, text, color, main, barsback):
        '''
        【说明】
            在当前Bar输出字符串

        【语法】
            void PlotText(stirng value, string text, int color, bool main, int barsback=0)

        【参数】
            value 输出的价格
            text 输出的字符串，最多支持19个英文字符
            color 输出值的显示颜色，默认表示使用属性设置框中的颜色；
            main  指标是否加载到主图，True-主图，False-幅图，默认主图
            barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。

        【备注】
            在当前Bar输出字符串，输出的值用于在上层调用模块显示。

        【示例】
            例1：PlotText("ORDER")
        '''
        return self._dataModel.setPlotText(value, text, color, main, barsback)

    def PlotVertLine(self, color, main, axis, barsback):
        '''
        【说明】
            在当前Bar输出一个竖线

        【语法】
            void PlotVertLine(color, bool main, bool axis, int barsback=0)

        【参数】
            color 输出值的显示颜色，默认表示使用属性设置框中的颜色；
            main  指标是否加载到主图，True-主图，False-幅图，默认主图
            axis  指标是否使用独立坐标，True-独立坐标，False-非独立坐标，默认非独立坐标
            barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。

        【备注】
            在当前Bar输出一条竖线，输出的值用于在上层调用模块显示。

        【示例】
            PlotVertLine(main=True, axis = True)
        '''
        return self._dataModel.setPlotVertLine(color, main, axis, barsback)

    def PlotPartLine(self, name, index1, price1, count, price2, color, main, axis, width):
        '''
        【说明】
            绘制斜线段

        【语法】
            void PlotPartLine(string name, int index1, float price1, int count, float price2, int color, bool main, bool axis, int width)

        【参数】
            name   名称
            index1 起始bar索引
            price1 起始价格
            count  从起始bar回溯到结束bar的根数
            price2 结束价格
            color  输出值的显示颜色，默认表示使用属性设置框中的颜色；
            main   指标是否加载到主图，True-主图，False-幅图，默认主图
            axis   指标是否使用独立坐标，True-独立坐标，False-非独立坐标，默认非独立坐标
            width  线段宽度，默认1

        【备注】
            在指定区间输出一个斜线，输出的值用于在上层调用模块显示。

        【示例】
            idx1 = CurrentBar()
            p1 = Close()[-1]
            if idx1 >= 100:
                count = 1
                p2 = Close()[-2]
                PlotPartLine("PartLine", idx1, p1, count, p2, RGB_Red(), True, True, 1)
        '''
        return self._dataModel.setPlotPartLine(name, index1, price1, count, price2, color, main, axis, width)

    def PlotStickLine(self, name, price1, price2, color, main, axis, barsback):
        '''
        【说明】
            绘制竖线段

        【语法】
            void PlotStickLine(string name, float price1, float price2, int color, bool main, bool axis, int barsback=0)

        【参数】
            name   名称
            price1 起始价格
            price2 结束价格
            color 输出值的显示颜色，默认表示使用属性设置框中的颜色；
            main  指标是否加载到主图，True-主图，False-幅图，默认主图
            axis  指标是否使用独立坐标，True-独立坐标，False-非独立坐标，默认非独立坐标
            barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。

        【备注】
            在当前Bar输出一个竖线段，输出的值用于在上层调用模块显示。

        【示例】
            PlotStickLine("StickLine", Close()[-1], Open()[-1], RGB_Blue(), True, True, 0)

        '''
        return self._dataModel.setPlotStickLine(name, price1, price2, color, main, axis, barsback)

    def UnPlotText(self, main, barsback):
        '''
        【说明】
            在当前Bar取消输出的字符串

        【语法】
            void UnPlotText(bool main, int barsback=0)

        【参数】
            main  指标是否加载到主图，True-主图，False-幅图，默认主图
            barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。

        【备注】

        【示例】
            UnPlotText()
        '''
        return self._dataModel.setUnPlotText(main, barsback)

    def UnPlotIcon(self, main, barsback):
        '''
        【说明】
            在当前Bar取消输出的Icon

        【语法】
            void UnPlotIcon(bool main, int barsback=0)

        【参数】
            main  指标是否加载到主图，True-主图，False-幅图，默认主图
            barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。

        【备注】

        【示例】
            UnPlotIcon()
        '''
        return self._dataModel.setUnPlotIcon(main, barsback)

    def UnPlotVertLine(self, main, barsback):
        '''
        【说明】
            在当前Bar取消输出的竖线

        【语法】
            void UnPlotVertLine(bool main, int barsback=0)

        【参数】
            main  指标是否加载到主图，True-主图，False-幅图，默认主图
            barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。

        【备注】

        【示例】
            UnPlotVertLine()
        '''
        return self._dataModel.setUnPlotVertLine(main, barsback)

    def UnPlotDot(self, name, main, barsback):
        '''
        【说明】
            在当前Bar取消输出的Dot

        【语法】
            void UnPlotDot(bool main, int barsback=0)

        【参数】
            name  名称
            main  指标是否加载到主图，True-主图，False-幅图，默认主图
            barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。

        【备注】

        【示例】
            UnPlotDot()
        '''
        return self._dataModel.setUnPlotDot(name, main, barsback)

    def UnPlotBar(self, name, main, barsback):
        '''
        【说明】
            在当前Bar取消输出的Bar

        【语法】
            void UnPlotBar(string name, bool main, int barsback=0)

        【参数】
            name  名称
            main  指标是否加载到主图，True-主图，False-幅图，默认主图
            barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。

        【备注】

        【示例】
            UnPlotBar(“Bar”)
        '''
        return self._dataModel.setUnPlotBar(name, main, barsback)

    def UnPlotNumeric(self, name, main, barsback):
        '''
        【说明】
            在当前Bar取消输出的Numeric

        【语法】
            void UnPlotNumeric(string name, bool main, int barsback=0)

        【参数】
            name  名称
            main  指标是否加载到主图，True-主图，False-幅图，默认主图
            barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。

        【备注】

        【示例】
            UnPlotNumeric("numeric")
        '''
        return self._dataModel.setUnPlotNumeric(name, main, barsback)

    def UnPlotPartLine(self, name, index1, count, main):
        '''
        【说明】
            在当前Bar取消输出的斜线段

        【语法】
            void UnPlotPartLine(string name, int index1, int count, bool main)

        【参数】
            name  名称
            index1 起始bar索引
            count  从起始bar回溯到结束bar的根数
            main  指标是否加载到主图，True-主图，False-幅图，默认主图

        【备注】

        【示例】
            UnPlotPartLine("PartLine", idx1, count, True)
        '''
        return self._dataModel.setUnPlotPartLine(name, index1, count, main)

    def UnPlotStickLine(self, name, main, barsback):
        '''
        【说明】
            在当前Bar取消输出的竖线段

        【语法】
            void UnPlotStickLine(string name, bool main, int barsback=0)

        【参数】
            name  名称
            main  指标是否加载到主图，True-主图，False-幅图，默认主图
            barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。

        【备注】

        【示例】
            UnPlotStickLine("StickLine")
        '''
        return self._dataModel.setUnPlotStickLine(name, main, barsback)

    def LogDebug(self, args):
        '''
        【说明】
             在运行日志窗口中打印用户指定的调试信息。

        【语法】
              LogDebug(args)

        【参数】
              args 用户需要打印的内容，如需要在运行日志窗口中输出多个内容，内容之间用英文逗号分隔。

        【备注】
              无

        【示例】
              accountId = A_AccountID()
              LogDebug("当前使用的用户账户ID为 : ", accountId)
              available = A_Available()
              LogDebug("当前使用的用户账户ID为 : %s，可用资金为 : %10.2f" % (accountId, available))
        '''
        return self._dataModel.LogDebug(args)

    def LogInfo(self, args):
        '''
        【说明】
             在运行日志窗口中打印用户指定的普通信息。

        【语法】
              LogInfo(args)

        【参数】
              args 用户需要打印的内容，如需要在运行日志窗口中输出多个内容，内容之间用英文逗号分隔。

        【备注】
              无

        【示例】
              accountId = A_AccountID()
              LogInfo("当前使用的用户账户ID为 : ", accountId)
              available = A_Available()
              LogInfo("当前使用的用户账户ID为 : %s，可用资金为 : %10.2f" % (accountId, available))
        '''
        return self._dataModel.LogInfo(args)

    def LogWarn(self, args):
        '''
        【说明】
             在运行日志窗口中打印用户指定的警告信息。

        【语法】
              LogWarn(args)

        【参数】
              args 用户需要打印的内容，如需要在运行日志窗口中输出多个内容，内容之间用英文逗号分隔。

        【备注】
              无

        【示例】
              accountId = A_AccountID()
              LogWarn("当前使用的用户账户ID为 : ", accountId)
              available = A_Available()
              LogWarn("当前使用的用户账户ID为 : %s，可用资金为 : %10.2f" % (accountId, available))
        '''
        return self._dataModel.LogWarn(args)

    def LogError(self, args):
        '''
        【说明】
             在运行日志窗口中打印用户指定的错误信息。

        【语法】
              LogError(args)

        【参数】
              args 用户需要打印的内容，如需要在运行日志窗口中输出多个内容，内容之间用英文逗号分隔。

        【备注】
              无

        【示例】
              accountId = A_AccountID()
              LogError("当前使用的用户账户ID为 : ", accountId)
              available = A_Available()
              LogError("当前使用的用户账户ID为 : %s，可用资金为 : %10.2f" % (accountId, available))
        '''
        return self._dataModel.LogError(args)

    def SMA(self, price, period, weight):
        '''
        【说明】
            获取加权移动平均值
        【语法】
            SMA(self, numpy.array price, int period, int weight)
        【参数】
            price   序列值，numpy数组
            period  周期
            weight  权重

        【备注】
            返回值为浮点型numpy.array；
            如果计算成功，此时返回值是计算出的sma值序列；
            如果计算失败，此时返回值numpy.array为空

        【示例】
            SMA(Close(), 12, 2)
        '''
        return self._dataModel.SMA(price, period, weight)
        
    def REF(self, price, length):
        '''
        【说明】
            求N周期前数据的值
        【语法】
            float REF(float price,int length)
            
        【参数】
            Price   价格
            Length  需要计算的周期数。

        【备注】
            Length不能小于0

        【示例】
            # 获得上一周期的收盘价，等价于Close[-2]
            REF(Close(), 1)
            # 返回10周期前的高低收价格的平均值
            REF((Close() + High() + Low())/ 3, 10)
        '''
        return self._dataModel.getRef(price, length)

    def ParabolicSAR(self, high, low, afstep, aflimit):
        '''
        【说明】
            计算抛物线转向
        【语法】
            ParabolicSAR(self, numpy.array high, numpy.array low, float afstep, float aflimit)
        【参数】
            high    最高价序列值，numpy数组
            low     最低价序列值，numpy数组
            afstep  加速因子
            aflimit 加速因子的限量

        【备注】
            返回值为四个值，均为数值型numpy.array
            第一个值序列为oParClose,当前bar的停损值；
            第二个值序列为oParOpen, 下一Bar的停损值；
            第三个值序列为oPosition，输出建议的持仓状态，1 - 买仓，-1 - 卖仓；
            第四个值序列为oTransition, 输出当前Bar的状态是否发生反转，1 或 -1 为反转，0 为保持不变。
            当输入high,low的numpy数组为空时，计算失败，返回的四个值均为空的numpy.array

        【示例】
            ParabolicSAR(High(), Low(), 0.02, 0.2)
        '''
        return self._dataModel.ParabolicSAR(high, low, afstep, aflimit)

    def Highest(self, price, length):
        '''
        【说明】
            求最高

        【语法】
            numpy.array Highest(list|numpy.array price, int length)

        【参数】
            price 用于求最高值的值，必须是数值型列表；
            length 需要计算的周期数，为整型。

        【备注】
            该函数计算指定周期内的数值型序列值的最高值，返回值为浮点数数字列表;
            当price的类型不是list或者price的长度为0时，则返回为空的numpy.array()

        【示例】
            Highest (Close(), 12); 计算12周期以来的收盘价的最高值；
            Highest (HisData(Enum_Data_Typical()), 10); 计算10周期以来高低收价格的平均值的最高值。
        '''
        return self._dataModel.getHighest(price, length)

    def Lowest(self, price, length):
        '''
        【说明】
            求最低

        【语法】
            numpy.array Lowest(list|numpy.array price, int length)

        【参数】
            price 用于求最低值的值，必须是数值型列表；
            length 需要计算的周期数，为整型。

        【备注】
            该函数计算指定周期内的数值型序列值的最低值，返回值为浮点数数字列表;
            当price的类型不是list或者price的长度为0时，则返回为空的numpy.array()

        【示例】
            # 计算12周期以来的收盘价的最低值
            Lowest (Close(), 12)
            # 计算10周期以来高低收价格的平均值的最低值
            Lowest (HisData(Enum_Data_Typical()), 10)
        '''
        return self._dataModel.getLowest(price, length)
        
    def CountIf(self, cond, period):
        '''
        【说明】
            获取最近N周期条件满足的计数

        【语法】
            int CountIf(bool condition, int period)

        【参数】
            condition 传入的条件表达式；
            period 计算条件的周期数

        【备注】
            获取最近N周期条件满足的计数

        【示例】
            CountIf(Close() > Open() , 10); 最近10周期出现Close>Open的周期总数
        '''
        return self._dataModel.getCountIf(cond, period)
        
    def CrossOver(self, price1, price2):
        '''
        【说明】
            求是否上穿

        【语法】
            Bool CrossOver(np.array Price1, np.array Price2)

        【参数】
            Price1 求相关系统的数据源1，必须是np数组;
            Price2 求相关系统的数据源2，必须是np数组;

        【备注】
            该函数返回Price1数值型序列值是否上穿Price2数值型序列值，返回值为布尔型。

        【示例】
            CrossOver(Close[1], AvgPrice); 判断上一个Bar的收盘价Close是否上穿AvgPrice.
            注意：在使用判断穿越的函数时，要尽量避免使用例如close等不确定的元素，否则会导致信号消失，
            一般情况下，Close可以改用High和Low分别判断向上突破（函数CrossOver）和向下突破（函数CrossUnder）。
        '''
        return self._dataModel.getCrossOver(price1, price2)
        
    def CrossUnder(self, price1, price2):
        '''
        【说明】
            求是否下破

        【语法】
            Bool CrossUnder(np.array Price1, np.array Price2)

        【参数】
            Price1 求相关系统的数据源1，必须是np数组;
            Price2 求相关系统的数据源2，必须是np数组;

        【备注】
            该函数返回Price1数值型序列值是否上穿Price2数值型序列值，返回值为布尔型。

        【示例】
            CrossOver(Close[1], AvgPrice); 判断上一个Bar的收盘价Close是否上穿AvgPrice.
            注意：在使用判断穿越的函数时，要尽量避免使用例如close等不确定的元素，否则会导致信号消失，
            一般情况下，Close可以改用High和Low分别判断向上突破（函数CrossOver）和向下突破（函数CrossUnder）。
        '''
        return self._dataModel.getCrossUnder(price1, price2)
     
    def SwingHigh(self, Price, Length, Instance, Strength):
        '''
        【说明】
            求波峰点

        【语法】
            float SwingHigh(np.array Price, int Length, int Instance, int Strength)

        【参数】
            Price 用于求波峰点的值，必须是np数组或者序列变量
            Length 是需要计算的周期数，为整型
            Instance 设置返回哪一个波峰点，1 - 最近的波峰点，2 - 倒数第二个，以此类推
            Strength 设置转折点两边的需要的周期数，必须小于Length；

        【备注】
            该函数计算指定周期内的数值型序列值的波峰点，返回值为浮点数;
            当序列值的CurrentBar小于Length时，该函数返回-1.0

        【示例】
            SwingHigh(Close(), 10, 1, 2);计算Close在最近10个周期的波峰点的值，最高点两侧每侧至少需要2个Bar。
        '''
        return self._dataModel.getSwingHigh(Price, Length, Instance, Strength)

    def SwingLow(self, Price, Length, Instance, Strength):
        '''
        【说明】
            求波谷点

        【语法】
           float SwingLow(np.array Price, int Length, int Instance, int Strength)

        【参数】
            Price 用于求波峰点的值，必须是np数组或者序列变量
            Length 是需要计算的周期数，为整型
            Instance 设置返回哪一个波峰点，1 - 最近的波谷点，2 - 倒数第二个，以此类推
            Strength 设置转折点两边的需要的周期数，必须小于Length；

        【备注】
            该函数计算指定周期内的数值型序列值的波谷点，返回值为浮点数;
            当序列值的CurrentBar小于Length时，该函数返回-1.0

        【示例】
            SwingLow(Close, 10, 1, 2);计算Close在最近10个周期的波谷点的值，最低点两侧需要至少2个Bar。
        '''
        return self._dataModel.getSwingLow(Price, Length, Instance, Strength)
        
    def Alert(self, Info, bKeep, level):
        '''
        【说明】
            弹出警告提醒

        【语法】
            void Alert(string Info, bool bKeep=True, string level='Signal')

        【参数】
            Info  提醒的内容
            bBeep 是否播放警告声音，默认为True 
            level 声音类型, 包括'Signal'、'Info'、'Warn'、'Error'

        【备注】
            多行提示信息需要自行换行，例如：
            AlertStr = '合约: ' + contNo + '\n'\
                       '方向: ' + self._bsMap[direct] + self._ocMap[offset] + '\n' +\
                       '数量: ' + str(share) + '\n' +\
                       '价格: ' + str(price) + '\n' +\
                       '时间: ' + str(curBar['DateTimeStamp']) + '\n'

        【示例】
            Alert("Hello"); 弹出提示
        '''
        return self._dataModel.setAlert(Info, bKeep, level)
        
    def strategyStatus(self):
        '''
        【说明】
             获取当前策略状态

        【语法】
              context.strategyStatus()

        【参数】
              无

        【备注】
              返回字符, 'H' 表示回测阶段; 'C' 表示实时数据阶段

        【示例】
              无
        '''
        pass
        
    def triggerType(self):
        '''
        【说明】
             获取当前触发类型 

        【语法】
              context.triggerType()

        【参数】
              无

        【备注】
              返回字符, 'T' 定时触发; 'C' 周期性触发; 'K' 实时阶段K线触发; 'H' 回测阶段K线触发; 'S' 即时行情触发; 'O' 委托状态变化触发

        【示例】
              无
        '''
        pass
        
    def contractNo(self):
        '''
        【说明】
             获取当前触发合约

        【语法】
              context.contractNo()

        【参数】
              无

        【备注】
              返回字符串,例如: 'SHFE|F|CU|1907'

        【示例】
              无
        '''
        pass
        
    def kLineType(self):
        '''
        【说明】
             获取当前触发的K线类型

        【语法】
              context.kLineType()

        【参数】
              无

        【备注】
              返回字符, 'T' 分笔; 'M' 分钟; 'D' 日线;

        【示例】
              无
        '''
        pass
        
    def kLineSlice(self):
        '''
        【说明】
             获取当前触发的K线周期

        【语法】
              context.kLineSlice()

        【参数】
              无

        【备注】
              返回整型，例如1

        【示例】
              无
        '''
        pass
        
    def tradeDate(self):
        '''
        【说明】
             获取当前触发的交易日

        【语法】
              context.tradeDate()

        【参数】
              无

        【备注】
              返回字符串, YYYYMMDD格式, '20190524'

        【示例】
              无
        '''
        pass
        
    def dateTimeStamp(self):
        '''
        【说明】
             获取当前触发的时间戳

        【语法】
              context.dateTimeStamp()

        【参数】
              无

        【备注】
              返回字符串, YYYYMMDD格式, '20190524'

        【示例】
              无
        '''
        pass
        
    def triggerData(self):
        '''
        【说明】
             获取当前触发类型对应的数据

        【语法】
              context.triggerData()

        【参数】
              无

        【备注】
              K线触发返回的是K线数据
              交易触发返回的是交易数据
              即时行情触发返回的是即时行情数据

        【示例】
              无
        '''
        pass
        
    def StrategyId(self):
        '''
        【说明】
             获取当前策略Id

        【语法】
             int StrategyId()

        【参数】
              无

        【备注】
              无
              
        【示例】
              无
        '''
        return self._dataModel.getStrategyId()

baseApi = BaseApi()

#////////////////////全局函数定义//////////////
#K线函数
def Date(contractNo='', kLineType='', kLineValue=0):
    return baseApi.Date(contractNo, kLineType, kLineValue)

def D(contractNo='', kLineType='', kLineValue=0):
    return baseApi.Date(contractNo, kLineType, kLineValue)

def Time(contractNo='', kLineType='', kLineValue=0):
    return baseApi.Time(contractNo, kLineType, kLineValue)

def T(contractNo='', kLineType='', kLineValue=0):
    return baseApi.Time(contractNo, kLineType, kLineValue)

def Open(contractNo='', kLineType='', kLineValue=0):
    return baseApi.Open(contractNo, kLineType, kLineValue)

def O(contractNo='', kLineType='', kLineValue=0):
    return baseApi.Open(contractNo, kLineType, kLineValue)

def High(contractNo='', kLineType='', kLineValue=0):
    return baseApi.High(contractNo, kLineType, kLineValue)

def H(contractNo='', kLineType='', kLineValue=0):
    return baseApi.High(contractNo, kLineType, kLineValue)

def Low(contractNo='', kLineType='', kLineValue=0):
    return baseApi.Low(contractNo, kLineType, kLineValue)

def L(contractNo='', kLineType='', kLineValue=0):
    return baseApi.Low(contractNo, kLineType, kLineValue)

def Close(contractNo='', kLineType='', kLineValue=0):
    return baseApi.Close(contractNo, kLineType, kLineValue)

def OpenD(daysAgo=0, contractNo=''):
    return baseApi.OpenD(daysAgo, contractNo)

def CloseD(daysAgo=0, contractNo=''):
    return baseApi.CloseD(daysAgo, contractNo)

def HighD(daysAgo=0, contractNo=''):
    return baseApi.HighD(daysAgo, contractNo)

def LowD(daysAgo=0, contractNo=''):
    return baseApi.LowD(daysAgo, contractNo)

def C(contractNo='', kLineType='', kLineValue=0):
    return baseApi.Close(contractNo, kLineType, kLineValue)

def Vol(contractNo='', kLineType='', kLineValue=0):
    return baseApi.Vol(contractNo, kLineType, kLineValue)

def V(contractNo='', kLineType='', kLineValue=0):
    return baseApi.Vol(contractNo, kLineType, kLineValue)

def OpenInt(contractNo='', kLineType='', kLineValue=0):
    return baseApi.OpenInt(contractNo, kLineType, kLineValue)

def TradeDate(contractNo='', kLineType='', kLineValue=0):
    return baseApi.TradeDate(contractNo, kLineType, kLineValue)

def BarCount(contractNo='', kLineType='', kLineValue=0):
    return baseApi.BarCount(contractNo, kLineType, kLineValue)

def CurrentBar(contractNo='', kLineType='', kLineValue=0):
    return baseApi.CurrentBar(contractNo, kLineType, kLineValue)

def CurrentBarEntity(contractNo='', kLineType='', kLineValue=0):
    return baseApi.CurrentBarEntity(contractNo, kLineType, kLineValue)

def BarStatus(contractNo='', kLineType='', kLineValue=0):
    return baseApi.BarStatus(contractNo, kLineType, kLineValue)

def HistoryDataExist(contractNo='', kLineType='', kLineValue=0):
    return baseApi.HistoryDataExist(contractNo, kLineType, kLineValue)

def HisData(type, period='', interval=0, contractNo='', maxLength=100):
    return baseApi.HisData(type, period, interval, contractNo, maxLength)

def HisBarsInfo(contractNo='', kLineType='', kLineValue=0, maxLength=None):
    return baseApi.HisBarsInfo(contractNo, kLineType, kLineValue, maxLength)

#即时行情
def Q_UpdateTime(contractNo=''):
    return baseApi.Q_UpdateTime(contractNo)

def Q_AskPrice(contractNo='', level=1):
    return baseApi.Q_AskPrice(contractNo, level)

def Q_AskPriceFlag(contractNo=''):
    return baseApi.Q_AskPriceFlag(contractNo)

def Q_AskVol(contractNo='', level=1):
    return baseApi.Q_AskVol(contractNo, level)

def Q_AvgPrice(contractNo=''):
    return baseApi.Q_AvgPrice(contractNo)

def Q_BidPrice(contractNo='', level=1):
    return baseApi.Q_BidPrice(contractNo, level)

def Q_BidPriceFlag(contractNo=''):
    return baseApi.Q_BidPriceFlag(contractNo)

def Q_BidVol(contractNo='', level=1):
    return baseApi.Q_BidVol(contractNo, level)

def Q_Close(contractNo=''):
    return baseApi.Q_Close(contractNo)

def Q_High(contractNo=''):
    return baseApi.Q_High(contractNo)

def Q_HisHigh(contractNo=''):
    return baseApi.Q_HisHigh(contractNo)

def Q_HisLow(contractNo=''):
    return baseApi.Q_HisLow(contractNo)

def Q_InsideVol(contractNo=''):
    return baseApi.Q_InsideVol(contractNo)

def Q_Last(contractNo=''):
    return baseApi.Q_Last(contractNo)

def Q_LastDate(contractNo=''):
    return baseApi.Q_LastDate(contractNo)

def Q_LastTime(contractNo=''):
    return baseApi.Q_LastTime(contractNo)

def Q_LastVol(contractNo=''):
    return baseApi.Q_LastVol(contractNo)

def Q_Low(contractNo=''):
    return baseApi.Q_Low(contractNo)

def Q_LowLimit(contractNo=''):
    return baseApi.Q_LowLimit(contractNo)

def Q_Open(contractNo=''):
    return baseApi.Q_Open(contractNo)

def Q_OpenInt(contractNo=''):
    return baseApi.Q_OpenInt(contractNo)

def Q_OpenIntFlag(contractNo=''):
    return baseApi.Q_OpenIntFlag(contractNo)

def Q_OutsideVol(contractNo=''):
    return baseApi.Q_OutsideVol(contractNo)

def Q_PreOpenInt(contractNo=''):
    return baseApi.Q_PreOpenInt(contractNo)

def Q_PreSettlePrice(contractNo=''):
    return baseApi.Q_PreSettlePrice(contractNo)

def Q_PriceChg(contractNo=''):
    return baseApi.Q_PriceChg(contractNo)

def Q_PriceChgRadio(contractNo=''):
    return baseApi.Q_PriceChgRadio(contractNo)

def Q_TodayEntryVol(contractNo=''):
    return baseApi.Q_TodayEntryVol(contractNo)

def Q_TodayExitVol(contractNo=''):
    return baseApi.Q_TodayExitVol(contractNo)

def Q_TotalVol(contractNo=''):
    return baseApi.Q_TotalVol(contractNo)

def Q_TurnOver(contractNo=''):
    return baseApi.Q_TurnOver(contractNo)

def Q_UpperLimit(contractNo=''):
    return baseApi.Q_UpperLimit(contractNo)
    
def Q_TheoryPrice(contractNo=''):
    return baseApi.Q_TheoryPrice(contractNo)

def Q_Sigma(contractNo=''):
    return baseApi.Q_Sigma(contractNo)
    
def Q_Delta(contractNo=''):
    return baseApi.Q_Delta(contractNo)
    
def Q_Gamma(contractNo=''):
    return baseApi.Q_Gamma(contractNo)

def Q_Vega(contractNo=''):
    return baseApi.Q_Vega(contractNo)

def Q_Theta(contractNo=''):
    return baseApi.Q_Theta(contractNo)

def Q_Rho(contractNo=''):
    return baseApi.Q_Rho(contractNo)

def QuoteDataExist(contractNo=''):
    return baseApi.QuoteDataExist(contractNo)

def CalcTradeDate(contractNo='', dateTimeStamp=0):
    return baseApi.CalcTradeDate(contractNo, dateTimeStamp)

#策略状态
def AvgEntryPrice(contractNo=''):
    return baseApi.AvgEntryPrice(contractNo)

def BarsSinceEntry(contractNo=''):
    return baseApi.BarsSinceEntry(contractNo)

def BarsSinceExit(contractNo=''):
    return baseApi.BarsSinceExit(contractNo)

def BarsSinceLastEntry(contractNo=''):
    return baseApi.BarsSinceLastEntry(contractNo)

def BarsSinceLastBuyEntry(contractNo=''):
    return baseApi.BarsSinceLastBuyEntry(contractNo)

def BarsSinceLastSellEntry(contractNo=''):
    return baseApi.BarsSinceLastSellEntry(contractNo)

def BarsSinceToday(contractNo='', barType='', barValue=''):
    return baseApi.BarsSinceToday(contractNo, barType, barValue)

def ContractProfit(contractNo=''):
    return baseApi.ContractProfit(contractNo)

def CurrentContracts(contractNo=''):
    return baseApi.CurrentContracts(contractNo)

def BuyPosition(contractNo=''):
    return baseApi.BuyPosition(contractNo)

def SellPosition(contractNo=''):
    return baseApi.SellPosition(contractNo)

def EntryDate(contractNo=''):
    return baseApi.EntryDate(contractNo)

def EntryPrice(contractNo=''):
    return baseApi.EntryPrice(contractNo)

def EntryTime(contractNo=''):
    return baseApi.EntryTime(contractNo)

def ExitDate(contractNo=''):
    return baseApi.ExitDate(contractNo)

def ExitPrice(contractNo=''):
    return baseApi.ExitPrice(contractNo)

def ExitTime(contractNo=''):
    return baseApi.ExitTime(contractNo)

def LastEntryDate(contractNo=''):
    return baseApi.LastEntryDate(contractNo)

def LastEntryPrice(contractNo=''):
    return baseApi.LastEntryPrice(contractNo)

def LastBuyEntryPrice(contractNo=''):
    return baseApi.LastBuyEntryPrice(contractNo)

def LastSellEntryPrice(contractNo=''):
    return baseApi.LastSellEntryPrice(contractNo)

def HighestSinceLastBuyEntry(contractNo=''):
    return baseApi.HighestSinceLastBuyEntry(contractNo)
    
def HighestSinceLastSellEntry(contractNo=''):
    return baseApi.HighestSinceLastSellEntry(contractNo)

def LowestSinceLastBuyEntry(contractNo=''):
    return baseApi.LowestSinceLastBuyEntry(contractNo)

def LowestSinceLastSellEntry(contractNo=''):
    return baseApi.LowestSinceLastSellEntry(contractNo)

def LastEntryTime(contractNo=''):
    return baseApi.LastEntryTime(contractNo)

def MarketPosition(contractNo=''):
    return baseApi.MarketPosition(contractNo)

def PositionProfit(contractNo=''):
    return baseApi.PositionProfit(contractNo)

def BarsLast(condition):
    return baseApi.BarsLast(condition)

# 策略性能
def Available():
    return baseApi.Available()

def CurrentEquity():
    return baseApi.CurrentEquity()

def FloatProfit(contractNo=''):
    return baseApi.FloatProfit(contractNo)

def GrossLoss():
    return baseApi.GrossLoss()

def GrossProfit():
    return baseApi.GrossProfit()

def Margin(contractNo=''):
    return baseApi.Margin(contractNo)

def NetProfit():
    return baseApi.NetProfit()

def NumEvenTrades():
    return baseApi.NumEvenTrades()

def NumLosTrades():
    return baseApi.NumLosTrades()

def NumWinTrades():
    return baseApi.NumWinTrades()

def NumAllTimes():
    return baseApi.NumAllTimes()

def NumWinTimes():
    return baseApi.NumWinTimes()

def NumLoseTimes():
    return baseApi.NumLoseTimes()

def NumEventTimes():
    return baseApi.NumEventTimes()

def PercentProfit():
    return baseApi.PercentProfit()

def TradeCost():
    return baseApi.TradeCost()

def TotalTrades(contractNo=''):
    return baseApi.TotalTrades(contractNo)

# 账户函数
def A_AccountID():
    return baseApi.A_AccountID()
    
def A_AllAccountID():
    return baseApi.A_AllAccountID()

def A_GetAllPositionSymbol(userNo=''):
    return baseApi.A_GetAllPositionSymbol(userNo)

def A_Cost(userNo=''):
    return baseApi.A_Cost(userNo)

def A_Assets(userNo=''):
    return baseApi.A_Assets(userNo)

def A_Available(userNo=''):
    return baseApi.A_Available(userNo)

def A_Margin(userNo=''):
    return baseApi.A_Margin(userNo)

def A_ProfitLoss(userNo=''):
    return baseApi.A_ProfitLoss(userNo)

def A_CoverProfit(userNo=''):
    return baseApi.A_CoverProfit(userNo)

def A_TotalFreeze(userNo=''):
    return baseApi.A_TotalFreeze(userNo)

def A_BuyAvgPrice(contractNo='', userNo=''):
    return baseApi.A_BuyAvgPrice(contractNo, userNo)

def A_BuyPosition(userNo='', contractNo=''):
    return baseApi.A_BuyPosition(contractNo, userNo)
    
def A_BuyPosition(contractNo='', userNo=''):
    return baseApi.A_BuyPosition(contractNo, userNo)

def A_BuyPositionCanCover(contractNo='',userNo=''):
    return baseApi.A_BuyPositionCanCover(contractNo, userNo)

def A_BuyProfitLoss(contractNo='', userNo=''):
    return baseApi.A_BuyProfitLoss(contractNo, userNo)

def A_SellAvgPrice(contractNo='', userNo=''):
    return baseApi.A_SellAvgPrice(contractNo, userNo)

def A_SellPosition(contractNo='', userNo=''):
    return baseApi.A_SellPosition(contractNo, userNo)

def A_SellPositionCanCover(contractNo='', userNo=''):
    return baseApi.A_SellPositionCanCover(contractNo, userNo)

def A_SellProfitLoss(contractNo='', userNo=''):
    return baseApi.A_SellProfitLoss(contractNo, userNo)

def A_TotalAvgPrice(contractNo='', userNo=''):
    return baseApi.A_TotalAvgPrice(contractNo, userNo)

def A_TotalPosition(contractNo='', userNo=''):
    return baseApi.A_TotalPosition(contractNo, userNo)

def A_TotalProfitLoss(contractNo='', userNo=''):
    return baseApi.A_TotalProfitLoss(contractNo, userNo)

def A_TodayBuyPosition(contractNo='', userNo=''):
    return baseApi.A_TodayBuyPosition(contractNo, userNo)

def A_TodaySellPosition(contractNo='', userNo=''):
    return baseApi.A_TodaySellPosition(contractNo, userNo)

def A_OrderBuyOrSell(localOrderId):
    return baseApi.A_OrderBuyOrSell('', localOrderId)

def A_OrderEntryOrExit(localOrderId):
    return baseApi.A_OrderEntryOrExit('', localOrderId)

def A_OrderFilledLot(localOrderId):
    return baseApi.A_OrderFilledLot('', localOrderId)

def A_OrderFilledPrice(localOrderId):
    return baseApi.A_OrderFilledPrice('', localOrderId)

def A_OrderLot(localOrderId):
    return baseApi.A_OrderLot('', localOrderId)

def A_OrderPrice(localOrderId):
    return baseApi.A_OrderPrice('', localOrderId)

def A_OrderStatus(localOrderId):
    return baseApi.A_OrderStatus('', localOrderId)

def A_OrderIsClose(localOrderId):
    return baseApi.A_OrderIsClose('', localOrderId)

def A_OrderTime(localOrderId):
    return baseApi.A_OrderTime('', localOrderId)

def A_FirstOrderNo(contractNo1='', contractNo2='', userNo=''):
    return baseApi.A_FirstOrderNo(contractNo1, contractNo2, userNo)

def A_NextOrderNo(localOrderId=0, contractNo1='', contractNo2='', userNo=''):
    return baseApi.A_NextOrderNo(localOrderId, contractNo1, contractNo2, userNo)

def A_LastOrderNo(contractNo1='', contractNo2='', userNo=''):
    return baseApi.A_LastOrderNo(contractNo1, contractNo2, userNo)

def A_FirstQueueOrderNo(contractNo1='', contractNo2='', userNo=''):
    return baseApi.A_FirstQueueOrderNo(contractNo1, contractNo2, userNo)

def A_NextQueueOrderNo(localOrderId=0, contractNo1='', contractNo2='', userNo=''):
    return baseApi.A_NextQueueOrderNo(localOrderId, contractNo1, contractNo2, userNo)

def A_AllQueueOrderNo(contractNo='', userNo=''):
    return baseApi.A_AllQueueOrderNo(contractNo, userNo)

def A_LatestFilledTime(contractNo='', userNo=''):
    return baseApi.A_LatestFilledTime(contractNo, userNo)

def A_AllOrderNo(contractNo='', userNo=''):
    return baseApi.A_AllOrderNo(contractNo, userNo)

def A_OrderContractNo(localOrderId=0, userNo=''):
    return baseApi.A_OrderContractNo(userNo, localOrderId)

def A_SendOrder(orderDirct, entryOrExit, orderQty, orderPrice, contractNo='', userNo='', orderType='2', validType='0', hedge='T', triggerType='N', triggerMode='N', triggerCondition='N', triggerPrice=0):
    return baseApi.A_SendOrder(userNo, contractNo, orderDirct, entryOrExit, orderQty, orderPrice, orderType, validType, hedge, triggerType, triggerMode, triggerCondition, triggerPrice)

def A_ModifyOrder(localOrderId, orderDirct, entryOrExit, orderQty, orderPrice, contractNo='', userNo='', orderType='2', validType='0', hedge='T', triggerType='N', triggerMode='N', triggerCondition='N', triggerPrice=0):
    return baseApi.A_ModifyOrder(userNo, localOrderId, contractNo, orderDirct, entryOrExit, orderQty, orderPrice, orderType, validType, hedge, triggerType, triggerMode, triggerCondition, triggerPrice)

def A_DeleteOrder(localOrderId):
    return baseApi.A_DeleteOrder('', localOrderId)

def A_GetOrderNo(localOrderId):
    return baseApi.A_GetOrderNo(localOrderId)

def DeleteAllOrders(contractNo='', userNo=''):
    return baseApi.DeleteAllOrders(contractNo, userNo)

#策略交易
def Buy(share=0, price=0, contractNo=None, needCover=True, userNo=''):
    return baseApi.Buy(share, price, contractNo, needCover, userNo)

def BuyToCover(share=0, price=0, contractNo=None, userNo='', coverFlag = 'A'):
    return baseApi.BuyToCover(share, price, contractNo, userNo, coverFlag)

def Sell(share=0, price=0, contractNo=None, userNo='', coverFlag = 'A'):
    return baseApi.Sell(share, price, contractNo, userNo, coverFlag)

def SellShort(share=0, price=0, contractNo=None, needCover=True, userNo=''):
    return baseApi.SellShort(share, price, contractNo, needCover, userNo)

def StartTrade():
    return baseApi.StartTrade()

def StopTrade():
    return baseApi.StopTrade()

def IsTradeAllowed():
    return baseApi.IsTradeAllowed()
    
# 枚举函数
def Enum_Buy():
    return baseApi.Enum_Buy()

def Enum_Sell():
    return baseApi.Enum_Sell()

def Enum_Entry():
    return baseApi.Enum_Entry()

def Enum_Exit():
    return baseApi.Enum_Exit()

def Enum_ExitToday():
    return baseApi.Enum_ExitToday()

def Enum_EntryExitIgnore():
    return baseApi.Enum_EntryExitIgnore()

def Enum_Sended():
    return baseApi.Enum_Sended()

def Enum_Accept():
    return baseApi.Enum_Accept()

def Enum_Triggering():
    return baseApi.Enum_Triggering()

def Enum_Active():
    return baseApi.Enum_Active()

def Enum_Queued():
    return baseApi.Enum_Queued()

def Enum_FillPart():
    return baseApi.Enum_FillPart()

def Enum_Filled():
    return baseApi.Enum_Filled()

def Enum_Canceling():
    return baseApi.Enum_Canceling()

def Enum_Modifying():
    return baseApi.Enum_Modifying()

def Enum_Canceled():
    return baseApi.Enum_Canceled()

def Enum_PartCanceled():
    return baseApi.Enum_PartCanceled()

def Enum_Fail():
    return baseApi.Enum_Fail()

def Enum_Suspended():
    return baseApi.Enum_Suspended()

def Enum_Apply():
    return baseApi.Enum_Apply()

def Enum_Period_Tick():
    return baseApi.Enum_Period_Tick()
    
# def Enum_Period_Dyna():
#     return baseApi.Enum_Period_Dyna()
#
# def Enum_Period_Second():
#     return baseApi.Enum_Period_Second()
    
def Enum_Period_Min():
    return baseApi.Enum_Period_Min()
    
# def Enum_Period_Hour():
#     return baseApi.Enum_Period_Hour()
    
def Enum_Period_Day():
    return baseApi.Enum_Period_Day()
    
# def Enum_Period_Week():
#     return baseApi.Enum_Period_Week()
#
# def Enum_Period_Month():
#     return baseApi.Enum_Period_Month()
#
# def Enum_Period_Year():
#     return baseApi.Enum_Period_Year()
#
# def Enum_Period_DayX():
#     return baseApi.Enum_Period_DayX()

def RGB_Red():
    return baseApi.RGB_Red()

def RGB_Green():
    return baseApi.RGB_Green()

def RGB_Blue():
    return baseApi.RGB_Blue()

def RGB_Purple():
    return baseApi.RGB_Purple()

def RGB_Gray():
    return baseApi.RGB_Gray()

def RGB_Brown():
    return baseApi.RGB_Brown()
    
def RGB_Yellow():
    return baseApi.RGB_Yellow()

def Enum_Order_Market():
    return baseApi.Enum_Order_Market()

def Enum_Order_Limit():
    return baseApi.Enum_Order_Limit()

def Enum_Order_MarketStop():
    return baseApi.Enum_Order_MarketStop()

def Enum_Order_LimitStop():
    return baseApi.Enum_Order_LimitStop()

def Enum_Order_Execute():
    return baseApi.Enum_Order_Execute()

def Enum_Order_Abandon():
    return baseApi.Enum_Order_Abandon()

def Enum_Order_Enquiry():
    return baseApi.Enum_Order_Enquiry()

def Enum_Order_Offer():
    return baseApi.Enum_Order_Offer()

def Enum_Order_Iceberg():
    return baseApi.Enum_Order_Iceberg()

def Enum_Order_Ghost():
    return baseApi.Enum_Order_Ghost()

def Enum_Order_Swap():
    return baseApi.Enum_Order_Swap()

def Enum_Order_SpreadApply():
    return baseApi.Enum_Order_SpreadApply()

def Enum_Order_HedgApply():
    return baseApi.Enum_Order_HedgApply()

def Enum_Order_OptionAutoClose():
    return baseApi.Enum_Order_OptionAutoClose()

def Enum_Order_FutureAutoClose():
    return baseApi.Enum_Order_FutureAutoClose()

def Enum_Order_MarketOptionKeep():
    return baseApi.Enum_Order_MarketOptionKeep()

def Enum_GFD():
    return baseApi.Enum_GFD()

def Enum_GTC():
    return baseApi.Enum_GTC()

def Enum_GTD():
    return baseApi.Enum_GTD()

def Enum_IOC():
    return baseApi.Enum_IOC()

def Enum_FOK():
    return baseApi.Enum_FOK()

def Enum_Speculate():
    return baseApi.Enum_Speculate()

def Enum_Hedge():
    return baseApi.Enum_Hedge()

def Enum_Spread():
    return baseApi.Enum_Spread()

def Enum_Market():
    return baseApi.Enum_Market()

def Enum_Data_Close():
    return baseApi.Enum_Data_Close()

def Enum_Data_Open():
    return baseApi.Enum_Data_Open()

def Enum_Data_High():
    return baseApi.Enum_Data_High()

def Enum_Data_Low():
    return baseApi.Enum_Data_Low()

def Enum_Data_Median():
    return baseApi.Enum_Data_Median()

def Enum_Data_Typical():
    return baseApi.Enum_Data_Typical()

def Enum_Data_Weighted():
    return baseApi.Enum_Data_Weighted()

def Enum_Data_Vol():
    return baseApi.Enum_Data_Vol()

def Enum_Data_Opi():
    return baseApi.Enum_Data_Opi()

def Enum_Data_Time():
    return baseApi.Enum_Data_Time()

# 设置函数
def GetConfig():
    return baseApi.GetConfig()

def SetUserNo(userNo):
    return baseApi.SetUserNo(userNo)

def SetBarInterval(contractNo, barType, barInterval, barCount=2000):
    return baseApi.SetBarInterval(contractNo, barType, barInterval, barCount)

# def SetSample(sampleType='C', sampleValue=2000):
#     return baseApi.SetSample(sampleType, sampleValue)

def SetInitCapital(capital=10000000):
    return baseApi.SetInitCapital(capital)

def SetMargin(type, value=0, contractNo=''):
    return baseApi.SetMargin(type, value, contractNo)

def SetTradeFee(type, feeType, feeValue, contractNo=''):
    return baseApi.SetTradeFee(type, feeType, feeValue, contractNo)

# def SetTradeMode(inActual, useSample, useReal):
# #     return baseApi.SetTradeMode(inActual, useSample, useReal)

def SetActual():
    return baseApi.SetActual()

def SetOrderWay(type):
    return baseApi.SetOrderWay(type)

def SetTradeDirection(tradeDirection):
    return baseApi.SetTradeDirection(tradeDirection)

def SetMinTradeQuantity(tradeQty=1):
    return baseApi.SetMinTradeQuantity(tradeQty)

def SetHedge(hedge):
    return baseApi.SetHedge(hedge)

def SetSlippage(slippage):
    return baseApi.SetSlippage(slippage)

def SetTriggerType(type, value=None):
    return baseApi.SetTriggerType(type, value)

def SetWinPoint(winPoint, nPriceType=0, nAddTick=0, contractNo=''):
    return baseApi.SetWinPoint(winPoint, nPriceType, nAddTick, contractNo)

def SetStopPoint(stopPoint, nPriceType=0, nAddTick=0, contractNo=''):
    return baseApi.SetStopPoint(stopPoint, nPriceType, nAddTick, contractNo)

def SetFloatStopPoint(startPoint, stopPoint, nPriceType=0, nAddTick=0, contractNo=''):
    return baseApi.SetFloatStopPoint(startPoint, stopPoint, nPriceType, nAddTick, contractNo)

def SetStopWinKtBlack(op, kt):
    return baseApi.SetStopWinKtBlack(op, kt)

def SubQuote(*args):
    return baseApi.SubQuote(args)

def UnsubQuote(*args):
    return baseApi.UnsubQuote(args)

# 属性函数
def BarInterval():
    return baseApi.BarInterval()

def BarType():
    return baseApi.BarType()

def BidAskSize(contractNo=''):
    return baseApi.BidAskSize(contractNo)

def CanTrade(contractNo=''):
    return baseApi.CanTrade(contractNo)

def ContractUnit(contractNo=''):
    return baseApi.ContractUnit(contractNo)

def ExchangeName(contractNo=''):
    return baseApi.ExchangeName(contractNo)
    
def ExchangeTime(exchangeNo):
    return baseApi.ExchangeTime(exchangeNo)
  
def ExchangeStatus(exchangeNo):
    return baseApi.ExchangeStatus(exchangeNo)
    
def CommodityStatus(commodityNo):
    return baseApi.CommodityStatus(commodityNo)

def ExpiredDate(contractNo=''):
    return baseApi.ExpiredDate(contractNo)

def GetSessionCount(contractNo=''):
    return baseApi.GetSessionCount(contractNo)

def GetSessionEndTime(contractNo='', index=0):
    return baseApi.GetSessionEndTime(contractNo, index)

def GetSessionStartTime(contractNo='', index=0):
    return baseApi.GetSessionStartTime(contractNo, index)

def GetNextTimeInfo(contractNo, timeStr):
    return baseApi.GetNextTimeInfo(contractNo, timeStr)
    
def TradeSessionBeginTime(contractNo='', tradeDate=0, index=0):
    return baseApi.TradeSessionBeginTime(contractNo, tradeDate, index)

def TradeSessionEndTime(contractNo='', tradeDate=0, index=-1):
    return baseApi.TradeSessionEndTime(contractNo, tradeDate, index)

def CurrentTime():
    return baseApi.CurrentTime()
    
def CurrentDate():
    return baseApi.CurrentDate()

def TimeDiff(datetime1, datetime2=-1.0):
    return baseApi.TimeDiff(datetime1, datetime2)

def IsInSession(contractNo=''):
    return baseApi.IsInSession(contractNo)

def MarginRatio(contractNo=''):
    return baseApi.MarginRatio(contractNo)

def MaxBarsBack():
    return baseApi.MaxBarsBack()

def MaxSingleTradeSize():
    return baseApi.MaxSingleTradeSize()

def PriceTick(contractNo=''):
    return baseApi.PriceTick(contractNo)

def OptionStyle(contractNo=''):
    return baseApi.OptionStyle(contractNo)

def OptionType(contractNo=''):
    return baseApi.OptionType(contractNo)

def PriceScale(contractNo=''):
    return baseApi.PriceScale(contractNo)

def RelativeSymbol():
    return baseApi.RelativeSymbol()

def StrikePrice():
    return baseApi.StrikePrice()

def Symbol():
    return baseApi.Symbol()

def SymbolName(contractNo=''):
    return baseApi.SymbolName(contractNo)

def SymbolType(contractNo=''):
    return baseApi.SymbolType(contractNo)

def GetTrendContract(contractNo=''):
    return baseApi.GetTrendContract(contractNo)

#其他函数
def PlotNumeric(name, value, color=0xdd0000, main=True, axis=False, barsback=0):
    return baseApi.PlotNumeric(name, value, color, main, axis, barsback)
    
def PlotIcon(value, icon=0, main=False, barsback=0):
    return baseApi.PlotIcon(value, icon, main, barsback)

def PlotDot(name, value, icon=0, color=0xdd0000, main=True, barsback=0):
    return baseApi.PlotDot(name, value, icon, color, main, barsback)

def PlotBar(name, vol1, vol2, color=0xdd0000, main=True, filled=True, barsback=0):
    return baseApi.PlotBar(name, vol1, vol2, color, main, filled, barsback)

def PlotText(value, text, color=0x999999, main=True, barsback=0):
    return baseApi.PlotText(value, text, color, main, barsback) 
    
def PlotVertLine(color=0xdd0000, main=True, axis=False, barsback=0):
    return baseApi.PlotVertLine(color, main, axis, barsback)

def PlotPartLine(name, index1, price1, count, price2, color=0xdd0000, main=True, axis=False, width=1):
    return baseApi.PlotPartLine(name, index1, price1, count, price2, color, main, axis, width)

def PlotStickLine(name, price1, price2, color=0xdd0000, main=True, axis=False, barsback=0):
    return baseApi.PlotStickLine(name, price1, price2, color, main, axis, barsback)

def UnPlotText(main=True, barsback=0):
    return baseApi.UnPlotText(main, barsback)

def UnPlotIcon(main=True, barsback=0):
    return baseApi.UnPlotIcon(main, barsback)

def UnPlotVertLine(main=True, barsback=0):
    return baseApi.UnPlotVertLine(main, barsback)

def UnPlotDot(name, main=True, barsback=0):
    return baseApi.UnPlotDot(name, main, barsback)

def UnPlotBar(name, main=True, barsback=0):
    return baseApi.UnPlotBar(name, main, barsback)

def UnPlotNumeric(name, main=True, barsback=0):
    return baseApi.UnPlotNumeric(name, main, barsback)

def UnPlotPartLine(name, index1, count, main=True):
    return baseApi.UnPlotPartLine(name, index1, count, main)

def UnPlotStickLine(name, main=True, barsback=0):
    return baseApi.UnPlotStickLine(name, main, barsback)

def LogDebug(*args):
    return baseApi.LogDebug(args)

def LogInfo(*args):
    return baseApi.LogInfo(args)

def LogWarn(*args):
    return baseApi.LogWarn(args)

def LogError(*args):
    return baseApi.LogError(args)

def SMA(price, period, weight):
    return baseApi.SMA(price, period, weight)
    
def REF(price, length):
    return baseApi.REF(price, length)

def ParabolicSAR(high, low, afstep, aflimit):
    return baseApi.ParabolicSAR(high, low, afstep, aflimit)

def Highest(price, length):
    return baseApi.Highest(price, length)

def Lowest(price, length):
    return baseApi.Lowest(price, length)
    
def CountIf(cond, peroid):
    return baseApi.CountIf(cond, peroid) 

def CrossOver(price1, price2):
    return baseApi.CrossOver(price1, price2) 

def CrossUnder(price1, price2):
    return baseApi.CrossUnder(price1, price2) 

def SwingHigh(Price, Length, Instance, Strength):
    return baseApi.SwingHigh(Price, Length, Instance, Strength)
    
def SwingLow(Price, Length, Instance, Strength):
    return baseApi.SwingLow(Price, Length, Instance, Strength)

def Alert(Info, bKeep=True, level='Signal'):
    return baseApi.Alert(Info, bKeep, level)
    
def StrategyId():
    return baseApi.StrategyId()

    
