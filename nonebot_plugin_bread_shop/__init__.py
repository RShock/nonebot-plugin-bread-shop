#!/usr/bin/python
# -*- coding:utf-8 -*-

import re

from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    GroupMessageEvent,
    Message,
    MessageSegment,
    Bot, 
    Event, 
    Message
)
from models.bag_user import BagUser

from .bread_handle import BreadDataManage, Action
from .bread_operate import *
from .bread_event import rob_events, buy_events, eat_events, give_events, bet_events
from .config import BANNED_GROUPS


__zx_plugin_name__ = "面包店"
__plugin_usage__ = """
usage：
    面包小游戏，用户可以通过“买|吃|抢|送面包”和“猜拳”操作来获取面包和使用面包。
    所有操作都有CD，但是可以支付800金使用“强行买面包”指令，支付400金使用“强行抢面包”指令，200金使用“强行吃面包”指令
    将会记录所有用户的面包数据进行排行
    所有的操作都可能产生特殊面包事件哦！
    一起来买面包吧！
""".strip()
__plugin_des__ = "(金币回收计划)面包小游戏"
__plugin_cmd__ = [
    "领面包",
    "买面包",
    "强行买面包",
    "强行抢面包",
    "强行吃面包",
    "吃面包",
    "抢面包",
    "送面包",
    "面包猜拳",
    "面包记录",
    "偷看面包",
    "面包帮助",
    "面包排行"
]
__plugin_type__ = ("群内小游戏", )
__plugin_version__ = 0.1
__plugin_author__ = "Mai-icy"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": __plugin_cmd__,
}

bread_buy = on_command("bread_", aliases={"买面包", "draw", "🍞"}, priority=5, block = True)
bread_buy2 = on_command("bread_buy", aliases={"强行买面包", "buy2", "🍞"}, priority=5, block = True)
bread_rob2 = on_command("bread_buy", aliases={"强行抢面包", "rob2", "🍞"}, priority=5, block = True)

bread_eat = on_command("bread_eat", aliases={"吃面包", "啃面包", "eat", "🍞🍞"}, priority=5, block = True)
bread_eat2 = on_command("bread_eat", aliases={"强行吃面包", "eat2", "🍞🍞"}, priority=5, block = True)
bread_rob = on_command("bread_rob", aliases={"抢面包", "rob", "🍞🍞🍞"}, priority=5, block = True)
bread_give = on_command("bread_give", aliases={"送面包", "give", "送"}, priority=5, block = True)
bread_bet = on_command("bread_bet", aliases={"面包猜拳", "赌面包", "bet"}, priority=5, block = True)
bread_log = on_command("bread_log", aliases={"面包记录", "记录", "logb"}, priority=5, block = True)
bread_check = on_command("bread_check", aliases={"偷看面包", "查看面包", "check"}, priority=5, block = True)
bread_top = on_command("bread_top", aliases={"面包排行", "breadtop", "面包排名"}, priority=5, block = True)
bread_help = on_command("bread_help", aliases={"面包帮助", "breadhelp", "helpb"}, priority=5, block = True)


EatEvent.add_events(eat_events)
BuyEvent.add_events(buy_events)
RobEvent.add_events(rob_events)
GiveEvent.add_events(give_events)
BetEvent.add_events(bet_events)


@bread_buy.handle()
async def _(event: Event, bot: Bot):
    user_qq = event.get_user_id()
    msg_at = Message(f"[CQ:at,qq={user_qq}]")

    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message="本群已禁止面包店！请联系bot管理员！")
        return

    wait_time = cd_wait_time(group_id, user_qq, Action.BUY)
    if wait_time > 0:
        data = BreadDataManage(group_id).get_bread_data(user_qq)
        msg_txt = f"您还得等待{wait_time // 60}分钟才能领面包w，现在一共拥有{data.bread_num}个面包！您的面包排名为:{data.no}"
    elif wait_time < 0:
        msg_txt = f"你被禁止领面包啦！{(abs(wait_time)+ CD.BUY.value) // 60}分钟后才能领！"
    else:
        event_ = BuyEvent(group_id)
        event_.set_user_id(user_qq)
        msg_txt = event_.execute()

    res_msg = msg_at + Message(msg_txt)
    await bot.send(event=event, message=res_msg)

