import pymongo

# this would be the interface between the DB and python
# adapters would be the interface between THIS and the scrapers

# this class is like main that runs all the strategy or adaptor pattern

# connection to the mongodb here
# use other classes

client = pymongo.MongoClient(
        "mongodb+srv://BCWATT:WattTime2021" +
        "@cluster0.tbh2o.mongodb.net/" +
        "WattTime?retryWrites=true&w=majority")

db = client.get_database('WattTime')

