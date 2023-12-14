from bleak import BleakClient
import logging
import time
import asyncio


WRITE_UID = "00001f1f-0000-1000-8000-00805f9b34fb"
LOGGER = logging.getLogger(__name__)

bDebug = False


def setup(hass, config):
    """Set up is called when Home Assistant is loading our component."""

    #LOGGER.debug(hass.config.time_zone)

    async def updateDevice(deviceAddress,actualPass=1,maxPass=1,bDebug=False,waitTime=10):
        LOGGER.debug("%s : Passe %s/%s",deviceAddress,actualPass,maxPass)
        try:
            async with BleakClient(deviceAddress,timeout=waitTime) as client:
                if not client.is_connected :
                    LOGGER.debug("Connecting to : %s",deviceAddress)
                    await client.connect()

                if bDebug : 
                    LOGGER.debug("Time : %s",time.time())
                    LOGGER.debug("Local Time : %s",time.localtime())
                    LOGGER.debug("Local Time : %s",time.mktime(time.localtime()))
                    LOGGER.debug("GM Time : %s",time.gmtime())
                    LOGGER.debug("GM Time : %s",time.mktime(time.gmtime()))
                    LOGGER.debug("DayLight : %s",time.daylight)
                

                #timestamp = time.time() + (time.daylight * 3600)
                timestamp = time.time() + time.mktime(time.localtime()) - time.mktime(time.gmtime()) #+ (time.daylight * 3600)
                if bDebug :
                    LOGGER.debug("Timestamp : %s",timestamp)

                blk = []
                blk.append(int("23",16))
                blk.append(int(timestamp) & 0xff)
                blk.append((int(timestamp) >> 8) & 0xff)
                blk.append((int(timestamp) >> 16) & 0xff)
                blk.append((int(timestamp) >> 24) & 0xff)

                LOGGER.debug("Sending : %s",blk)
                retour = await client.write_gatt_char(WRITE_UID,bytearray(blk),True)
                LOGGER.debug("Answer to write %s",retour)
                bOk = True
                LOGGER.debug("Disconnecting")
                await client.disconnect()
        except Exception as e:
            LOGGER.error("updateDevice " + deviceAddress + " - Exception :" + repr(e))
            if actualPass < maxPass:
                await asyncio.sleep(1)
                await updateDevice(deviceAddress=deviceAddress,actualPass=actualPass+1,maxPass=maxPass,waitTime=waitTime,bDebug=bDebug)

    async def getDeviceChar(deviceAddress,actualPass=1,maxPass=1,waitTime=10):
        LOGGER.debug("%s : Passe %s/%s",deviceAddress,actualPass,maxPass)
        try:
            async with BleakClient(deviceAddress,timeout=waitTime) as client:
                if not client.is_connected :
                    LOGGER.debug("Connecting to : %s",deviceAddress)
                    await client.connect()


                LOGGER.debug("Services:")
                for service in client.services:
                    LOGGER.debug("- Service : %s",service)
                    for char in service.characteristics:
                        value=await client.read_gatt_char(char.uuid)
                        LOGGER.debug("      -> %s ==> %s",char,value)
                    
                LOGGER.debug("Disconnecting")
                await client.disconnect()
        except Exception as e:
            LOGGER.error("getDeviceChar " + deviceAddress + " - Exception :" + repr(e))
            if actualPass < maxPass:
                await asyncio.sleep(1)
                await getDeviceChar(deviceAddress=deviceAddress,actualPass=actualPass+1,maxPass=maxPass,waitTime=waitTime)

    async def handle_atc_time(call):
        """Handle the service call."""
        LOGGER.debug("handle_atc_time called with %s",repr(call))
        bt_address = call.data.get("device_address", "")
        wait_time = call.data.get("wait_time", "10")
        await updateDevice(bt_address,maxPass=3,waitTime=wait_time,bDebug=True)

    async def handle_atc_characteristics(call):
        """Handle the service call."""
        LOGGER.debug("handle_atc_time called with %s",repr(call))
        bt_address = call.data.get("device_address", "")
        wait_time = call.data.get("wait_time", "10")
        await getDeviceChar(bt_address,maxPass=3,waitTime=wait_time)
        

    hass.services.register("atc_time", "set_atc_time", handle_atc_time)
    hass.services.register("atc_time", "get_characteristics", handle_atc_characteristics)

    # Return boolean to indicate that initialization was successful.
    return True