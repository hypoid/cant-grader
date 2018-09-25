#!/bin/bash
cd /home/ubuntu/ADVANTECH_IO_ADAPTER/linux_driver_source_3.2.11.0_64bit/
cp inc/* /usr/include/
cp libs/* /usr/lib/
cd /home/ubuntu/ADVANTECH_IO_ADAPTER/linux_driver_source_3.2.11.0_64bit/drivers/driver_base/src/lnx_ko
make clean
make
make install
cd /home/ubuntu/ADVANTECH_IO_ADAPTER/linux_driver_source_3.2.11.0_64bit/drivers/usb4750/src/lnx_ko/
make clean
make
make install

