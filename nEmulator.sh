#!/bin/bash

#Number of parameters: 9
#Parameter:
#    $1: <emulator's receiving UDP port number in the forward (sender) direction>
#    $2: <receiver's network address>
#    $3: <receiver's receiving UDP port number>
#    $4: <emulator's receiving UDP port number in the backward (receiver) direction>
#    $5: <sender's network address>
#    $6: <sender's receiving UDP port number>
#    $7: <maximum delay of the link in units of millisecond>
#    $8: <packet discard probability>
#    $9: <verbose-mode> (Boolean: Set to 1, the network emulator will output its internal processing, one
                       #per line, e.g. receiving Packet seqnum /SACK seqnum, discarding Packet seqnum /SACK seqnum,
                       #forwarding Packet seqnum /SACK seqnum).

#For Python implementation
if [ "$#" -ne 9 ];
then
  echo "Error: Program takes 9 parameters"
  exit 1
fi

python3 network_emulator.py $1 $2 $3 $4 $5 $6 $7 $8 $9