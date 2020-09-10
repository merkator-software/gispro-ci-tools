#-------------------------------------------------------------------------------
# Name:        ContinuousIntegrationTools
# Purpose:     Contains the tools to convert ArcGIS Pro Map to GIT Safe JSON and from GIT Safe JSON to ArcGIS Pro Map
#
# Author:      Joël Hempenius
#
# Created:     27-12-2019
# Copyright:   Gis-Admin.com
#-------------------------------------------------------------------------------

import arcpy, configparser, os, getopt, json,urllib, ssl

import urllib.request

iniFileName = 'gispro-ci-tools.ini'

if not hasattr(sys, 'argv'):
    sys.argv  = ['']


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "ContinuousIntegrationToolsbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [MapToJSONTool, JSONToMapTool]



class MapToJSONTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "MapToJSON"
        self.description = ""
        self.canRunInBackground = False


    def getParameterInfo(self):
        """Define parameter definitions"""

        #read ini file
        configreader = Configuration()
        configsections = configreader.readSection("CONFIGSECTIONS")


        # First parameter
        inmap = arcpy.Parameter(
            displayName="Map",
            name="in_map",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")

        arcgisServer = arcpy.Parameter(
            displayName="ArcGIS Server environment",
            name="arcgis_server",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        if 'arcgissections'  in configsections:
            arcgisServer.filter.type = 'ValueList'
            arcgisServer.filter.list  = configsections['arcgissections'].split(',')

        username = arcpy.Parameter(
            displayName="Administrative User",
            name="username",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        password = arcpy.Parameter(
            displayName="Password",
            name="password",
            datatype="GPStringHidden",
            parameterType="Required",
            direction="Input")

        proxy = arcpy.Parameter(
            displayName="Use Proxy",
            name="proxy",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")

        outjson = arcpy.Parameter(
            displayName="Output JSON",
            name="out_json",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")


        params = [inmap, arcgisServer, username, password,  outjson, proxy]

        return params


    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcgisprodocument = parameters[0].value.value
        jsonfile = parameters[4].value.value
        username = parameters[2].value
        password = parameters[3].value
        server = parameters[1].value
        proxy = parameters[5].value
        #read ini file
        configreader = Configuration()
        configuration = configreader.readSection(server)


        writer = MapToJSON()
        writer.execute(arcgisprodocument, jsonfile, username, password, configuration, proxy)
        return

class JSONToMapTool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "JSONToMap"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        #read ini file
        configreader = Configuration()
        configsections = configreader.readSection("CONFIGSECTIONS")


        # First parameter
        inmap = arcpy.Parameter(
            displayName="Output Map",
            name="in_map",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")

        arcgisServer = arcpy.Parameter(
            displayName="ArcGIS Server environment",
            name="arcgis_server",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        if 'arcgissections'  in configsections:
            arcgisServer.filter.type = 'ValueList'
            arcgisServer.filter.list  = configsections['arcgissections'].split(',')

        username = arcpy.Parameter(
            displayName="Administrative User",
            name="username",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        password = arcpy.Parameter(
            displayName="Password",
            name="password",
            datatype="GPStringHidden",
            parameterType="Required",
            direction="Input")

        database = arcpy.Parameter(
            displayName="Database",
            name="database",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")

        proxy = arcpy.Parameter(
            displayName="Use Proxy",
            name="proxy",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")

        outjson = arcpy.Parameter(
            displayName="Input JSON",
            name="out_json",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")

        params = [outjson, arcgisServer, username, password, database, inmap, proxy]

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcgisprodocument = parameters[5].value.value
        jsonfile = parameters[0].value.value
        username = parameters[2].value
        password = parameters[3].value
        server = parameters[1].value
        database = parameters[4].value
        proxy = parameters[6].value
        #read ini file
        configreader = Configuration()
        configuration = configreader.readSection(server)

        reader =  JSONToMap()
        reader.execute(arcgisprodocument, jsonfile, username, password, database, configuration, proxy)

        return

class Configuration(object):
    def readSection(self, section):
        #construct file path and open file
        iniFileNamePath = os.path.join( sys.path[0],iniFileName)
        config = configparser.SafeConfigParser()
        config.readfp(open(iniFileNamePath))

        #create dictionary with parameters
        configparams = {}

        #read section and push to parameters
        for item in config.items(section.upper()):
            configparams[item[0]] = item[1]

        return configparams

class ArcgisServerDatasources(object):
    token = None
    portalurl = None
    serverurl = None
    isFederated = None
    newRegistered = []
    useproxy = False
    proxy = None
    def __init__(self, configuration, username, password, useproxy=False):
        self.useproxy = useproxy
        if 'proxy' in configuration:
            self.proxy = configuration['proxy']
        if 'portalurl' in configuration:
            self.portalurl = configuration['portalurl']
        if 'serverurl' in configuration:
            self.serverurl = configuration['serverurl']
        if 'federated' in configuration:
            self.isFederated = configuration['federated'] == 'true'
        if self.isFederated and ':6443' not in self.serverurl:
            signInResponse = arcpy.SignInToPortal(self.portalurl, username, password)
            self.token = signInResponse['token']
        elif self.isFederated and ':6443' in self.serverurl:
            referer = None
            if 'referer' in configuration:
                referer = configuration['referer']
                arcpy.AddMessage(referer)
            tokenurl = '/admin/generateToken'
            if 'tokenurl' in configuration:
                tokenurl = configuration['tokenurl']
                arcpy.AddMessage(tokenurl)
            self.token = self.GetToken(tokenurl, referer, username, password,self.useproxy, self.proxy)
        else:
            referer = None
            tokenurl = '/admin/generateToken'
            if 'tokenurl' in configuration:
                tokenurl = configuration['tokenurl']
            self.token = self.GetToken(tokenurl, referer, username, password,self.useproxy, self.proxy)
    def getDatasources(self):
        url = self.serverurl + '/admin/data/findItems'
        parameters = { 'f'     : 'pjson', 'parentPath': r'/enterpriseDatabases', 'types': 'egdb'}

        if self.token is not None:
            parameters['token'] = self.token
        data = self.RequestWithToken(url, parameters,headers=None, useproxy=self.useproxy, proxy=self.proxy)
        datasources = json.loads(data)
        for item in datasources['items']:
            path =item['path']
            item['cicdname'] = path.split(r'/')[-1]

        message = "Datastores read from ArcGIS Server"
        arcpy.AddMessage(message)
        return datasources

    def registerDatasource(self, datasource, connectionstring):
        if datasource not in self.newRegistered:
            url = self.serverurl +  '/admin/data/validateDataItem'

            parameters = {
                 'f': 'json',
                 'item': '{"type":"egdb","info":{"dataStoreConnectionType":"shared","isManaged":false,"connectionString":"'+connectionstring+'"},"path":"/enterpriseDatabases/'+datasource+'"}'
            }
            if self.token is not None:
                parameters['token'] = self.token

            data = self.RequestWithToken(url, parameters,headers=None, useproxy=self.useproxy, proxy=self.proxy)
            result = json.loads(data)
            if result['status'] =='success':
                url = self.serverurl +  '/admin/data/registerItem'
                data = self.RequestWithToken(url, parameters, headers=None, useproxy=self.useproxy, proxy=self.proxy)
                result = json.loads(data)
                if  result['success']:
                    self.newRegistered.append(datasource)
                    message = "Datastore registered with ArcGIS Server: " + datasource
                    arcpy.AddMessage(message)
                else:
                    message = "Datastore not registered with ArcGIS Server: " + datasource
                    arcpy.AddWarning(message)
            else:
                arcpy.AddWarning("Datastores not valid" + datasource)

    def GetToken(self, tokenURL, referer, username, password, useproxy = False, proxy = None):
        # Token URL is typically http://portalserver.domain.tld/portalwebadapter/sharing/rest/generateToken
        if referer is None:
            params = urllib.parse.urlencode({'username': username, 'password': password, 'client': 'requestip', 'f': 'json'}).encode("utf-8") #standalone token request
        else:
            params = urllib.parse.urlencode({'username': username, 'password': password, 'client': 'referer', 'referer': referer,'f': 'json'}).encode("utf-8") #portal token request
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        #by default system proxy is used, useproxy=False forces the request not to use the proxy, useproxy=True and setting proxy value forces to this proxy
        if useproxy and proxy is not None:
            proxy_handler = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)
        else:
            proxy_handler = urllib.request.ProxyHandler({})
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)

        # Connect to URL and post parameters
        request = urllib.request.Request(tokenURL)
        for item in headers:
            request.add_header(item, headers[item])
        #request.add_data(params)

        result = urllib.request.urlopen(request,data=params, timeout= 500)
        data = result.read()

        # Extract the token from it
        token = json.loads(data)
        return token['token']

    def RequestWithToken(self, url, data,  headers = None, useproxy = True, proxy = None, timeout=500):
        try:
            #by default system proxy is used, useproxy=False forces the request not to use the proxy, useproxy=True and setting proxy value forces to this proxy
            if useproxy and proxy is not None:
                proxy_handler = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
                opener = urllib.request.build_opener(proxy_handler)
                urllib.request.install_opener(opener)
            else:
                proxy_handler = urllib.request.ProxyHandler({})
                opener = urllib.request.build_opener(proxy_handler)
                urllib.request.install_opener(opener)

            # generate response
            request = urllib.request.Request(url)
            if headers is not None:
                for item in headers:
                    request.add_header(item, headers[item])
            if data is not None:
                if type(data) is not str:
                    data = urllib.parse.urlencode(data).encode("utf-8")
                    with urllib.request.urlopen(request,data=data, timeout =timeout ) as result:
                        resp =  result.read()
                        return resp
                else:
                    request  = urllib.request.Request(url, data, headers)
                    with urllib.request.urlopen(request,timeout =timeout ) as result:
                        resp =  result.read()
                        return resp
            else:
                with urllib.request.urlopen(request,timeout =timeout ) as result:
                    resp =  result.read()
                    return resp
        except Exception as e:
            arcpy.AddError(str(e))
            raise e


class MapToJSON(object):
    def execute(self, promap, jsonfile, username, password ,configuration, proxy):
        json_map = None
        with open(promap,"r",encoding='utf8') as inputfile:
            data = inputfile.read()
            json_map = json.loads(data)
        message = 'Reading:' + promap
        arcpy.AddMessage(message)

        serverDatasources = ArcgisServerDatasources(configuration, username, password)
        datasources = serverDatasources.getDatasources()
        self.replaceDataSources(json_map, datasources, serverDatasources)

        message = 'Writing:' + jsonfile
        arcpy.AddMessage(message)
        with open(jsonfile, 'w',encoding='utf8' ) as outputfile:
            json.dump(json_map, outputfile, indent=4, sort_keys=True,separators=(',', ': '))

    def replaceDataSources(self, json_map, datasources, serverDatasources):
        self.findDataSources(json_map, datasources, serverDatasources)

    def findDataSources(self, js, datasources, serverDatasources):
        for key in js:
            if type(key) is dict or type(key) is list:
                if 'dataConnection' in key:
                    self.replaceDataSource(key['dataConnection'], datasources, serverDatasources)
                else:
                    self.findDataSources(key, datasources, serverDatasources)
            elif type(js) is dict and (type(js[key]) is dict or type(js[key]) is list):
                if 'dataConnection' in js[key]:
                    self.replaceDataSource(js[key]['dataConnection'], datasources, serverDatasources)
                else:
                    self.findDataSources(js[key], datasources, serverDatasources)

    def replaceDataSource(self, dataConnection, datasources, serverDatasources):
        if dataConnection['type'] =='CIMRelQueryTableDataConnection':
            self.replaceRelationDataSource(dataConnection,datasources,serverDatasources)
        elif dataConnection['type'] =='CIMStandardDataConnection' or dataConnection['type'] =='CIMSqlQueryDataConnection':
            self.replaceTableDataSource(dataConnection,datasources,serverDatasources)

    def replaceRelationDataSource(self, dataConnection, datasources, serverDatasources):
        self.replaceTableDataSource(dataConnection['sourceTable'], datasources, serverDatasources)
        self.replaceTableDataSource(dataConnection['destinationTable'], datasources, serverDatasources)

    def replaceTableDataSource(self, dataConnection, datasources, serverDatasources):
        if dataConnection['workspaceFactory'] =='SDE':
            workspaceConnectionString =  dataConnection['workspaceConnectionString']
            found = False
            for ds in datasources['items']:
                servercsdict = self.connectionStringToDict(ds['info']['connectionString'])
                if self.compareConnectionString(ds['info']['connectionString'],workspaceConnectionString) and 'USER' in servercsdict:
                    dataConnection['workspaceConnectionString'] = servercsdict['USER']
                    arcpy.AddMessage('Replaced: ' + servercsdict['USER'])
                    found = True
                    continue
            if not found:
                dsname = ''
                key = ''
                csdict = self.connectionStringToDict(workspaceConnectionString)
                if 'USER' in csdict:
                    dsname = csdict['USER']
                    key = csdict['USER']
                if 'DATABASE' in csdict: #postgres
                    dsname = dsname + '@' + csdict['DATABASE']
                if 'SERVER' in csdict: #oracle
                    dsname = dsname + '@' + csdict['INSTANCE'].split(':')[-1]
                serverDatasources.registerDatasource(dsname, workspaceConnectionString)
                dataConnection['workspaceConnectionString'] = key

    def connectionStringToDict(self, connectionstring):
        c_props = connectionstring.split(";")
        c_dict = {}
        for p  in c_props:
            prop = p.split("=")
            c_dict[prop[0]] = prop[1]
        return c_dict

    def compareConnectionString(self, a, b):
        a_dict = self.connectionStringToDict(a)
        b_dict = self.connectionStringToDict(b)
        for prop in a_dict:
            if prop != 'ENCRYPTED_PASSWORD':
                if prop not in b_dict:
                    return False
                elif b_dict[prop] != a_dict[prop]:
                    return False
        return True




class JSONToMap(object):
    def execute(self, prodocument, jsonfile, username, password, database, configuration, proxy):
        json_map = None
        with open(jsonfile,"r",encoding='utf8') as inputfile:
            data = inputfile.read()
            json_map = json.loads(data)

        message = 'Reading:' + jsonfile
        arcpy.AddMessage(message)
        serverDatasources = ArcgisServerDatasources(configuration, username, password)
        datasources = serverDatasources.getDatasources()
        self.replaceDataSources(json_map, datasources, database)

        message = 'Writing:' + prodocument
        arcpy.AddMessage(message)
        with open(prodocument, 'w',encoding='utf8' ) as outputfile:
            json.dump(json_map, outputfile, indent=4, sort_keys=True,separators=(',', ': '))

    def replaceDataSources(self, json_map, datasources, database):
        self.findDataSources(json_map, datasources, database)

    def findDataSources(self, js, datasources, database):
        for key in js:
            if type(key) is dict or type(key) is list:
                if 'dataConnection' in key:
                    self.replaceDataSource(key['dataConnection'], datasources, database)
                else:
                    self.findDataSources(key, datasources,database)
            elif type(js) is dict and (type(js[key]) is dict or type(js[key]) is list):
                if 'dataConnection' in js[key]:
                    self.replaceDataSource(js[key]['dataConnection'], datasources, database)
                else:
                    self.findDataSources(js[key], datasources, database)

    def replaceDataSource(self, dataConnection, datasources, database):
        if dataConnection['type'] =='CIMRelQueryTableDataConnection' :
            self.replaceRelationDataSource(dataConnection,datasources,database)
        elif dataConnection['type'] =='CIMStandardDataConnection' or dataConnection['type'] =='CIMSqlQueryDataConnection':
            self.replaceTableDataSource(dataConnection,datasources,database)

    def replaceRelationDataSource(self, dataConnection, datasources, database):
        self.replaceTableDataSource(dataConnection['sourceTable'], datasources, database)
        self.replaceTableDataSource(dataConnection['destinationTable'], datasources, database)

    def replaceTableDataSource(self, dataConnection, datasources, database):
        if database == None:
            database = ''
        if dataConnection['workspaceFactory'] =='SDE':
            workspaceConnectionString =  dataConnection['workspaceConnectionString']
            found = False
            arcpy.AddMessage("Restore connection: " + workspaceConnectionString)
            for ds in datasources['items']:
                connectiondict = self.connectionStringToDict( ds['info']['connectionString'])
                if ('USER' in connectiondict and database !='' and workspaceConnectionString.upper() == connectiondict['USER'].upper() and database in ds['info']['connectionString']) or ('USER' in connectiondict and database =='' and workspaceConnectionString.upper() == connectiondict['USER'].upper()):
                    dataConnection['workspaceConnectionString'] = ds['info']['connectionString']
                    if 'DATABASE'  in connectiondict:
                        dataConnection['dataset'] = '.'.join([connectiondict['DATABASE']] + dataConnection['dataset'].split('.')[-2:])
                    found = True
                    continue
            if not found:
                arcpy.AddWarning("Could not restore connection")

    def connectionStringToDict(self, connectionstring):
        c_props = connectionstring.split(";")
        c_dict = {}
        for p  in c_props:
            prop = p.split("=")
            c_dict[prop[0]] = prop[1]
        return c_dict

def main(argv):
    opts, args = getopt.getopt(argv,"xa:j:e:u:p:d:f",["arcgisprodocument=","jsonfile=","environment=","user=","password=","readorwrite=","filter="])

    arcgisprodocument = ''
    jsonfile = ''
    username = ''
    password = ''
    server = ''
    read = True
    database = ''

    for opt, arg in opts:
        if opt == '-x':
            print ('ContinuousIntegrationTools.pyt -a <arcgisprodocument> -j <jsonfile> -m <map> -e <environment> -u <user> -p <password> -d read/write')
            print('-a / arcgisprodocument = Required, ArcGIS Pro document (.aprx or mapx)')
            print('-j / jsonfile = Required, the JSON file with the GIT safe mapdocument')
            print('-e / enviroment= Required, ArcGIS Server enviroment to check or retrieve the datasources, the environment should be configured in the gispro-python-deploy.ini file')
            print('-s / user= Required, Administrative user')
            print('-p / password= Required, Password')
            print('-d / readorwrite= Required. read / write, Read = Convert the JSON to an ArcGIS Pro document, Write = Convert the map in the ArcGIS Pro document to JSON')
            print('-f / filter = Optional. Filter databases from the ArcGIS Server datastores when reading the json and converting it to a mapx')
            sys.exit()
        elif opt in ("-a", "--arcgisprodocument"):
            arcgisprodocument = arg
        elif opt in ("-u", "--user"):
            username = arg
        elif opt in ("-p", "--password"):
            password = arg
        elif opt in ("-j", "--jsonfile"):
            jsonfile = arg
        elif opt in ("-m", "--mapname"):
            mapname = arg
        elif opt in ("-e", "--enviroment"):
            server = arg
        elif opt in ("-d", "--readorwrite"):
            read = arg == "read"
        elif opt in ("-f", "--filter"):
            database = arg
    if server !='':
    #read ini file
        configreader = Configuration()
        configuration = configreader.readSection(server)

        if read:
            reader =  JSONToMap()
            reader.execute(arcgisprodocument, jsonfile, username, password,database, configuration)
        else:
            writer = MapToJSON()
            writer.execute(arcgisprodocument, jsonfile, username, password, configuration)


if __name__ == '__main__':
    main(sys.argv[1:])
