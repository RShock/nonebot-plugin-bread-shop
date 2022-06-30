#!/usr/bin/python
# -*- coding:utf-8 -*-
from enum import Enum

# 自定义物品，改掉默认的”面包“
THING = "面包"

# 被禁止的群聊
BANNED_GROUPS = []

# 设置升一级所需要的面包数量（数据库不保存等级！！等级会随之而变！）
LEVEL_NUM = 10


class CD(Enum):
    """操作冷却（单位：秒）"""
    BUY = 3600
    EAT = 3600
    ROB = 7200
    GIVE = 0
    BET = 0


class MAX(Enum):
    """操作随机值上限"""
    BUY = 10
    EAT = 7
    ROB = 7
    GIVE = 10
    BET = 10


class MIN(Enum):
    """操作随机值下限"""
    BUY = 1
    EAT = 1
    ROB = 1
    GIVE = 1
    BET = 5
