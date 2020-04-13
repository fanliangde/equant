#ifndef EQUANTAPI_TYPE_H
#define EQUANTAPI_TYPE_H

#pragma pack(push, 1)

//++++++++++++++++++++++++基础数据类型++++++++++++++++++++++++++++
//布尔类型
typedef signed char					B8;

//有符号整数
typedef signed char					I8;
typedef signed short				I16;
typedef signed int					I32;
typedef signed long long			I64;

//无符号整数
typedef unsigned char				U8;
typedef unsigned short				U16;
typedef unsigned int				U32;
typedef unsigned long long			U64;

//浮点数
typedef float						F32;
typedef double						F64;

//字符类型
typedef  char						C8;
typedef  wchar_t				    C16;

//指针类型
typedef void*						PTR;

//字符串类型
typedef C8							STR10[11];
typedef C8							STR20[21];
typedef C8							STR30[31];
typedef C8							STR40[41];
typedef C8							STR50[51];
typedef C8							STR100[101];
typedef C8							STR200[201];

typedef I32                         EEquRetType;				//返回值类型

typedef U8                          EEquSrvSrcType;				//服务类型
static const EEquSrvSrcType			EEQU_SRVSRC_QUOTE = 'Q';	//行情服务
static const EEquSrvSrcType			EEQU_SRVSRC_HISQUOTE = 'H';	//历史行情服务
static const EEquSrvSrcType			EEQU_SRVSRC_TRADE = 'T';	//交易服务
static const EEquSrvSrcType			EEQU_SRVSRC_SERVICE = 'S';	//9.5服务端

typedef U8                          EEquSrvEventType;			  		//服务事件类型
static const EEquSrvEventType		EEQU_SRVEVENT_CONNECT = 0x01;		//连接	Q H T S
static const EEquSrvEventType		EEQU_SRVEVENT_DISCONNECT = 0x02;	//断开

static const EEquSrvEventType		EEQU_SRVEVENT_QUOTELOGIN = 0x20;	//登录行情前置
static const EEquSrvEventType		EEQU_SRVEVENT_QINITCOMPLETED = 0x21;//行情初始化完成
static const EEquSrvEventType		EEQU_SRVEVENT_QUOTESNAP = 0x22;		//即时行情--
static const EEquSrvEventType		EEQU_SRVEVENT_EXCHANGE = 0x23;		//交易所
static const EEquSrvEventType		EEQU_SRVEVENT_COMMODITY = 0x24;		//品种
static const EEquSrvEventType		EEQU_SRVEVENT_CONTRACT = 0x25;		//合约
static const EEquSrvEventType		EEQU_SRVEVENT_QUOTESNAPLV2 = 0x26;	//深度行情--
static const EEquSrvEventType		EEQU_SRVEVENT_SPRAEDMAPPING = 0x27;	//套利合约映射关系
static const EEquSrvEventType		EEQU_SRVEVENT_UNDERLAYMAPPING = 0x28;//虚拟合约映射关系

static const EEquSrvEventType		EEQU_SRVEVENT_HISLOGIN = 0x40;		//登录历史行情
static const EEquSrvEventType		EEQU_SRVEVENT_HINITCOMPLETED = 0x41;//历史初始化完成
static const EEquSrvEventType		EEQU_SRVEVENT_HISQUOTEDATA = 0x42;	//历史行情数据查询应答
static const EEquSrvEventType		EEQU_SRVEVENT_HISQUOTENOTICE = 0x43;//历史行情数据变化通知
static const EEquSrvEventType		EEQU_SRVEVENT_TIMEBUCKET = 0x44;	//时间模板

static const EEquSrvEventType       EEQU_SRVEVENT_TRADE_LOGINQRY = 0x60; //登陆账号查询
static const EEquSrvEventType       EEQU_SRVEVENT_TRADE_LOGINNOTICE = 0x61; //登陆账号通知
static const EEquSrvEventType       EEQU_SRVEVENT_TRADE_ORDERQRY = 0x62;//交易委托查询--
static const EEquSrvEventType       EEQU_SRVEVENT_TRADE_ORDER = 0x63;	//交易委托变化--
static const EEquSrvEventType       EEQU_SRVEVENT_TRADE_MATCHQRY = 0x64;//交易成交查询--
static const EEquSrvEventType       EEQU_SRVEVENT_TRADE_MATCH = 0x65;   //交易成交变化--
static const EEquSrvEventType       EEQU_SRVEVENT_TRADE_POSITQRY = 0x66;//交易持仓查询--
static const EEquSrvEventType       EEQU_SRVEVENT_TRADE_POSITION = 0x67;//交易持仓变化--
static const EEquSrvEventType       EEQU_SRVEVENT_TRADE_FUNDQRY = 0x68; //交易资金查询
static const EEquSrvEventType       EEQU_SRVEVENT_TRADE_USERQRY = 0x6B; //资金账号查询
static const EEquSrvEventType       EEQU_SRVEVENT_TRADE_EXCSTATEQRY = 0x6C;//交易所状态查询--
static const EEquSrvEventType       EEQU_SRVEVENT_TRADE_EXCSTATE = 0x6D;	//交易所状态变化通知--
//错误码类型
typedef U32							EEquErrorCodeType;
typedef STR200                      EEquErrorTextType;              //错误信息

typedef PTR							EEquSrvDataType;				//数据指针
typedef U8                          EEquSrvChainType;
static const EEquSrvChainType		EEQU_SRVCHAIN_END = '0';		//没有后续报文
static const EEquSrvChainType		EEQU_SRVCHAIN_NOTEND = '1';		//有后续报文
																
typedef U16                         EEquFieldSizeType;				//数据体长度
typedef U16                         EEquFieldCountType;				//数据体个数

typedef U32                         EEquStrategyIdType;				//策略编号
typedef STR50                       EEquStrategyNameType;			//策略名称

typedef U8                          EEquStrategyStateType;			//策略状态
static const EEquStrategyStateType	EEQU_STATE_RUN = '0';			//运行
static const EEquStrategyStateType	EEQU_STATE_SUSPEND = '1';		//挂起
static const EEquStrategyStateType	EEQU_STATE_STOP = '2';			//停止

