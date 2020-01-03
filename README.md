# gispro-ci-tools
ArcGIS Pro Python tools to make Continuous Integration possible on Mapx files. The advantage of Mapx files is that they contain json, and this makes it possible to diff, merge and review changes in GIT. Mapx files contain connection strings and should therefore not be stored as-is in a GIT repository. gispro-ci-tools removes the connection string from the Mapx files and replaces these with keys and the resulting file is safe to store in GIT. Using the ArcGIS Server datastores, gispro-ci-tools can restore the keys to the full connection string and save to Mapx 

# Configuration
The toolbox uses a global configurationfile with urls to your ArcGIS Server and Portal Servers. 
- CONFIGSECTIONS: arcgissections = TEMPLATE (replace TEMPLATE with a comma separated list of ArcGIS Enterprise Environments, use the same identifier in to replace the TEMPLATE Section 
- TEMPLATE: tokenurl = url for generating the token, can be Portal (federated) or ArcGIS Server (standalone) , 
- TEMPLATE: referer = referer for the token
- TEMPLATE: portalurl = the public url of your Portal (can be omitted when the ArcGIS Server is not federated) 
- TEMPLATE: serverurl = the administrative url of your ArcGIS Server
- TEMPLATE: federated = true/false: true if the ArcGIS Server is federated, false when the ArcGIS Server is standalone
- TEMPLATE: publicurl = the public url of your ArcGIS Server (reserved for future use)

If you have a Staging and Production Enviroment copy the TEMPLATE Section and rename the first section to STAGING and the second section to PRODUCTION and configure CONFIGSECTIONS: arcgissections = STAGING,PRODUCTION

# Usage
Writing to JSON:
- Save the map to a Mapx file: Share -> Save As -> Map File
- Run MapToJSON from the toolbox 
- Add the json file to GIT and commit

- command line:
propy.bat  ContinuousIntegrationTools.pyt -a "path/to/mapxfile.mapx" -j "path/to/jsonfile.json" -u portaladministrativeuser -p password -d write -e arcgisenvironment

Reading from JSON:
- Run JSONTOMap from the toolbox (the Database parameter is an optional filter when the ArcGIS Server uses the same key for different databases)
- Open or import the Mapx file in ArcGIS Pro

- command line:
propy.bat  ContinuousIntegrationTools.pyt -a "path/to/mapxfile.mapx" -j "path/to/jsonfile.json" -u portaladministrativeuser -p password -d read -e arcgisenvironment -f DatabaseFilter

# Database registration
The database connection names must be formatted with <username>@<database>. The toolbox will use this formatting to get the key from ArcGIS Server when writing the json and use this key to get the connection string from ArcGIS Server.
You can use this mechanism to update your connectionstrings very quickly from STAGING to PRODUCTION. Run MapToJSON with a Mapx using your staging Database and the Staging Environment and then run JSONTOMap using the Production Environment to create a Mapx which uses the Production database.
  
# Remarks
- I tested with a SDE Enabled PostGIS database, other Enterprise Geodatabases should also work
- The Standalone server should work, but I didn't have one available, so this is also not tested. 

# gispro-python-deploy tools
This toolbox is also part of gispro-python-deploy, a CI/CI Solution for Jenkins to automate creating and sharing Mapservices. Contact us at info(AT]merkator.com for more information.
 
