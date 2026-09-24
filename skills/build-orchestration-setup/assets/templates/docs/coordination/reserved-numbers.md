# Reserved numbers and shared resources

Anything two lanes could both pick (migration numbers, ports, test database names, feature-flag names)
is reserved HERE before use, in the same commit that starts the work.

| Resource | Value | Reserved by (ID / lane) | Date | State (reserved / used / released) |
|---|---|---|---|---|
| migration | {{TODO: next free}} | | | |
| test DB port | {{TODO: e.g. 55432 - never the general local port}} | infra | | used |