typedef STR50                       EEquSeriesNameType;				//指标名称
typedef STR50                       EEquItemNameType;				//指标线名称
typedef U32						    EEquSeriesThickType;			//线段宽度
typedef I32						    EEquSeriesCoordType;			//坐标
typedef I32						    EEquSeriesIconType;				//图标 点
static const EEquSeriesIconType		EEQU_ICON_RUN = 0;				//正常表情
static const EEquSeriesIconType		EEQU_ICON_SMILE = 1;			//笑脸
static const EEquSeriesIconType		EEQU_ICON_CRYING = 2;			//哭脸
static const EEquSeriesIconType		EEQU_ICON_UP = 3;				//上箭头
static const EEquSeriesIconType		EEQU_ICON_DOWN = 4;				//下箭头
static const EEquSeriesIconType		EEQU_ICON_UP2 = 5;				//上箭头2
static const EEquSeriesIconType		EEQU_ICON_DOWN2 = 6;			//下箭头2
static const EEquSeriesIconType		EEQU_ICON_HORN = 7;				//喇叭
static const EEquSeriesIconType		EEQU_ICON_LOCK = 8;				//加锁
static const EEquSeriesIconType		EEQU_ICON_UNLOCK = 9;			//解锁
static const EEquSeriesIconType		EEQU_ICON_MONEYADD = 10;		//货币+
static const EEquSeriesIconType		EEQU_ICON_MONEYSUB = 11;		//货币-
static const EEquSeriesIconType		EEQU_ICON_ADD = 12;				//加号
static const EEquSeriesIconType		EEQU_ICON_SUB = 13;				//减号
static const EEquSeriesIconType		EEQU_ICON_WARNING = 14;			//叹号
static const EEquSeriesIconType		EEQU_ICON_ERROR = 15;			//叉号

typedef U32                         EEquColorType;				  	//颜色							    
typedef U32						    EEquDataCountType;				//数量
typedef U32						    EEquParamNumType;				//参数个数
typedef U8						    EEquSeriesGroupType;			//分组
								    
typedef STR20					    EEquParamNameType;				//参数名
typedef F64						    EEquParamValueType;				//参数值
								    
typedef B8						    EEquSeriesAxisType;				//是否独立坐标
static const EEquSeriesAxisType	    EEQU_IS_AXIS = '0';				//独立
static const EEquSeriesAxisType	    EEQU_ISNOT_AXIS = '1';			//非独立
								    
typedef U8						    EEquIsMain;						//主副图
static const EEquIsMain			    EEQU_IS_MAIN = '0';				//主图
static const EEquIsMain			    EEQU_ISNOT_MAIN = '1';			//副图 

typedef U8                          EEquSeriesType;				  	//线型
static const EEquSeriesType			EEQU_VERTLINE = 0;				//竖直直线
static const EEquSeriesType			EEQU_INDICATOR = 1;				//指标线
static const EEquSeriesType			EEQU_BAR = 2;					//柱子
static const EEquSeriesType			EEQU_STICKLINE = 3;				//竖线段
static const EEquSeriesType			EEQU_COLORK = 4;				//变色K线
static const EEquSeriesType			EEQU_PARTLINE = 5;				//线段
static const EEquSeriesType			EEQU_ICON = 6;					//图标
static const EEquSeriesType			EEQU_DOT = 7;					//点
static const EEquSeriesType			EEQU_ANY = 8;					//位置格式
static const EEquSeriesType			EEQU_TEXT = 9;					//文本

typedef C8                          STR19[20];
typedef STR19						EEquSigTextType;				//字符串

typedef STR10						EEquExchangeNoType;				//交易所编号
typedef STR50						EEquExchangeNameType;			//交易所名称

typedef STR20						EEquCommodityNoType;			//品种编号（含交易所和品种类型）
typedef STR50						EEquCommodityNameType;			//品种名称

typedef C8							EEquCommodityTypeType;			//品种类型
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_NONE = 'N';		//无
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_SPOT = 'P';		//现货
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_DEFER = 'Y';		//延期
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_FUTURES = 'F';	//期货
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_OPTION = 'O';	//期权
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_MONTH = 'S';		//跨期套利
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_COMMODITY = 'M';	//跨品种套利
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_BUL = 'U';		//看涨垂直套利
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_BER = 'E';		//看跌垂直套利
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_STD = 'D';		//跨式套利
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_STG = 'G';		//宽跨式套利
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_PRT = 'R';		//备兑组合
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_BLT = 'L';		//看涨水平期权
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_BRT = 'Q';		//看跌水平期权
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_DIRECT = 'X';	//外汇 直接汇率 USD是基础货币 USDxxx
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_INDIRECT = 'I';	//外汇 间接汇率 xxxUSD
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_CROSS = 'C';		//外汇 交叉汇率 xxxxxx
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_INDEX = 'Z';		//指数
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_STOCK = 'T';		//股票
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_SPDMON = 's';	//极星跨期 SPD|s|SR|801|805
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_SPDCOM = 'm';	//极星跨品种 SPD|m|A+M2-B|805
static const EEquCommodityTypeType  EEQU_COMMODITYTYPE_SPDDEFER = 'y';	//延期 SPD|m|A+M2-B|805

typedef F64							EEquCommodityNumeType;			//最小变动价 分子
typedef U16							EEquCommodityDenoType;			//最小变动价 分母
typedef F64							EEquCommodityTickType;			//最小变动价 分子/分母
typedef U8							EEquCommodityPrecType;			//最小变动价 精度
typedef F32							EEquPriceMultipleType;			//执行价格倍数类型(期权合约描述的执行价乘以此倍数，数量级等同与标的价格)
typedef F64							EEquCommodityDotType;			//商品乘数

typedef STR100						EEquContractNoType;				//定长合约编号
typedef STR100						EEquContractCodeType;			//合约显示代码
typedef STR100						EEquContractNameType;			//合约名称

typedef C8							EEquCoverModeType;				//平仓方式
static const EEquCoverModeType		EEQU_COVERMODE_NONE = 'N';		//不区分开平
static const EEquCoverModeType		EEQU_COVERMODE_UNFINISH = 'U';	//平仓未了解
static const EEquCoverModeType		EEQU_COVERMODE_COVER = 'C';		//开仓、平仓
static const EEquCoverModeType		EEQU_COVERMODE_TODAY = 'T';		//开仓、平仓、平今

typedef C8							EEquDirect;						//买卖
typedef C8							EEquOffset;						//开平
																	//行情数据类型---------------------------------------------------------------
