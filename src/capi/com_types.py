from ctypes import *

# 内部通讯协议定义
'''
msg = 
{
    'EventSrc'        : 事件来源, str
    'EventCode'       : 事件编号, int
    'StrategyId'      : 策略ID, int
    'SessionId'       : 会话ID, int
    'Data'            : 消息内容,str,dict,list or other built-in types
}
'''

# CApi->PyApi交互协议
'''
msg = 
{
    'SrvSrc'         , 事件来源, c_ubyte
    'SrvEvent'       , 事件类型, c_ubyte
    'SrvChain'       , 是否有后续报文，c_ubyte
    'SrvErrorCode'   , 错误码, c_int
    'SrvErrorText'   , 错误信息, c_char*201
    'SrvData'        , 事件消息体, c_void_p
    'DataFieldSize'  , 单个消息体大小, c_ushort
    'DataFieldCount' , 消息体个数, c_ushort
    'UserNo'         , 用户号, c_char*21
    'ContractNo'     , 合约号, c_char*101
    'KLineType'      , K线类型, c_char
    'KLineSlice'     , K线周期, c_ubyte
    'SessionId'      , 会话号, c_uint
}
'''

#PyApi->策略引擎交互协议
'''
msg = 
{
    'SrvSrc'         , 事件来源, str
    'SrvEvent'       , 事件类型, int
    'SrvChain'       , 是否有后续报文, str
    'SrvErrorCode'   , 错误码, int
    'SrvErrorText'   , 错误信息, str
    'SrvData'        , 事件消息体, list[dict]
    'DataFieldSize'  , 单个消息体大小, int
    'DataFieldCount' , 消息体个数, int
    'UserNo'         , 用户号, str
    'ContractNo'     , 合约号, str
    'KLineType'      , K线类型, str
    'KLineSlice'     , K线周期, int
    'SessionId'      , 会话号, int
}
'''
        
# 事件类型定义

#////////////////////界面->引擎事件定义////////////////////////
EV_UI2EG_LOADSTRATEGY             = 0x101           # 加载策略
EV_UI2EG_REPORT                   = 0x102           # 出报告，可分发事件
EV_UI2EG_STRATEGY_PAUSE           = 0x103           # 策略暂停
EV_UI2EG_STRATEGY_RESUME          = 0x104           # 策略恢复
EV_UI2EG_EQUANT_EXIT              = 0x105           # 量化退出
EV_UI2EG_STRATEGY_QUIT            = 0x106           # 策略停止
EV_UI2EG_STRATEGY_FIGURE          = 0x107           # 策略信号和指标图
EV_UI2EG_STRATEGY_REMOVE          = 0x108           # 删除策略
EV_UI2EG_STRATEGY_RESTART         = 0x109           # 更改参数启动策略
EV_UI2EG_SYNCPOS_CONF             = 0x110           # 持仓同步参数

#////////////////////引擎->界面事件定义////////////////////////
EV_EG2UI_LOADSTRATEGY_RESPONSE    = 0x181           # 策略加载应答
EV_EG2UI_REPORT_RESPONSE          = 0x182           # 回测报告应答
EV_EG2UI_CHECK_RESULT             = 0x183           # 检测结果
EV_EG2ST_MONITOR_INFO             = 0x184           # 监控信息
EV_EG2UI_STRATEGY_STATUS          = 0x185           # 策略变化事件 
EV_EG2UI_POSITION_NOTICE          = 0x186           # 持仓同步信息
EV_EG2UI_USER_LOGOUT_NOTICE       = 0x187           # 资金账号登出消息
EV_EG2UI_RUNMODE_SWITCH           = 0x188           # 策略运行模式切换，实盘/虚拟

#////////////////////策略->引擎事件定义////////////////////////
EV_ST2EG_EXCHANGE_REQ             = 0x201           #查询交易所信息
EV_ST2EG_CURRENCY_REQ             = 0x202           #查询币种
EV_ST2EG_COMMODITY_REQ            = 0x203           #查询品种信息
EV_ST2EG_CONTRACT_REQ             = 0x204           #查询合约信息
EV_ST2EG_TIMEBUCKET_REQ           = 0x205           #查询品种时间模板
EV_ST2EG_UNDERLAYMAPPING_REQ      = 0x209           #查询主力/近月的合约

EV_ST2EG_SUB_QUOTE                = 0x220           #订阅即时行情
EV_ST2EG_UNSUB_QUOTE              = 0x221           #退订即时行
EV_ST2EG_SUB_HISQUOTE             = 0x223           #订阅历史行情
EV_ST2EG_UNSUB_HISQUOTE           = 0x224           #退订历史行情

EV_ST2EG_LOGINNO_REQ              = 0x240           #请求登录账号
EV_ST2EG_USERNO_REQ               = 0x241           #请求资金账号
EV_ST2EG_MONEY_REQ                = 0x242           #请求资金信息
EV_ST2EG_ORDER_REQ                = 0x243           #请求委托信息
EV_ST2EG_MATCH_REQ                = 0x244           #请求成交信息
EV_ST2EG_POSITION_REQ             = 0x245           #请求持仓信息
EV_ST2EG_POSITION_NOTICE          = 0x246           #同步持仓信息

EV_ST2EG_ACTUAL_ORDER             = 0x260           # 实盘订单
EV_ST2EG_ACTUAL_CANCEL_ORDER      = 0x261           # 实盘撤单
EV_ST2EG_ACTUAL_MODIFY_ORDER      = 0x262           # 实盘改单


EV_ST2EG_SWITCH_STRATEGY          = 0x280           #切换策略图
EV_ST2EG_NOTICE_KLINEDATA         = 0x281           #推送K线数据
EV_ST2EG_UPDATE_KLINEDATA         = 0x282           #更新K线数据
EV_ST2EG_ADD_KLINESERIES          = 0x283           #增加指标数据
EV_ST2EG_NOTICE_KLINESERIES       = 0x284           #推送指标数据
EV_ST2EG_UPDATE_KLINESERIES       = 0x285           #更新指标数据
EV_ST2EG_ADD_KLINESIGNAL          = 0x286           #增加信号数据
EV_ST2EG_NOTICE_KLINESIGNAL       = 0x287           #推送信号数据
EV_ST2EG_UPDATE_KLINESIGNAL       = 0x288           #更新信号数据
EV_ST2EG_UPDATE_STRATEGYDATA      = 0x289           #刷新信号、指标数
EV_ST2EG_STRATEGY_EXCEPTION       = 0x28A           #策略出现异常事件
ST_ST2EG_SYNC_CONFIG              = 0x28B           #策略向引擎同步自己的配置

#///////////////////引擎->策略事件定义////////////////////////
EV_EG2ST_EXCHANGE_RSP             = 0X301           #查询交易所信息
EV_EG2ST_CURRENCY_RSP             = 0x302           #查询币种
EV_EG2ST_COMMODITY_RSP            = 0x303           #查询品种信息
EV_EG2ST_CONTRACT_RSP             = 0x304           #查询合约信息
EV_EG2ST_TIMEBUCKET_RSP           = 0x305           #查询品种时间模板
EV_EG2ST_UNDERLAYMAPPING_RSP      = 0x306           #查询主力/近月对应的合约

