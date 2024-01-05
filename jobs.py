import threading
import time

from schedule import Scheduler

from .models import Transaction


def check_flw_trans():
    transactions = Transaction.objects.filter(status="pending")
    for transaction in transactions:
        if transaction.wallet_address and transaction.status == "pending":
            transaction.check_flw_tran()
    

    

def run_continuously(self, interval=70):
    """Continuously run, while executing pending jobs at each elapsed
    time interval.
    @return cease_continuous_run: threading.Event which can be set to
    cease continuous run.
    Please note that it is *intended behavior that run_continuously()
    does not run missed jobs*. For example, if you've registered a job
    that should run every minute and you set a continuous run interval
    of one hour then your job won't be run 60 times at each interval but
    only once.
    """

    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):

        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                self.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.setDaemon(True)
    continuous_thread.start()
    return cease_continuous_run

Scheduler.run_continuously = run_continuously

def start_scheduler():
    scheduler = Scheduler()
    scheduler.every(5).minutes.do(check_flw_trans)
    scheduler.run_continuously()