typedef U8							EEquFidMeanType;			  	//行情字段含义
static const EEquFidMeanType		EEQU_FID_PRECLOSINGPRICE = 0;	//昨收盘价
static const EEquFidMeanType		EEQU_FID_PRESETTLEPRICE = 1;	//昨结算价
static const EEquFidMeanType		EEQU_FID_PREPOSITIONQTY = 2;	//昨持仓量
static const EEquFidMeanType		EEQU_FID_OPENINGPRICE = 3;		//开盘价
static const EEquFidMeanType		EEQU_FID_LASTPRICE = 4;			//最新价
static const EEquFidMeanType		EEQU_FID_HIGHPRICE = 5;			//最高价
static const EEquFidMeanType		EEQU_FID_LOWPRICE = 6;			//最低价
static const EEquFidMeanType		EEQU_FID_HISHIGHPRICE = 7;		//历史最高价
static const EEquFidMeanType		EEQU_FID_HISLOWPRICE = 8;		//历史最低价
static const EEquFidMeanType		EEQU_FID_LIMITUPPRICE = 9;		//涨停价
static const EEquFidMeanType		EEQU_FID_LIMITDOWNPRICE = 10;	//跌停价
static const EEquFidMeanType		EEQU_FID_TOTALQTY = 11;			//当日总成交量
static const EEquFidMeanType		EEQU_FID_POSITIONQTY = 12;		//持仓量
static const EEquFidMeanType		EEQU_FID_AVERAGEPRICE = 13;		//均价
static const EEquFidMeanType		EEQU_FID_CLOSINGPRICE = 14;		//收盘价
static const EEquFidMeanType		EEQU_FID_SETTLEPRICE = 15;		//结算价
static const EEquFidMeanType		EEQU_FID_LASTQTY = 16;			//最新成交量
static const EEquFidMeanType		EEQU_FID_BESTBIDPRICE = 17;		//最优买价
static const EEquFidMeanType		EEQU_FID_BESTBIDQTY = 18;		//最优买量
static const EEquFidMeanType		EEQU_FID_BESTASKPRICE = 19;		//最优卖价
static const EEquFidMeanType		EEQU_FID_BESTASKQTY = 20;		//最优卖量
static const EEquFidMeanType		EEQU_FID_IMPLIEDBIDPRICE = 21;	//隐含买价
static const EEquFidMeanType		EEQU_FID_IMPLIEDBIDQTY = 22;	//隐含买量
static const EEquFidMeanType		EEQU_FID_IMPLIEDASKPRICE = 23;	//隐含卖价
static const EEquFidMeanType		EEQU_FID_IMPLIEDASKQTY = 24;	//隐含卖量
static const EEquFidMeanType		EEQU_FID_TOTALBIDQTY = 25;		//委买总量
static const EEquFidMeanType		EEQU_FID_TOTALASKQTY = 26;		//委卖总量
static const EEquFidMeanType		EEQU_FID_TOTALTURNOVER = 27;	//总成交额
static const EEquFidMeanType		EEQU_FID_CAPITALIZATION = 28;	//总市值
static const EEquFidMeanType		EEQU_FID_CIRCULATION = 29;		//流通市值
static const EEquFidMeanType		EEQU_FID_THEORETICALPRICE = 30;	//理论价
static const EEquFidMeanType		EEQU_FID_RATIO = 31;			//波动率 非价格处理
static const EEquFidMeanType		EEQU_FID_DELTA = 32;			//Delta
static const EEquFidMeanType		EEQU_FID_GAMMA = 33;			//Gamma
static const EEquFidMeanType		EEQU_FID_VEGA = 34;				//Vega
static const EEquFidMeanType		EEQU_FID_THETA = 35;			//Theta
static const EEquFidMeanType		EEQU_FID_RHO = 36;				//Rho
static const EEquFidMeanType		EEQU_FID_INTRINSICVALUE = 37;	//期权内在价值
static const EEquFidMeanType		EEQU_FID_UNDERLYCONT = 38;		//虚拟合约对应的标的合约
static const EEquFidMeanType		EEQU_FID_SubBidPrice1 = 39;		//买价1
static const EEquFidMeanType		EEQU_FID_SubBidPrice2 = 40;		//买价2
static const EEquFidMeanType		EEQU_FID_SubBidPrice3 = 41;		//买价3
static const EEquFidMeanType		EEQU_FID_SubBidPrice4 = 42;		//买价4
static const EEquFidMeanType		EEQU_FID_SubAskPrice1 = 43;		//卖价1
static const EEquFidMeanType		EEQU_FID_SubAskPrice2 = 44;		//卖价2
static const EEquFidMeanType		EEQU_FID_SubAskPrice3 = 45;		//卖价3
static const EEquFidMeanType		EEQU_FID_SubAskPrice4 = 46;		//卖价4
static const EEquFidMeanType		EEQU_FID_SubLastPrice1 = 47;	//最新价1
static const EEquFidMeanType		EEQU_FID_SubLastPrice2 = 48;	//最新价2
static const EEquFidMeanType		EEQU_FID_SubLastPrice3 = 49;	//最新价3
static const EEquFidMeanType		EEQU_FID_SubLastPrice4 = 50;	//最新价4
static const EEquFidMeanType		EEQU_FID_PreAveragePrice = 51;	//昨日均价

static const EEquFidMeanType		EEQU_FID_TIMEVALUE = 111;		//期权时间价值
static const EEquFidMeanType		EEQU_FID_UPDOWN = 112;			//涨跌
static const EEquFidMeanType		EEQU_FID_GROWTH = 113;			//涨幅
static const EEquFidMeanType		EEQU_FID_NOWINTERST = 114;		//增仓
static const EEquFidMeanType		EEQU_FID_TURNRATE = 115;		//换手率
static const EEquFidMeanType		EEQU_FID_CODE = 122;			//合约代码
static const EEquFidMeanType		EEQU_FID_SRCCODE = 123;			//原始合约代码
static const EEquFidMeanType		EEQU_FID_NAME = 124;			//合约名称
static const EEquFidMeanType		EEQU_FID_DATETIME = 125;		//更新时间												   
static const EEquFidMeanType		EEQU_FID_SPREADRATIO = 126;		//套利行情系数

static const EEquFidMeanType		EEQU_FID_MEAN_COUNT = 128;		//字段总数量

typedef C8							EEquFidAttrType;			  	//行情字段属性
static const EEquFidAttrType		EEQU_FIDATTR_NONE = 0;			//无值
static const EEquFidAttrType		EEQU_FIDATTR_VALID = 1;			//有值
static const EEquFidAttrType		EEQU_FIDATTR_IMPLIED = 2;		//隐含

typedef C8							EEquFidTypeType;			  	//字段类型类型
static const EEquFidTypeType		EEQU_FIDTYPE_NONE = 0;			//无效
static const EEquFidTypeType		EEQU_FIDTYPE_PRICE = 1;			//价格
static const EEquFidTypeType		EEQU_FIDTYPE_QTY = 2;			//数量
static const EEquFidTypeType		EEQU_FIDTYPE_GREEK = 3;			//希腊字母
static const EEquFidTypeType		EEQU_FIDTYPE_DATETIME = 4;		//日期时间
static const EEquFidTypeType		EEQU_FIDTYPE_DATE = 5;			//日期
static const EEquFidTypeType		EEQU_FIDTYPE_TIME = 6;			//时间
static const EEquFidTypeType		EEQU_FIDTYPE_STATE = 7;			//状态
static const EEquFidTypeType		EEQU_FIDTYPE_STR = 8;			//字符串 最大7字节
static const EEquFidTypeType		EEQU_FIDTYPE_PTR = 9;			//指针

static const EEquFidTypeType		EEQU_FIDTYPE_ARRAY[] =
{
	EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, //0
	EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, //8
	EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_PRICE, //16
	EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_GREEK, //24
	EEQU_FIDTYPE_GREEK, EEQU_FIDTYPE_GREEK, EEQU_FIDTYPE_GREEK, EEQU_FIDTYPE_GREEK, EEQU_FIDTYPE_GREEK, EEQU_FIDTYPE_PRICE , EEQU_FIDTYPE_STR , EEQU_FIDTYPE_PRICE, //32
	EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, //40
	EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , //48
	EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , //56
	EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , //64
	EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , //72
	EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , //80
	EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , //88
	EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , //96
	EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_PRICE, //104
	EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_QTY  , EEQU_FIDTYPE_PRICE, EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , //112
	EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_NONE , EEQU_FIDTYPE_STR  , EEQU_FIDTYPE_STR  , EEQU_FIDTYPE_STR  , EEQU_FIDTYPE_DATETIME, EEQU_FIDTYPE_STR, EEQU_FIDTYPE_NONE, //120
};

