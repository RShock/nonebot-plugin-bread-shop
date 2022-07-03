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
from .config import BANNED_GROUPS, COST, THING, LEVEL_NUM

__zx_plugin_name__ = f"{THING}店"
__plugin_usage__ = f"""
usage：
    {THING}小游戏，用户可以通过“买|吃|抢|送{THING}”和“猜拳”操作来获取{THING}和使用{THING}。
    所有操作都有CD
    但是可以支付800金使用“强行买{THING}”指令，支付400金使用“强行抢{THING}”指令，200金使用“强行吃{THING}”指令
    输入{THING}帮助以获取更多信息
    将会记录所有用户的{THING}数据进行排行
    所有的操作都可能产生特殊{THING}事件哦！
    一起来买{THING}吧！
""".strip()
__plugin_des__ = "(金币回收计划){THING}小游戏"
__plugin_cmd__ = [
    f"领{THING}",
    f"买{THING}",
    f"强行买{THING}",
    f"强行抢{THING}",
    f"强行吃{THING}",
    f"吃{THING}",
    f"抢{THING}",
    f"送{THING}",
    f"{THING}猜拳",
    f"{THING}记录",
    f"偷看{THING}",
    f"{THING}帮助",
    f"{THING}排行"
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

bread_buy = on_command("bread_buy", aliases={f"买{THING}", "🍞"}, priority=5, block = True)
bread_buy2 = on_command("bread_force_buy", aliases={f"强行买{THING}", f"强制买{THING}", f"强买{THING}"}, priority=5, block = True)
bread_rob2 = on_command("bread_force_rob", aliases={f"强行抢{THING}", f"强制抢{THING}", f"强抢{THING}"}, priority=5, block = True)
bread_eat = on_command("bread_eat", aliases={f"吃{THING}", f"啃{THING}"}, priority=5, block = True)
bread_eat2 = on_command("bread_force_eat", aliases={f"强行吃{THING}", f"强制吃{THING}", f"强吃{THING}"}, priority=5, block = True)
bread_rob = on_command("bread_rob", aliases={f"抢{THING}"}, priority=5, block = True)
bread_give = on_command("bread_give", aliases={f"送{THING}"}, priority=5, block = True)
bread_bet = on_command("bread_bet", aliases={f"赌{THING}"}, priority=5, block = True)
bread_log = on_command("bread_log", aliases={f"{THING}记录"}, priority=5, block = True)
bread_check = on_command("bread_check", aliases={f"偷看{THING}", f"查看{THING}", f"我的{THING}"}, priority=5, block = True)
bread_top = on_command("bread_top", aliases={f"{THING}排行", f"{THING}排名",f"谁的{THING}"}, priority=5, block = True)
bread_help = on_command("bread_help", aliases={f"{THING}帮助"}, priority=5, block = True)

EatEvent.add_events(eat_events)
BuyEvent.add_events(buy_events)
RobEvent.add_events(rob_events)
GiveEvent.add_events(give_events)
BetEvent.add_events(bet_events)


@bread_buy.handle()
async def _(event: Event, bot: Bot):
    user_qq = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    msg_name = await get_nickname(bot, user_qq, group_id)

    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message=f"本群已禁止{THING}店！请联系bot管理员！")
        return

    wait_time = cd_wait_time(group_id, user_qq, Action.BUY)
    if wait_time > 0:
        data = BreadDataManage(group_id).get_bread_data(user_qq)
        msg_txt = f"您还得等待{wait_time // 60}分钟才能买{THING}w，现在一共拥有{data.bread_num}个{THING}！您的{THING}排名为:{data.no}"
    elif wait_time < 0:
        msg_txt = f"你被禁止购买{THING}啦！{(abs(wait_time)+ CD.BUY.value) // 60}分钟后才能购买！"

    else:
        event_ = BuyEvent(group_id)
        event_.set_user_id(user_qq)
        msg_txt = event_.execute()

    res_msg = msg_name + Message(msg_txt)
    await bot.send(event=event, message=res_msg)

@bread_buy2.handle()
async def _(event: Event, bot: Bot):
    user_qq = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    msg_name = await get_nickname(bot, user_qq, group_id)

    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message="本群已禁止{THING}店！请联系bot管理员！")
        return

    if isinstance(event, GroupMessageEvent):
        cost_coin = COST.BUY.value
        have_gold = await BagUser.get_gold(event.user_id, event.group_id)
        if have_gold < cost_coin:
            await bot.send(message=f"强行买{THING}需要{cost_coin}金币,你的金币不够!", event = event)
            return
        await BagUser.spend_gold(event.user_id, event.group_id,
                                    cost_coin)
        await bot.send(message=f"扣除{cost_coin}金币来买{THING}", event = event)

        BreadDataManage(group_id).cd_refresh(str(event.user_id), Action.BUY)
        event_ = BuyEvent(group_id)
        event_.set_user_id(user_qq)
        msg_txt = event_.execute()

        res_msg = msg_name + Message(msg_txt)
        await bot.send(event=event, message=res_msg)

