import sys
import temp_history
import local_config
import time

def send_updates(hours_plotted, hours_to_email):
    plotting_interval = hours_plotted * 3600.0
    email_interval = hours_to_email * 3600.0
    while True:
        th = temp_history.TempHistory(local_config.temp_history_fpath)
        start_time = time.time()
        th.plot_temp_history(
                start=time.time()-plotting_interval,
                stop=None,
                email=True)
        print 'Email sent'
        time.sleep(email_interval)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('Usage: send_reports.py <hours_plotted> <hours_between_emails>')

    hours_plotted, hours_to_email = map(float, sys.argv[1:])
    send_updates(hours_plotted, hours_to_email)
