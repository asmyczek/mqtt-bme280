import machine
import bme280
from umqtt.robust import MQTTClient
from ujson import dumps
import config
import uasyncio

I2C = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4))
BME = bme280.BME280(i2c=I2C)


def measure():
    t, p, h = BME.read_compensated_data()
    return {'temperature': t / 100, 'pressure': p // 25600, 'humidity': h // 1024}


class Client(object):

    def __init__(self):
        self._client = self._create_client()
        self._lights_callback = None

    def _create_client(self):
        try:
            client = MQTTClient('bme280-outside',
                                config.MQTT_HOST,
                                user=config.MQTT_USER,
                                password=config.MQTT_PASSWORD,
                                port=config.MQTT_PORT)
            client.set_callback(self.on_message)
            if not client.connect(clean_session=False):
                print("MQTT new session being set up.")
                client.subscribe('cmnd/{}/#'.format(config.MQTT_TOPIC), qos=1)
            return client
        except Exception as e:
            print(e)
            return None

    def check_msg(self):
        self._client.check_msg()

    def on_message(self, topic, message):
        print('{} - {}'.format(topic, message))
        if topic == 'cmnd/{}/sync'.format(config.MQTT_TOPIC):
            self.publish_stats(measure())
        else:
            print('Unrecognised topic {}.'.format(topic))

    def publish_stats(self, stats):
        if self._client:
            self._client.publish(topic='stats/{}/stats'.format(config.MQTT_TOPIC), msg=dumps(stats))

    def publish_status(self, status):
        if self._client:
            self._client.publish(topic='stats/{}/status'.format(config.MQTT_TOPIC), msg=status)

    def publish_error(self, error):
        if self._client:
            self._client.publish(topic='info/{}/error'.format(config.MQTT_TOPIC), msg=error, retain=False)

    def disconnect(self):
        self._client.disconnect()


CLIENT = Client()


async def start_mqtt_client():
    while True:
        CLIENT.check_msg()
        await uasyncio.sleep(1)
    CLIENT.disconnect()


async def start_sensor_check():
    while True:
        CLIENT.publish_stats(measure())
        await uasyncio.sleep(60)


def start_sensor():
    print('Starting BME280 sensor service.')
    print('Time: {}'.format(machine.RTC().datetime()))

    loop = uasyncio.get_event_loop()
    loop.create_task(start_mqtt_client())
    loop.create_task(start_sensor_check())

    try:
        loop.run_forever()
    except Exception as e:
        CLIENT.publish_status('INTERRUPTED')
        CLIENT.publish_error(e)
        print(e)
    finally:
        print('BME sensor service stopped.')


start_sensor()

