import sys
import temp_history
import local_config
import time

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
        if len(sys.argv) != 4:
            sys.exit(usage)
        hours_plotted, hours_to_email = map(float, sys.argv[2:])
        send_updates(hours_plotted, hours_to_email)
    elif action == 'one':
        if len(sys.argv) != 4:
            sys.exit(usage)
        ends = sys.argv[2:]
        for i in range(2):
            if ends[i] == 'None':
                ends[i] = None
            else:
                ends[i] = float(ends[i])
        send_plot(*ends)
    else:
        sys.exit(usage)