EV_EG2ST_SUBQUOTE_RSP             = 0x320           #行情订阅应答
EV_EG2ST_SNAPSHOT_NOTICE          = 0X321           #普通行情推送
EV_EG2ST_DEPTH_NOTICE             = 0x322           #深度行情推送
EV_EG2ST_HISQUOTE_RSP             = 0x323           #历史K线查询应答
EV_EG2ST_HISQUOTE_NOTICE          = 0x324           #历史行情推送

EV_EG2ST_LOGINNO_RSP              = 0x340           #登录账号应答，适用登录后启动的策略
EV_EG2ST_USERNO_RSP               = 0x341           #资金账号应答，适用登录后启动的策略
EV_EG2ST_MONEY_RSP                = 0x342           #资金信息应答  
EV_EG2ST_ORDER_RSP                = 0x343           #委托信息应答，适用登录后启动的策略
EV_EG2ST_MATCH_RSP                = 0x344           #成交信息应答，适用登录后启动的策略     
EV_EG2ST_POSITION_RSP             = 0x345           #持仓信息应答，适用登录后启动的策略

EV_EG2ST_STRATEGY_SYNC            = 0x360           #引擎向策略同步信息


# /////////////CAPI->PyAPI、PyAPi->引擎事件定义////////////////
EEQU_SRVEVENT_CONNECT             = 0x01		    #连接	Q H T S
EEQU_SRVEVENT_DISCONNECT          = 0x02	        #断开
                                                    
EEQU_SRVEVENT_QUOTELOGIN          = 0x20	        #登录行情前置
EEQU_SRVEVENT_QINITCOMPLETED      = 0x21            #行情初始化完成
EEQU_SRVEVENT_QUOTESNAP           = 0x22		    #即时行情--
EEQU_SRVEVENT_EXCHANGE            = 0x23		    #交易所
EEQU_SRVEVENT_COMMODITY           = 0x24		    #品种
EEQU_SRVEVENT_CONTRACT            = 0x25		    #合约
EEQU_SRVEVENT_QUOTESNAPLV2        = 0x26	        #深度行情--
EEQU_SRVEVENT_SPRAEDMAPPING       = 0x27
EEQU_SRVEVENT_UNDERLAYMAPPING     = 0x28
                                                    
EEQU_SRVEVENT_HISLOGIN            = 0x40		    #登录历史行情
EEQU_SRVEVENT_HINITCOMPLETED      = 0x41            #历史初始化完成
EEQU_SRVEVENT_HISQUOTEDATA        = 0x42	        #历史行情数据查询应答
EEQU_SRVEVENT_HISQUOTENOTICE      = 0x43            #历史行情数据变化通知
EEQU_SRVEVENT_TIMEBUCKET          = 0x44	        #时间模板
                                                    
EEQU_SRVEVENT_TRADE_LOGINQRY      = 0x60            #登陆账号查询
EEQU_SRVEVENT_TRADE_LOGINNOTICE   = 0x61            #登陆账号通知
EEQU_SRVEVENT_TRADE_ORDERQRY      = 0x62            #交易委托查询--
EEQU_SRVEVENT_TRADE_ORDER         = 0x63	        #交易委托变化--
EEQU_SRVEVENT_TRADE_MATCHQRY      = 0x64            #交易成交查询--
EEQU_SRVEVENT_TRADE_MATCH         = 0x65            #交易成交变化--
EEQU_SRVEVENT_TRADE_POSITQRY      = 0x66            #交易持仓查询--
EEQU_SRVEVENT_TRADE_POSITION      = 0x67            #交易持仓变化--
EEQU_SRVEVENT_TRADE_FUNDQRY       = 0x68            #交易资金查询
EEQU_SRVEVENT_TRADE_USERQRY       = 0x6B            #资金账号查询
EEQU_SRVEVENT_TRADE_EXCSTATEQRY   = 0x6C            #交易所状态查询
EEQU_SRVEVENT_TRADE_EXCSTATE      = 0x6D            #交易所状态变化通知

#////////////////////内部协议定义/////////////////////////////////
# 模块定义
EEQU_EVSRC_API                    = 'A'             #api模块
EEQU_EVSRC_ENGINE                 = 'E'             #策略引擎
EEQU_EVSRC_STRATEGU               = 'S'             #策略进程
EEQU_EVSRC_UI                     = 'U'             #界面
EEQU_EVSRC_NONE                   = 'N'             #不区分来源

#策略引擎状态
TE_STATUS_DISCONNECT_ESTAR        = 0x00
TE_STATUS_DISCONNECT_HISQUOTE     = 0x01
TE_STATUS_DISCONNECT_QUOTE        = 0x02
TE_STATUS_DISCONNECT_TRADE        = 0x03
TE_STATUS_CONNECT_ESTAR           = 0x10
TE_STATUS_CONNECT_HISQUOTE        = 0x11
TE_STATUS_CONNECT_QUOTE           = 0x12
TE_STATUS_CONNECT_TRADE           = 0x13     

#引擎交易数据状态定义
TM_STATUS_NONE                    = 0               #未定义
TM_STATUS_LOGIN                   = 1               #登陆账号查询完成
TM_STATUS_USER                    = 2               #资金账号查询完成
TM_STATUS_ORDER                   = 3               #委托查询完成
TM_STATUS_MATCH                   = 4               #成交查询完成
TM_STATUS_POSITION                = 5               #持仓查询完成

#策略执行状态
ST_STATUS_NONE                    = 'N'             #初始状态
ST_STATUS_HISTORY                 = 'H'             #回测状态
ST_STATUS_CONTINUES               = 'C'             #运行状态
ST_STATUS_PAUSE                   = 'P'             #暂停状态
ST_STATUS_QUIT                    = 'Q'             #停止状态
ST_STATUS_REMOVE                  = 'R'             #移除状态
ST_STATUS_EXCEPTION               = 'E'

# 策略触发事件定义
ST_TRIGGER_TIMER                  = 'T'              # 定时触发
ST_TRIGGER_CYCLE                  = 'C'              # 周期性触发
ST_TRIGGER_KLINE                  = 'K'              # K线触发
# 即时行情到来了,  处理的时候才决定是否触发
ST_TRIGGER_SANPSHOT_FILL          = 'S'
# *****************************************
ST_TRIGGER_TRADE_ORDER            = 'O'              # 交易触发
ST_TRIGGER_TRADE_MATCH            = 'M'              # 交易触发
ST_TRIGGER_FILL_DATA              = 'F'
ST_TRIGGER_NONE                   = 'N'
ST_TRIGGER_HIS_KLINE              = 'H'

#策略触发操作定义
ST_EVENT_TRIGGER                  = 0               #触发操作
ST_EVENT_STOP                     = 1               #停止操作


#////////////////////CAPI<--->PyAPI交互协议定义///////////////////

# CApi-PyApi服务类型定义
EEQU_SRVSRC_QUOTE                 = 'Q'	            #行情服务
EEQU_SRVSRC_HISQUOTE              = 'H'	            #历史行情服务
EEQU_SRVSRC_TRADE                 = 'T'	            #交易服务
EEQU_SRVSRC_SERVICE               = 'S'	            #9.5服务端
                                                    
                                                    
EEQU_SRVCHAIN_END                 = '0';		    #没有后续报文
EEQU_SRVCHAIN_NOTEND              = '1';		    #有后续报文
                                                    