static const U8						EEQU_MAX_L2_DEPTH = 10;				//L2最大深度
typedef F64                         EEquPriceType;						//价格类型
typedef U64                         EEquQtyType;						//数量类型
typedef C8                          EEquStateType;						//状态类型
typedef C8                          EEquStrType[8];						//行情字段短字符串类型
typedef PTR                         EEquPtrType;						//指针类型
typedef F64                         EEquGreekType;						//希腊字母类型
typedef F64                         EEquVolatilityType;					//波动率类型
typedef STR20						EEquPriceStrType;					//价格格式化为显示的字符串
typedef U16                         EEquWidthType;						//宽度类型
typedef U64                         EEquDateTimeType;			  		//日期时间
typedef U32                         EEquDateType;				  		//日期
typedef U32                         EEquTimeType;				  		//时间
typedef U16							EEquDaysType;				  		//日期数

typedef U8							EEquKLineSliceType;					//k线片段类型 多秒，多分钟，多日
typedef I32							EEquKLineIndexType;					//k线索引
typedef U32							EEquKLineCountType;					//k线数量

typedef C8							EEquKLineTypeType;				 	//k线类型
static const EEquKLineTypeType		EEQU_KLINE_TICK = 'T';				//分笔 RawKLineSliceType 为0
static const EEquKLineTypeType		EEQU_KLINE_MINUTE = 'M';			//分钟线
static const EEquKLineTypeType		EEQU_KLINE_DAY = 'D';				//日线

typedef U8							EEquNeedNotice;
static const EEquNeedNotice			EEQU_NOTICE_NOTNEED = '0';			//需要后续刷新推送
static const EEquNeedNotice			EEQU_NOTICE_NEED = '1';				//不需要后续推送

typedef U32							EEquSessionIdType;					//订阅会话序号
typedef U32							EEquLastQtyType;					//明细现手变化
typedef I32							EEquPositionChgType;				//明细持仓变化

typedef I16							EEquTimeBucketIndexType;			//交易时段模板顺序
typedef I16							EEquTimeBucketCalCountType;			//交易时段计算分钟数

typedef C8										EEquTimeBucketTradeStateType;			//交易时段状态 交易时段仅用'3','4','5'，行情交易状态用所有
static const EEquTimeBucketTradeStateType		EEQU_TRADESTATE_BID = '1';	//集合竞价
static const EEquTimeBucketTradeStateType		EEQU_TRADESTATE_MATCH = '2';	//集合竞价撮合
static const EEquTimeBucketTradeStateType		EEQU_TRADESTATE_CONTINUOUS = '3';	//连续交易
static const EEquTimeBucketTradeStateType		EEQU_TRADESTATE_PAUSED = '4';	//暂停
static const EEquTimeBucketTradeStateType		EEQU_TRADESTATE_CLOSE = '5';	//闭式
static const EEquTimeBucketTradeStateType		EEQU_TRADESTATE_DEALLAST = '6';	//闭市处理时间
static const EEquTimeBucketTradeStateType		EEQU_TRADESTATE_SWITCHTRADE = '0';	//交易日切换时间
static const EEquTimeBucketTradeStateType		EEQU_TRADESTATE_UNKNOWN = 'N';	//未知状态
static const EEquTimeBucketTradeStateType		EEQU_TRADESTATE_INITIALIZE = 'I';	//正初始化
static const EEquTimeBucketTradeStateType		EEQU_TRADESTATE_READY = 'R';	//准备就绪

typedef C8										EEquTimeBucketDateFlagType; 			//交易时段日期标志 T-1,T,T+1
static const EEquTimeBucketDateFlagType			EEQU_DATEFLAG_PREDAY = '0';	//T-1
static const EEquTimeBucketDateFlagType			EEQU_DATEFLAG_CURDAY = '1';	//T
static const EEquTimeBucketDateFlagType			EEQU_DATEFLAG_NEXTDAY = '2';	//T+1

//交易所信息查询请求
typedef struct EEquExchangeReq
{
	EEquExchangeNoType              ExchangeNo;		//交易所代码
} EEquExchangeReq;

//交易所信息查询数据
typedef struct EEquExchangeData
{
	EEquExchangeNoType              ExchangeNo;		//交易所代码
	EEquExchangeNameType            ExchangeName;	//交易所名称
} EEquExchangeData;

//品种信息查询请求消息
typedef struct EEquCommodityReq
{
	EEquCommodityNoType             CommodityNo;	//填空从头开始查，续查每次把应答包发回请求
} EEquCommodityReq;

//品种信息查询数据
typedef struct EEquCommodityData
{
	EEquExchangeNoType				ExchangeNo;	
	EEquCommodityNoType				CommodityNo;	//品种代码
	EEquCommodityTypeType			CommodityType;	//品种类型
	EEquCommodityNameType			CommodityName;	//品种名称
	EEquCommodityNumeType			PriceNume;		//分子
	EEquCommodityDenoType			PriceDeno;		//分母
	EEquCommodityTickType			PriceTick;		//最小变动价
	EEquCommodityPrecType			PricePrec;		//价格精度
	EEquCommodityDotType			TradeDot;		//每手乘数
	EEquCoverModeType				CoverMode;		//平仓方式
} EEquCommodityData;

//合约信息查询请求
typedef struct EEquContractReq
{
	EEquContractNoType              ContractNo;		//合约编号
} EEquContractReq;

//合约信息查询数据
typedef struct EEquContractData
{
	EEquExchangeNoType				ExchangeNo;		//交易所
	EEquCommodityNoType				CommodityNo;	//品种代码
	EEquContractNoType              ContractNo;     //合约编号
} EEquContractData;

//订阅和退订请求, 普通行情和level2行情均使用此结构
typedef struct EEquSnapShotReq
{
	EEquContractNoType				ContractNo;    //合约编号(客户端向后台订阅使用合约)

} EEquSnapShotReq;

//行情快照中各字段
typedef struct EEquQuoteField
{
	union
	{
		EEquFidMeanType				FidMean;		//变化行情使用标识
		EEquFidAttrType				FidAttr;		//固定行情使用属性
	};
	union
	{
		EEquPriceType				Price;
		EEquQtyType					Qty;
		EEquGreekType				Greek;
		EEquVolatilityType			Volatility;
		EEquDateTimeType			DateTime;
		EEquDateType				Date;
		EEquTimeType				Time;
		EEquStateType				State;
		EEquStrType					Str;
		EEquPtrType					Ptr;
	};
} EEquQuoteField;

//行情快照部分					   
typedef struct EEquSnapShotData
{
	EEquDateTimeType				UpdateTime;     //行情更新时间
	EEquFidMeanType					FieldCount;     //EquSnapShotField的数量
	EEquQuoteField	                FieldData[1];   //数据字段的起始位置，无数据时此结构不包含此字段长度
} EEquSnapShotData;

