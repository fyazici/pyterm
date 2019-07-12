PyTerm
======

Simple serial port communication interface made with Tkinter GUI. 

- Scans devices under `/dev/tty*` on start and on demand
- Provides a collection of standard baudrates as well as ***allowing arbitrary speeds***
- Non-blocking threaded data receive
- Threaded data send worker (no GUI freeze)
- Separate received/sent text displays with scrollable history

Although these features seem standard for most GUI applications, I have faced with lack of some with every serial terminal application I have tried.

For example **(reckless criticism, no offense)**:
- `screen` does not support modern high baudrates such as 12Mbaud (which I needed for FT2232H communication). Hangs sometimes (when cable unplugged etc.). Does not have separate sent/received windows
- `cu` all above plus that ugly exit sequence ~. !?
- `minicom` no GUI, old terminology, confusing configuration (probably it is a one-time setup but *aint nobody got time for that*)
- `moserial` nice GUI with features but LACKS THE DAMN 12MBAUD SETTING!
- `putty` linux version did not open a serial connection at all (although there probably is a fix somewhere, I couldn't be bothered)

Notice: This application is just a scratch code to enable my workflow on some other projects, so quick development was above software quality on all aspects. So don't expect bugless, structured, highly maintainable, SOLID-compliant, pylint-defectless ... code :)

Dependencies: python3, pyserial