@bread_buy2.handle()
async def _(event: Event, bot: Bot):
    user_qq = event.get_user_id()
    msg_at = Message(f"[CQ:at,qq={user_qq}]")

    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message="本群已禁止面包店！请联系bot管理员！")
        return

    if isinstance(event, GroupMessageEvent):
        cost_coin = 800
        have_gold = await BagUser.get_gold(event.user_id, event.group_id)
        if have_gold < cost_coin:
            await bot.send(message=f"强行买面包需要{cost_coin}金币,你的金币不够!", event = event)
            return
        await BagUser.spend_gold(event.user_id, event.group_id,
                                    cost_coin)
        await bot.send(message=f"扣除{cost_coin}金币来买面包", event = event)

        event_ = BuyEvent(group_id)
        event_.set_user_id(user_qq)
        msg_txt = event_.execute()

        res_msg = msg_at + Message(msg_txt)
        await bot.send(event=event, message=res_msg)

@bread_eat.handle()
async def _(event: Event, bot: Bot):
    user_qq = event.get_user_id()
    msg_at = Message(f"[CQ:at,qq={user_qq}]")

    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message="本群已禁止面包店！请联系bot管理员！")
        return

    wait_time = cd_wait_time(group_id, user_qq, Action.EAT)
    if wait_time > 0:
        data = BreadDataManage(group_id).get_bread_data(user_qq)
        msg_txt = f"您还得等待{wait_time // 60}分钟才能吃面包w，现在你的等级是Lv.{data.bread_eaten // 10}！您的面包排名为:{data.no}"
    elif wait_time < 0:
        msg_txt = f"你被禁止吃面包啦！{(abs(wait_time)+ CD.EAT.value) // 60}分钟后才能吃哦！"
    else:
        event_ = EatEvent(group_id)
        event_.set_user_id(user_qq)
        msg_txt = event_.execute()

    res_msg = msg_at + Message(msg_txt)
    await bot.send(event=event, message=res_msg)

@bread_eat2.handle()
async def _(event: Event, bot: Bot):
    user_qq = event.get_user_id()
    msg_at = Message(f"[CQ:at,qq={user_qq}]")

    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message="本群已禁止面包店！请联系bot管理员！")
        return

    if isinstance(event, GroupMessageEvent):
        cost_coin = 200
        have_gold = await BagUser.get_gold(event.user_id, event.group_id)
        if have_gold < cost_coin:
            await bot.send(message=f"强行吃面包需要{cost_coin}金币,你的金币不够!", event = event)
            return
        await BagUser.spend_gold(event.user_id, event.group_id,
                                    cost_coin)
        await bot.send(message=f"扣除{cost_coin}金币来吃面包", event = event)
        event_ = EatEvent(group_id)
        event_.set_user_id(user_qq)
        msg_txt = event_.execute()

        res_msg = msg_at + Message(msg_txt)
        await bot.send(event=event, message=res_msg)

@bread_rob.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_qq = event.get_user_id()
    msg_at = Message(f"[CQ:at,qq={user_qq}]")

    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message="本群已禁止面包店！请联系bot管理员！")
        return

    robbed_qq = None
    for arg in args:
        if arg.type == "at":
            robbed_qq = arg.data.get("qq", "")
    if not robbed_qq:
        return
    robbed_name = await get_nickname(bot, robbed_qq, group_id)

    wait_time = cd_wait_time(group_id, user_qq, Action.ROB)
    if wait_time > 0:
        msg_txt = f"您还得等待{wait_time // 60}分钟才能抢面包w"
    elif wait_time < 0:
        msg_txt = f"你被禁止抢面包啦！{(abs(wait_time)+ CD.ROB.value) // 60}分钟后才能抢哦！"
    else:
        event_ = RobEvent(group_id)
        event_.set_user_id(user_qq)
        event_.set_robbed_id(robbed_qq, robbed_name)
        msg_txt = event_.execute()

    res_msg = msg_at + msg_txt
    await bot.send(event=event, message=res_msg)

