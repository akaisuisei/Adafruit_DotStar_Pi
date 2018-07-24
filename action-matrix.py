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
    MQTT_IP_ADDR = "raspi-mika.local"
    signal.signal(signal.SIGINT, sig_handler)
    c = Concierge(MQTT_IP_ADDR, "default", False)
    m = ConciergeMatrix("default", c)
    r = None
    try:
        r = Remote("default", c)
    except:
        pass
    c.loop_forever()
