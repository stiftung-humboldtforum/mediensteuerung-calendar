from datetime import datetime
from typing import Callable

from dateutil import parser
from dateutil.relativedelta import relativedelta
import dateutil.rrule
from pytz import timezone, tzinfo

from misc import localizer, logger


class EventActions:
    def __init__(self, start, end):
        self.start = start
        self.end = end


class Event:
    def __init__(self,
                 start: str | None = None,
                 end: str | None = None,
                 allDay: bool | None = None,
                 rrule: str | None = None,
                 duration: float | None = None,
                 type: str | None = None,
                 id: int | None = None,
                 actions: EventActions | None = None,
                 cb: Callable | None = None):
        assert start is not None
        assert end is not None
        assert allDay is not None
        assert type is not None
        assert id is not None
        assert actions is not None

        self.start = parser.parse(start)
        self.end = parser.parse(end)
        self.allDay = allDay
        if rrule is not None:
            values = rrule.split(';')
            for i, value in enumerate(values):
                if value.startswith('UNTIL') and not value.endswith('Z'):
                    logger.debug('Hotfix UTC UNTIL')
                    values[i] = value + 'Z'
            self.rrule = dateutil.rrule.rrulestr(';'.join(values))
        else:
            self.rrule = None
        if duration is None:
            self.duration = relativedelta(self.end, self.start)
        else:
            self.duration = relativedelta(seconds=int(duration / 1000))
        self.type = type
        self.id = id
        self.actions = actions
        self.cb = cb
        self._is_happening = False

    @property
    def is_happening(self):
        return self._is_happening

    @is_happening.setter
    def is_happening(self, val):
        if val != self._is_happening:
            if self.cb is not None:
                edge = 'start' if val else 'end'
                action = self.actions.start if val else self.actions.end
                self.cb(edge, self.type, self.id, action)
            self._is_happening = val

    def update(self, now: datetime):
        start = self.start.replace(tzinfo=now.tzinfo)
        end = self.end.replace(tzinfo=now.tzinfo)
        if now > self.start and now < end:
            self.is_happening = True
            return
        elif self.rrule is not None:
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            if (start - self.duration).day != start.day:
                today -= relativedelta(start, start - self.duration)
            if occurrence := self.rrule.after(today):
                end = occurrence + self.duration
                if self.id == 72:
                    logger.info('%s %s\n%s\n%s\n%s', now > occurrence,
                                now < end, now, occurrence, end)
                if now > occurrence and now < end:
                    self.is_happening = True
                    return
        self.is_happening = False

    def set_options(self, event: 'Event'):
        self.start = event.start
        self.end = event.end
        self.allDay = event.allDay
        self.rrule = event.rrule
        self.duration = event.duration
        self.type = event.type
        self.id = event.id
        self.actions = event.actions
        self.cb = event.cb
