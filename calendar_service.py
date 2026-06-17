import asyncio
from datetime import datetime
import json

from misc import logger, localizer
from mqtt_client import Client
from db import db
from event import Event, EventActions


class Calendar:
    def __init__(self, client: Client):
        self.client = client
        self.message_queue = []
        self.events = {}

    def callback(self, edge, type, id, method):
        logger.debug('Event %s - %s with id "%s": %s', edge, type, id, method)
        if method == '':
            method = 'clear'
        self.message_queue.append(
            (f'calendar/{edge}/{type}/{method}', json.dumps({'data': {'id': id}})))

    async def load_events(self):
        logger.debug('Loading')
        cursor = db.events.find()
        new_events = {}
        async for event in cursor:
            logger.debug('Create event %s', event)
            new_events[event['_id']] = Event(
                start=event['start'],
                end=event['end'],
                allDay=event['allDay'],
                rrule=event['rrule'],
                duration=event['duration'],
                type=event['extendedProps']['type'],
                id=event['extendedProps']['id'],
                actions=EventActions(**event['extendedProps']['actions']),
                cb=self.callback
            )

        for _id, event in list(self.events.items()):
            if _id not in new_events:
                event.is_happening = False
                del self.events[_id]

        for _id, event in new_events.items():
            if _id not in self.events:
                self.events[_id] = event
            else:
                self.events[_id].set_options(event)

        logger.debug('Loaded %s event(s)', len(self.events))

    async def tick(self):
        now = localizer.localize(datetime.now())
        for event in self.events.values():
            # One malformed event must not kill the whole 5s evaluation loop.
            try:
                event.update(now=now)
            except Exception as e:
                logger.exception(e)

    async def start(self):
        while True:
            await self.tick()
            await asyncio.sleep(5)
            # FIFO: preserve the order edges were produced (pop() drained LIFO,
            # reordering start/end within a tick).
            for _ in range(len(self.message_queue)):
                message = self.message_queue.pop(0)
                await self.client.publish(*message, qos=1)
