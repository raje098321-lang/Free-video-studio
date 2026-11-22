# Free stack and realistic launch limits

Research checked on 22 November 2026. Provider free tiers and policies can change.

## Best no-cost starting stack

- **Frontend hosting:** Cloudflare Pages Free. Suitable for a static website and light routing.
- **Login and quota database:** Supabase Free. It currently lists 50,000 monthly active users, 500 MB database, 1 GB storage and 5 GB egress. Free projects may pause after inactivity.
- **Video generation:** public Hugging Face ZeroGPU Spaces for testing. Free account quota currently lists 5 GPU minutes/day; anonymous access is lower. This is a personal/demo allowance, not a guaranteed production API pool.
- **Assembly:** FFmpeg, free/open-source, but a hosted server still needs CPU/storage and may not fit free hosting limits.
- **Ads/payments:** add only after the app has real users and provider costs are measured.

## Important limits

- The Hugging Face free GPU quota belongs to the Hugging Face account making the inference request. If every user runs through the owner's token, the owner's quota is shared and can run out.
- Public community Spaces have different API schemas, queues, model licenses and uptime. Provider fallback can only switch to a provider that is actually configured and available.
- Free hosting is not free AI inference. Do not promise unlimited video generation or 10 videos of 4 minutes each per month until real costs and capacity are funded.
- The current starter's quota and rewarded-ad modules are demo scaffolding. They are not safe for public users because they lack real authentication, persistent per-user accounting and an ad network's server-side reward verification.
- Never place provider keys in frontend JavaScript or public repository files.

## Suggested launch offer

### Phase 1 — personal testing
Use the app privately, test short clips, and learn which provider returns a usable MP4. No public promises or payment.

### Phase 2 — free public tool
Offer story planning, scene prompt generation and MP4 assembly for user-uploaded clips free. If video generation is enabled, make the free allowance a small, clearly disclosed trial based on the provider's actual budget.

### Phase 3 — monetization
Only after measuring cost per completed video:
- free monthly credits capped by actual provider budget;
- paid credits priced above the real inference, storage, transfer and payment fees;
- optional rewarded ads only through a compliant provider and only after server-side completion verification;
- stop accepting generation jobs when the budget/quota is exhausted.

## Ads and payment account note

Google AdSense applicants must be 18+. If a publisher is under 18, Google says a parent or guardian may apply using their own Google Account and receive payments. Stripe says an under-18 account requires a legal guardian to become the account owner before charges and payouts can be enabled. Have a parent/guardian handle the legal account, payment, tax and payout setup; do not bypass age or identity checks.
