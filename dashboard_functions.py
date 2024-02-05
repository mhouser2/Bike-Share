import redshift_connector
import pandas as pd
import os
import duckdb

os.getenv("mapboxtoken")

def get_dataframe_redshift(query):

    conn = redshift_connector.connect(
        host=os.getenv('redshift_host'),
        port=5439,
        database='dev',
        user=os.getenv('redshift_user'),
        password=os.getenv('redshift_password')
    )

    cursor = conn.cursor()

    cursor.execute(query)
    df = cursor.fetch_dataframe()
    cursor.close()
    conn.close()
    return df

def get_dataframe_duckdb(query):

    conn = duckdb.connect("C:\\Users\\matti\\Bike Share\\bikes.db")
    df = conn.sql(query).df()
    return df