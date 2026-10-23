"""Unit-Tests für Event.update (Serien-Termine).

Pinnt den Fix vom 2026-10-23 (Gesamt-Review R4): Serien, die über Mitternacht
laufen, starteten ab dem zweiten Tag erst um 00:00; Serien ab genau 00:00
feuerten nach dem ersten Tag nie. Die Regeln haben das Format, das das Frontend
mit rrule.js und tzid speichert.

Kein Broker, keine Datenbank nötig. Im calendar-Image ausführen:

    pip install pytest && python -m pytest tests/test_event.py -v
"""
from datetime import datetime

from event import Event, EventActions
from misc import localizer


def _serie(start, end, dtstart):
    edges = []
    event = Event(
        start=start, end=end, allDay=False,
        rrule=f'DTSTART;TZID=Europe/Berlin:{dtstart}\nRRULE:FREQ=DAILY',
        duration=None, type='location', id=1,
        actions=EventActions(start='shutdown', end='wake'),
        cb=lambda edge, *_: edges.append(edge))
    return event, edges


def _um(tag, stunde, minute=0):
    return localizer.localize(datetime(2026, 10, tag, stunde, minute))


def test_nachtserie_startet_am_zweiten_tag_puenktlich():
    event, edges = _serie('2026-10-01T20:00:00+02:00', '2026-10-02T08:00:00+02:00', '20261001T200000')
    event.update(_um(2, 19, 59))
    assert not event.is_happening
    event.update(_um(2, 20, 30))
    assert event.is_happening and edges == ['start']
    event.update(_um(3, 7, 59))
    assert event.is_happening
    event.update(_um(3, 8, 1))
    assert not event.is_happening and edges == ['start', 'end']


def test_serie_ab_mitternacht_feuert_auch_am_zweiten_tag():
    event, edges = _serie('2026-10-01T00:00:00+02:00', '2026-10-01T07:00:00+02:00', '20261001T000000')
    event.update(_um(2, 3))
    assert event.is_happening and edges == ['start']
    event.update(_um(2, 7, 1))
    assert not event.is_happening


def test_tagesserie_nach_ende_aus():
    event, _ = _serie('2026-10-01T10:00:00+02:00', '2026-10-01T12:00:00+02:00', '20261001T100000')
    event.update(_um(2, 11))
    assert event.is_happening
    event.update(_um(2, 12, 30))
    assert not event.is_happening
