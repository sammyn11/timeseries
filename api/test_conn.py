from pymongo import MongoClient

uri = "mongodb+srv://esimiyu_db_user:4Dj7M2pThYTRE0P4@energy.8n8lpt7.mongodb.net/"
client = MongoClient(uri, serverSelectionTimeoutMS=10000)

try:
    client.admin.command("ping")
    print("✅ Connected to Atlas!")
    print("Databases:", client.list_database_names())
    
    db = client["energy_db"]
    print("Collections in energy_db:", db.list_collection_names())
except Exception as e:
    print("❌ Connection failed:", e)