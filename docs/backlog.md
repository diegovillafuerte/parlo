# Feature Backlog

Postponed features and enhancements tracked for future implementation.

## Business Website

- [ ] **Image upload for business websites** — Add image storage (S3/Cloudinary), logo + service photos upload during/after onboarding. Display on public website.
- [ ] **Google Maps embed** — Embed interactive Google Maps widget on business website instead of just a link.
- [ ] **SEO structured data** — Add LocalBusiness JSON-LD schema markup for better search engine visibility.
- [ ] **Social proof / reviews** — Display customer reviews or ratings on business website.

## Onboarding

- [ ] **Rethink onboarding prompt strategy** — The system prompt is getting long and complex (500+ lines). Consider breaking it into smaller focused prompts per step, or using a structured state machine that selects the right prompt section. The current monolithic prompt risks the AI ignoring instructions buried in the middle.
