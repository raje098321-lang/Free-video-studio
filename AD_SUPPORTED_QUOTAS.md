# Ad-supported quota design

## Target
- Maximum assembled project: 240 seconds (4 minutes).
- Generate short clips/scenes and stitch them; do not claim the model generates a single 4-minute clip.
- Default: 1 free scene credit/day, plus 1 scene credit per verified rewarded-ad completion, capped at 5 rewarded completions/day in the prototype. These are product defaults and should be adjusted after measuring real provider GPU consumption and ad revenue.

## Why credits are scene-based
A credit represents one short scene request (default 5 seconds), not a guaranteed number of final-video seconds. Different providers/models have different generation lengths, GPU runtime, quality and restrictions. A provider's free quota may expire or be exhausted even when the app wallet has credits.

## Longest free project
The scene planner supports 240 seconds:
- 48 x 5-second scenes = 240 seconds.
- 24 x 10-second scenes = 240 seconds, if a model/provider supports 10-second clips.

The free ad quota does not guarantee a completed 4-minute video. At the prototype's default 1 free + 5 ad credits/day, a user can request up to 6 scenes/day (nominal 30 seconds at 5 seconds/scene), if GPU providers are available. To reach 4 minutes, the user would need additional ad credits over time, provider capacity, or an ad revenue budget that pays for inference.

## Rewarded-ad requirements
- Show a clear opt-in before the ad: “Watch this ad to earn 1 video scene credit (5 seconds, subject to provider availability).”
- User may decline without blocking normal app use.
- Grant the credit only after a valid completed-ad server callback.
- Bind the reward to the logged-in user and a unique completion/transaction ID.
- Reject replayed, invalid, expired, or mismatched callbacks.
- Never ask users to click ads; only completion of a supported rewarded format earns the disclosed reward.
- Credits are non-transferable and usable only inside this app.
- Check the ad network's current policies and obtain approval before serving real ads.

## Production work still required
- User accounts and persistent database wallet.
- Server-side ad verification for the selected ad provider.
- Provider-specific API adapters, quota/health tracking, and retry queue.
- Storage for generated clips and project files.
- Abuse prevention, privacy notice, consent controls, and age-appropriate ad settings.
- Actual hosting and provider testing.

## Provider fallback
Fallback is allowed only between providers that the app is authorized to use and that have their own valid availability/quota. Do not rotate fake accounts or evade provider limits. A provider failure should pause/resume the job rather than consume a user's credit unless a clip was successfully returned.
