import math
import sys
import pandas as pd
from pathlib import Path
from dataclasses import dataclass, field
from ipaddress import IPv4Address

class ExcelFileReader():
    def __init__(self, accessedDir: Path, fileName: str, onlyTheseColumns: list):
        self.accessedDir = accessedDir
        self.fileName = fileName
        self.onlyTheseColumns = onlyTheseColumns
        self.data = None
        self.__readData()
    
    # Reads Excel file into a pandas dataframe.
    def __readData(self):
        fullPath = self.accessedDir.joinpath(self.fileName)
        self.data = pd.read_excel(fullPath, usecols=self.onlyTheseColumns, engine="openpyxl")
    
    # Dataframe Getter
    def getData(self) -> pd:
        return self.data
    
    # Function that takes Excel cells that should be lists but are strings and reformats to an actual list
    def reformatData(self, columnsToFormat: list, sep: list, replaceVal: list, intToSliceChars: list): # TODO: Needs further testing...
        for i, element in enumerate(columnsToFormat):
            self.data[element] = self.data[element].apply(lambda x: 
                                self.__reformatter(x, sep[i], replaceVal[i], intToSliceChars[i]))
    
    # Sub-function that takes strings and removes/replaces specified characters
    def __reformatter(self, stringVal: str, sep: list, replaceVal: list, intToSliceChars: list) -> str: #TODO: Needs further testing...
        if intToSliceChars:
            stringVal = stringVal[intToSliceChars:-intToSliceChars]
        
        stringVal = stringVal.replace(replaceVal,"").split(sep)
        return stringVal



