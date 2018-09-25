#include <stdlib.h>
#include <stdio.h>
#include "../inc/compatibility.h"
#include "../inc/bdaqctrl.h"
using namespace Automation::BDaq;
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
   InstantDoCtrl * instantDoCtrl = AdxInstantDoCtrlCreate();
   do
   {
      DeviceInformation devInfo(deviceDescription);
      ret = instantDoCtrl->setSelectedDevice(devInfo);
      CHK_RESULT(ret);

      byte  bufferForWriting[64] = {0};
      bufferForWriting[0] = 0x04;
      ret = instantDoCtrl->Write(startPort,portCount,bufferForWriting );
      CHK_RESULT(ret);


   }while(false);

	instantDoCtrl->Dispose();

   if(BioFailed(ret))
   {
      printf(" Some error occurred. And the last error code is Ox%X.\n", ret);
      waitAnyKey();
   }
   return 0;
}
