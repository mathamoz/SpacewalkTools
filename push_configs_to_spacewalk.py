#!/usr/bin/python
import os, getpass, xmlrpclib
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-u", "--username", dest="username", help="Spacewalk Username", metavar="name")
parser.add_option("-P", "--password", dest="password", help="Spacewalk Password", metavar="pass")
parser.add_option("-f", "--file", dest="file", help="Path to config file to push", metavar="name")
parser.add_option("-d", "--directory", dest="dir", help="Directory containing config file(s) to push", metavar="path")
parser.add_option("-l", "--location", dest="location", help="Base path for all files (eg. /usr/share/tomcat6/portal/)", metavar="path")
parser.add_option("-c", "--channel", dest="channel", help="Destination configuration channel label (not name).", metavar="label")
parser.add_option("-o", "--owner", dest="owner", help="Owner of the file(s)", metavar="name")
parser.add_option("-g", "--group", dest="group", help="Group of the file(s)", metavar="name")
parser.add_option("-p", "--permissions", dest="permissions", help="Permissions for the file(s) (eg. 644)", metavar="name")
parser.add_option("-s", "--server", dest="server", help="Spacewalk Server", metavar="server")

(cfg, args) = parser.parse_args()

# Check to make sure the required params are set
if not cfg.username:
	parser.error("Username is required!  Specify with -u or --username")

if not cfg.server:
    parser.error("Server is required!  Specify with -s or --server")

if not cfg.file and not cfg.dir:
	parser.error("Either a config file or a directory containing config files is required, you've specified neither. -h for help")
elif cfg.dir and cfg.dir[len(cfg.dir)-1] != '/':
	cfg.dir += "/"

if not cfg.location:
	parser.error("You must specify the base path for the file(s) you are uploading!  Specify with -l or --location")
elif cfg.location[len(cfg.location)-1] != '/':
	# Add a trailing slash if it was not specified
	cfg.location += "/"

if not cfg.channel:
	parser.error("You must specify the destination configuration channel!  Specify with -c or --channel")

# Warn about these params and set their default
meta = [['owner','root'],['group','root'],['permissions','600']]

for attr in meta:
	if not getattr(cfg, attr[0]):
		print "** Warning: %s not specified, using default of %s." % (attr[0],attr[1])
		setattr(cfg, attr[0], attr[1])

#
# Helper function for pushing the files
#
def push_file(file, contents):
	full_path = cfg.location + file
	client.configchannel.createOrUpdatePath(key, cfg.channel, full_path, False,
		{"contents": contents, "owner": cfg.owner, "group": cfg.group,
		 "permissions": cfg.permissions, "selinux_ctx": "", "macro-start-delimiter": "",
		 "macro-end-delimiter": "", "revision": ""})

spacewalk_url = "http://%s/rpc/api" % cfg.server

# Prompt for user password if it wasn't supplied
# NB: Expected use of an arg passed password is via 
#     a script using a shared known password, not your password...
if not cfg.password:
	password = getpass.getpass()

# Login to spacewalk
client = xmlrpclib.Server(spacewalk_url, verbose=0)
key = client.auth.login(cfg.username, password)

if cfg.file:
	print "Pushing %s to server..." % cfg.file
	f = open(cfg.file, 'r')
	contents = f.read()
	f.close()
	push_file(cfg.file, contents)
else:
	files = os.listdir(cfg.dir)
	for file in files:
		print "Pushing %s to server..." % file
		f = open(cfg.dir + file, 'r')
		contents = f.read()
		f.close()
		push_file(file, contents)

client.auth.logout(key)

