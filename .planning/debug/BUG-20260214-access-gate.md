# Bug Investigation: Access Gate Task 6

## Summary
Access gate behavior blocked GEO/IP+GEO requests due to ignored GeoIP lookup results, relied on global mutable config, and could 500 on malformed rule data.

## Symptoms Observed
- GEO and IP_AND_GEO filter modes always blocked when geo_allowed was unset.
- Global site configs lived in a module-level dict.
- Invalid IP/rule data could raise exceptions during rule evaluation.

## Root Cause
- _evaluate_geo_allowed discarded lookup results and always returned None.
- Site config state was stored in a global dict shared across tests/threads.
- evaluate_ip_rules did not guard against invalid IPs or malformed rule dicts.

## Hypothesis Testing
- Hypothesis 1: GEO lookup return value is ignored -> ACCEPTED (function returns None after lookup).
- Hypothesis 2: Config storage is global mutable state -> ACCEPTED (_SITE_CONFIGS dict).
- Hypothesis 3: Malformed IP/rule data can raise -> ACCEPTED (ip_address/ip_network and rule access unguarded).

## Fix Applied
- Use per-app SiteConfigRegistry stored on app.state and update register/clear helpers.
- Handle sync/async GeoIP lookup results and treat truthy mapping as allowed.
- Catch exceptions in rule evaluation and return None on bad data.

## Verification
- Planned: python -m pytest backend/tests/test_access_gate.py -v
