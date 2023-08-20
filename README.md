# Subnetting-Algorithm
Subnetting Algorithm originally created for aid in the OpenConduit software tool used by the CyPres Research Team at Texas A&amp;M University.

Between subnets in a network, there is always a subtraction gap of at the very least three from the last usable IP address in one subnet to the first usable IP address in the next subnet. This is caused by the broadcast and network addresses in a subnet not being usable. The only exception to this would of course be the complete last usable value (host bits wise) of .254 or where the last usable IPs in a /24 network technically include .254 even if .254 isn't specifically used or listed. This is fixed by appending 257.

Exception caused by the number of necessary subnet "pairs" for this operation being equivalent to the number of subnets. It should be noted that this number of subnet "pairs" is not representative of all possible subnet pairing combinations, but rather the successive subnet pairs in each unique network's ascendingly sorted list of IP host bits. This exception is solved by appending the value of 257 to each of the lists to act as a pseudo extra subnet that can also be used to signify the end of the list.

Assumptions:
- Proper subnetting practices where undertaken when giving nodes within the network their IP addresses.
- No supernetting was involved for this network and the number of network bits for each network is 24, i.e., a CIDR of /24.

Start:
- Based on IP values given in the provided data, determine the number of unique networks, i.e., the number IPs whose first 24 network bits are unique.
- For each unique network, create a list of their IPs' host bit values (ipHostBits), then sort each so that they are in ascending order. Append a value of 257 to each.
- For each unique network, loop through the ipHostBits list, appending each value whose result from a subtraction of their value and previous value is equivalent to 1 to a new subnet IP list (subnetIPs). There is an exception for the first value or index of 0, which is just appended since this subtraction operation is not possible.
- If the aforementioned subtraction operation result is 1 or the index is 0, the values from ipHostBits list is appended to the subnetIPs list.
- If the aforementioned subtraction operation result is a value of 3 or greater, then the current value from the ipHostBits list represents the first usable IP address in the next subnet.
- Using this value and the original subnet's subnet address, the subnet CIDR prefix can be determined.
- The subnet's (for which the subnetIPs list has been filled) subnet address can be determined by taking the length of the recently created subnetIPs list, then subtracting the index value of the next subnet's first usable IP in the ipHostBits list by this length. The resulting subtraction value is as an index value in the ipHostBits list again. This will give us the first usable IP address of the original subnet, which if subtracted by 1, will give us the subnet's subnet address.
- By subtracting 32 by the result of the log of base 2 for the next subnet's first usable IP minus the first subnet's subnet address minus one (32 - log2(subnet2IP1 - subnet1SubnetIP - 1)), we can then get our subnet CIDR. We can also ensure that the size of the subnet does not exceed the available/usable IP addresses by converting the result of the log of base two to an integer using int() and then subtracting. Using the int causes the result to truncate and therefore not exceed the bounds of usable IPs.
- With this, we can be accurate to all subnets within the network with the exception of the final subnet. To fine tune the accuracy as much as possible, we can add an if statement that checks if the final subnet only has two addresses, and if the nodes to which these addresses belong to are both routers or one is a firewall and the other is a router, we can be confident in knowing that the subnet has a /30 CIDR. (Based on typical network architecture.) However, again, there is still the possibility for error in getting the subnet size wrong, as the last subnet, if not the exception just mentioned, will always end up being as large as allowably possible. This could easily be corrected, however, by implementing user validation, which would allow the user to change the necessary subnet CIDR if they saw any errors in the subnet values.
- Once the elif statement is exited (the elif statement being for the case of the subtraction difference between IP host bits being a value of three or greater), the subnetIPs list is emptied and so is the subnet mask string for the next subnet.
- If a value of 2 or anything less than zero is somehow found in the IP host bits list, then an error is raised.