//行情快照L2
typedef struct EEquQuoteFieldL2
{
	EEquPriceType					Price;
	EEquQtyType						Qty;
} EEquQuoteFieldL2;

typedef struct EEquQuoteSnapShotL2
{
	EEquQuoteFieldL2				BData[EEQU_MAX_L2_DEPTH];
	EEquQuoteFieldL2				SData[EEQU_MAX_L2_DEPTH];
} EEquQuoteSnapShotL2;

//K线查询请求
typedef struct EEquKLineReq
{
	EEquKLineCountType				ReqCount;        //期望数量（扩展使用）
	EEquContractNoType              ContractNo;      //合约ID
	EEquKLineTypeType               KLineType;       //K线类型
	EEquKLineSliceType              KLineSlice;      //K线多秒(0 tick) 分钟 日线
	EEquNeedNotice					NeedNotice;		//需要订阅通知
} EEquKLineReq;

typedef struct EEquKLineData //sizeof 80字节
{
	EEquKLineIndexType              KLineIndex;      //K线索引  tick每笔连续序号，min交易分钟序号，day无效
	EEquDateType					TradeDate;       //交易日   tick无效，min可能和时间戳不同，day和时间戳相同
	EEquDateTimeType				DateTimeStamp;   //时间戳，不同数据类型，精度不同
	EEquQtyType						TotalQty;       //行情快照 总成交量
	EEquQtyType						PositionQty;    //行情快照 持仓量
	EEquPriceType					LastPrice;      //最新价（收盘价）

	union
	{
		struct
		{
			EEquQtyType				KLineQty;       //K线成交量 day  min
			EEquPriceType			OpeningPrice;   //开盘价  day  min
			EEquPriceType			HighPrice;      //最高价  day  min
			EEquPriceType			LowPrice;       //最低价  day  min
			EEquPriceType			SettlePrice;    //结算价  day  min

		};
		struct
		{
			EEquLastQtyType			LastQty;        //明细现手  tick
			EEquPositionChgType		PositionChg;    //持仓量变化 tick
			EEquPriceType			BuyPrice;       //买价 tick
			EEquPriceType			SellPrice;      //卖价 tick
			EEquQtyType				BuyQty;         //买量 tick
			EEquQtyType				SellQty;        //卖量 tick
		};
	};
} EEquKLineData;
	

//K线策略切换
typedef struct EEquKLineStrategySwitch
{
	EEquStrategyIdType				StrategyId;		 //策略ID
	EEquStrategyNameType			StrategyName;	 //策略名称
	EEquContractNoType              ContractNo;      //合约ID
	EEquKLineTypeType               KLineType;       //K线类型
	EEquKLineSliceType				KLineSlice;		 //多秒 分钟 日线
} EEquKLineStrategySwitch;

//K线结果推送
typedef struct EEquKLineDataResult
{
	EEquStrategyIdType				StrategyId;		 //策略编号

	EEquKLineCountType				Count;			 //数量
	EEquKLineData					*Data;		     //数据
} EEquKLineDataResult;

typedef struct EEquKLineSeries
{
	EEquKLineIndexType				KLineIndex;		//索引0无效
	EEquPriceType					Value;			//InvalidNumeric 表示无效数据
	union
	{
		struct //变色K线,竖直线
		{
			EEquColorType			ClrK;
		};

		struct //图标类型,点类型
		{
			EEquSeriesIconType		Icon;
		};

		struct //竖线
		{
			EEquColorType			ClrStick;
			EEquPriceType			StickValue;
		};

		struct  //柱子
		{
			EEquColorType			ClrBar;
			B8						Filled;
			EEquPriceType			BarValue;
		};

		struct  //线段		  `
		{
			EEquSeriesCoordType		Idx2;	        //线段的末端K线坐标
			EEquColorType			ClrLine;	    //线段颜色
			EEquPriceType			LineValue;		//线段末端数据
			EEquSeriesThickType		LinWid;			//线段宽度
		};
		struct //文本
		{
			EEquSigTextType			Text;		
		};
	};
}EEquKLineSeries;

//参数信息
typedef struct EEquSeriesParam
{
	EEquParamNameType				ParamName;		//参数名
	EEquParamValueType				ParamValue;		//参数值
}EEquSeriesParam;

//K线指标参数
typedef struct EEquKLineSeriesInfo
{
	EEquItemNameType				ItemName;		//具体指标线 名称
	EEquSeriesType					Type;			//线型	
	EEquColorType					Color;			//颜色
	EEquSeriesThickType				Thick;			//线宽
	EEquSeriesAxisType				OwnAxis;		//是否独立坐标
	
	EEquSeriesParam					Param[10];		//参数 Max10
	EEquParamNumType				ParamNum;		//参数个数
	EEquSeriesGroupType				Groupid;		//组号 
	EEquSeriesNameType				GroupName;		//组名（指标名）
	EEquIsMain						Main;			//0-主图 1-副图1
	
	EEquStrategyIdType				StrategyId;		//策略ID
} EEquKLineSeriesInfo;

//K线指标推送
typedef struct EEquKLineSeriesResult
{
	EEquStrategyIdType				StrategyId;		 //策略编号
	EEquSeriesNameType				SeriesName;		 //指标名称

	EEquSeriesType					SeriesType;		 //指标线型		//弃用
	EEquIsMain						IsMain;			 //主图 副图	//弃用

	EEquKLineCountType				Count;			 //数量
	EEquKLineSeries					*Data;		     //数据
} EEquKLineSeriesResult;

typedef EEquKLineSeriesInfo			EEquKLineSignalInfo;

//信号数据
typedef struct EEquSignalItem
{
	EEquKLineIndexType				KLineIndex;		//K线索引
	EEquContractNoType              ContractNo;     //合约ID
	EEquDirect						Direct;			//买卖方向
	EEquOffset						Offset;			//开平
	EEquPriceType					Price;			//价格
	EEquQtyType						Qty;			//数量
		
}EEquSignalItem;

//K线信号推送
typedef struct EEquKLineSignalResult
{
	EEquStrategyIdType				StrategyId;		//策略ID
	EEquSeriesNameType				SeriesName;		//信号名称
	
	EEquDataCountType				Count;			//数量
	EEquSignalItem					*Data;			//数据
} EEquKLineSignalResult;

//K线biao推送
typedef struct EEquStrategyDataUpdateNotice
{
	EEquStrategyIdType				StrategyId;		//策略ID
} EEquStrategyDataUpdateNotice;

//策略状态更新
typedef struct EEquKlineStrategyStateNotice
{
	EEquStrategyIdType				StrategyId;		//策略ID
	EEquStrategyStateType			StrategyState;	//策略状态
} EEquKlineStrategyStateNotice;

