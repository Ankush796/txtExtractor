#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

class Config:
    # All from environment
    BOT_TOKEN = os.environ.get("BOT_TOKEN") or ""
    API_ID = int(os.environ.get("API_ID") or 0)
    API_HASH = os.environ.get("API_HASH") or ""
    AUTH_USERS = os.environ.get("AUTH_USERS", "")