# 行情字段属性                                      
EEQU_FIDATTR_NONE                 = 0 			    # 无值
EEQU_FIDATTR_VALID                = 1 			    # 有值
EEQU_FIDATTR_IMPLIED              = 2 		        # 隐含

# 字段类型类型
EEQU_FIDTYPE_NONE                 = 0 			    # 无效
EEQU_FIDTYPE_PRICE                = 1 			    # 价格
EEQU_FIDTYPE_QTY                  = 2 			    # 数量
EEQU_FIDTYPE_GREEK                = 3 			    # 希腊字母
EEQU_FIDTYPE_DATETIME             = 4 		        # 日期时间
EEQU_FIDTYPE_DATE                 = 5 			    # 日期
EEQU_FIDTYPE_TIME                 = 6 			    # 时间
EEQU_FIDTYPE_STATE                = 7 			    # 状态
EEQU_FIDTYPE_STR                  = 8 			    # 字符串 最大7字节
EEQU_FIDTYPE_PTR                  = 9 			    # 指针


# 策略状态
EEQU_STRATEGY_STATE_RUNNING       = 0x01
EEQU_STRATEGY_STATE_PAUSE         = 0x02
EEQU_STRATEGY_STATE_ERROR         = 0x03
EEQU_STRATEGY_STATE_QUIT          = 0x04

# 手续费收费方式
EEQU_FEE_TYPE_RATIO                = 'R' # 按比例
EEQU_FEE_TYPE_FIXED                = 'F' # 按固定值

# 1档行情各FieldMean对应类型值
EEQU_FIDTYPE_ARRAY = [
	EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, #0
	EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, #8
	EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_PRICE, #16
	EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_GREEK, #24
	EEQU_FIDTYPE_GREEK, EEQU_FIDTYPE_GREEK, EEQU_FIDTYPE_GREEK, EEQU_FIDTYPE_GREEK, EEQU_FIDTYPE_GREEK, EEQU_FIDTYPE_PRICE , EEQU_FIDTYPE_STR , EEQU_FIDTYPE_PRICE, #32
	EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, #40
	EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , #48
	EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , #56
	EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , #64
	EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , #72
	EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , #80
	EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , #88
	EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , #96
	EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_PRICE, #104
	EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , #112
	EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_STR  , EEQU_FIDTYPE_STR  , EEQU_FIDTYPE_STR  , EEQU_FIDTYPE_DATETIME, EEQU_FIDTYPE_STR, EEQU_FIDTYPE_NONE, #120
]


EEQU_MAX_L2_DEPTH                = 10			     # L2最大深度

# K线周期类型
EEQU_KLINE_TIMEDIVISION          = 't'			     # 分时
EEQU_KLINE_TICK                  = 'T'			     # 分笔 RawKLineSliceType 为0
EEQU_KLINE_SECOND                = 'S'			     # 秒线
EEQU_KLINE_MINUTE                = 'M'			     # 分钟线
EEQU_KLINE_HOUR                  = 'H'			     # 小时线
EEQU_KLINE_DAY                   = 'D'			     # 日线
EEQU_KLINE_WEEK                  = 'W'			     # 周线
EEQU_KLINE_MONTH                 = 'm'			     # 月线
EEQU_KLINE_YEAR                  = 'Y'			     # 年线
EEQU_KLINE_DayX                  = 'X'			     # 多日
                                                     
EEQU_NOTICE_NOTNEED              = '0'			     #不需要后续刷新推送
EEQU_NOTICE_NEED                 = '1'		         #需要后续推送

EEQU_IS_AXIS                     = '0'		         #独立坐标
EEQU_ISNOT_AXIS                  = '1'			     #非独立坐标
								    
EEQU_IS_MAIN                     = '0'		         #主图
EEQU_ISNOT_MAIN                  = '1'			     #副图

EEQU_IS_FILLED                   = 1;			     #填充
EEQU_ISNOT_FILLED                = 0;		         #非填充

EEQU_STATE_RUN                   = '0';			     #运行
EEQU_STATE_SUSPEND               = '1';		         #挂起
EEQU_STATE_STOP                  = '2';			     #停止

EEQU_VERTLINE                    = 0			     #竖直直线
EEQU_INDICATOR                   = 1			     #指标线
EEQU_BAR                         = 2				 #柱子
EEQU_STICKLINE                   = 3				 #竖线段
EEQU_COLORK                      = 4				 #变色K线
EEQU_PARTLINE                    = 5				 #线段
EEQU_ICON                        = 6				 #图标
EEQU_DOT                         = 7				 #点
EEQU_ANY                         = 8				 #位置格式
EEQU_TEXT                        = 9;				 #文本


EQU_ICON_NORMAL                  = 0;	             #正常表情
EQU_ICON_SMILE                   = 1;		         #笑脸
EQU_ICON_CRYING                  = 2;	             #哭脸
EQU_ICON_UP                      = 3;	             #上箭头
EQU_ICON_DOWN                    = 4;		         #下箭头	
EQU_ICON_UP2                     = 5;		         #上箭头2
EQU_ICON_DOWN2                   = 6;		         #下箭头2
EQU_ICON_HORN                    = 7;		         #喇叭
EQU_ICON_LOCK                    = 8;		         #加锁
EQU_ICON_UNLOCK                  = 9;	             #解锁
EQU_ICON_MONEYADD                = 10;	             #货币+
EQU_ICON_MONEYSUB                = 11;	             #货币-		
EQU_ICON_ADD                     = 12;		         #加号
EQU_ICON_SUB                     = 13;		         #减号
EQU_ICON_WARNING                 = 14;	             #叹号
EQU_ICON_ERROR                   = 15;	             #叉号


# trade type
EEQU_TRADE_TYPE_H                = 'H'
EEQU_TRADE_TYPE_A                = 'A'


# 日志消息类型
EEQU_LOG_TYPE_SIGNAL             = '0'          # 下单信号
EEQU_LOG_TYPE_ERROR              = '1'          # 策略调试错误
EEQU_LOG_TYPE_USER               = '2'          # 用户自定义

# 登录状态
EEQU_READY			             = '1';			#完成
EEQU_NOTREADY		             = '0';			#未完成

# 买卖
dNone                            = 'N'
dBuy                             = 'B'          # 买入
dSell                            = 'S'          # 卖出
dBoth                            = 'A'          # 双边


# 开平
oNone                            = 'N'          # 无
oOpen                            = 'O'          # 开仓
oCover                           = 'C'          # 平仓,平昨
oCoverT                          = 'T'          # 平今
oCoverA                          = 'A'          # 自适应，拆分成平今平昨，优先平昨
oOpenCover                       = '1'          # 开平，应价时有效, 本地套利也可以
oCoverOpen                       = '2'          # 平开，应价时有效, 本地套利也可以

# 订单类型
otUnDefine                      = 'U'
otMarket                        = '1'
otLimit                         = '2'
otMarketStop                    = '3'
otLimitStop                     = '4'
otExecute                       = '5'
otAbandon                       = '6'
otEnquiry                       = '7'
otOffer                         = '8'
otIceberg                       = '9'
otGhost                         = 'A'
otSwap                          = 'B'
otSpreadApply                   = 'C'
otHedgApply                     = 'D'
otOptionAutoClose               = 'F'
otFutureAutoClose               = 'G'
otMarketOptionKeep              = 'H'