typedef EEquCommodityReq			EEquCommodityTimeBucketReq;
//时间模板
typedef struct EEquHisQuoteTimeBucket
{
	EEquTimeBucketIndexType			Index;
	EEquTimeType					BeginTime;
	EEquTimeType					EndTime;
	EEquTimeBucketTradeStateType	TradeState;
	EEquTimeBucketDateFlagType		DateFlag;
	EEquTimeBucketCalCountType		CalCount;						//基础模版对应计算模版的分钟数
	EEquCommodityNoType				Commodity;
} EEquHisQuoteTimeBucket;
///////////////////////////////////////////////////////////交易///////////////////////////////////////////////////////////

typedef STR20 						EEquLoginNoType;					//登录账号
typedef STR50 						EEquLoginNameType;					//登录名称
typedef C8							EEquUserType;						//用户类型
typedef STR20 						EEquUserNoType;						//资金账号
typedef STR50 						EEquUserNameType;					//资金账户名称
typedef STR20 						EEquSignType;						//服务器标识
typedef U32							EEquCountType;						//请求数量
typedef STR50						EEquLoginApiType;					//API类型
typedef STR10						EEquTradeDateType;					//交易日
typedef C8							EEquReadyType;						//初始化完成 0未完成 1完成
static const EEquReadyType			EEQU_READY			= '1';			//完成
static const EEquReadyType			EEQU_NOTREADY		= '0';			//未完成
typedef C8							EEquNextType;						//是否接着查询

typedef STR20						EEquCurrencyNoType;					//币种
typedef F64                         EEquExchangeRateType;				//币种汇率
typedef F64                         EEquMoneyValueType;					//资金信息
typedef STR20                       EEquUpdateTimeType;					//更新时间
typedef STR20                       EEquValidTimeType;					//有效时间
typedef STR50                       EEquRemarkInfoType;					//备注
typedef U32							EEquOrderIdType;					//定单号
typedef STR20	                    EEquOrderNoType;					//委托号
typedef STR20	                    EEquMatchNoType;					//成交号
typedef STR50	                    EEquPositionNoType;					//持仓号
typedef STR50						EEquSystemNo;						//系统号
typedef I32							EEquErrorCode;						//错误码
typedef STR200						EEquErrorText;						//错误信息

typedef C8	 EEquOrderType;			//定单类型
static const EEquOrderType			otUnDefine = 'U';//未定义
static const EEquOrderType			otMarket = '1';//市价单
static const EEquOrderType			otLimit = '2';//限价单
static const EEquOrderType			otMarketStop = '3';//市价止损
static const EEquOrderType			otLimitStop = '4';//限价止损
static const EEquOrderType			otExecute = '5';//行权
static const EEquOrderType			otAbandon = '6';//弃权
static const EEquOrderType			otEnquiry = '7';//询价
static const EEquOrderType			otOffer = '8';//应价
static const EEquOrderType			otIceberg = '9';//冰山单
static const EEquOrderType			otGhost = 'A';//影子单
static const EEquOrderType			otSwap = 'B';//互换
static const EEquOrderType			otSpreadApply = 'C';//套利申请
static const EEquOrderType			otHedgApply = 'D';//套保申请
static const EEquOrderType			otOptionAutoClose = 'F';//行权前期权自对冲申请
static const EEquOrderType			otFutureAutoClose = 'G';//履约期货自对冲申请
static const EEquOrderType			otMarketOptionKeep = 'H';//做市商留仓

typedef C8	 EEquValidType;			//有效类型
static const EEquValidType			vtNone = 'N';//无
static const EEquValidType			vtFOK = '4';//即时全部
static const EEquValidType			vtIOC = '3';//即时部分
static const EEquValidType			vtGFD = '0';//当日有效
static const EEquValidType			vtGTC = '1';//长期有效
static const EEquValidType			vtGTD = '2';//限期有效

typedef C8	 EEquDirect;				//买卖
static const EEquDirect				dNone = 'N';
static const EEquDirect				dBuy = 'B';//买入
static const EEquDirect				dSell = 'S';//卖出
static const EEquDirect				dBoth = 'A';//双边

typedef C8	 EEquOffset;				//开平
static const EEquOffset				oNone = 'N';//无
static const EEquOffset				oOpen = 'O';//开仓
static const EEquOffset				oCover = 'C';//平仓
static const EEquOffset				oCoverT = 'T';//平今
static const EEquOffset				oOpenCover = '1';//开平，应价时有效, 本地套利也可以
static const EEquOffset				oCoverOpen = '2';//平开，应价时有效, 本地套利也可以

typedef C8   EEquHedge;				//投保标记
static const EEquHedge				hNone = 'N';//无
static const EEquHedge				hSpeculate = 'T';//投机
static const EEquHedge				hHedge = 'B';//套保
static const EEquHedge				hSpread = 'S';//套利
static const EEquHedge				hMarket = 'M';//做市

typedef C8   EEquOrderState;		 //报单状态
static const EEquOrderState			osNone = 'N';//无
static const EEquOrderState			osSended = '0';//已发送
static const EEquOrderState			osAccept = '1';//已受理
static const EEquOrderState			osTriggering = '2';//待触发
static const EEquOrderState			osActive = '3';//已生效
static const EEquOrderState			osQueued = '4';//已排队
static const EEquOrderState			osPartFilled = '5';//部分成交
static const EEquOrderState			osFilled = '6';//完全成交
static const EEquOrderState			osCanceling = '7';//待撤
static const EEquOrderState			osModifying = '8';//待改
static const EEquOrderState			osCanceled = '9';//已撤单
static const EEquOrderState			osPartCanceled = 'A';//已撤余单
static const EEquOrderState			osFail = 'B';//指令失败
static const EEquOrderState			osChecking = 'C';//待审核
static const EEquOrderState			osSuspended = 'D';//已挂起
static const EEquOrderState			osApply = 'E';//已申请
static const EEquOrderState			osInvalid = 'F';//无效单
static const EEquOrderState			osPartTriggered = 'G';//部分触发
static const EEquOrderState			osFillTriggered = 'H';//完全触发
static const EEquOrderState			osPartFailed = 'I';//余单失败


typedef C8	 EEquStrategyType;		//策略类型
static const EEquStrategyType		stNone = 'N'; //无
static const EEquStrategyType		stPreOrder = 'P'; //预备单(埋单)
static const EEquStrategyType		stAutoOrder = 'A'; //自动单
static const EEquStrategyType		stCondition = 'C'; //条件单

typedef C8	 EEquUserType;			//用户身份
static const EEquUserType			uiNone = 'n';
static const EEquUserType			uiUnDefine = 'u';//未定义
static const EEquUserType			uiUser = 'c';//单客户
static const EEquUserType			uiProxy = 'd';//下单人
static const EEquUserType			uiBroker = 'b';//经纪人
static const EEquUserType			uiTrader = 't';//交易员
static const EEquUserType			uiQUser = 'q';//行情客户

typedef C8	 EEquCoverMode;			//平仓方式
static const EEquCoverMode			cmNone = 'N';//不区分开平
static const EEquCoverMode			cmUnfinish = 'U';//平仓未了解
static const EEquCoverMode			cmCover = 'C';//开仓、平仓
static const EEquCoverMode			cmCoverToday = 'T';//开仓、平仓、平今

