import signal
import sys
from concierge_python.concierge import Concierge
from conciergeMatrix import ConciergeMatrix
from remote import Remote

if __name__ == "__main__":
    def sig_handler(sig, frame):
        c.disconnect()
        m.stop()
        if r:
            r.stop()
        sys.exit(0)
    site_id = 'default'
    site_id = 'remote'
    MQTT_IP_ADDR = "raspi-mika.local"
    signal.signal(signal.SIGINT, sig_handler)
    c = Concierge(MQTT_IP_ADDR, site_id, False)
    m = ConciergeMatrix(site_id, c)
    r = None
    try:
        r = Remote(site_id, c)
        r.start()
    except:
        print("error occured")
        pass
    c.loop_forever()