# 有效类型
vtNone                          = 'N'
vtGFD                           = '0'
vtGTC                           = '1'
vtGTD                           = '2'
vtIOC                           = '3'
vtFOK                           = '4'

# 投保标记
hNone                           = 'N'
hSpeculate                      = 'T'
hHedge                          = 'B'
hSpread                         = 'S'
hMarket                         = 'M'

# 委托状态
osNone                          = 'N' # 无
osSended                        = '0' # 已发送
osAccept                        = '1' # 已受理
osTriggering                    = '2' # 待触发
osActive                        = '3' # 已生效
osQueued                        = '4' # 已排队
osFillPart                      = '5' # 部分成交
osFilled                        = '6' # 完全成交
osCanceling                     = '7' # 待撤
osModifying                     = '8' # 待改
osCanceled                      = '9' # 已撤单
osPartCanceled                  = 'A' # 已撤余单
osFail                          = 'B' # 指令失败
osAuditing                      = 'C' # 待审核
osSuspended                     = 'D' # 已挂起
osApply                         = 'E' # 已申请
osInvalid                       = 'F' # 无效单
osTriggerPart                   = 'G' # 部分触发
osTriggered                     = 'H' # 完全触发
osPartFailed                    = 'I' # 余单失败

# 触发模式
tmNone = 'N'
tmLatest = 'L'
tmBid = 'B'
tmAsk = 'A'

# 触发条件
tcNone = 'N'                    # 无
tcGreater = 'g'                 # 大于
tcGreaterEEqual = 'G'           # 大于等于
tcLess = 'l'                    # 小于
tcLessEEqual = 'L'              # 小于等于

# 策略类型
stNone = 'N'                    # 无
stPreOrder = 'P'                # 预备单(埋单)
stAutoOrder = 'A'               # 自动单
stCondition = 'C'               # 条件单

# 交易时段
tsDay = 'D'                     # 白天交易时段
tsNight = 'N'                   # 晚上（T+1）交易时段
tsAll = 'A'                     # 全交易时段

#
ProcessEvent                = 1
CApiEvent                   = 2

# 策略状态
StrategyStatusReady         = "Ready"
StrategyStatusRunning       = "Running"
StrategyStatusPause         = "Pause"
StrategyStatusExit          = "Exit"

# 发单方式
SendOrderRealTime           = '1'
SendOrderStable             = '2'

# 交易所状态
tsUnknown                       = 'N'   #未知状态
tsIniting                       = 'I'   #正初始化
tsReady                         = 'R'   #准备就绪
tsSwitchDay                     = '0'   #交易日切换
tsBiding                        = '1'   #竞价申报
tsMakeMatch                     = '2'   #竞价撮合
tsTradeing                      = '3'   #连续交易
tsPause                         = '4'   #交易暂停
tsClosed                        = '5'   #交易闭市   
tsBidPause                      = '6'   #竞价暂停
tsGatewayDisconnect             = '7'   #报盘未连
tsTradeDisconnect               = '8'   #交易未连
tsCloseDeal                     = '9'   #闭市处理

# 品种交易状态
EEQU_TRADESTATE_BID             = '1'   # 集合竞价
EEQU_TRADESTATE_MATCH           = '2'   # 集合竞价撮合
EEQU_TRADESTATE_CONTINUOUS      = '3'   # 连续交易
EEQU_TRADESTATE_PAUSED          = '4'   # 暂停
EEQU_TRADESTATE_CLOSE           = '5'   # 闭式
EEQU_TRADESTATE_DEALLAST        = '6'   # 闭市处理时间
EEQU_TRADESTATE_SWITCHTRADE     = '0'   # 交易日切换时间
EEQU_TRADESTATE_UNKNOWN         = 'N'   # 未知状态
EEQU_TRADESTATE_INITIALIZE      = 'I'   # 正初始化
EEQU_TRADESTATE_READY           = 'R'   # 准备就绪

# 日期标记
EEQU_DATEFLAG_PRE               = '0'   #前一日
EEQU_DATEFLAG_CUR               = '1'   #当日
EEQU_DATEFLAG_NEXT              = '2'   #下一日

# 品种类型
EEQU_COMMODITYTYPE_NONE         = 'N'   # 无
EEQU_COMMODITYTYPE_SPOT         = 'P'   # 现货
EEQU_COMMODITYTYPE_DEFER        = 'Y'   # 延期
EEQU_COMMODITYTYPE_FUTURES      = 'F'   # 期货
EEQU_COMMODITYTYPE_OPTION       = 'O'   # 期权
EEQU_COMMODITYTYPE_MONTH        = 'S'   # 跨期套利
EEQU_COMMODITYTYPE_COMMODITY    = 'M'   # 跨品种套利
EEQU_COMMODITYTYPE_BUL          = 'U'   # 看涨垂直套利
EEQU_COMMODITYTYPE_BER          = 'E'   # 看跌垂直套利
EEQU_COMMODITYTYPE_STD          = 'D'   # 跨式套利
EEQU_COMMODITYTYPE_STG          = 'G'   # 宽跨式套利
EEQU_COMMODITYTYPE_PRT          = 'R'   # 备兑组合
EEQU_COMMODITYTYPE_BLT          = 'L'   # 看涨水平期权
EEQU_COMMODITYTYPE_BRT          = 'Q'   # 看跌水平期权
EEQU_COMMODITYTYPE_DIRECT       = 'X'   # 外汇 直接汇率 USD是基础货币 USDxxx
EEQU_COMMODITYTYPE_INDIRECT     = 'I'   # /外汇 间接汇率 xxxUSD
EEQU_COMMODITYTYPE_CROSS        = 'C'   # 外汇 交叉汇率 xxxxxx
EEQU_COMMODITYTYPE_INDEX        = 'Z'   # 指数
EEQU_COMMODITYTYPE_STOCK        = 'T'   # 股票
EEQU_COMMODITYTYPE_SPDMON       = 's'   # 极星跨期 SPD|s|SR|801|805
EEQU_COMMODITYTYPE_SPDCOM       = 'm'   # 极星跨品种 SPD|m|A+M2-B|805
EEQU_COMMODITYTYPE_SPDDEFER     = 'y'   # 延期 SPD|m|A+M2-B|805

# 单笔最大下单量
MAXSINGLETRADESIZE              = 1000

# 加载按钮属性设置变量列表
VUser                        = "1"      # 用户
VInitFund                    = "2"      # 初始资金
VDefaultType                 = "3"      # 默认下单方式
VDefaultQty                  = "4"      # 默认下单量（或资金、或比例）
VMinQty                      = "5"      # 最小下单量
VHedge                       = "6"      # 投保标志
VMargin                      = "7"      # 保证金
VOpenType                    = "8"      # 开仓收费方式
VCloseType                   = "9"      # 平仓收费方式
VOpenFee                     = "10"     # 开仓手续费（率）
VCloseFee                    = "11"     # 平仓手续费（率）
VDirection                   = "12"     # 交易方向
VSlippage                    = "13"     # 滑点损耗
VContract                    = "14"     # 合约
VTimer                       = "15"     # 定时触发
VIsCycle                     = "16"     # 是否按周期触发
VCycle                       = "17"     # 周期
VIsKLine                     = "18"     # K线触发
VIsMarket                    = "19"     # 行情触发
VIsTrade                     = "20"     # 交易数据触发

