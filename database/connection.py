import psycopg2
#import os

#from dotenv import load_dotenv

#load_dotenv()

#def conectar():

    #conn = psycopg2.connect(
      #  os.getenv("DATABASE_URL"),
     #   sslmode="require"
    #)

    #return conn

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def conectar():

    database_url = os.getenv("DATABASE_URL")

    print("DATABASE_URL:", database_url)

    conn = psycopg2.connect(
        database_url,
        sslmode="require"
    )

    return conn