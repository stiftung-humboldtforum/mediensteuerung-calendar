import asyncio
import os
import ssl

import asyncclick as click

from mqtt_client import Client
from calendar_service import Calendar


@click.command()
@click.option('--ca_certificate', default='/opt/tls/ca_certificate.pem')
@click.option('--client_certificate', default='/opt/tls/client_certificate.pem')
@click.option('--client_key', default='/opt/tls/client_key.pem')
async def main(ca_certificate, client_certificate, client_key):
    ssl_context = ssl.create_default_context(cafile=ca_certificate)
    ssl_context.load_cert_chain(
        client_certificate, client_key)
    loop = asyncio.get_event_loop()
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
        async for message in client.messages:
            if message.topic.matches('api/calendar/update'):
                await calendar.load_events()
    await calendar_task


if __name__ == '__main__':
    main()