VSampleVar                   = "21"     # 样本类型： 0. 所有K线  1. 起始日期  2. 固定根数  3. 不执行历史K线
VBeginDate                   = "22"     # 起始日期
VFixQty                      = "23"     # 固定根数

VKLineType                   = "24"     # K线类型
VKLineSlice                  = "25"     # K线周期
VSendOrderMode               = "26"     # 发单时机： 0. 实时发单 1. K线稳定后发单
VIsActual                    = "27"     # 实时发单
VIsOpenTimes                 = "28"     # 每根K线同向开仓次数标志
VOpenTimes                   = "29"     # 每根K线同向开仓次数
VIsConOpenTimes              = "30"     # 最大连续同向开仓次数标志
VConOpenTimes                = "31"     # 最大连续同向开仓次数
VCanClose                    = "32"     # 开仓的当前K线不允许平仓
VCanOpen                     = "33"     # 平仓的当前K线不允许开仓
VParams                      = "34"     # 用户设置的参数
VContSettings                = "35"     # 多合约设置信息\
VIsAlarm                     = "36"     # 发单报警
VIsPop                       = "37"     # 允许弹窗

# K线数据类型
BarDataClose        = 'C' # 收盘价
BarDataOpen         = 'O' # 开盘价
BarDataHigh         = 'H' # 最高价
BarDataLow          = 'L' # 最低价
BarDataMedian       = 'M' # 中间价
BarDataTypical      = 'B' # 标准价
BarDataWeighted     = 'W' # 加权收盘价
BarDataVol          = 'V' # 成交量
BarDataOpi          = 'I' # 持仓量
BarDataTime         = 'T' # Bar线时间

#
OrderSuccess                 = 0
OrderFail                    = 1

# 资金限制
OrderLimitFromFund          = 1000
# 最大持仓限制
OrderLimitFromMaxTotalPosition = 1001
# 最大连续开仓限制
# 最大连续平仓限制
# 当前k线最大开仓限制
# 当前k线最大平仓限制

# 最新价来源
LastPriceFromQuote          = 10000
LastPriceFromKLine          = 10001

#
KLineFromHis                = 20000
KLineFromRealTime           = 20001

# 不同K线类型最大数量
TickKLineMaxCount           = 160000        # 分笔
SecondKLineMaxCount         = 160000        # 秒线
DayKLineMaxCount            = 2000          # 日线
MinuteKLineMaxCount         = 80000         # 分钟线


# 按日期订阅Tick类型K线时每次取数据的最大根数
MaxCountTick                = 40000

class EEquExchangeReq(Structure):
    """交易所信息查询请求"""
    _pack_ = 1
    _fields_ = [
        ('ExchangeNo',  c_char*11)		             # 交易所代码
    ]
    
class EEquExchangeData(Structure):
    """交易所信息查询结果"""
    _pack_ = 1
    _fields_ = [
        ('ExchangeNo',   c_char*11),		         # 交易所代码
        ('ExchangeName', c_char*51),	             # 交易所名称
    ]


class EEquCommodityReq(Structure):
    """品种信息查询请求"""
    _pack_ = 1
    _fields_ = [
        ('CommodityNo', c_char*21)	                 # 填空从头开始查，续查每次把应答包发回请求
    ]


class EEquCommodityData(Structure):
    """品种信息查询结果"""
    _pack_ = 1
    _fields_ = [
        ('ExchangeNo',      c_char*11),
        ('CommodityNo',     c_char*21),	             # 品种代码
        ('CommodityType',   c_char),                 # 品种类型
        ('CommodityName',   c_char*51),              # 品种名称
        ('PriceNume',       c_double),		         # 分子
        ('PriceDeno',       c_ushort),		         # 分母
        ('PriceTick',       c_double),		         # 最小变动价
        ('PricePrec',       c_ubyte),		         # 价格精度
        ('TradeDot',        c_double),		         # 每手乘数
        ('CoverMode',       c_char)		             # 平仓方式
    ]


class EEquContractReq(Structure):
    """合约信息查询请求"""
    _pack_ = 1
    _fields_ = [
        ('ContractNo', c_char*101)                   # 合约编号
    ]
    

class EEquContractData(Structure):
    """合约信息查询结果"""
    _pack_ = 1
    _fields_ = [
        ('ExchangeNo',  c_char*11),                  # 交易所
        ('CommodityNo', c_char*21),                  # 品种代码
        ('ContractNo',  c_char*101),                 # 合约编号
    ]


class EEquSnapShotReq(Structure):
    """订阅和退订请求, 普通和深度行情均使用此结构"""
    _pack_ = 1
    _fields_ = [
        ('ContractNo', c_char*101)                   # 合约编号(客户端向后台订阅使用合约)
    ]


class EEquQuoteFieldUnion0(Union):
    '''行情快照part3-FidMean'''
    _pack_ = 1
    _fields_ = [
        ('FidMean', c_ubyte),                        # 变化行情使用标识
        ('FidAttr', c_char)                          # 固定行情使用属性
    ]
    

class EEquQuoteFieldUnion1(Union):
    '''行情快照part3-FidValue'''
    _pack_ = 1
    _fields_ = [
        ('Price', c_double),                         # 价格
        ('Qty', c_ulonglong),                        # 数量
        ('Greek', c_double),
        ('Volatility', c_double),
        ('DateTime', c_ulonglong),
        ('Date', c_uint),
        ('Time', c_uint),
        ('State', c_char),
        ('Str', c_char*8),
        ('Ptr', c_void_p),
    ]
    

class EEquQuoteField(Structure):
    """行情快照part2"""
    _pack_ = 1
    _fields_ = [
        ('QuoteFieldUnion0', EEquQuoteFieldUnion0),
        ('QuoteFieldUnion1', EEquQuoteFieldUnion1)
    ]
    

class EEquSnapShotData(Structure):
    """行情快照part1	"""
    _pack_ = 1
    _fields_ = [
        ('UpdateTime', c_ulonglong),                 # 行情更新时间
        ('FieldCount', c_ubyte),                     # EquSnapShotField的数量
        ('FieldData', POINTER(EEquQuoteField)),      # 数据字段的起始位置，无数据时此结构不包含此字段长度
    ]
    
class EEquQuoteFieldL2(Structure):
    '''深度行情part2'''
    _pack_ = 1
    _fields_ = [
        ('Price', c_double),
        ('Qty', c_ulonglong)
    ]
    
class EEquQuoteSnapShotL2(Structure):
    '''深度行情part1'''
    _pack_ = 1
    _fields_ = [
        ('BidQuoteFieldL2', EEquQuoteFieldL2*EEQU_MAX_L2_DEPTH), # 买深度，最多10档
        ('AskQuoteFieldL2', EEquQuoteFieldL2*EEQU_MAX_L2_DEPTH), # 卖深度，最多10档
    ]

