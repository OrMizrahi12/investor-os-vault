# Inbox

New items from the sensors, waiting to be read. One note per filing, plus any idea notes from the monthly hunt.

`sensors/8k-watch/watch.py` writes the notes here. A note is a dated record of a filing, not a view on the company. New facts go in the company's note once checked.

You can delete or move a note when you are done with it. The sensor will not write it again. It will not overwrite a note you edited.

`sensors/hunt/hunt.py` writes `YYYY-MM-DD TICKER idea.md`, once the Desktop task is live. An idea is a lead to read, never a pick. It names why it surfaced, with its source and date.
