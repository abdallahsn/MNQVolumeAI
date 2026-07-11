# CME Session Definition

Internal timestamps remain UTC.

Exchange-local fields are derived with IANA timezone `America/Chicago`; no fixed UTC offset is hard-coded. Daylight-saving changes are handled by Python `zoneinfo`.

Default session rules:

- CME equity-index futures session start: `17:00:00` exchange local time.
- Session close: `16:00:00` exchange local time.
- RTH start: `08:30:00` exchange local time.
- RTH end: `15:00:00` exchange local time.

Trading-date rule:

- if exchange-local timestamp time is `>= 17:00:00`, trading date is local date plus one day;
- otherwise trading date is local date.

Partial-session detection:

- observed first and last sessions are flagged when observed min/max timestamps do not cover configured session bounds within tolerance;
- these warnings are advisory and are recorded in `session_report`.