class EEquKLineReq(Structure):
    """K线查询请求"""
    _pack_ = 1
    _fields_ = [
        ('ReqCount', c_uint),                        # 期望数量（扩展使用）
        ('ContractNo', c_char*101),                  # 合约ID
        ('KLineType', c_char),                       # K线类型
        ('KLineSlice', c_ubyte),                     # K线多秒(0 tick) 分钟 日线
        ('NeedNotice', c_char)                       # 需要订阅通知
    ]


class EEquKLineDataStruct0(Structure):
    '''日线、分钟线'''
    _pack_ = 1
    _fields_ = [
        ('KLineQty', c_ulonglong),                   # K线成交量 day  min
        ('OpeningPrice', c_double),                  # 开盘价  day  min
        ('HighPrice', c_double),                     # 最高价  day  min
        ('LowPrice', c_double),                      # 最低价  day  min
        ('SettlePrice', c_double),                   # 结算价  day  min
    ]


class EEquKLineDataStruct1(Structure):
    '''成交明细'''
    _pack_ = 1
    _fields_ = [
        ('LastQty', c_uint),                         # 明细现手  tick
        ('PositionChg', c_int),                      # 持仓量变化 tick
        ('BuyPrice', c_double),                      # 买价 tick
        ('SellPrice', c_double),                     # 卖价 tick
        ('BuyQty', c_ulonglong),                     # 买量 tick
        ('SellQty', c_ulonglong),                    # 卖量 tick
    ]


class EEquKLineDataUnion(Union):
    '''K线应答推送 part2, 日线、分钟线Struct0, tick Struct1'''
    _pack_ = 1
    _fields_ = [
        ('KLineData0', EEquKLineDataStruct0),
        ('KLineData1', EEquKLineDataStruct1)
    ]


class EEquKLineData(Structure):   # sizeof 80字节
    '''K线应答推送 part1'''
    _pack_ = 1
    _fields_ = [                                          
        ('KLineIndex', c_int),                        # K线索引  tick每笔连续序号，min交易分钟序号，day无效
        ('TradeDate', c_uint),                        # 交易日   tick无效，min可能和时间戳不同，day和时间戳相同
        ('DateTimeStamp', c_ulonglong),               # 时间戳，不同数据类型，精度不同
        ('TotalQty', c_ulonglong),                    # 行情快照 总成交量
        ('PositionQty', c_ulonglong),                 # 行情快照 持仓量
        ('LastPrice', c_double),                      # 最新价（收盘价）
        ('KLineData', EEquKLineDataUnion)             # K线数据，分tick和日线、分钟线
    ]


class EEquKLineStrategySwitch(Structure):
    """K线策略切换"""
    _pack_ = 1
    _fields_ = [
        ('StrategyId', c_uint),                       # 策略ID
        ('StrategyName', c_char*51),                  # 策略名称
        ('ContractNo', c_char*101),                   # 合约ID
        ('KLineType', c_char),                        # K线类型
        ('KLineSlice', c_ubyte),                      # 多秒 分钟 日线
    ]


class EEquKLineDataResult(Structure):
    """K线结果推送"""
    _pack_ = 1
    _fields_ = [
        ('StrategyId', c_uint),                       # 策略编号
        ('Count', c_uint),                            # 数量
        ('Data', POINTER(EEquKLineData)),             # 数据
    ]


class EEquSeriesParam(Structure):
    """参数信息"""
    _pack_ = 1
    _fields_ = [
        ('ParamName', c_char*21), 		                  # 参数名
        ('ParamValue', c_double), 		                  # 参数值
    ]


class EEquKLineSeriesInfo(Structure):
    """K线指标参数"""
    _pack_ = 1
    _fields_ = [
        ('ItemName', c_char*51),                          # 具体指标线 名称
        ('Type', c_ubyte),                                # 线型
        ('Color', c_uint),                                # 颜色
        ('Thick', c_uint),                                # 线宽
        ('OwnAxis', c_char),                              # 是否独立坐标
        ('Param', EEquSeriesParam*10),                    # 参数 Max10
        ('ParamNum', c_uint),                             # 参数个数
        ('Groupid', c_ubyte),                             # 组号
        ('GroupName', c_char*51),                         # 组名（指标名）
        ('Main', c_ubyte),                                # 0 - 主图 1 - 副图1
                                                          
        ('StrategyId', c_uint),                           # 策略ID
    ]


class EEquKLineSeriesStruct0(Structure):
    """变色K线,竖直线"""
    _pack_ = 1
    _fields_ = [
        ('ClrK', c_uint)
    ]

class EEquKLineSeriesStruct1(Structure):
    """图标类型,点类型"""
    _pack_ = 1
    _fields_ = [
        ('Icon', c_int)
    ]


class EEquKLineSeriesStruct2(Structure):
    """竖线"""
    _pack_ = 1
    _fields_ = [
        ('ClrStick', c_uint),
        ('StickValue', c_double)
    ]


class EEquKLineSeriesStruct3(Structure):
    """柱子"""
    _pack_ = 1
    _fields_ = [
        ('ClrBar', c_uint),
        ('Filled', c_char),
        ('BarValue', c_double),
    ]


class EEquKLineSeriesStruct4(Structure):
    """线段	"""
    _pack_ = 1
    _fields_ = [
        ('Idx2', c_int),
        ('ClrLine', c_uint),
        ('LineValue', c_double),
        ('LinWid', c_uint),
    ]
    
class EEquKLineSeriesStruct5(Structure):
    """图标类型,点类型"""
    _pack_ = 1
    _fields_ = [
        ('Text', c_char*20)
    ]


class EEquKLineSeriesUnion(Union):
    '''增加指标线结构 part2'''
    _pack_ = 1
    _fields_ = [
        ('_KLineSeriesStructure0', EEquKLineSeriesStruct0),
        ('_KLineSeriesStructure1', EEquKLineSeriesStruct1),
        ('_KLineSeriesStructure2', EEquKLineSeriesStruct2),
        ('_KLineSeriesStructure3', EEquKLineSeriesStruct3),
        ('_KLineSeriesStructure4', EEquKLineSeriesStruct4),
        ('_KLineSeriesStructure5', EEquKLineSeriesStruct5),
    ]


class EEquKLineSeries(Structure):
    '''增加指标线结构 part1'''
    _pack_ = 1
    _anonymous_ = ("KLineSeriesUnion",)
    _fields_ = [
        ('KLineIndex', c_int), 		                      # 索引0无效
        ('Value', c_double), 			                  # InvalidNumeric 表示无效数据
        ('KLineSeriesUnion', EEquKLineSeriesUnion)
    ]
    
    
class EEquKLineSeriesResult(Structure):
    """K线指标推送"""
    _pack_ = 1
    _fields_ = [
        ('StrategyId', c_uint),                           # 策略编号
        ('SeriesName', c_char*51),                        # 指标名称
        ('SeriesType', c_ubyte),                          # 指标线型
        ('IsMain', c_ubyte),                              # 主图 副图
                                                          
        ('Count', c_uint),                                # 数量
        # TODO 指针
        ('Data', POINTER(EEquKLineSeries)),               # 数据
    ]


class EEquSignalItem(Structure):
    """信号数据"""
    _pack_ = 1
    _fields_ = [
        ('KLineIndex', c_int),  		                  # K线索引
        ('ContractNo', c_char*101),                       #合约ID
        ('Direct', c_char),  			                  # 买卖方向
        ('Offset', c_char),  			                  # 开平
        ('Price', c_double),  			                  # 价格
        ('Qty', c_ulonglong),  			                  # 数量
    ]


