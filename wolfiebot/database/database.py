import logging
import os
import wolfiebot

from pymongo import ASCENDING, MongoClient
from dotenv import load_dotenv, find_dotenv

log = logging.getLogger(__name__)

class Database:
    
    def __init__(self):
        load_dotenv(find_dotenv())
        MONGODB_CONNECTION = os.environ.get("MONGODB_CONNECTION")
        self.client = MongoClient(MONGODB_CONNECTION)
        log.info("database connected")
        
    def edit_user_data(self, user_id, name, value):
        document = self.client["wolfie"]["users"]
        document.find_one_and_update({"_id": user_id}, {"$set" : { name : value }}, upsert=True)
        
    def append_user_data(self, user_id, name, value):
        document = self.client["wolfie"]["users"]
        document.find_one_and_update({"_id" : user_id}, {"$push" : { name : value }}, upsert=True)
        
    def read_user_data(self, user_id, name=None):
        document = self.client["wolfie"]["users"]
        raw_data = document.find({"_id" : user_id}, {})
        for data in raw_data:
            if name is not None:
                return data[name]
        return raw_data
        
    def delete_user_data(self, user_id, name):
        document = self.client["wolfie"]["users"]
        document.update_one({"_id" : user_id}, { "$unset" : { name : {} } })
        
    def edit_guild_data(self, guild_id, name, value):
        document = self.client["wolfie"]["guilds"]
        document.find_one_and_update({"_id": guild_id}, {"$set" : { name : value }}, upsert=True)
        
    def append_guild_data(self, guild_id, name, value):
        document = self.client["wolfie"]["guilds"]
        document.find_one_and_update({"_id" : guild_id}, {"$push" : { name : value }}, upsert=True)   
        
    def remove_guild_data_array(self, guild_id, name, value):
        document = self.client["wolfie"]["guilds"]
        document.find_one_and_update({"_id" : guild_id}, {"$pull" : { name : value }}, upsert=True)   
        
    def read_guild_data(self, guild_id, name=None):
        document = self.client["wolfie"]["guilds"]
        raw_data = document.find({"_id" : guild_id}, {})
        for data in raw_data:
            if name is not None:
                return data[name]
        return raw_data
    
    def delete_guild_data(self, guild_id, name):
        document = self.client["wolfie"]["guilds"]
        document.update_one({"_id" : guild_id}, { "$unset" : { name : {} } })