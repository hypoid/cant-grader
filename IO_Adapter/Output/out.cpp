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
*    StaticDO.cpp
*
* Example Category:
*    DIO
*
* Description:
*    This example demonstrates how to use Static DO function.
*
* Instructions for Running:
*    1. Set the 'deviceDescription' for opening the device. 
*    2. Set the 'startPort'as the first port for Do .
*    3. Set the 'portCount'to decide how many sequential ports to operate Do.
*
* I/O Connections Overview:
*    Please refer to your hardware reference manual.
*
******************************************************************************/
#include <stdlib.h>
#include <stdio.h>
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
   // Step 1: Create a instantDoCtrl for DO function.
   InstantDoCtrl * instantDoCtrl = AdxInstantDoCtrlCreate();
   do
   {
      // Step 2: Select a device by device number or device description and specify the access mode.
      // in this example we use AccessWriteWithReset(default) mode so that we can 
      // fully control the device, including configuring, sampling, etc.
      DeviceInformation devInfo(deviceDescription);
      ret = instantDoCtrl->setSelectedDevice(devInfo);
      CHK_RESULT(ret);

      // Step 3: Write DO ports
      byte  bufferForWriting[64] = {0};//the first element is used for start port
      //for ( int32 i = startPort;i < portCount + startPort; ++i)
      //{
      //   printf(" Input a 16 hex number for DO port %d to output(for example, 0x00): ", i);
      //   scanf("0%x", &bufferForWriting[i-startPort]);
      //}
      bufferForWriting[0] = 0x02;
      ret = instantDoCtrl->Write(startPort,portCount,bufferForWriting );
      CHK_RESULT(ret);
      SLEEP(1);
      bufferForWriting[0] = 0x00;
      ret = instantDoCtrl->Write(startPort,portCount,bufferForWriting );
      CHK_RESULT(ret);

      // Read back the DO status. 
      // Note: 
      // For relay output, the read back must be deferred until the relay is stable.
      // The delay time is decided by the HW SPEC.
      //BYTE bufferForReading[64] = {0};
      //ret = instantDoCtrl->Read( startPort,portCount,bufferForReading );
      //if(BioFailed(ret))
      //{
      //    break;
      //}
      // Show DO ports' status
      //for ( LONG i = startPort;i < portCount + startPort; ++i)
      //{
      //    printf("Now, DO port %d status is:  0x%X\n\n", i, bufferForReading[i-startPort]);
      //}
   }while(false);

	// Step 4: Close device and release any allocated resource.
	instantDoCtrl->Dispose();

	// If something wrong in this execution, print the error code on screen for tracking.
   if(BioFailed(ret))
   {
      printf(" Some error occurred. And the last error code is Ox%X.\n", ret);
      waitAnyKey();
   }
   //waitAnyKey();
   return 0;
}