class EEquKLineSignalResult(Structure):
    """K线信号推送"""
    _pack_ = 1
    _fields_ = [
        ('StrategyId', c_uint),                           # 策略ID
        ('SeriesName', c_char*51),                        # 信号名称
                                                          
        ('Count', c_uint),                                # 数量
        #  TODO 指针
        ('Data', POINTER(EEquSignalItem)),                # 数据
    ]


class EEquStrategyDataUpdateNotice(Structure):
    """K线biao推送"""
    _pack_ = 1
    _fields_ = [
        ('StrategyId', c_uint)                            # 策略ID
    ]
    
class EEquKlineStrategyStateNotice(Structure):
    """策略状态推送"""
    _pack_ = 1
    _fields_ = [
        ('StrategyId', c_uint),                            # 策略ID
        ('StrategyState', c_ubyte)                         # 策略状态
    ]


class EEquCommodityTimeBucketReq(Structure):
    _pack_ = 1
    _fields_ = [
        ('CommodityNo', c_char*21)	                      # 填空从头开始查
    ]


class EEquHisQuoteTimeBucket(Structure):
    """时间模板"""
    _pack_ = 1
    _fields_ = [
        ('Index', c_short),
        ('BeginTime', c_uint),
        ('EndTime', c_uint),
        ('TradeState', c_char),
        ('DateFlag', c_char),
        ('CalCount', c_short),					         # 基础模版对应计算模版的分钟数
        ('Commodity', c_char*21)                         # 品种编号
    ]


class EEquLoginInfoReq(Structure):
    """登陆账号查询请求"""
    _pack_ = 1
    _fields_ = [
        ('LoginNo', c_char*21),
        ('Sign', c_char*21)
    ]
    

class EEquLoginInfoRsp(Structure):
    """登录账号查询应答"""
    _pack_ = 1
    _fields_ = [
        ('LoginNo', c_char*21),
        ('Sign', c_char*21),
        ('LoginName', c_char*51),
        ('LoginApi', c_char*51),
        ('TradeDate', c_char*11),
        ('IsReady', c_char),
    ]
    

class EEquUserInfoReq(Structure):
    """资金账号查询请求"""
    _pack_ = 1
    _fields_ = [
        ('UserNo', c_char*21),
        ('Sign', c_char*21),
    ]


class EEquUserInfoRsp(Structure):
    """资金账号查询应答"""
    _pack_ = 1
    _fields_ = [
        ('UserNo', c_char*21),
        ('Sign', c_char*21),
        ('LoginNo', c_char*21),
        ('UserName', c_char*51),
    ]


class EEquUserMoneyReq(Structure):
    """资金查询请求"""
    _pack_ = 1
    _fields_ = [
        ('UserNo', c_char*21),					          # 不为空
        ('Sign', c_char*21),					          # 不为空
        ('CurrencyNo', c_char*21),				          # 空 全查
    ]


class EEquUserMoneyRsp(Structure):
    """资金查询应答"""
    _pack_ = 1
    _fields_ = [
        ('UserNo', c_char*21),
        ('Sign', c_char*21),
        ('CurrencyNo', c_char*21),			              # 币种号(Currency_Base表示币种组基币资金)
        ('ExchangeRate', c_double),			              # 币种汇率
                                                          
        ('FrozenFee', c_double),			              # 冻结手续费20
        ('FrozenDeposit', c_double),		              # 冻结保证金19
        ('Fee', c_double),					              # 手续费(包含交割手续费)
        ('Deposit', c_double),				              # 保证金
                                                          
        ('FloatProfit', c_double),			              # 不含LME持仓盈亏,盯市 market to market
        ('FloatProfitTBT', c_double),	                  # 逐笔浮赢 trade by trade
        ('CoverProfit', c_double),			              # 平盈 盯市
        ('CoverProfitTBT', c_double),		              # 逐笔平盈
                                                          
        ('Balance', c_double),				              # 今资金=PreBalance+Adjust+CashIn-CashOut-Fee(TradeFee+DeliveryFee+ExchangeFee)+CoverProfitTBT+Premium
        ('Equity', c_double),				              # 今权益=Balance+FloatProfitTBT(NewFloatProfit+LmeFloatProfit)+UnExpiredProfit
        ('Available', c_double),			              # 今可用=Equity-Deposit-Frozen(FrozenDeposit+FrozenFee)
                                                          
        ('UpdateTime', c_char*21),			              # 更新时间
    ]


class EEquOrderQryReq(Structure):
    """委托查询请求"""
    _pack_ = 1
    _fields_ = [
        ('UserNo', c_char*21),
        ('Sign', c_char*21),
    ]


class EEquOrderInsertReq(Structure):
    """委托请求"""
    _pack_ = 1
    _fields_ = [
        ('UserNo', c_char*21),
        ('Sign', c_char*21),
        ('Cont', c_char*101),				              # 行情合约
        ('OrderType', c_char),				              # 定单类型
        ('ValidType', c_char),				              # 有效类型
        ('ValidTime', c_char*21),			              # 有效日期时间(GTD情况下使用)
        ('Direct', c_char),					              # 买卖方向
        ('Offset', c_char),					              # 开仓平仓 或 应价买入开平
        ('Hedge', c_char),					              # 投机保值
        ('OrderPrice', c_double),			              # 委托价格 或 期权应价买入价格
        ('TriggerPrice', c_double),			              # 触发价格
        ('TriggerMode', c_char),			              # 触发模式
        ('TriggerCondition', c_char),		              # 触发条件
        ('OrderQty', c_ulonglong),			              # 委托数量 或 期权应价数量
        ('StrategyType', c_char),			              # 策略类型
        ('Remark', c_char*51),				              # 下单备注字段，只有下单时生效。如果需要唯一标识一个或一组定单，最好以GUID来标识，否则可能和其他下单途径的ID重复
        ('AddOneIsValid', c_char),			              # T+1时段有效(仅港交所)
    ]


class EEquOrderCancelReq(Structure):
    """委托撤单"""
    _pack_ = 1
    _fields_ = [
        ('OrderId', c_uint),				              # 定单号
    ]


class EEquOrderModifyReq(Structure):
    """委托改单"""
    _pack_ = 1
    _fields_ = [
        ('UserNo', c_char*21),
        ('Sign', c_char*21),
        ('Cont', c_char*101),				              # 行情合约
        ('OrderType', c_char),				              # 定单类型
        ('ValidType', c_char),				              # 有效类型
        ('ValidTime', c_char*21),			              # 有效日期时间(GTD情况下使用)
        ('Direct', c_char),					              # 买卖方向
        ('Offset', c_char),					              # 开仓平仓 或 应价买入开平
        ('Hedge', c_char),					              # 投机保值
        ('OrderPrice', c_double),			              # 委托价格 或 期权应价买入价格
        ('TriggerPrice', c_double),			              # 触发价格
        ('TriggerMode', c_char),			              # 触发模式
        ('TriggerCondition', c_char),		              # 触发条件
        ('OrderQty', c_ulonglong),			              # 委托数量 或 期权应价数量
        ('StrategyType', c_char),			              # 策略类型
        ('Remark', c_char*51),				              # 下单备注字段，只有下单时生效。如果需要唯一标识一个或一组定单，最好以GUID来标识，否则可能和其他下单途径的ID重复
        ('AddOneIsValid', c_char),			              # T+1时段有效(仅港交所)
                                                          
        ('OrderId', c_uint),				              # 定单号
    ]


