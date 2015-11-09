import sys
import temp_history
import local_config
import time
import events

def send_updates(hours_plotted, hours_to_email):
    plotting_interval = hours_plotted * 3600.0
    email_interval = hours_to_email * 3600.0
    while True:
        start = time.time() - plotting_interval
        send_plot(start, None)
        time.sleep(email_interval)

def send_plot(start, stop):
    th = temp_history.TempHistory(local_config.temp_history_fpath)
    th.plot_temp_history(
            start=start,
            stop=stop,
            email=True)
    print 'Email sent'


def send_brew_plot(brew_id):
    brew_events = events.get_brew_events(brew_id)
    start = brew_events['in']
    if 'out' in brew_events:
        stop = brew_events['out']
    else:
        stop = None
    event_times = [tme for name, tme in sorted(brew_events.items())]
    event_labels = [name for name, tme in sorted(brew_events.items())]
    th = temp_history.TempHistory(local_config.temp_history_fpath)
    th.plot_temp_history(
            start=start,
            stop=stop,
            title=events.get_brew_name(brew_id),
            event_times=event_times,
            event_labels=event_labels,
            email=True)
    print 'Email sent'


if __name__ == '__main__':
    usage = """
send_reports.py <action> [args]

Action options:
    regular <hours_plotted> <hours_between_emails>
    one <start> <stop>
    brew <id>
"""
    try:
        action = sys.argv[1].lower()
    except IndexError:
        sys.exit(usage)

    if action == 'regular':
        assert len(sys.argv) == 4, usage
        hours_plotted, hours_to_email = map(float, sys.argv[2:])
        send_updates(hours_plotted, hours_to_email)

    elif action == 'one':
        assert len(sys.argv) == 4, usage
        ends = sys.argv[2:]
        for i in range(2):
            if ends[i] == 'None':
                ends[i] = None
            else:
                ends[i] = float(ends[i])
        send_plot(*ends)

    elif action == 'brew':
        assert len(sys.argv) == 3, usage
        brew_id = sys.argv[2]
        send_brew_plot(brew_id)

    else:
        sys.exit(usage)

