#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  4 20:00:20 2020

@author: yujuquan
"""

"""
A chat robot that can help you find information of movies and TV works.
The bot has been dep
"""

"""
Useage: search 
"""

# Import necessary modules
import logging
import re
import random
import ast
import http.client
from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler)
from rasa_nlu.training_data import load_data
from rasa_nlu.model import Trainer
from rasa_nlu import config


# 11111111111111****************************************
# 连接api
conn = http.client.HTTPSConnection("movie-database-imdb-alternative.p.rapidapi.com")
headers = {
    'x-rapidapi-host': "movie-database-imdb-alternative.p.rapidapi.com",
    'x-rapidapi-key': "a1a70a2702msh4ea2df369954209p19cfa8jsn6ad6b6661ac3"
    }

# 训练rasa解释器
trainer = Trainer(config.load("config_spacy.yml"))
# Load the training data
training_data = load_data('mooda-rasa.md')
# Create an interpreter by training the model
interpreter = trainer.train(training_data)

# 2222222222222****************************************
# 全局变量声明
params = []
# 不懂回复
default = "Sorry, I don't understand what you mean. ε(┬┬﹏┬┬)3"
# 闲聊回复
rules = {'i wish (.*)': ['What would it mean if {0}', 
                         'Why do you wish {0}', 
                         "What's stopping you from realising {0}"
                        ], 
         'do you remember (.*)': ['Did you think I would forget {0}', 
                                  "Why haven't you been able to forget {0}", 
                                  'What about {0}', 
                                  'Yes .. and?'
                                 ], 
         'do you think (.*)': ['if {0}? Absolutely.', 
                               'No chance.'
                              ], 
         'if (.*)': ["Do you really think it's likely that {0}", 
                     'Do you wish that {0}', 
                     'What do you think about {0}', 
                     'Really--if {0}'
                    ]
        }
# 定义回复规则
response = [
    "I'm sorry, I couldn't find anything like that. ╮(๑•́ ₃•̀๑)╭",
    "Great! Here are some brief information about {}:",
    "Bingo! I found the following items: ", 
]
# ****************************************


updater = Updater(token='1002334016:AAHXRwpSUboSzqxYc6DM03rCIt8vImLct2M', use_context=True)

dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# start命令
def start(update, context):
     update.message.reply_text(
        "Hi! My name is Mooda. I can help you search for information about any movies or TV works.\n\n"
        "Remember that the work's name should be capitalized.\n"
        "For example 'search Avengers: Endgame for me'.\n\n"
        "If you don't want to type an uppercase name, you can prefix it with 'name*'.\n"
        "For example 'search name* avengers: endgame'.\n\n"
        "You can also ask specific information of a work, "
        "including director, actors, plot, released date, runtime, genre, ratings & awards, poster.\n"
        "For example 'who directs the movie', 'what does Space Transformer tell'.\n\n"
        "Welcome to chat with me! (๑•ᴗ•๑)♡ "
        )

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

# 大小写转换命令
def caps(update, context):
    print(type(context.args))
    text_caps = ' '.join(context.args).upper()
    return text_caps

caps_handler = CommandHandler('caps', caps)
dispatcher.add_handler(caps_handler)

# 未知命令
def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=default)

unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

# ****************************************
# 替换人称
def replace_pronouns(message):
    
    message = message.lower()
    
    if 'me' in message:
        # Replace 'me' with 'you'
        return re.sub('me', 'you', message)
    if 'my' in message:
        # Replace 'my' with 'your'
        return re.sub('my', 'your', message)
    if 'your' in message:
        # Replace 'your' with 'my'
        return re.sub('your', 'my', message)
    if 'you' in message:
        # Replace 'you' with 'me'
        return re.sub('you', 'me', message)
    
    return message

# 匹配回复规则
def match_rule(update, context, message):
    
    for pattern, value in rules.items():
        # Create a match object
        match = re.search(pattern, message)
        # 如果匹配成功
        if match is not None:
            # Choose a random response
            response = random.choice(rules[pattern])
            # 如果需要人称替换
            if '{0}' in response:
                phrase = re.search(pattern, message).group(1)
                phrase = replace_pronouns(phrase)
                # 回复消息
                update.message.reply_text(response.format(phrase))
            else:
                # 回复消息
                update.message.reply_text(response)
            return True
        
    return False

# 提取电影名
def find_name(message):
    name = None
    name_words = []
    
    # Create a pattern for finding capitalized words
    name_pattern = re.compile("[A-Z]{1}[a-z]*")
    
    # Get the matching words in the string
    name_words += name_pattern.findall(message)
    
    # Create a pattern for checking if the keywords occur
    name_keyword = re.compile("name|call|movie|TV series|tv series|television show|drama|show", re.I)
    
    if name_keyword.search(message) or name_words:
        name_new_pattern = re.compile("[0-9]{1}[0-9]*")
        name_words += name_new_pattern.findall(message)
        
    if len(name_words) > 0:
        # Return the name if the keywords are present
        name = '%20'.join(name_words)
     
    return name

# 自动将电影名转换大写
def turn_name(message):
    if "name*" in message:
        index = message.index("name*") + len("name*")
        name = message[index:].upper()
        name_list = name.split(' ')
        
        for i in range(len(name_list)):
            if name_list[i] == '':
                continue
            else:
                index = i
                break
                
        newname = '%20'.join(name_list[index:])
        return newname

# work_search
def search_work(update, context, name):
    if name == None:
        update.message.reply_text(default)
        return params
    # 获得api数据
    conn.request("GET", "/?page=1&r=json&s=" + name, headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    
    # 将字符串转换为字典格式
    data = ast.literal_eval(data)
    
    # 搜索错误时返回
    if len(data) <= 2:
        update.message.reply_text(response[0])
        return []
    
    # params存放搜索结果
    params = data["Search"]
    # rename存放搜索结果名
    rename = [r['Title'] for r in params]
    
    # 根据检索到的数目选择回复
    n = min(eval(data["totalResults"]), 2)
    update.message.reply_text(response[n].format(*rename))
    
    # 检索到两条以上回复请求索引
    if n == 2:
        # 得到检索到信息的长度
        lenth = len(rename)
        for i in range(lenth):
            update.message.reply_text("{}. {}".format(i + 1, rename[i]))
        update.message.reply_text("Tell me the index of which to view specific information.\n"
                                  "For example 'the third one', '5'"
                                 )
    
    # 仅检索到一条时打印相关电影信息
    else:
        for key in params[0]:
            if key == "imdbID":
                continue
            # 打印海报需要特殊处理
            if key == "Poster":
                update.message.reply_text("Poster:")
                # 打印海报
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=params[0][key])
                continue
            update.message.reply_text("{}: {}".format(key, params[0][key]))
        
    # 更新params    
    return params 

# number_work
def number_work(update, context, message, params):
    name = message
    
    if "1" in name:
        if name.find("0") < 0:
            id = 1
        else:
            id = 10
    elif "one" in name or "first" in name:
        id = 1
    elif "2" in name or "two" in name or "second" in name:
        id = 2
    elif "3" in name or "three" in name or "third" in name:
        id = 3
    elif "4" in name or "four" in name or "fourth" in name:
        id = 4
    elif "5" in name or "five" in name or "fifth" in name:
        id = 5
    elif "6" in name or "six" in name or "sixth" in name:
        id = 6
    elif "7" in name or "seven" in name or "seventh" in name:
        id = 7
    elif "8" in name or "eight" in name or "eighth" in name:
        id = 8
    elif "9" in name or "nine" in name or "ninth" in name:
        id = 9
    elif "10" in name or "ten" in name or "tenth" in name:
        id = 10
    else:
        id = 15
    
    # 索引错误时返回
    if id > len(params):
        update.message.reply_text("Please give me right index. (๑• . •๑)")
        return params
    
    # 索引正确时更新params并给出电影信息
    params = [params[id - 1]]
    update.message.reply_text("Here are some brief information about {}:".format(params[0]["Title"]))
    for key in params[0]:
            if key == "imdbID":
                continue
            # 打印海报需要特殊处理
            if key == "Poster":
                update.message.reply_text("Poster:")
                #############################################################
                update.message.reply_photo(params[0][key])
                continue
            update.message.reply_text("{}: {}".format(key, params[0][key]))
    
    return params

# poster_work
def poster_work(update, context, name, params):
    # name已经在params中
    for i in range(len(params)):
        if name == params[i]["Title"] or name == None:
            update.message.reply_text("Here is a poster of {}:".format(params[i]["Title"]))
            update.message.reply_photo(params[i]["Poster"])
            return params
    
    # name不在则检索
    
    # 获得api数据
    conn.request("GET", "/?page=1&r=json&s=" + name, headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    
    # 将字符串转换为字典格式
    data = ast.literal_eval(data)
    
    # 没有检索到
    if len(data) <= 2:
        update.message.reply_text(default)
        # 返回空params
        return []
    
    # 更新params
    params = data["Search"]
    
    # 打印海报
    update.message.reply_text("Here is a poster of {}:".format(params[0]["Title"]))
    update.message.reply_photo(params[0]["Poster"])
    
    return params

# plot_work
def plot_work(update, context, name, params):
    # 首先看看name是不是在params中
    for i in range(len(params)):
        if name == params[i]["Title"] or name == None:
            workID = params[i]["imdbID"]
            conn.request("GET", "/?i=" + workID + "&r=json", headers=headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            
            # 将字符串转换为字典格式
            data = ast.literal_eval(data)
            
            update.message.reply_text("Here is the plot of {}:".format(params[i]["Title"]))
            update.message.reply_text("{}".format(data["Plot"]))
            
            return params
    
    # 如果不在则检索
                                      
    # 获得api数据
    conn.request("GET", "/?page=1&r=json&s=" + name, headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
                                      
    # 将字符串转换为字典格式
    data = ast.literal_eval(data)
                                      
    # 记录结果和结果名字
    if len(data) <= 2:
        update.message.reply_text("{}".format(default))
        return []
    params = data["Search"]
    
    # 根据ID进一步检索
    workID = params[0]["imdbID"]
    conn.request("GET", "/?i=" + workID + "&r=json", headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
                                      
    # 将字符串转换为字典格式
    data = ast.literal_eval(data)
    
    update.message.reply_text("Here is the plot of {}:".format(params[0]["Title"]))
    update.message.reply_text("{}".format(data["Plot"]))
    
    return params

# actors_work(name, params)
def actors_work(update, context, name, params):
    # 首先看看name是不是在params中
    for i in range(len(params)):
        if name == params[i]["Title"] or name == None:
            workID = params[i]["imdbID"]
            conn.request("GET", "/?i=" + workID + "&r=json", headers=headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            
            # 将字符串转换为字典格式
            data = ast.literal_eval(data)
            
            update.message.reply_text("Main actors of {}:".format(params[i]["Title"]))
            update.message.reply_text("{}".format(data["Actors"]))
            
            return params
        
    # 如果不在则检索
                                      
    # 获得api数据
    conn.request("GET", "/?page=1&r=json&s=" + name, headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
                                      
    # 将字符串转换为字典格式
    data = ast.literal_eval(data)
                                      
    # 记录结果和结果名字
    if len(data) <= 2:
        update.message.reply_text("{}".format(default))
        return []
    params = data["Search"]
    
    # 根据ID进一步检索
    workID = params[0]["imdbID"]
    conn.request("GET", "/?i=" + workID + "&r=json", headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
                                      
    # 将字符串转换为字典格式
    data = ast.literal_eval(data)
    
    update.message.reply_text("Main actors of {}:".format(params[i]["Title"]))
    update.message.reply_text("{}".format(data["Actors"]))
    
    return params
    
# directors_work(name, params)
def directors_work(update, context, name, params):
    # 首先看看name是不是在params中
    for i in range(len(params)):
        if name == params[i]["Title"] or name == None:
            workID = params[i]["imdbID"]
            conn.request("GET", "/?i=" + workID + "&r=json", headers=headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            
            # 将字符串转换为字典格式
            data = ast.literal_eval(data)
            
            update.message.reply_text("The director of {}:".format(params[i]["Title"]))
            update.message.reply_text("{}".format(data["Director"]))
            
            return params
        
    # 如果不在则检索
    # 获得api数据
    conn.request("GET", "/?page=1&r=json&s=" + name, headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    # 将字符串转换为字典格式
    data = ast.literal_eval(data)
    
    # 记录结果和结果名字
    if len(data) <= 2:
        update.message.reply_text("{}".format(default))
        return []
    params = data["Search"]
    
    # 根据ID进一步检索
    workID = params[0]["imdbID"]
    conn.request("GET", "/?i=" + workID + "&r=json", headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
                                      
    # 将字符串转换为字典格式
    data = ast.literal_eval(data)
    
    update.message.reply_text("The director of {}:".format(params[0]["Title"]))
    update.message.reply_text("{}".format(data["Director"]))
    
    return params

# rank_work(update, context, name, params)
def rank_work(update, context, name, params):
    # 首先看看name是不是在params中
    for i in range(len(params)):
        if name == params[i]["Title"] or name == None:
            workID = params[i]["imdbID"]
            conn.request("GET", "/?i=" + workID + "&r=json", headers=headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            
            # 将字符串转换为字典格式
            data = ast.literal_eval(data)
            
            update.message.reply_text("Awards information of {}:".format(params[i]["Title"]))
            update.message.reply_text("{}".format(data["Awards"]))
            update.message.reply_text("Ratings of {}:".format(params[i]["Title"]))
            for dict in data["Ratings"]:
                update.message.reply_text("{}: {}".format(dict["Source"], dict["Value"]))
            
            
            return params
        
    # 如果不在则检索
    # 获得api数据
    conn.request("GET", "/?page=1&r=json&s=" + name, headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    # 将字符串转换为字典格式
    data = ast.literal_eval(data)
    
    # 记录结果和结果名字
    if len(data) <= 2:
        update.message.reply_text("{}".format(default))
        return []
    params = data["Search"]
    
    # 根据ID进一步检索
    workID = params[0]["imdbID"]
    conn.request("GET", "/?i=" + workID + "&r=json", headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
                                      
    # 将字符串转换为字典格式
    data = ast.literal_eval(data)
    
    update.message.reply_text("Awards information of {}:".format(params[0]["Title"]))
    update.message.reply_text("{}".format(data["Awards"]))
    update.message.reply_text("Ratings of {}:".format(params[0]["Title"]))
    for dict in data["Ratings"]:
        update.message.reply_text("{}: {}".format(dict["Source"], dict["Value"]))
    
    return params

# date_work(update, context, name, params)
def date_work(update, context, name, params):
# 首先看看name是不是在params中
    for i in range(len(params)):
        if name == params[i]["Title"] or name == None:
            workID = params[i]["imdbID"]
            conn.request("GET", "/?i=" + workID + "&r=json", headers=headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            
            # 将字符串转换为字典格式
            data = ast.literal_eval(data)
            
            update.message.reply_text("{} was released on {}.".format(params[i]["Title"], data["Released"]))
            
            return params
        
    # 如果不在则检索
    # 获得api数据
    conn.request("GET", "/?page=1&r=json&s=" + name, headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    # 将字符串转换为字典格式
    data = ast.literal_eval(data)
    
    # 记录结果和结果名字
    if len(data) <= 2:
        update.message.reply_text("{}".format(default))
        return []
    params = data["Search"]
    
    # 根据ID进一步检索
    workID = params[0]["imdbID"]
    conn.request("GET", "/?i=" + workID + "&r=json", headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
                                      
    # 将字符串转换为字典格式
    data = ast.literal_eval(data)
    
    update.message.reply_text("{} was released on {}.".format(params[0]["Title"], data["Released"]))
    
    return params

# genre_work(update, context, name, params)
def genre_work(update, context, name, params):
# 首先看看name是不是在params中
    for i in range(len(params)):
        if name == params[i]["Title"] or name == None:
            workID = params[i]["imdbID"]
            conn.request("GET", "/?i=" + workID + "&r=json", headers=headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            
            # 将字符串转换为字典格式
            data = ast.literal_eval(data)
            
            update.message.reply_text("The genre of {} is {}.".format(params[i]["Title"], data["Genre"]))
            
            return params
        
    # 如果不在则检索
    # 获得api数据
    conn.request("GET", "/?page=1&r=json&s=" + name, headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    # 将字符串转换为字典格式
    data = ast.literal_eval(data)
    
    # 记录结果和结果名字
    if len(data) <= 2:
        update.message.reply_text("{}".format(default))
        return []
    params = data["Search"]
    
    # 根据ID进一步检索
    workID = params[0]["imdbID"]
    conn.request("GET", "/?i=" + workID + "&r=json", headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
                                      
    # 将字符串转换为字典格式
    data = ast.literal_eval(data)
    
    update.message.reply_text("The genre of {} is {}.".format(params[0]["Title"], data["Genre"]))
    
    return params

# time_work(update, context, name, params)
def time_work(update, context, name, params):
# 首先看看name是不是在params中
    for i in range(len(params)):
        if name == params[i]["Title"] or name == None:
            workID = params[i]["imdbID"]
            conn.request("GET", "/?i=" + workID + "&r=json", headers=headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            
            # 将字符串转换为字典格式
            data = ast.literal_eval(data)
            
            update.message.reply_text("The runtime of {} is {}.".format(params[i]["Title"], data["Runtime"]))
            
            return params
        
    # 如果不在则检索
    # 获得api数据
    conn.request("GET", "/?page=1&r=json&s=" + name, headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    # 将字符串转换为字典格式
    data = ast.literal_eval(data)
    
    # 记录结果和结果名字
    if len(data) <= 2:
        update.message.reply_text("{}".format(default))
        return []
    params = data["Search"]
    
    # 根据ID进一步检索
    workID = params[0]["imdbID"]
    conn.request("GET", "/?i=" + workID + "&r=json", headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
                                      
    # 将字符串转换为字典格式
    data = ast.literal_eval(data)
    
    update.message.reply_text("The runtime of {} is {}.".format(params[0]["Title"], data["Runtime"]))
    
    return params

# 理解消息并回复
def respond(update, context, message):
    target = interpreter.parse(message)
    global params
    
    # 去掉消息中所有标点
    r = '[’!"#$%&\'()+,-./:;<=>?@[\\]^_`{|}~]+'
    message = re.sub(r,'',message)
    print(message)
    # params test
    print(params)
    
    # name存放用户消息中的电影名
    name = None
    if(target['entities'] is not None):
        name = find_name(message)
        if name == None:
            name = turn_name(message)
    print(name)
    
    message = message.lower()
    
    print(target['intent']['name'])
    # 判断意图进行检索
    if target['intent']['name'] == 'work_search':
        params = search_work(update, context, name)
        
    elif target['intent']['name'] == 'work_number':
        params = number_work(update, context, message, params)
        
    elif target['intent']['name'] == 'work_poster':
        params = poster_work(update, context, name, params)
    
    elif target['intent']['name'] == 'work_plot':
        params = plot_work(update, context, name, params)
        
    elif target['intent']['name'] == 'work_actors':
        params = actors_work(update, context, name, params)
    
    elif target['intent']['name'] == 'work_directors':
        params = directors_work(update, context, name, params)
    
    elif target['intent']['name'] == 'work_rank':
        params = rank_work(update, context, name, params)
    
    elif target['intent']['name'] == 'work_date':
        params = date_work(update, context, name, params)
    
    elif target['intent']['name'] == 'work_genre':
        params = genre_work(update, context, name, params)
    
    elif target['intent']['name'] == 'work_time':
        params = time_work(update, context, name, params)
    
    elif target['intent']['name'] == 'greet':
        # greet消息
        greet = [
                    "Hello~",
                    "Hey!", 
                    "Hi~",
                    "Hey there~"
                ]
        update.message.reply_text(random.choice(greet))
    
    elif target['intent']['name'] == 'bot_challenge':
        # bot challenge消息
        bot = [
                "I'm Robot Mooda. I can help you find information about movies or TV works. (๑•ᴗ•๑)♡", 
                "My name is Robot Mooda. I can help you find information about movies or TV works. (๑•ᴗ•๑)♡",
                "My name is Robot Mooda, you can call me Mooda. I can help you find information about movies or TV works. (๑•ᴗ•๑)♡"
              ]
        update.message.reply_text(random.choice(bot))
    
    elif target['intent']['name'] == 'mood_great':
        # mood great消息
        great = [
                    "Great! o(^▽^)o",
                    "Yeah! o(^▽^)o",
                    "Cheers! o(^▽^)o"
                ]
        update.message.reply_text(random.choice(great))
    
    elif target['intent']['name'] == 'thanks':
        # thank消息
        thank = [
                    "I am glad I can help. (ฅ◑ω◑ฅ)",
                    "You are welcome. (ฅ◑ω◑ฅ)",
                    "So kind of you. (ฅ◑ω◑ฅ)",
                    "It is my pleasure. (ฅ◑ω◑ฅ)"
                ]
        update.message.reply_text(random.choice(thank))
    
    elif target['intent']['name'] == 'goodbye':
        # goodbye消息
        bye = [
                "bye ~",
                "goodbye ~",
                "see you around ~",
                "see you later ~",
                "see you ~"
              ]
        update.message.reply_text(random.choice(bye))
    
    else:
        update.message.reply_text(default)

# 消息回复功能
def msg(update, context):
    message = update.message.text
    
    result = match_rule(update, context, message)
    
    if result == False:
        respond(update, context, message)
    
    
msg_handler = MessageHandler(Filters.text, msg)
dispatcher.add_handler(msg_handler)
# ****************************************

# 启停
updater.start_polling()
#updater.idle()

# inline
from telegram import InlineQueryResultArticle, InputTextMessageContent
def inline_caps(update, context):
    query = update.inline_query.query
    if not query:
        return
    results = list()
    results.append(
        InlineQueryResultArticle(
            id=query.upper(),
            title='Caps',
            input_message_content=InputTextMessageContent(query.upper())
        )
    )
    context.bot.answer_inline_query(update.inline_query.id, results)

from telegram.ext import InlineQueryHandler
inline_caps_handler = InlineQueryHandler(inline_caps)
dispatcher.add_handler(inline_caps_handler)
