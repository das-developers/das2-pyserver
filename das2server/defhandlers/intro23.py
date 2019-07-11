"""Default Handler for no argument hit on the top level of the server"""

import sys
import os
from os.path import join as pjoin

##############################################################################
def pout(sOut):
	sys.stdout.write(sOut)
	sys.stdout.write('\r\n')
	
##############################################################################
# Provide a list of name and directory tuples from a given data level

def _getDataDirs(U, dConf, fLog, sRelPath):
	"""Get a list of links and names for everything at a particular level
	
	sRelPath - Level under SCRIPT/source, use a '/' to get
	           information for the top of the dsid root
	"""

	sScriptURL = U.io.getScriptUrl()
	
	# Keep a list of directories

	if not dConf.has_key('DSDF_ROOT'):
		fLog.write("   ERROR: Configuration item DSDF_ROOT missing")
		return None

	sRoot = dConf['DSDF_ROOT']
	
	if not os.path.isdir(sRoot):
		fLog.write("   ERROR: DSID_ROOT dir '%s' does not exist"%sRoot)
		return None
	
	if sRelPath == '/':
		sPath = sRoot
	else:
		sPath = pjoin(sRoot, sRelPath)
		
	if not os.path.isdir(sPath):
		fLog.write("   ERROR: Data directory '%s' does not exist"%sPath)
		return None
	
	lOut = []
	
	lDirs = os.listdir(sPath)
	lDirs.sort()
	
	fLog.write("   INFO: Listing data in %s"%sPath)
	for sDir in lDirs:
		if not os.path.isdir( pjoin(sPath, sDir) ):
			continue
		
		bVisible = True
		sDirDsdf = pjoin(sPath, sDir, '_dirinfo_.dsdf')
		if os.path.isfile(sDirDsdf):
			try:
				fIn = file(sDirDsdf, 'rb')
				for sLine in fIn:
					if sLine.find('#') != -1:
						sLine = sLine[: sLine.find('#') ]
					sLine = sLine.strip()
					if sLine.startswith('browse'):
						lLine = [s.strip().strip("'") for s in sLine.split('=')]
						if len(lLine) > 1:
							if lLine[1].lower() in ('no','0'):
								bVisible = False
						break
			except:
				pass
									
		
		if bVisible:
			sUrl = '%s/source%s%s/'%(sScriptURL, sRelPath, sDir)
		
			sName = sDir.replace('_',' ').upper()
			lOut.append( (sName, sUrl) )
	
	
	return lOut

##############################################################################
def allowViewLog(dConf, fLog, sIP):
	"""Check the config and see if sIP is allowed to view log files"""
	
	fLog.write("   WARNING: das2server.util.site.allowViewLog not implemented, always says yes")
	
	return True
	

##############################################################################
# Helper for browseHeader, provides an optional header that shows the data
# hierarchy down to the current level

def _dataNavHeader(U, sReqType, dConf, fLog, form, sPathInfo):
	
	sScriptURL = U.io.getScriptUrl()
	
	sDataSet = sPathInfo.replace('/source/', '')
	
	# Split the path up into parts that retain the trailing '/'
	lParts = [ '%s/'%s for s in sDataSet.split('/')]
	
	if lParts[-1] == '/':
		lParts[-2] = "%s/"%(lParts[-2])
		lParts = lParts[:-1]
		
	if len(lParts) < 1:
		return
	
	pout('  <center><ul id="datanav">')
	
	
	for i in xrange(0, len(lParts)):
		sPart = lParts[i]
		sName = 	lParts[i].rstrip('/').replace('_',' ').upper()
		
		sUrl = '%s/data/%s'%(sScriptURL, ''.join(lParts[:i+1]))
		
		if i > 0:
			sSep = ' &gt '
		else:
			sSep = ''
			
		pout('    <li>%s<a href="%s">%s</a></li>'%(sSep, sUrl, sName))
	
	pout(' </ul></center>')
		
	
