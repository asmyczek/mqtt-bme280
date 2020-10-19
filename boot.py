import config
import network
import esp
import gc
import webrepl


esp.osdebug(None)
gc.collect()


def setup_network():
    # Disable ap
    print('Disabling AP')
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)

    # Connect to home wifi
    wifi_if = network.WLAN(network.STA_IF)
    wifi_if.active(True)
    if not wifi_if.isconnected():
        print('Connecting to Smyczek')
        wifi_if.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        while not wifi_if.isconnected():
            pass
    print('Network configuration:', wifi_if.ifconfig())


# Start service
setup_network()
webrepl.start()

