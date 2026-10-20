"""Post-upload processing: scan -> metadata -> alert.

``scan``, ``metadata`` and ``alert_policy`` are pure and dependency-free;
``pipeline`` orchestrates them against the database and the storage.
"""
