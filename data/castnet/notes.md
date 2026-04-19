# CASTNET Notes

For the HackAugie MVP, Aeris uses a compact processed profile derived from the CASTNET sustainability dataset.

The demo profile intentionally reduces the raw dataset into judge-readable fields:

- location label
- CASTNET profile/site label
- ozone risk bucket
- deposition risk bucket
- active risk mode
- short environmental summary

This keeps CASTNET operational in the product without spending the hackathon on a full ingestion platform.

## Demo Mapping

```text
high ozone risk -> protect_plants_and_sensitive_equipment
otherwise       -> general_outdoor_protection
```

The processed profile is used by the backend as Fixed Context. The async agentic decision layer combines that context with visible scene objects to rank what should be protected first. A local fallback policy exists only as a safety net if LLM providers are unavailable.