@bread_eat.handle()
async def _(event: Event, bot: Bot):
    user_qq = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    msg_name = await get_nickname(bot, user_qq, group_id)

    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message=f"本群已禁止{THING}店！请联系bot管理员！")
        return

    wait_time = cd_wait_time(group_id, user_qq, Action.EAT)
    if wait_time > 0:
        data = BreadDataManage(group_id).get_bread_data(user_qq)
        msg_txt = f"您还得等待{wait_time // 60}分钟才能吃{THING}w，现在你的等级是Lv.{data.bread_eaten // LEVEL_NUM}！您的{THING}排名为:{data.no}"
    elif wait_time < 0:
        msg_txt = f"你被禁止吃{THING}啦！{(abs(wait_time)+ CD.EAT.value) // 60}分钟后才能吃哦！"
    else:
        event_ = EatEvent(group_id)
        event_.set_user_id(user_qq)
        msg_txt = event_.execute()

    res_msg = msg_name + Message(msg_txt)
    await bot.send(event=event, message=res_msg)

@bread_eat2.handle()
async def _(event: Event, bot: Bot):
    user_qq = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    msg_name = await get_nickname(bot, user_qq, group_id)

    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message="本群已禁止{THING}店！请联系bot管理员！")
        return

    if isinstance(event, GroupMessageEvent):
        cost_coin = COST.EAT.value
        have_gold = await BagUser.get_gold(event.user_id, event.group_id)
        if have_gold < cost_coin:
            await bot.send(message=f"强行吃{THING}需要{cost_coin}金币,你的金币不够!", event = event)
            return
        await BagUser.spend_gold(event.user_id, event.group_id,
                                    cost_coin)
        await bot.send(message=f"扣除{cost_coin}金币来吃{THING}", event = event)
        BreadDataManage(group_id).cd_refresh(str(event.user_id), Action.EAT)

        event_ = EatEvent(group_id)
        event_.set_user_id(user_qq)
        msg_txt = event_.execute()

        res_msg = msg_name + Message(msg_txt)
        await bot.send(event=event, message=res_msg)

@bread_rob.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_qq = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    msg_name = await get_nickname(bot, user_qq, group_id)

    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message=f"本群已禁止{THING}店！请联系bot管理员！")
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
        msg_txt = f"您还得等待{wait_time // 60}分钟才能抢{THING}w"
    elif wait_time < 0:
        msg_txt = f"你被禁止抢{THING}啦！{(abs(wait_time) + CD.ROB.value) // 60}分钟后才能抢哦！"
    else:
        event_ = RobEvent(group_id)
        event_.set_user_id(user_qq)
        event_.set_robbed_id(robbed_qq, robbed_name)
        msg_txt = event_.execute()

    res_msg = msg_name + msg_txt
    await bot.send(event=event, message=res_msg)

@bread_rob2.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_qq = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    msg_name = await get_nickname(bot, user_qq, group_id)

    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message="本群已禁止{THING}店！请联系bot管理员！")
        return

    robbed_qq = None
    for arg in args:
        if arg.type == "at":
            robbed_qq = arg.data.get("qq", "")
    if not robbed_qq:
        return
    robbed_name = await get_nickname(bot, robbed_qq, group_id)

    if isinstance(event, GroupMessageEvent):
        cost_coin = COST.ROB.value
        have_gold = await BagUser.get_gold(event.user_id, event.group_id)
        if have_gold < cost_coin:
            await bot.send(message=f"强行抢{THING}需要{cost_coin}金币,你的金币不够!", event = event)
            return
        await BagUser.spend_gold(event.user_id, event.group_id,
                                    cost_coin)

        await bot.send(message=f"扣除{cost_coin}金币来抢{THING}", event = event)
        BreadDataManage(group_id).cd_refresh(str(event.user_id), Action.ROB)
        event_ = RobEvent(group_id)
        event_.set_user_id(user_qq)
        event_.set_robbed_id(robbed_qq, robbed_name)
        msg_txt = event_.execute()

        res_msg = msg_name + msg_txt
        await bot.send(event=event, message=res_msg)

