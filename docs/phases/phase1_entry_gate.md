# Phase 1 Entry Gate

Status: GO for Phase 1 only.

The July 11, 2026 implementation request explicitly authorizes the greenfield Phase 1 data foundation. This does not authorize Phase 2 features, labels, models, backtests, paper trading, or live trading.

Gate conditions:

- Legacy `QuantSystemFinal` Python code remains out of runtime scope.
- Phase 1 uses only Databento MBO schema contracts and non-code research/planning material.
- The canonical trade tape must reconcile output rows and volume to valid `action == "T"` rows.
- `action == "F"` must not be double counted.
- Session assignment must use an exchange-aware timezone.
- Invalid rows must fail, quarantine, or warn by explicit policy.
