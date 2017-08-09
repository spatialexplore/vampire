import time
import config
import arcpy
import arceditor
import os
import sys
import logging

LOG_FILENAME = 'Vampire_log.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
date = time.strftime('%c')
product = config.config['product']
keycode = config.config['keycode']
country = config.config['country']
host = config.config['postgreHost']
dba = config.config['dba']
dbapass = config.config['dbapass']
sdeuser = config.config['sdeuser']
sdepass = config.config['sdepass']
proj = config.config['proj']
file_path = config.config['gdbpath']
directory = file_path+'\\'+country
storingConfig = config.config['storingConfig']

def createFileGDB(gdb_name, location):
    arcpy.CreateFileGDB_management(location, gdb_name, "CURRENT")


def createEntGDB(host, product, dba, dbapass, sdeuser, sdepass, keycode):
    gdb_name = country.lower()+'_'+product
    #print(gdb_name)
    arcpy.CreateEnterpriseGeodatabase_management("PostgreSQL", host, gdb_name, "DATABASE_AUTH", dba, dbapass,
                                                 "SDE_SCHEMA", sdeuser, sdepass, "", keycode)
    logging.debug(date+": Enterprise Geodatabase " + x + " is created")
    arcpy.CreateDatabaseConnection_management("Database Connections",
                                              gdb_name + ".sde",
                                              "POSTGRESQL",
                                              host,
                                              "DATABASE_AUTH",
                                              sdeuser,
                                              sdepass,
                                              "SAVE_USERNAME",
                                              gdb_name,
                                              "#",
                                              "POINT_IN_TIME",
                                              "#",
                                              "5/19/2017 8:43:41 AM")
    logging.debug(date+": Database connection for geodatabase " + x + " is created")
def checkdatadir(file_path, x):
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.debug(date+": directory "+x+" is created")
        else:
            logging.debug(date+": directory " + x + " is already exist")

def checkFileGDB(gdb_name,directory):
        fileGDBPath = directory +'\\'+ gdb_name +'.gdb'
        if not os.path.exists(fileGDBPath):
            createFileGDB(gdb_name, directory)
            logging.debug(date+": File Geodatabase " + gdb_name + " is created")
        else:
            logging.debug(date+": File Geodatabase  " + gdb_name + " is already exist")

try:

    if storingConfig == 'file':
        logging.debug(date+": we are using file geodatabase")
        for x in product:
            checkdatadir(directory,x)
            checkFileGDB(x, directory)

    elif storingConfig == 'ent':
        logging.debug(date+": we are using enterprise geodatabase")
        for x in product:
            createEntGDB(host, x, dba, dbapass, sdeuser, sdepass, keycode)


except Exception:
    e = sys.exc_info()[1]
    logging.debug(date+": "+e.args[0])
    print(e.args[0])
