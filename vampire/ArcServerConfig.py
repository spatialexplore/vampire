import arcpy
import configArcGIS as config
import sys
import logging
import time
import os
import xml.dom.minidom as DOM

LOG_FILENAME = 'Vampire_log.log'


server_url = "http://localhost:6080/arcgis/admin"
use_arcgis_desktop_staging_folder = False
username = "dio.dafrista@wfp.org"
password = "Semangat@2017"
product = config.config['product']
storingConfig = config.config['storingConfig']
ws = "D:/SharedFolder/DIO/vampire/"
date = time.strftime('%c')

country = config.config['country']
file_path = config.config['gdbpath']
directory = file_path+'\\'+country
sdeCatalog = "C:/Users/dio.dafrista/AppData/Roaming/ESRI/Desktop10.3/ArcCatalog/"
template = config.config['template']

def createagsfile(ws, out_name, server_url, username, password):
    arcpy.mapping.CreateGISServerConnectionFile("PUBLISH_GIS_SERVICES",
                                            ws,out_name,
                                            server_url,
                                            "ARCGIS_SERVER",
                                            False,
                                            ws,
                                            username,
                                            password,
                                            "SAVE_USERNAME")
    print("Connection Server file is created")

def createImageSDDraft(fc, sddraft, service, con):
    arcpy.CreateImageSDDraft(fc, sddraft, service, 'ARCGIS_SERVER',
                             con, False, None, "Publish las MD",
                             "las,image service")
    print("SDDraft file for "+x+" is created")


def analyzeSDDraft(sddraft, sd):
    analysis = arcpy.mapping.AnalyzeForSD(sddraft)
    print("Service Definition analysis for " + x + " :")
    for key in ('messages', 'warnings', 'errors'):
        print "----" + key.upper() + "---"
        vars = analysis[key]
        for ((message, code), layerlist) in vars.iteritems():
            print "    ", message, " (CODE %i)" % code
            print "       applies to:",
            for layer in layerlist:
                print layer.name,
            print
    if analysis['errors'] == {}:
        # Execute StageService
        arcpy.StageService_server(sddraft, sd)
        # Execute UploadServiceDefinition
    else:
        # if the sddraft analysis contained errors, display them
        print analysis['errors']

def insertRTFFile(product, sddraft):
    fileRTF = template[product]
    print("fileRTF :" +fileRTF+ " in "+sddraft)
    doc = DOM.parse(sddraft)
    x = doc.getElementsByTagName("PropertySetProperty")
    for i in x:
        y = i.getElementsByTagName("Key")
        for j in y:
            if j.childNodes[0].nodeValue == "rasterFunctions":
                price = i.getElementsByTagName("Value")
                for p in price:
                    if p.firstChild == None:
                        p.appendChild(doc.createTextNode(fileRTF))
                        print("RTF data " + fileRTF + " is added")
                    else:
                        p.firstChild.replaceWholeText(fileRTF)
                        print("RTF data " + fileRTF + " is added")
    with open(sddraft, "wb") as f:
        doc.writexml(f)

try:
    if storingConfig == 'file':
        for x in product:
            createagsfile(ws, x, server_url, username, password)
            fc1 = os.path.join(directory, x+'.gdb')
            fc = os.path.join(fc1, x)
            if arcpy.Exists(fc):
                print("data "+x+" is available")
            else:
                print("data "+x+" is not availabe")
            con = os.path.join(ws, x+".ags")
            service = x
            sddraft = os.path.join(ws, x+".sddraft")
            sd = os.path.join(ws, x+".sd")
            createImageSDDraft(fc, sddraft, service, con)
            insertRTFFile(service,sddraft)
            if not os.path.exists(sd):
                analyzeSDDraft(sddraft, sd)
            else:
                print("file "+sd+" already exist")
            if not os.path.exists(con):
                print("file "+con+" is not exist")
            else:
                print("file "+con+" already exist")
                arcpy.UploadServiceDefinition_server(sd, con)
            print(con)


    elif storingConfig == 'ent':
        for x in product:
            countProduct = country.lower() + "_" + x
            createagsfile(ws, countProduct, server_url, username, password)
            sdeCon = sdeCatalog+countProduct+'.sde/'
            fc = sdeCon+countProduct
            print(fc)
            if arcpy.Exists(fc):
                print("data "+x+" is available")
            else:
                print("data "+x+" is not availabe")
            con = os.path.join(ws, x + ".ags")
            service = x
            sddraft = os.path.join(ws, x + ".sddraft")
            sd = os.path.join(ws, x + ".sd")
            createImageSDDraft(fc, sddraft, service, con)
            insertRTFFile(x, sddraft)
            if not os.path.exists(sd):
                analyzeSDDraft(sddraft, sd)
            else:
                print("file "+sd+" already exist")
            if not os.path.exists(con):
                print("file "+con+" is not exist")
            else:
                print("file "+con+" already exist")
                arcpy.UploadServiceDefinition_server(sd, con)
            print(con)

except Exception:
    e = sys.exc_info()[1]
    logging.debug(date+":"+e.args[0])
    print(e.args[0])