class CreateNetwork():
    def __init__(self, npviewData: pd):
        self.npviewData = npviewData
        self.nodeDict = dict() # Dictionary that stores CoreNode objects
        self.networkAndHostBits = dict() # Dictionary that stores unique networks and lists of their host bits
        self.subnetIPs = list() # Amendable list of IPs for a subnet
        self.subnetMask = str() # Amendable string of a subnet's subnet mask/CIDR
    
    # Function used to create nodes from the NP-View dataframe data specifically
    def assetInventoryNodes(self):
        for node, type, ipList in self.npviewData.to_numpy():
            self.nodeCreation(node, type, ipList, None)
    
    """The function that passes its parameters to the Interface and CoreNode dataclasses.
    Each Interface in a specific node is added to an Interface list in the CoreNode dataclass.
    The name of the node is used as a key in a dictionary, while its corresponding CoreNode object is
    the stored value."""
    def nodeCreation(self, node: str, type: str, ipList: list, subnet: str = None):
        interfaceList = [Interface(ip, subnet) for ip in ipList]
        self.nodeDict[node] = CoreNode(interfaceList, type)

    # Node Dictionary Getter
    def getNodeDict(self) -> dict:
        return self.nodeDict
    
    # START OF ALGORITHM FUNCTIONS
    """Function finds all the unique network bits (first 24 bits) in an IPv4
    address in order to determine the number of different networks in the overall
    network topology. These networks are then used as keys in a dictionary, where
    there values are a list of each networks host bits. At the end, this list has
    a value of 257 appended to it and is then sorted to be in ascending order."""
    def findAndSortAllNetworks(self):
        for nodes in self.nodeDict.values():
            for interface in nodes.interfaceList:
                ipInDecimal = (int(IPv4Address(interface.ipaddress)) & 
                                int(IPv4Address("255.255.255.0")))
                ipDiff = int(IPv4Address(interface.ipaddress)) - ipInDecimal
            
                if ipInDecimal in self.networkAndHostBits.keys():
                    self.networkAndHostBits[ipInDecimal].append(ipDiff)
                else:
                    self.networkAndHostBits.update({ipInDecimal: [ipDiff]})
        
        for ipList in self.networkAndHostBits.values():
            ipList.append(257)
            ipList.sort(key = int)
    
    """Function that determines the subnets of the network topology based on the given
    IP and device type information given."""
    def subnetDetermination(self):
        for network, ipList in self.networkAndHostBits.items():
            try:
                if len(ipList) == 1:
                    raise Exception("Subnetting Error: there exists only one IP for a subnet.")
                for i, ip in enumerate(ipList):
                    # First index value in list or subtraction of successive IP host bits returns a 1
                    if (
                        i == 0 or 
                        ip - ipList[i-1] == 1
                    ):
                        self.subnetIPs.append(str(IPv4Address(network + ip)))
                        continue
                    # When subtraction of successive IP host bits returns a value of three or greater
                    elif ip - ipList[i-1] >= 3:
                        self.__subnetMaskGeneration(
                            ip, # Parameter for current IP host bit value
                            ipList[i-len(self.subnetIPs)] - 1, # Parameter for subnet host bit value
                            ip - ipList[i-1] # Parameter for subnet gap value
                        )

                        ipOfSubnet = f"{IPv4Address(network + (ipList[i-1] - len(self.subnetIPs)))}{self.subnetMask}"
                        self.__addSubnetsToNodes(ipOfSubnet)

                    else:
                        raise Exception("Subnetting Error: improper address assignments")

                    # Resetting the subnet IP list and subnet mask string value for use in the next iterations subnet
                    self.subnetIPs.clear()
                    self.subnetMask = str()

                    """Continues unless the current IP value is the sentinel value of 257.
                    The value of 257 is needed since this algorithm is requires the number
                    of successive subnet pairs to be equal to the number of real subnets. By
                    adding a value 257, we add a pseudo subnet (one that is not possible and
                    not real) so that the number of pairs is equivalent to the number of real subnets."""
                    if ip != 257:
                        self.subnetIPs.append(str(IPv4Address(network + ip)))
            
            except Exception:
                sys.exit(1)
    
    """Sub-function where the math behind the algorithm that allows a subnet mask's value
    to be found is. By using the value of the current IP (the IP which caused the gap, therefore not
    being in the same subnet), then subtracting this by the subnet address' host bit value and a further
    value of 1, we obtain the total number of IPs used in the subnet, including the subnet and broadcast addresses.
    If the log of base two is taken for the result of this subtraction, we get the exponent for the result. By
    subtracting 32 by this exponent value, the CIDR prefix for the subnet can be obtained."""
    def __subnetMaskGeneration(self, currentIP: str, subnetHostVal: str, subnetGapVal: str) -> str:
        # Nested if statements that check for the last subnet exception case
        if (
            len(self.subnetIPs) == 2 and 
            currentIP == 257 and 
            subnetGapVal > 3
        ):
            if self.__slashThirtyCase(): # Function returns a True or False boolean value
                self.subnetMask = "/30"
    
        if not self.subnetMask: # Empty strings are false
            mathForSubnet = math.log2(currentIP - subnetHostVal - 1)
            """int() used here in order to ensure that any non-whole numbers produced from the
            log base two (caused by the last subnet given not having a base 2 number of IPs) will
            be truncated, meaning the subnet will be able to fit within the confines of the available 
            and allowable IPs left."""
            self.subnetMask = f"/{(32 - int(mathForSubnet))}"

    """/30 exception sub-function used to narrow down the possibility of an incorrect subnet CIDR value being given.
    If the there are only two devices, the subnet gap is greater than three, and the sentinel IP is being
    used, we need to check if the last two devices are just routers and or firewalls. Router to router and
    firewall to router should always be /30, which is why this case is applied. However, the logic flaw here
    is that firewall to firewall combination could also be chosen, since they often contain other devices in
    their subnets. If not all the devices for a firewall to firewall subnet have been added, this could occur."""
    def __slashThirtyCase(self) -> bool:
        trueCount = 0
        
        # Only searches nodes of these two device types
        for node in self.nodeDict.values():
            if (
                node.deviceType == "router" or
                node.deviceType == "firewall"
            ):
                for interface in node.interfaceList:
                    if interface.ipaddress in self.subnetIPs:
                        trueCount += 1

                        # Exits once the two IPs have been matched with two firewall or router nodes
                        if trueCount == 2:
                            return True
        return False
    
    """Sub-function used to the subnet mask to their corresponding Interfaces within
    the CoreNodes."""
    def __addSubnetsToNodes(self, ipOfSubnet: str):
        ipCount = 0

        for node in self.nodeDict.values():
            for interface in node.interfaceList:
                if interface.ipaddress in self.subnetIPs:
                    interface.ipnetmask = ipOfSubnet
                    ipCount += 1

            if ipCount == len(self.subnetIPs):
                break
    # END OF ALGORITHM FUNCTIONS

# TODO: Add interface that allows user to correct and account for any possible subnetting errors!

# The Interface dataclass houses the IP Address and Netmask for an interface.
@dataclass
class Interface():
	ipaddress: str
	ipnetmask: str


"""The CoreNode dataclass houses each node's list of Interfaces 
dataclass instances and its device type."""
@dataclass
class CoreNode():
	interfaceList: list[Interface] = field(default_factory = list)
	deviceType: str = field(default_factory = str)
