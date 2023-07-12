# HA_ATC_Time
Home Assistant service to update Time on ATC firmwares

## Installation
- copy the folder "atc_time" into *config/custom_components* in homeassistant
- add "atc_time:" entry into *config/configuration.yaml*
- restart HA

Now you can call the service from the developers tab or in yaml:
```
service: atc_time.set_atc_time
data:
  device_address: A4:C1:38:63:21:1D
```
