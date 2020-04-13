#ifndef EQUANTAPI_API_H
#define EQUANTAPI_API_H

#include "EquantApi_Type.h"
#include <functional>
#ifdef LIB_TRADER_API_EXPORT
#define TRADER_API_EXPORT __declspec(dllexport)
#else
#define TRADER_API_EXPORT __declspec(dllimport)
#endif

//回调函数指针定义
typedef EEquRetType(*EEqu_SrvFunc)(EEquServiceInfo* service);
//typedef std::function<EEquRetType(EEquServiceInfo* service)> *EEqu_SrvFunc;

extern "C"
{
/**
*  @brief 注册事件回调函数
*
*  @param func 回调函数指针
*  @return 0: 注册成功；<0: 注册失败或者已经注册
*
*  @details 注册事件回调函数
*/
TRADER_API_EXPORT EEquRetType E_RegEvent(EEqu_SrvFunc func);

/**
*  @brief 注销事件回调函数
*
*  @param func 回调函数指针
*  @return 0: 注销成功；<0: 注销失败或者重复注销
*
*  @details 注销事件回调函数
*/
TRADER_API_EXPORT EEquRetType E_UnregEvent(EEqu_SrvFunc func);

////////////////////////////////////系统启动接口///////////////////////////

/**
*  @brief 系统初始化接口
*
*  @return 0: 初始化成功；<0: 初始化失败
*
*  @details 
*/
TRADER_API_EXPORT EEquRetType E_Init();

/**
*  @brief 系统初始化接口
*
*  @return 0: 成功；<0:失败 
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_DeInit();

/**
*  @brief 请求交易所
*
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqQryExchangeInfo(EEquSessionIdType* SessionId, EEquExchangeReq* req);

/**
*  @brief 请求品种信息
*
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqQryCommodityInfo(EEquSessionIdType* SessionId, EEquCommodityReq* req);

/**
*  @brief 请求合约信息
*
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqQryContractInfo(EEquSessionIdType* SessionId, EEquContractReq* req);

/**
*  @brief 请时间模板
*
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqQryTimeBucketInfo(EEquSessionIdType* SessionId, EEquCommodityTimeBucketReq* req);

/**
*  @brief 订阅即时行情
*
*  @param req :合约
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqSubQuote(EEquSessionIdType* SessionId, EEquContractNoType req[],U32 uLen);

/**
*  @brief 退订即时行情
*
*  @param req :合约（"" 退订全部）
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqUnSubQuote(EEquSessionIdType* SessionId, EEquContractNoType* req, U32 uLen);

/**
*  @brief 订阅历史行情
*
*  @param  
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqSubHisQuote(EEquSessionIdType* SessionId, EEquKLineReq* req);

/**
*  @brief 退订历史行情
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqUnSubHisQuote(EEquSessionIdType* SessionId, EEquContractNoType req);

/**
*  @brief 获取登陆账号
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqQryLoginInfo(EEquSessionIdType* SessionId, EEquLoginInfoReq* req);

/**
*  @brief 获取资金账号
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqQryUserInfo(EEquSessionIdType* SessionId, EEquUserInfoReq* req);

/**
*  @brief 获取资金信息
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqQryMoney(EEquSessionIdType* SessionId, EEquUserMoneyReq* req);

/**
*  @brief 获取委托定单
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqQryOrder(EEquSessionIdType* SessionId, EEquOrderQryReq* req);

/**
*  @brief 获取成交单
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqQryMatch(EEquSessionIdType* SessionId, EEquMatchQryReq* req);

/**
*  @brief 获取持仓信息
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqQryPosition(EEquSessionIdType* SessionId, EEquPositionQryReq* req);

/**
*  @brief 委托下单
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqInsertOrder(EEquSessionIdType* SessionId, EEquOrderInsertReq* req);

/**
*  @brief 委托撤单
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqCancelOrder(EEquSessionIdType* SessionId, EEquOrderCancelReq* req);

/**
*  @brief 委托改单
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqModifyOrder(EEquSessionIdType* SessionId, EEquOrderModifyReq* req);


/**
*  @brief 切换图标显示策略
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_KLineStrategySwitch(EEquSessionIdType* SessionId, EEquKLineStrategySwitch* data);

/**
*  @brief 推送回测历史数据
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_KLineDataResult(EEquSessionIdType* SessionId, EEquKLineDataResult* data);
/**
*  @brief 更新回测历史数据
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_KLineDataResultNotice(EEquSessionIdType* SessionId, EEquKLineDataResult* data);

/**
*  @brief 增加指标线信息
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_AddKLineSeriesInfo(EEquSessionIdType* SessionId, EEquKLineSeriesInfo* data);

/**
*  @brief 推送回测指标数据
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_KLineSeriesResult(EEquSessionIdType* SessionId, EEquKLineSeriesResult* data);
/**
*  @brief 更新指标数据
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_KLineSeriesResultNotice(EEquSessionIdType* SessionId, EEquKLineSeriesResult* data);

/**
*  @brief 增加信号线信息
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_AddKLineSignalInfo(EEquSessionIdType* SessionId, EEquKLineSignalInfo* data);

/**
*  @brief 推送回测信号数据
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_KLineSignalResult(EEquSessionIdType* SessionId, EEquKLineSignalResult* data);
/**
*  @brief 更新信号数据
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_KLineSignalResultNotice(EEquSessionIdType* SessionId, EEquKLineSignalResult* data);
/**
*  @brief 刷新指标、信号通知
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_StrategyDataUpdateNotice(EEquSessionIdType* SessionId, EEquStrategyDataUpdateNotice* data);
/**
*  @brief 策略状态更新
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_KLineStrategyStateNotice(EEquSessionIdType* SessionId, EEquKlineStrategyStateNotice* data);
/**
*  @brief 交易所状态查询
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqExchangeStateQry(EEquSessionIdType* SessionId, EEquExchangeStateReq* data);

/**
*  @brief 套利原始合约查询
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqQrySpreadMapping(EEquSessionIdType* SessionId, EEquSpreadMappingReq* data);

/**
*  @brief 虚拟查询
*
*  @param
*  @return 0: 发送成功；<0: 发送失败
*
*  @details
*/
TRADER_API_EXPORT EEquRetType E_ReqQryUnderlayMapping(EEquSessionIdType* SessionId, EEquUnderlayMappingReq* data);
}

#endif