@bread_rob2.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_qq = event.get_user_id()
    msg_at = Message(f"[CQ:at,qq={user_qq}]")

    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message="本群已禁止面包店！请联系bot管理员！")
        return

    robbed_qq = None
    for arg in args:
        if arg.type == "at":
            robbed_qq = arg.data.get("qq", "")
    if not robbed_qq:
        return
    robbed_name = await get_nickname(bot, robbed_qq, group_id)

    if isinstance(event, GroupMessageEvent):
        cost_coin = 400
        have_gold = await BagUser.get_gold(event.user_id, event.group_id)
        if have_gold < cost_coin:
            await bot.send(message=f"强行抢面包需要{cost_coin}金币,你的金币不够!", event = event)
            return
        await BagUser.spend_gold(event.user_id, event.group_id,
                                    cost_coin)
        await bot.send(message=f"扣除{cost_coin}金币来抢面包", event = event)
        event_ = RobEvent(group_id)
        event_.set_user_id(user_qq)
        event_.set_robbed_id(robbed_qq, robbed_name)
        msg_txt = event_.execute()

        res_msg = msg_at + msg_txt
        await bot.send(event=event, message=res_msg)

@bread_give.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_qq = event.get_user_id()
    msg_at = Message(f"[CQ:at,qq={user_qq}]")

    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message="本群已禁止面包店！请联系bot管理员！")
        return

    robbed_qq = None
    for arg in args:
        if arg.type == "at":
            robbed_qq = arg.data.get("qq", "")
    if not robbed_qq:
        return
    robbed_name = await get_nickname(bot, robbed_qq, group_id)

    wait_time = cd_wait_time(group_id, user_qq, Action.GIVE)
    if wait_time > 0:
        msg_txt = f"您还得等待{wait_time // 60}分钟才能送面包w"
    elif wait_time < 0:
        msg_txt = f"你被禁止送面包啦！{(abs(wait_time)+ CD.GIVE.value) // 60}分钟后才能赠送哦！"
    else:
        event_ = GiveEvent(group_id)
        event_.set_user_id(user_qq)
        event_.set_given_id(robbed_qq, robbed_name)
        msg_txt = event_.execute()

    res_msg = msg_at + msg_txt
    await bot.send(event=event, message=res_msg)


@bread_bet.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_qq = event.get_user_id()
    msg_at = Message(f"[CQ:at,qq={user_qq}]")
    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message="本群已禁止面包店！请联系bot管理员！")
        return

    wait_time = cd_wait_time(group_id, user_qq, Action.BET)
    if wait_time > 0:
        msg_txt = f"您还得等待{wait_time // 60}分钟才能猜拳w"
        await bot.send(event=event, message=msg_at + msg_txt)
        return
    elif wait_time < 0:
        msg_txt = f"你被禁止猜拳啦！{(abs(wait_time)+ CD.BET.value) // 60}分钟后才能猜拳哦！"
        await bot.send(event=event, message=msg_at + msg_txt)
        return
    else:
        ges = args.extract_plain_text()

        if ges not in ["石头", "剪刀", "布"]:
            await bot.send(event=event, message=f"没有{ges}这种东西啦！请输入“石头”或“剪刀”或“布”！例如 ’/bet 石头‘ ")
            return
        if ges == "石头":
            ges_ = BetEvent.G(0)
        elif ges == "布":
            ges_ = BetEvent.G(1)
        else:
            ges_ = BetEvent.G(2)

        event_ = BetEvent(group_id)
        event_.set_user_id(user_qq)
        event_.set_user_gestures(ges_)
        msg_txt = event_.execute()

        res_msg = msg_at + msg_txt
        await bread_bet.finish(res_msg)


@bread_check.handle()
async def _(event: Event, bot: Bot, args: Message = CommandArg()):
    user_qq = event.get_user_id()
    msg_at = Message(f"[CQ:at,qq={user_qq}]")

    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message="本群已禁止面包店！请联系bot管理员！")
        return

    checked_qq = user_qq
    for arg in args:
        if arg.type == "at":
            checked_qq = arg.data.get("qq", "")
    if checked_qq == user_qq:
        user_data = BreadDataManage(group_id).get_bread_data(user_qq)
        msg = f"你现在拥有{user_data.bread_num}个面包，等级为Lv.{user_data.level}，排名为{user_data.no}！"
    else:
        checked_name = await get_nickname(bot, checked_qq, group_id)
        checked_data = BreadDataManage(group_id).get_bread_data(checked_qq)
        msg = f"{checked_name} 现在拥有{checked_data.bread_num}个面包，等级为Lv.{checked_data.level}，排名为{checked_data.no}！"

    await bot.send(event=event, message=msg_at + msg)