typedef C8   EEquTrigMode;			 //触发模式
static const EEquTrigMode			tmNone = 'N';//无
static const EEquTrigMode			tmLatest = 'L';//最新价
static const EEquTrigMode			tmBid = 'B';//买价
static const EEquTrigMode			tmAsk = 'A';//卖价

typedef C8	 EEquTrigCond;			//触发条件
static const EEquTrigCond			tcNone = 'N';//无
static const EEquTrigCond			tcGreater = 'g';//大于
static const EEquTrigCond			tcGreaterEEqual = 'G';//大于等于
static const EEquTrigCond			tcLess = 'l';//小于
static const EEquTrigCond			tcLessEEqual = 'L';//小于等于

typedef C8   EEquTradeSect;			//交易时段
static const EEquTradeSect			tsDay = 'D'; //白天交易时段
static const EEquTradeSect			tsNight = 'N'; //晚上（T+1）交易时段
static const EEquTradeSect			tsAll = 'A'; //全交易时段

typedef C8   EEquBoolType;			//是否
static const EEquBoolType			bYes = 'Y'; //是
static const EEquBoolType			bNo = 'N'; //否

typedef STR20						EEquExchDateTimeType;				//交易所时间

typedef C8	 EEquTradeState;
static const EEquTradeState			tsUnknown = 'N'; //未知状态
static const EEquTradeState			tsIniting = 'I'; //正初始化
static const EEquTradeState			tsReady = 'R'; //准备就绪
static const EEquTradeState			tsSwitchDay = '0'; //交易日切换
static const EEquTradeState			tsBiding = '1'; //竞价申报
static const EEquTradeState			tsMakeMatch = '2'; //竞价撮合
static const EEquTradeState			tsTradeing = '3'; //连续交易
static const EEquTradeState			tsPause = '4'; //交易暂停
static const EEquTradeState			tsClosed = '5'; //交易闭市   
static const EEquTradeState			tsBidPause = '6'; //竞价暂停
static const EEquTradeState			tsGatewayDisconnect = '7'; //报盘未连
static const EEquTradeState			tsTradeDisconnect = '8'; //交易未连
static const EEquTradeState			tsCloseDeal = '9'; //闭市处理

//登陆账号查询请求
typedef struct EEquLoginInfoReq
{
	EEquLoginNoType					LoginNo;
	EEquSignType					Sign;
}EEquLoginInfoReq;
//登录账号查询应答
typedef struct EEquLoginInfoRsp
{
	EEquLoginNoType					LoginNo;
	EEquSignType					Sign;
	EEquLoginNameType				LoginName;
	EEquLoginApiType				LoginApi;
	EEquTradeDateType				TradeDate;
	EEquReadyType					IsReady;
}EEquLoginInfoRsp;

//资金账号查询请求
typedef struct EEquUserInfoReq
{
	EEquLoginNoType					UserNo;
	EEquSignType					Sign;
}EEquUserInfoReq;
//资金账号查询应答
typedef struct EEquUserInfoRsp
{
	EEquUserNoType					UserNo;
	EEquSignType					Sign;
	EEquLoginNoType					LoginNo;
	EEquUserNameType				UserName;
}EEquUserInfoRsp;

//资金查询请求
typedef struct EEquUserMoneyReq
{
	EEquUserNoType					UserNo;					//不为空
	EEquSignType					Sign;					//不为空
	EEquCurrencyNoType				CurrencyNo;				//空 全查
}EEquUserMoneyReq;

//资金查询应答
typedef struct EEquUserMoneyRsp
{
	EEquUserNoType					UserNo;
	EEquSignType					Sign;
	EEquCurrencyNoType				CurrencyNo;				//币种号(Currency_Base表示币种组基币资金)
	EEquExchangeRateType			ExchangeRate;			//币种汇率

	EEquMoneyValueType				FrozenFee;				//冻结手续费20
	EEquMoneyValueType				FrozenDeposit;			//冻结保证金19
	EEquMoneyValueType				Fee;					//手续费(包含交割手续费)
	EEquMoneyValueType				Deposit;				//保证金

	EEquMoneyValueType				FloatProfit;			//不含LME持仓盈亏,盯市 market to market
	EEquMoneyValueType				FloatProfitTBT;			//逐笔浮赢 trade by trade
	EEquMoneyValueType				CoverProfit;			//平盈 盯市
	EEquMoneyValueType				CoverProfitTBT;			//逐笔平盈

	EEquMoneyValueType				Balance;				//今资金=PreBalance+Adjust+CashIn-CashOut-Fee(TradeFee+DeliveryFee+ExchangeFee)+CoverProfitTBT+Premium 
	EEquMoneyValueType				Equity;					//今权益=Balance+FloatProfitTBT(NewFloatProfit+LmeFloatProfit)+UnExpiredProfit
	EEquMoneyValueType				Available;				//今可用=Equity-Deposit-Frozen(FrozenDeposit+FrozenFee)

	EEquUpdateTimeType				UpdateTime;				//更新时间
}EEquUserMoneyRsp;

//委托查询请求
typedef struct EEquOrderQryReq
{
	EEquUserNoType					UserNo;
	EEquSignType					Sign;
}EEquOrderQryReq;

