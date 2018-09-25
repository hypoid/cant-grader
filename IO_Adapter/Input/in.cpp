
/*******************************************************************************
Copyright (c) 1983-2012 Advantech Co., Ltd.
********************************************************************************
THIS IS AN UNPUBLISHED WORK CONTAINING CONFIDENTIAL AND PROPRIETARY INFORMATION
WHICH IS THE PROPERTY OF ADVANTECH CORP., ANY DISCLOSURE, USE, OR REPRODUCTION,
WITHOUT WRITTEN AUTHORIZATION FROM ADVANTECH CORP., IS STRICTLY PROHIBITED. 

================================================================================
REVISION HISTORY
--------------------------------------------------------------------------------
$Log:  $

--------------------------------------------------------------------------------
$NoKeywords:  $
*/
/******************************************************************************
*
* Windows Example:
*    StaticDI.cpp
*
* Example Category:
*    DIO
*
* Description:
*    This example demonstrates how to use Static DI function.
*
* Instructions for Running:
*    1. Set the 'deviceDescription' for opening the device. 
*    2. Set the 'startPort' as the first port for Di scanning.
*    3. Set the 'portCount' to decide how many sequential ports to operate Di scanning.
*
* I/O Connections Overview:
*    Please refer to your hardware reference manual.
*
******************************************************************************/
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include "../inc/compatibility.h"
#include "../inc/bdaqctrl.h"
using namespace Automation::BDaq;
//-----------------------------------------------------------------------------------
// Configure the following three parameters before running the demo
//-----------------------------------------------------------------------------------
//#define  deviceDescription  L"DemoDevice,BID#0"
#define  deviceDescription  L"USB-4750,BID#0"

typedef unsigned char byte;

int32    startPort = 0;
int32    portCount = 1;

inline void waitAnyKey()
{
   do{SLEEP(1);} while(!kbhit());
} 

int main(int argc, char* argv[])
{
   ErrorCode        ret = Success;
   // Step 1: Create a 'InstantDiCtrl' for DI function.
   //printf(" Reading ports' status is in progress, any key to quit !\n\n");
   InstantDiCtrl * instantDiCtrl = AdxInstantDiCtrlCreate();
   do
   {
      // Step 2: select a device by device number or device description and specify the access mode.
      // in this example we use AccessWriteWithReset(default) mode so that we can 
      // fully control the device, including configuring, sampling, etc.
      DeviceInformation devInfo(deviceDescription);
      ret = instantDiCtrl->setSelectedDevice(devInfo);
      CHK_RESULT(ret);

      // Step 3: Read DI ports' status and show.
      //printf(" Reading ports' status is in progress, any key to quit !\n\n");
      byte  bufferForReading[64] = {0};//the first element of this array is used for start port
      do
      {
         ret = instantDiCtrl->Read(startPort,portCount,bufferForReading);
         CHK_RESULT(ret);  
         //Show ports' status
         printf("0x%X\n", bufferForReading[0]);
         //for ( int32 i = startPort;i < startPort+portCount; ++i)
         //{
         //   printf(" DI port %d status is: 0x%X\n\n", i, bufferForReading[i-startPort]);
         //}
         //SLEEP(0.01);
      }while(true);//!kbhit());

   }while(false);

	// Step 4: Close device and release any allocated resource.
	instantDiCtrl->Dispose();

	// If something wrong in this execution, print the error code on screen for tracking.
   if(BioFailed(ret))
   {
      printf(" Some error occurred. And the last error code is Ox%X.\n", ret);
      waitAnyKey();
   }
   return 0;
}