class EEquOrderDataNotice(Structure):
    """委托通知"""
    _pack_ = 1
    _fields_ = [
        ('SessionId', c_uint),
        ('UserNo', c_char*21),
        ('Sign', c_char*21),
        ('Cont', c_char*101),				              # 行情合约
        ('OrderType', c_char),				              # 定单类型
        ('ValidType', c_char),				              # 有效类型
        ('ValidTime', c_char*21),			              # 有效日期时间(GTD情况下使用)
        ('Direct', c_char),					              # 买卖方向
        ('Offset', c_char),					              # 开仓平仓 或 应价买入开平
        ('Hedge', c_char),					              # 投机保值
        ('OrderPrice', c_double),			              # 委托价格 或 期权应价买入价格
        ('TriggerPrice', c_double),			              # 触发价格
        ('TriggerMode', c_char),			              # 触发模式
        ('TriggerCondition', c_char),		              # 触发条件
        ('OrderQty', c_ulonglong),			              # 委托数量 或 期权应价数量
        ('StrategyType', c_char),			              # 策略类型
        ('Remark', c_char*51),				              # 下单备注字段，只有下单时生效。如果需要唯一标识一个或一组定单，最好以GUID来标识，否则可能和其他下单途径的ID重复
        ('AddOneIsValid', c_char),			              # T+1时段有效(仅港交所)
                                                          
        ('OrderState', c_char),				              # 委托状态
        ('OrderId', c_uint),				              # 定单号
        ('OrderNo', c_char*21),				              # 委托号
        ('MatchPrice', c_double),			              # 成交价
        ('MatchQty', c_ulonglong),			              # 成交量
        ('ErrorCode', c_int),				              # 最新信息码
        ('ErrorText', c_char*201),		                  # 最新错误信息
        ('InsertTime', c_char*21),			              # 下单时间
        ('UpdateTime', c_char*21),			              # 更新时间
    ]


class EEquMatchNotice(Structure):
    """成交数据查询应答/通知"""
    _pack_ = 1
    _fields_ = [
        ('UserNo', c_char*21),
        ('Sign', c_char*21),
        ('Cont', c_char*101),				              # 行情合约
        ('Direct', c_char),					              # 买卖方向
        ('Offset', c_char),					              # 开仓平仓 或 应价买入开平
        ('Hedge', c_char),					              # 投机保值
        ('OrderNo', c_char*21),				              # 委托号
        ('MatchPrice', c_double),			              # 成交价
        ('MatchQty', c_ulonglong),			              # 成交量
        ('FeeCurrency', c_char*21),			              # 手续费币种
        ('MatchFee', c_double),				              # 成交手续费
        ('MatchDateTime', c_char*21),		              # 更新时间
        ('AddOne', c_char),					              # T+1成交
        ('Deleted', c_char),				              # 是否删除
        ('MatchNo', c_char * 21),                         # 成交号
    ]


class EEquPositionNotice(Structure):
    """持仓数据查询应答、通知"""
    _pack_ = 1
    _fields_ = [
        ('PositionNo', c_char*51),
        ('UserNo', c_char*21),
        ('Sign', c_char*21),
        ('Cont', c_char*101),				              # 行情合约
        ('Direct', c_char),					              # 买卖方向
        ('Hedge', c_char),					              # 投机保值
        ('Deposit', c_double),				              # 客户初始保证金
        ('PositionQty', c_ulonglong),		              # 总持仓量
        ('PrePositionQty', c_ulonglong),                  # 昨仓数量
        ('PositionPrice', c_double),		              # 价格
        ('ProfitCalcPrice', c_double),		              # 浮盈计算价
        ('FloatProfit', c_double),			              # 浮盈
        ('FloatProfitTBT', c_double),		              # 逐笔浮赢 trade by trade
    ]
    
class EEquExchangeStateReq(Structure):
    """交易所状态及时间查询请求"""
    _pack_ = 1
    _fields_ = [
    ]
    
class EEquExchangeStateRsp(Structure):
    '''主力合约和月份合约关系应答'''
    _pack_ = 1
    _fields_ = [
        ("Sign", c_char*21),                              #服务器标识
        ("ExchangeNo", c_char*11),                        #交易所编号
        ("ExchangeDateTime", c_char*21),                  #交易所系统时间
        ("LocalDateTime", c_char*21),                     #本地系统时间
        ("TradeState", c_char),                           #交易所状态
        ("CommodityNo", c_char*21),                       #品种
    ]

class EEquSpreadMappingReq(Structure):
    """极星套利合约映射关系查询请求"""
    _pack_ = 1
    _fields_ = [
    ]


class EEquSpreadMappingDataResponse(Structure):
    '''极星套利合约映射关系应答'''
    _pack_ = 1
    _fields_ = [
        ("ContractNo", c_char*101),                       #客户端合约编号
        ("SrcContractNo", c_char*101),                    #原始合约编号
    ]

class EEquTrendMappingDataResponse(Structure):
    '''主力合约和月份合约关系应答'''
    _pack_ = 1
    _fields_ = [
        ("ContractNo", c_char * 101),                     #虚拟合约编号,MAIN,NEARBY
        ("UnderlayContractNo", c_char * 101),             #真实合约编号,月份合约
    ]

    
class EEquServiceInfo(Structure):
    '''服务信息结构，用于C Api事件回调'''
    _pack_ = 1
    _fields_ = [
        ('SrvSrc'         , c_ubyte),                     #事件来源
        ('SrvEvent'       , c_ubyte),                     #事件类型
        ('SrvChain'       , c_ubyte),                     #是否有后续报文，'0'没有后续报文，'1'有后续报文
        ('SrvErrorCode'   , c_int),                       #错误码
        ('SrvErrorText'   , c_char*201),                  #错误信息
        ('SrvData'        , c_void_p),                    #事件消息体
        ('DataFieldSize'  , c_ushort),                    #单个消息体大小
        ('DataFieldCount' , c_ushort),                    #消息体个数
        ('UserNo'         , c_char*21),                   #用户号
        ('ContractNo'     , c_char*101),                  #合约号
        ('KLineType'      , c_char),                      #K线类型
        ('KLineSlice'     , c_ubyte),                     #K线切片值
        ('SessionId'      , c_uint),                      #会话号
    ]


class EEquSpreadMappingReq(Structure):
    """委托查询请求"""
    _pack_ = 1
    _fields_ = [
    ]


class EEquSpreadMappingDataResponse(Structure):
    _pack_ = 1
    _fields_ = [
        ("ContractNo", c_char*101),
        ("SrcContractNo", c_char*101),
    ]

class EEquTrendMappingDataResponse(Structure):
    _pack_ = 1
    _fields_ = [
        ("ContractNo", c_char * 101),
        ("UnderlayContractNo", c_char * 101),
    ]


ServiceCallBackFuncType = CFUNCTYPE(c_int, POINTER(EEquServiceInfo))