##############################################################################
def handleReq(U, sReqType, dConf, fLog, form, sPathInfo):
	"""The interface for a handler function is as follows:
	
	Parameter Inputs:
	
	   U - The das2server utility module, contains handy functions
	
	   sReqType - A string indicating the internal name for this type of 
		    request

		dConf - A dictionary containing all the parameters loaded from 
		    the configuration file
			 
		fLog - A DasLogFile object, contains a write member, just use that
		
		form - A cgi.FieldStorage instance, provides the query parameters
		
		sPathInfo - The URL path after the script name itself

   File Inputs:

      stdin - Has already been consumed by the FieldStorage instance, theres
		   nothing to read there
			
   Environment Inputs:
	
	   The standard CGI environment variables are present and set up, some of
		the utilitly module functions use these is the background
			
	Outputs:
		stdout - Write any data ment for the client program to standard output
		
		stderr - Not used, don't even bother unless you are doing some wierd
		         non-embedded testing
					
	   fLog - Log your errors or other information in fLog, or better yet use
		       the error output functions in U.io.
		
	Return Value:
	
	   Return 0 if everything went okay, non-zero to indicate an error return
		
	
	Exceptions:
		There is a traceback handler at the top level, so thrown exceptions will
		be caught, logged and sent to the client.  In addition the log message
		will be sent as plain  text or as a das2exception packet depending on the
		client type.
	"""
	
	pout('Content-Type: text/html; charset=utf-8\r\n')
	pout('<!DOCTYPE html>')
	
	dReplace = {"script":U.io.getScriptUrl()}
	
	sExQuery = ""
	if dConf.has_key('SAMPLE_DSDF'):
		dReplace['dataset'] = dConf['SAMPLE_DSDF']
			
	if dConf.has_key('SAMPLE_START') and dConf.has_key('SAMPLE_END'):
		dReplace['start_time'] = dConf['SAMPLE_START']
		dReplace['end_time'] = dConf['SAMPLE_END']
	
	bHSubSys	= False
	sKey = "ENABLE_HAPI_SUBSYS"
	if sKey in dConf:
		bHSubSys = dConf[sKey].lower() in ('true','yes','1')
	
				
	sViewLog = ""
	sViewLogNav = ""
	if dConf.has_key('VIEW_LOG_URL'):
		if len(dConf['VIEW_LOG_URL']) > 0:
			sViewLog = '<a href="%s">Recent '%dConf['VIEW_LOG_URL']+\
			           'activity logs</a> for your IP address are available.'
			sViewLogNav = '<hr><a href="%s">Activity Log</a>'%dConf['VIEW_LOG_URL'] 
	
	sScriptURL = U.io.getScriptUrl()
	
	if dConf.has_key('SITE_NAME'):
		sSiteId = dConf['SITE_NAME']
	else:
		sSiteId = "Set SITE_NAME in %s"%dConf['__file__']
	dReplace['SITE_NAME'] = sSiteId	

	if dConf.has_key('SERVER_ID'):
		sServerId = dConf['SERVER_ID'].upper()
	else:
		sServerId = "{Set SERVER_ID in %s}"%dConf['__file__']
	dReplace['SERVER_ID'] = sServerId

	if dConf.has_key('STYLE_SHEET'):
		sCssLink = "%s/resource/%s"%(sScriptURL, dConf['STYLE_SHEET'])
	else:
		sCssLink = "%s/resource/das2server.css"%sScriptURL
	
	pout('''
<html>
<head>
   <title>%s</title>
   <link rel="stylesheet" type="text/css" media="screen" href="%s" />
</head>
'''%(sSiteId, sCssLink))
	
	pout('''
<body>
<div class="header">
	<div class="hdr_left">
		<img src="%(script)s/logo" alt="%(SERVER_ID)s" width="70" height="70" >
	</div> 
	<div class="hdr_center">
	%(SERVER_ID)s, a Das 2.3 Server
	<h1>%(SITE_NAME)s</h1>
	</div>
	<div class="hdr_right">
		<a href="http://das2.org">
		<img src="%(script)s/resource/das2logo_rv.png" alt="Das2" width="80" height="80">
		</a>
	</div>
	</a>
</div>
'''%dReplace)
	pout('<div class="main">')

	pout('<div class="nav">Data Sources<hr>')
	pout('  <ul>')
	
	lTop = _getDataDirs(U, dConf, fLog, '/')
	
	if lTop != None:
		for (sName, sUrl) in lTop:
			pout('    <li><a href="%s">%s</a><br><br></li>'%(sUrl, sName))

	pout('  </ul>')
	pout('''%s
  <br><br>
  <a href="%s/peers">Peer Servers</a>
</div>'''%(sViewLogNav, sScriptURL))
	
	pout('<div class="article">')
	
	if sPathInfo.startswith('/source/'):
		if sPathInfo != '/source/':
			_dataNavHeader(U, sReqType, dConf, fLog, form, sPathInfo)
	

	
	if bHSubSys:
		sTmp = """This is a Das 2.3 (prototype) Server, it provides access to
		          space physics data sources using a three distinct HTTP GET based
					 query protocols:
					 <ul>
					 <li>The <a href="http://das2.org/Das2.2.2-ICD_2017-05-09.pdf">Das 2.2</a> 
                    service protocol</li>
					 <li>The Das 2.3 service protocol, a more browseable path based layout
                    using JSON metadata</li>
					 <li>The <a href="https://github.com/hapi-server/data-specification">
                    HAPI 1.1</a> protocol, a simplified time series cube service
					     defined by the heliophysics API group. </li></ul>"""
	else:
		sTmp = """This is a Das 2.3 (prototype) Server, it provides access to
		          space physics data sources using a two distinct HTTP GET based
					 query protocols, the established Das 2.2 protocol and the
					 evolving path based 2.3 protocol."""
	
	pout("""
<p>%s %s
</p>

<p>Full use of this site requires a client progam capable of reading data in
Das2 stream or QStream format.  <a href="http://autoplot.org">Autoplot</a> is a
general client for plotting many types of space physics data, including
streams from this server, and the 
<a href="http://www-pw.physics.uiowa.edu/das2/demo-apps.html">Das2 Clients</a>
from the University of Iowa provide specific interfaces tailored to certian
data sets.
<p>
</p>
Since this server delivers information over HTTP, limited functionality
is available using any standard web browser.  Some example queries are 
provided below.
</p>
"""%(sTmp, sViewLog))

	pout("""
<h2>Das 2.3 Service Queries</h2>
<ul>

<li><b>Services List</b> -- To see a get a list of all services supported
by this particular server use the following URL:
<br><br>
<a href="%(script)s/services.json">%(script)s/services</a>
<br><br>
</li>

<li><b>Data Source List</b> -- To download a list of all data sources known to
this server use the following URL:
<br /><br />
<a href="%(script)s/catalog.json">%(script)s/catalog</a>
<br /><br />
</li>"""%dReplace)

	pout("""
<li><b>Peers List</b> -- To download a list of other Das2 servers known to this
site use the following URL:
<br /><br />
<a href="%(script)s/peers.xml">%(script)s/peers</a>
<br> <i>Todo: Output as JSON</i>
<br /><br />
</li>
"""%dReplace)

	pout("""
<li><b>Source Descriptor</b> -- To obtain a JSON description of a data source
that provides sufficent information to download data enter a URL with
the pattern:
<br /><br />
%(script)s/source/<i>SOURCE_DEF_PATH</i>
<br /><br />
Where the <i>SOURCE_DEF_PATH</i> is one of the file paths provided by a 
catalog listing.
"""%dReplace)

	if dReplace.has_key('dataset'):
		pout("""
For example:
<br /><br />
<a href="%(script)s?/source%(dataset)s">
%(script)s/source%(dataset)s</a>
		"""%dReplace)
	
	pout("<br /><br /></li>")
	
	pout("""
<li><b>Data Download</b> -- To download data as either 
a Das2 stream or QStream enter a URL with the pattern:
<br /><br />
DATA_SOURCE_URL</i>&start_time=<i>BEGIN</i>&end_time=<i>END</i>
<br /><br />
Where the <i>DATA_SOURCE_URL</i> is the source URL provided by a source
descriptor and <i>START</i> and <i>END</i> are time strings.  Though many time 
formats will work with most data sources, ISO-8601 format strings are 
recommended, in general these look like YYYY-MM-DDTHH:MM:SS.sss where 
uneeded time fields may be omitted.
"""%dReplace)

	if dReplace.has_key('start_time') and dReplace.has_key('end_time'):
		pout("""
For example:
<br /><br />
<a href="%(script)s?/source/%(dataset)s?time.min=%(start_time)s&time.max=%(end_time)s">
%(script)s/source/%(dataset)s?start_time=%(start_time)s&end_time=%(end_time)s</a>
		"""%dReplace)
	
	pout("<br /><br /></li>")
	
	#if dConf.has_key('PNG_MAKER'):
	#	pout("""
