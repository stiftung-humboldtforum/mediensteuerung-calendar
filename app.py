import asyncio
import os
import ssl

import asyncclick as click
from aiomqtt import MqttError

from misc import logger
from mqtt_client import Client
from calendar_service import Calendar


async def run(ssl_context):
    loop = asyncio.get_running_loop()
    async with Client(
            os.environ['MQTT_HOSTNAME'],
            identifier='calendar',
            port=8883,
            keepalive=60,
            tls_context=ssl_context,
            max_concurrent_outgoing_calls=2000,
    ) as client:
        calendar = Calendar(client)
        await calendar.load_events()
        calendar_task = loop.create_task(calendar.start())
        client.pending_calls_threshold = 500
        await client.subscribe('api/calendar/update')
        try:
            async for message in client.messages:
                if message.topic.matches('api/calendar/update'):
                    await calendar.load_events()
        finally:
            calendar_task.cancel()


@click.command()
@click.option('--ca_certificate', default='/opt/tls/ca_certificate.pem')
@click.option('--client_certificate', default='/opt/tls/client_certificate.pem')
@click.option('--client_key', default='/opt/tls/client_key.pem')
async def main(ca_certificate, client_certificate, client_key):
    ssl_context = ssl.create_default_context(cafile=ca_certificate)
    ssl_context.load_cert_chain(
        client_certificate, client_key)
    # Reconnect with backoff instead of exiting on broker disconnect.
    while True:
        try:
            await run(ssl_context)
        except MqttError as e:
            logger.error('MQTT connection lost (%s); reconnecting in 5s', e)
            await asyncio.sleep(5)


if __name__ == '__main__':
    main()
