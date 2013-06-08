#!/usr/bin/env python

##############################################################
##      DNS Primary Secondary Proxy                         ##
##      Used for having a single IP for two DNS servers     ##
##############################################################

#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

###
# @author Karl Kloppenborg
# @company Invention Labs

import socket
import asyncore
import yaml

class dnsProxyServer(asyncore.dispatcher):

    config = None ##Holder waiting for the configuration settings

    def __init__(self, config):
        asyncore.dispatcher.__init__(self) #init the parent
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.set_reuse_addr()
        self.bind((config['binding_host'], config['binding_port']))
        print "Initialized the socket!"
        self.config = config
    
    def handle_connect(self):
        print "Connected!"
        pass

    def handle_read(self):
        data,addr = self.recvfrom(8192)
        print "Reading from IP %s" % repr(addr)

        ## Initialize the first proxy, we can push to that.
        try:
            print "Opening socket to primary DNS"
            p1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM);
            p1.settimeout(5.0)
            ##Send fourth the request
            print "Sending data to primary DNS"
            p1.sendto(data, (config['dns_primary']['ip_address'], config['dns_primary']['port']));
            ##Get the response
            print "Recieving from primary DNS"
            recv_data, p1addr = p1.recvfrom(8192)

            print "Passing back to client the response"
            p1.close() ##Close the connection
        except:
            try:
                print "Primary DNS failed, lets try the secondary"
                p1.close() ##Close the connection

                p2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM);
                p2.settimeout(5.0)
                ##Send the request for the second time
                p2.sendto(data, (config['dns_secondary']['ip_address'], config['dns_secondary']['port']));
                ##Get the response
                print "Recieving from secondary DNS"
                recv_data, p2addr = p2.recvfrom(8192)

                print "Passing back to the client"
                p2.close() ##Close the connection

            except:
                print "All DNS servers failed, returning the client with nothing and exiting the connection"
                p2.close() ##Ensure this is closed too
                return ## Return, we don't want to help the client.

        print "We finally got here"

        ##Push back to the client
        self.sendto(recv_data, addr)

    def handle_close(self):
        print 'handle_close'
        self.close()

if __name__ == "__main__":

    try:
        #Open the configuration file so we can get the details needed to handle the queries
        configStream = open("config.yml", "r")
        config = yaml.load(configStream)

        print "Starting the DNS Proxy server"
        server = dnsProxyServer(config) 
        asyncore.loop()
    except (KeyboardInterrupt, SystemExit):
        print "\n\nShutting down DNS Proxy....\n\n"
