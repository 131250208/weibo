# -*- coding:utf-8 -*-

import scrapy
import json
from w3lib.html import remove_tags
import re

class CommentsSpider(scrapy.Spider):
    name = "comments"

    def start_requests(self):
        uid_list = self.settings.get("UIDS")
        urls = []
        for uid in uid_list:
            urls.append("https://m.weibo.cn/api/container/getIndex?type=uid&value=%s&containerid=107603%s&page=1" % (uid, uid))

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    # 处理每个用户的微博，访问第一页取得总页数
    def parse(self, response):
        jsonob = json.loads(response.text)

        if jsonob["ok"] == 1:
            mb_nums = jsonob["data"]["cardlistInfo"]["total"]

            for p in range(mb_nums // 10 + 1):
                url = response.url[:-1] + str(p + 1)
                yield scrapy.Request(url=url, callback=self.parse_mblog)# 请求每一页

    # 处理每一页的微博
    def parse_mblog(self, response):
        jsonob = json.loads(response.text)

        cards = []
        try:
            if jsonob["ok"] == 1:
                cards = jsonob["data"]["cards"]
                for card in cards:
                    if card["card_type"] != 9:continue
                    mid = card["mblog"]["id"]
                    url = "https://m.weibo.cn/api/comments/show?id=%s&page=1" % mid
                    yield scrapy.Request(url=url, callback=self.parse_comments)
        except Exception as e:
            self.logger.warning("fail.. %s" % response.url)

    # 处理每一篇微博的评论，请求第一页获取评论总数
    def parse_comments(self, response):
        jsonob = json.loads(response.text)
        if jsonob["ok"] == 1:
            max = jsonob["data"]["max"]
            pg_end = min(max, 100)
            for page in range(pg_end):
                url = response.url[:-1] + str(page + 1)
                yield scrapy.Request(url=url, callback=self.parse_comments_perpg)  # 请求每一页的评论

    def parse_comments_perpg(self, response):
        jsonob = json.loads(response.text)
        if jsonob["ok"] == 1:
            comments = jsonob["data"]["data"]
            for com in comments:
                text = remove_tags(com["text"])
                text = re.sub("回复.*:", "", text)
                text = re.sub("\@小冰", "", text)

                if text == "": continue

                comment = {
                    "user_id": com["user"]["id"],
                    "text": text,
                }
                if "reply_id" in com:
                    comment["reply_id"] = com["reply_id"]


                yield {
                    com["id"]: comment
                }