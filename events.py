import sys
import time
import local_config


def make_brew_name_given_id():
    brew_name_given_id = {}
    for line in open(local_config.brew_id_fpath):
        var = line.strip().split()
        brew_name_given_id[var[0]] = ' '.join(var[1:])
    return brew_name_given_id


def get_brew_ids():
    return set(make_brew_name_given_id().keys())


def get_brew_name(brew_id):
    brew_name_given_id = make_brew_name_given_id()
    return brew_name_given_id[brew_id]


def add_brew(brew_id, brew_name):
    if brew_id in get_brew_ids():
        raise ValueError('%s already exists.\n%s: %s' % (brew_id, brew_id, get_brew_name(brew_id)))
    try:
        year = int(brew_id[-6:-2])
        month = int(brew_id[-2:])
        assert 2015 <= year < 2100 and 1 <= month <= 12, 'Brew id must end YYYYMM.'
    except:
        raise ValueError('Brew id must end YYYYMM.')

    with open(local_config.brew_id_fpath, 'a') as out:
        out.write('\t'.join([brew_id, brew_name]) + '\n')


def list_brews(time_frame='recent'):
    def is_recent(brew_id):
        brew_year = int(brew_id[-6:-2])
        brew_month = int(brew_id[-2:])
        now_year, now_month = time.localtime()[:2]
        return bool((brew_year == now_year and brew_month >= now_month - 3)
                    or (brew_year == now_year - 1 and brew_month >= now_month - 3 + 12))

    print
    for line in open(local_config.brew_id_fpath):
        var = line.strip().split()
        brew_id = var[0]
        brew_name = ' '.join(var[1:])
        if time_frame == 'recent' and not is_recent(brew_id):
            continue
        print '%s    %s' % (brew_id.ljust(30), brew_name)


def add_brew_event(brew_id, event, when='now'):
    assert brew_id in get_brew_ids(), 'Invalid brew_id.'
    if event_exists(brew_id, event):
        raise ValueError('Event already exists:\n%s\t%s\t%s'
                         % (brew_id, event, event_time(brew_id, event)))
    if when == 'now':
        when = time.time()
    else:
        when = time.mktime(time.strptime(when, '%m/%d/%y %I:%M %p'))

    with open(local_config.brew_events_fpath, 'a') as out:
        out.write('%s\t%s\t%f\n' % (brew_id, event, when))


def get_events():
    events = {brew_id: {} for brew_id in get_brew_ids()}
    for line in open(local_config.brew_events_fpath):
        brew_id, event, when = line.strip().split()
        events[brew_id][event] = float(when)
    return events


def get_brew_events(brew_id):
    return get_events()[brew_id]


def event_exists(brew_id, event):
    events = get_events()
    return event in events[brew_id]


def event_time(brew_id, event):
    events = get_events()
    return events[brew_id][event]

if __name__ == '__main__':
    usage = """
events.py action [args]

Actions:
    add_brew <brew_id> <brew_name>
    list_brews [recent, all] (default: recent)
    brew_in <brew_id>
    brew_out <brew_id>
    brew_racked <brew_id>
    add_brew_event <brew_id> <event> [MM/DD/YY HH:MM AM/PM]
"""
    if len(sys.argv) == 1:
        sys.exit(usage)
    action = sys.argv[1]

    if action == 'add_brew':
        assert len(sys.argv) >=4, usage
        brew_id = sys.argv[2]
        brew_name = ' '.join(sys.argv[3:])
        add_brew(brew_id, brew_name)

    elif action == 'list_brews':
        if len(sys.argv) == 2:
            list_brews()
        else:
            assert len(sys.argv) == 3, usage
            list_brews(sys.argv[2])

    elif action == 'brew_in':
        assert len(sys.argv) == 3, usage
        add_brew_event(sys.argv[2], 'in')

    elif action == 'brew_out':
        assert len(sys.argv) == 3, usage
        brew_id = sys.argv[2]
        if not event_exists(brew_id, 'in'):
            raise ValueError('Brew never put in.')
        add_brew_event(brew_id, 'out')

    elif action == 'brew_racked':
        assert len(sys.argv) == 3, usage
        brew_id = sys.argv[2]
        if not event_exists(brew_id, 'in'):
            raise ValueError('Brew never put in.')
        if event_exists(brew_id, 'out'):
            raise ValueError('Brew already out.')
        add_brew_event(brew_id, 'racked')

    elif action == 'add_brew_event':
        assert len(sys.argv) >= 3, usage
        brew_id, event = sys.argv[2:4]
        if len(sys.argv) == 4:
            add_brew_event(brew_id, event)
        else:
            assert len(sys.argv) == 7, usage
            when = ' '.join(sys.argv[4:])
            add_brew_event(brew_id, event, when)