#<li><b>Plot Download</b> -- This server has been extended with a server side
#plotter which delivers data as PNG images.  To use this functionality enter a
#URL with the pattern:
#<br /><br />
#%(script)s?server=image&dataset=<i>DATA_SET_NAME</i>&start_time=<i>BEGIN</i>&end_time=<i>END</i>		
#<br /><br />
#"""%dReplace)
#
#		if dReplace.has_key('start_time') and dReplace.has_key('end_time') and \
#		   dReplace.has_key('dataset'):
#			pout("""
#For example:
#<br /><br />
#<a href="%(script)s?server=image&dataset=%(dataset)s&start_time=%(start_time)s&end_time=%(end_time)s">
#%(script)s?server=image&dataset=%(dataset)s&start_time=%(start_time)s&end_time=%(end_time)s</a>
#		"""%dReplace)
#			
#		pout("</li>")
		

	pout("</ul>")
	
	pout("""
<h2>Das 2.2 Service Queries</h2>
<p>Though no examples are provided here, the 2.2 service protocol is supported
by this server and will be <em>supported indefinitly</em> for the benefit of current
client programs.
</p>""")

	
	
	if bHSubSys:
		pout("""
<h2>Helophysics API Support</h2>
<p>All queries rooted at <a href="%s/hapi">%s/hapi</a> will respond to
helophysics API requests as documented at 
https://github.com/hapi-server/data-specification</p>
"""%(dReplace["script"], dReplace["script"]))
		
		
	pout('''
</div>
</div>


<div class="footer">
  <div>More information about das2 can be found at:
  <a href="http://das2.org/">http://das2.org/</a>.</div>
  <div>%s</div>
</div>'''%os.getenv('SERVER_SIGNATURE'))

	pout('''
</body>
</html>''')
	
	return 0

	