//委托请求
typedef struct EEquOrderInsertReq
{
	EEquUserNoType					UserNo;
	EEquSignType					Sign;
	EEquContractNoType				Cont;					//行情合约
	EEquOrderType					OrderType;				//定单类型 
	EEquValidType					ValidType;				//有效类型 
	EEquValidTimeType				ValidTime;				//有效日期时间(GTD情况下使用)
	EEquDirect						Direct;					//买卖方向 
	EEquOffset						Offset;					//开仓平仓 或 应价买入开平 
	EEquHedge						Hedge;					//投机保值 
	EEquPriceType					OrderPrice;				//委托价格 或 期权应价买入价格
	EEquPriceType					TriggerPrice;			//触发价格
	EEquTrigMode					TriggerMode;			//触发模式
	EEquTrigCond					TriggerCondition;		//触发条件
	EEquQtyType						OrderQty;				//委托数量 或 期权应价数量
	EEquStrategyType				StrategyType;			//策略类型
	EEquRemarkInfoType				Remark;					//下单备注字段，只有下单时生效。如果需要唯一标识一个或一组定单，最好以GUID来标识，否则可能和其他下单途径的ID重复
	EEquTradeSect					AddOneIsValid;			//T+1时段有效(仅港交所)
}EEquOrderInsertReq;
//委托撤单
typedef struct EEquOrderCancelReq
{
	EEquOrderIdType					OrderId;				//定单号
}EEquOrderCancelReq;
//委托改单
typedef struct EEquOrderModifyReq
{
	EEquUserNoType					UserNo;
	EEquSignType					Sign;
	EEquContractNoType				Cont;					//行情合约
	EEquOrderType					OrderType;				//定单类型 
	EEquValidType					ValidType;				//有效类型 
	EEquValidTimeType				ValidTime;				//有效日期时间(GTD情况下使用)
	EEquDirect						Direct;					//买卖方向 
	EEquOffset						Offset;					//开仓平仓 或 应价买入开平 
	EEquHedge						Hedge;					//投机保值 
	EEquPriceType					OrderPrice;				//委托价格 或 期权应价买入价格
	EEquPriceType					TriggerPrice;			//触发价格
	EEquTrigMode					TriggerMode;			//触发模式
	EEquTrigCond					TriggerCondition;		//触发条件
	EEquQtyType						OrderQty;				//委托数量 或 期权应价数量
	EEquStrategyType				StrategyType;			//策略类型
	EEquRemarkInfoType				Remark;					//下单备注字段，只有下单时生效。如果需要唯一标识一个或一组定单，最好以GUID来标识，否则可能和其他下单途径的ID重复
	EEquTradeSect					AddOneIsValid;			//T+1时段有效(仅港交所)

	EEquOrderIdType					OrderId;				//定单号
}EEquOrderModifyReq;
//委托通知
typedef struct EEquOrderDataNotice
{
	EEquSessionIdType				SessionId;				//会话号
	EEquUserNoType					UserNo;
	EEquSignType					Sign;
	EEquContractNoType				Cont;					//行情合约
	EEquOrderType					OrderType;				//定单类型 
	EEquValidType					ValidType;				//有效类型 
	EEquValidTimeType				ValidTime;				//有效日期时间(GTD情况下使用)
	EEquDirect						Direct;					//买卖方向 
	EEquOffset						Offset;					//开仓平仓 或 应价买入开平 
	EEquHedge						Hedge;					//投机保值 
	EEquPriceType					OrderPrice;				//委托价格 或 期权应价买入价格
	EEquPriceType					TriggerPrice;			//触发价格
	EEquTrigMode					TriggerMode;			//触发模式
	EEquTrigCond					TriggerCondition;		//触发条件
	EEquQtyType						OrderQty;				//委托数量 或 期权应价数量
	EEquStrategyType				StrategyType;			//策略类型
	EEquRemarkInfoType				Remark;					//下单备注字段，只有下单时生效。如果需要唯一标识一个或一组定单，最好以GUID来标识，否则可能和其他下单途径的ID重复
	EEquTradeSect					AddOneIsValid;			//T+1时段有效(仅港交所)

	EEquOrderState					OrderState;				//委托状态
	EEquOrderIdType					OrderId;				//定单号
	EEquOrderNoType					OrderNo;				//委托号
	EEquPriceType					MatchPrice;				//成交价
	EEquQtyType						MatchQty;				//成交量
	EEquErrorCode					ErrorCode;				//最新信息码				
	EEquErrorText					ErrorText;				//最新错误信息
	EEquUpdateTimeType				InsertTime;				//下单时间
	EEquUpdateTimeType				UpdateTime;				//更新时间
}EEquOrderDataNotice;

typedef EEquOrderQryReq				EEquMatchQryReq;		//成交查询结构
//成交数据查询应答/通知
typedef struct EEquMatchNotice
{
	EEquUserNoType					UserNo;
	EEquSignType					Sign;
	EEquContractNoType				Cont;					//行情合约
	EEquDirect						Direct;					//买卖方向 
	EEquOffset						Offset;					//开仓平仓 或 应价买入开平 
	EEquHedge						Hedge;					//投机保值 
	EEquOrderNoType					OrderNo;				//委托号
	EEquPriceType					MatchPrice;				//成交价
	EEquQtyType						MatchQty;				//成交量
	EEquCurrencyNoType				FeeCurrency;			//手续费币种
	EEquMoneyValueType				MatchFee;				//成交手续费
	EEquUpdateTimeType				MatchDateTime;			//更新时间
	EEquBoolType					AddOne;					//T+1成交
	EEquBoolType					Deleted;				//是否删除
	EEquMatchNoType					MatchNo;				//成交号 20200410
}EEquMatchNotice;

//持仓查询请求结构
typedef EEquOrderQryReq				EEquPositionQryReq;		
//持仓数据查询应答、通知
typedef struct EEquPositionNotice
{
	EEquPositionNoType				PositionNo;
	EEquUserNoType					UserNo;
	EEquSignType					Sign;
	EEquContractNoType				Cont;					//行情合约
	EEquDirect						Direct;					//买卖方向 
	EEquHedge						Hedge;					//投机保值 
	EEquMoneyValueType				Deposit;				//客户初始保证金
	EEquQtyType						PositionQty;			//总持仓量	
	EEquQtyType					    PrePositionQty;			//昨仓数量
	EEquPriceType					PositionPrice;			//价格
	EEquPriceType					ProfitCalcPrice;		//浮盈计算价
	EEquMoneyValueType				FloatProfit;			//浮盈
	EEquMoneyValueType				FloatProfitTBT;			//逐笔浮赢 trade by trade
}EEquPositionNotice;


//////////////////////////////////////////////////////////////////////////////////////////
//服务信息
typedef struct EEquServiceInfo
{
	EEquSrvSrcType					SrvSrc;
	EEquSrvEventType				SrvEvent;
	EEquSrvChainType                SrvChain;
	EEquRetType                     SrvErrorCode;
	EEquErrorTextType               SrvErrorText;
	EEquSrvDataType                 SrvData;
	EEquFieldSizeType               DataFieldSize;
	EEquFieldCountType				DataFieldCount;
	
	EEquUserNoType					UserNo;

	EEquContractNoType				ContractNo;
	EEquKLineTypeType				KLineType;
	EEquKLineSliceType				KLineSlice;
	EEquSessionIdType				SessionId;
} EEquServiceInfo;

//市场状态 时间查询请求
typedef struct EEquExchangeStateReq
{
}EEquExchangeStateReq;
//市场状态 时间查询应答
typedef struct EEquExchangeStateRsp
{
	EEquSignType					Sign;
	EEquExchangeNoType				ExchangeNo;
	EEquExchDateTimeType			ExchangeDateTime;
	EEquExchDateTimeType			LocalDateTime;
	EEquTradeState					TradeState;
	EEquCommodityNoType				CommodityNo;
}EEquExchangeStateRsp;

typedef EEquExchangeStateRsp		EEquExchangeStateNotice;

//套利映射信息查询请求
typedef struct EEquSpreadMappingReq
{
} EEquContractMappingReq;

//套利映射信息查询数据
typedef struct EEquSpreadMappingData
{
	EEquContractNoType              ContractNo;     //客户端合约编号
	EEquContractNoType              SrcContractNo;  //原始合约编号
} EEquSpreadMappingData;

//虚拟映射信息查询请求
typedef EEquSpreadMappingReq EEquUnderlayMappingReq;

//虚拟映射信息查询数据
typedef struct EEquUnderlayMappingData
{
	EEquContractNoType              ContractNo;			//虚拟合约编号
	EEquContractNoType              UnderlayContractNo; //真实合约编号
} EEquUnderlayMappingData;

#pragma pack(pop)

#endif // !EQUANTAPI_TYPE_H