@bread_give.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_qq = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    msg_name = await get_nickname(bot, user_qq, group_id)

    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message=f"本群已禁止{THING}店！请联系bot管理员！")
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
        msg_txt = f"您还得等待{wait_time // 60}分钟才能送{THING}w"
    elif wait_time < 0:
        msg_txt = f"你被禁止送{THING}啦！{(abs(wait_time) + CD.GIVE.value) // 60}分钟后才能赠送哦！"
    else:
        event_ = GiveEvent(group_id)
        event_.set_user_id(user_qq)
        event_.set_given_id(robbed_qq, robbed_name)
        msg_txt = event_.execute()

    res_msg = msg_name + msg_txt
    await bot.send(event=event, message=res_msg)


@bread_bet.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_qq = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    msg_name = await get_nickname(bot, user_qq, group_id)
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message=f"本群已禁止{THING}店！请联系bot管理员！")
        return

    wait_time = cd_wait_time(group_id, user_qq, Action.BET)
    if wait_time > 0:
        msg_txt = f"您还得等待{wait_time // 60}分钟才能猜拳w"
        await bot.send(event=event, message=msg_name + msg_txt)
        return
    elif wait_time < 0:
        msg_txt = f"你被禁止猜拳啦！{(abs(wait_time) + CD.BET.value) // 60}分钟后才能猜拳哦！"
        await bot.send(event=event, message=msg_name + msg_txt)
        return
    else:
        ges = args.extract_plain_text()

        if ges not in ["石头", "剪刀", "布"]:
            await bot.send(event=event, message=f"没有{ges}这种东西啦！请输入“石头”或“剪刀”或“布”！例如 ’赌面包 石头‘ ")
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

        res_msg = msg_name + msg_txt
        await bread_bet.finish(res_msg)


@bread_check.handle()
async def _(event: Event, bot: Bot, args: Message = CommandArg()):
    user_qq = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    msg_name = await get_nickname(bot, user_qq, group_id)

    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message=f"本群已禁止{THING}店！请联系bot管理员！")
        return

    checked_qq = user_qq
    for arg in args:
        if arg.type == "at":
            checked_qq = arg.data.get("qq", "")
    if checked_qq == user_qq:
        user_data = BreadDataManage(group_id).get_bread_data(user_qq)
        msg = f"你现在拥有{user_data.bread_num}个{THING}，等级为Lv.{user_data.level}，排名为{user_data.no}！"
    else:
        checked_name = await get_nickname(bot, checked_qq, group_id)
        checked_data = BreadDataManage(group_id).get_bread_data(checked_qq)
        msg = f"{checked_name} 现在拥有{checked_data.bread_num}个{THING}，等级为Lv.{checked_data.level}，排名为{checked_data.no}！"

    await bot.send(event=event, message=msg_name + msg)


@bread_log.handle()
async def _(event: Event, bot: Bot, args: Message = CommandArg()):
    user_qq = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    msg_name = await get_nickname(bot, user_qq, group_id)

    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message=f"本群已禁止{THING}店！请联系bot管理员！")
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
            msg = f'没有{add_arg}这个操作啦！只有"买"，"吃"，"抢"，"赠送"，"猜拳" 例如：{THING}记录 买'
            await bot.send(event=event, message=msg_name + msg)
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
    await bot.send(event=event, message=msg_name + msg)


@bread_help.handle()
async def _(event: Event, bot: Bot):
    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message=f"本群已禁止{THING}店！请联系bot管理员！")
        return

    msg = f"""       🍞商店使用说明🍞
指令	        说明
买{THING}    	购买随机{THING}
啃{THING}	    吃随机{THING}
抢{THING}+@	  抢随机{THING}
送{THING}+@	  送随机{THING}
赌{THING}+""	猜拳赌随机{THING}
{THING}记录+""   查看操作次数最多的人
{THING}记录+@    查看操作次数
查看{THING}+@    查看{THING}数据
{THING}排行	    本群排行榜top5
强行买{THING}   花费额外金币购买{THING}
强行吃{THING}   花费额外金币吃{THING}
强行抢{THING}   花费额外金币抢{THING}
更多详情见本项目地址：
https://github.com/Mai-icy/nonebot-plugin-bread-shop"""
    await bot.send(event=event, message=msg)


@bread_top.handle()
async def _(bot: Bot, event: Event):
    group_id = await get_group_id(event.get_session_id())
    if group_id in BANNED_GROUPS:
        await bot.send(event=event, message=f"本群已禁止{THING}店！请联系bot管理员！")
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
    append_text = f"🍞本群{THING}排行top5！🍞\n"
    for data in all_data:
        if int(data.user_id) in user_id_list:
            num += 1
            name = await get_nickname(bot, data.user_id, group_id)
            append_text += f"top{num} : {name} Lv.{data.bread_eaten // LEVEL_NUM}，拥有{THING}{data.bread_num}个\n"
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
