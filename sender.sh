#!/bin/bash


#Number of parameters: 5
#Parameter:
#    $1: <host  address  of  the  network  emulator>
#    $2: <UDP  port  number  used  by  the  emulator  to receive data from the sender>
#    $3: <UDP port number used by the sender to receive ACKs from the emulator>
#    $4: <timeout interval in units of millisecond>
#    $5: <name of the file to be transferred>


#For Python implementation
if [ "$#" -ne 5 ];
then
  echo "Program takes 5 parameters, <host  address  of  the  network  emulator>,  <UDP  port  number  used  by  the  emulator  to receive data from the sender>, <UDP port number used by the sender to receive ACKs from the emulator>, <timeout interval in units of millisecond> and <name of the file to be transferred>"
  exit 1
fi
python3 sender.py "$@"
