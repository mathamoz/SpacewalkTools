#!/usr/bin/python
import os, sys, getpass, xmlrpclib, urllib
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-u", "--username", dest="username", help="Spacewalk Username", metavar="name")
parser.add_option("-p", "--password", dest="password", help="Spacewalk Password", metavar="pass")
parser.add_option("-c", "--channel", dest="channel", help="Configuration channel label (not name).", metavar="label")
parser.add_option("-s", "--src", dest="source", help="Source spacewalk server URL. eg: spacewalk.example.net", metavar="source")
parser.add_option("-d", "--dst", dest="destination", help="Destination spacewalk server URL. eg: spacewalk.example.net", metavar="destination")

(cfg, args) = parser.parse_args()

# Check to make sure the required params are set
if not cfg.username:
    parser.error("Username is required!  Specify with -u or --username")

if not cfg.channel:
    parser.error("You must specify the configuration channel!  Specify with -c or --channel")

if not cfg.source:
    parser.error("You must specify the source spacewalk server!  Specify with -s or --src")

if not cfg.destination:
    parser.error("You must specify the destination spacewalk server!  Specify with -d or --dst")

#
# Helper function for listing packages in a channel
#
def listPackages():
    return source_client.channel.software.listAllPackages(source_key, cfg.channel)

#
# Helper function for downloading a package
#
def downloadPackage(package_id):
    url = source_client.packages.getPackageUrl(source_key, package_id)
    bits = url.split("/")
    filename = bits[len(bits)-1]
    urllib.urlretrieve (url, filename)
    print "Pushing %s to spacewalk server" % filename
    os.system("echo %s | rhnpush --channel=%s  --server=http://%s/APP --stdin --username=%s --password=%s --tolerant --nosig" % (filename, cfg.username, cfg.password, cfg.channel, cfg.destination))
    os.remove(filename)

#
# Helper function for checking pkg existence on dest server
#
def checkDestination(name, version, release, arch):
    package = dest_client.packages.findByNvrea(dest_key, name, version, release, "", arch)

    if package:
    return True

    return False

#
# Poor mans start of the program.  Probably should use a main function...
#
source_spacewalk_url = "http://%s/rpc/api" % cfg.source
dest_spacewalk_url = "http://%s/rpc/api" % cfg.destination

# Prompt for user password if it wasn't supplied
# NB: Expected use of an arg passed password is via 
#     a script using a shared known password, not your password...
if not cfg.password:
    password = getpass.getpass()
    cfg.password = password
else:
    password = cfg.password

# Login to spacewalk
source_client = xmlrpclib.Server(source_spacewalk_url, verbose=0)
source_key = source_client.auth.login(cfg.username, password)

dest_client = xmlrpclib.Server(dest_spacewalk_url, verbose=0)
dest_key = dest_client.auth.login(cfg.username, password)

synced = 0
skipped = 0

packages = listPackages()

for package in packages:
    id = package.get("id")
    name = package.get("name")
    version = package.get("version")
    release = package.get("release")
    arch = package.get("arch_label")

    if checkDestination(name, version, release, arch):
        print "%s-%s exists at destination, skipping." % (name,version)
        skipped += 1
    else:
        downloadPackage(id)
        synced += 1

print "\n%s packages were synchronized, %s already existed and were skipped." % (synced, skipped)
source_client.auth.logout(source_key)
dest_client.auth.logout(dest_key)
