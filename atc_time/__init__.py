from bleak import BleakClient
import logging
import time

WRITE_UID = "00001f1f-0000-1000-8000-00805f9b34fb"
LOGGER = logging.getLogger(__name__)

def setup(hass, config):
    """Set up is called when Home Assistant is loading our component."""

    #LOGGER.debug(hass.config.time_zone)

    async def handle_atc_time(call):
        """Handle the service call."""
        bt_address = call.data.get("device_address", "")
       
        client = BleakClient(bt_address,None,None,30)
        
        
        bOk=False
        for x in range(60): #On test 10 connections
            if bOk == False :
                

                try:
                    LOGGER.debug("Connecting to : %s",bt_address)
                    await client.connect()

                    #timestamp = time.time() + (time.daylight * 3600)
                    timestamp = time.time() + time.mktime(time.localtime()) - time.mktime(time.gmtime()) + (time.daylight * 3600)
                    
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
                    time.sleep(1)
                    LOGGER.debug("Disconnecting")
                    await client.disconnect()
                except Exception as e:
                    LOGGER.debug(e)
                    time.sleep(1)

    hass.services.register("atc_time", "set_atc_time", handle_atc_time)

    # Return boolean to indicate that initialization was successful.
    return True