"""Everything this dashboard reads and every way it reports a reading.

`config` declares the settings, `hostinfo` takes the readings, `ui` renders
provenance and gaps. Pages under `app_pages/` compose those three and hold no
data access of their own, so a new page is a layout decision rather than a
new place for a reading to go wrong.
"""