@bread_log.handle()
async def _(event: Event, bot: Bot, args: Message = CommandArg()):
    user_qq = event.get_user_id()
    msg_at = Message(f"[CQ:at,qq={user_qq}]")

    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message="本群已禁止面包店！请联系bot管理员！")
        return

    add_arg = args.extract_plain_text()
    if add_arg:
        action_args = ["买", "吃", "抢", "赠送", "猜拳"]
        if add_arg in action_args:
            val_index = action_args.index(add_arg)
            action = Action(val_index)
            data = BreadDataManage(group_id).get_action_log(action)
            name = await get_nickname(bot, data.user_id, group_id)
            attr_val = BreadDataManage.LOG_COLUMN[val_index].lower()
            app_msg = ["哇好有钱！", "好能吃，大胃王！", "大坏比！", "我超，带好人！", "哇塞，赌狗！"]
            msg = f"{add_arg}次数最多是{name}！共{getattr(data, attr_val)}次！" + app_msg[val_index]
            await bot.send(event=event, message=msg)
            return
        else:
            msg = f'没有{add_arg}这个操作啦！只有"买"，"吃"，"抢"，"赠送"，"猜拳" 例如：/logb 买'
            await bot.send(event=event, message=msg_at + msg)
            return

    checked_qq = user_qq
    for arg in args:
        if arg.type == "at":
            checked_qq = arg.data.get("qq", "")
    if checked_qq == user_qq:
        user_log = BreadDataManage(group_id).get_log_data(user_qq)
        msg = f"你共购买{user_log.buy_times}次，吃{user_log.eat_times}次，抢{user_log.rob_times}次，" \
              f"赠送{user_log.give_times}次，猜拳{user_log.eat_times}次！"
    else:
        checked_name = await get_nickname(bot, checked_qq, group_id)
        checked_log = BreadDataManage(group_id).get_log_data(checked_qq)
        msg = f"{checked_name}共购买{checked_log.buy_times}次，吃{checked_log.eat_times}次，抢{checked_log.rob_times}次，" \
              f"赠送{checked_log.give_times}次，猜拳{checked_log.eat_times}次！"
    await bot.send(event=event, message=msg_at + msg)


@bread_help.handle()
async def _(event: Event, bot: Bot):
    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message="本群已禁止面包店！请联系bot管理员！")
        return

    msg = """       🍞商店使用说明🍞
指令	        说明
买面包    	购买随机面包
啃面包	    吃随机面包
抢面包+@	  抢随机面包
送面包+@	  送随机面包
赌面包+""	猜拳赌随机面包
面包记录+""   查看操作次数最多的人
面包记录+@    查看操作次数
查看面包+@    查看面包数据
面包排行	    本群排行榜top5
强行买面包   花费额外金币购买面包
强行吃面包   花费额外金币吃面包
强行抢面包   花费额外金币抢面包
更多详情见本项目地址：
https://github.com/Mai-icy/nonebot-plugin-bread-shop"""
    await bot.send(event=event, message=msg)


@bread_top.handle()
async def _(bot: Bot, event: Event):
    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message="本群已禁止面包店！请联系bot管理员！")
        return
    msg = await get_group_top(bot, group_id)
    await bot.send(event=event, message=msg)


async def get_group_id(session_id):
    res = re.findall("_(.*)_", session_id)
    group_id = res[0]
    return group_id


async def get_group_top(bot: Bot, group_id) -> Message:
    group_member_list = await bot.get_group_member_list(group_id=int(group_id))
    user_id_list = {info['user_id'] for info in group_member_list}
    all_data = BreadDataManage(group_id).get_all_data()
    num = 0
    append_text = "🍞本群面包排行top5！🍞\n"
    for data in all_data:
        if int(data.user_id) in user_id_list:
            num += 1
            name = await get_nickname(bot, data.user_id, group_id)
            append_text += f"top{num} : {name} Lv.{data.bread_eaten // 10}，拥有面包{data.bread_num}个\n"
        if num == 5:
            break
    append_text += "大家继续加油w！"
    return Message(append_text)


async def get_nickname(bot: Bot, user_id, group_id=None):
    if group_id:
        info = await bot.get_group_member_info(group_id=int(group_id), user_id=int(user_id))
        other_name = info.get("card", "") or info.get("nickname", "")
        if not other_name:
            info = await bot.get_stranger_info(user_id=int(user_id))
            other_name = info.get("nickname", "")
    else:
        info = await bot.get_stranger_info(user_id=int(user_id))
        other_name = info.get("nickname", "")
    return other_name
