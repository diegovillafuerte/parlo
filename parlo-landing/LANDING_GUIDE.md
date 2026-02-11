# Parlo Website & Landing Pages — Working Guide

This guide walks you through everything you need to work on the Parlo website and landing pages. You'll be editing an Astro project (the `parlo-landing` folder inside the `yume` repo) and using Claude tools to help you build and push changes to GitHub.

---

## 1. What You're Working With

### The Astro Project

Astro is the framework we use for the public-facing website — landing pages, blog posts, marketing content, etc. It takes your content and turns it into fast, static web pages. No server needed — the output is plain HTML, CSS, and JS that can be hosted anywhere.

**Our repo:** `https://github.com/diegovillafuerte/yume.git`
**The landing page lives in:** `parlo-landing/` (a subfolder of the main repo)
**Production URL:** `https://parlo.mx`

### Project Structure (What's Actually in the Folder)

```
parlo-landing/
├── src/
│   ├── pages/
│   │   ├── index.astro              ← The homepage (beauty/barbershop default)
│   │   └── [...slug].astro          ← Dynamic route — generates ALL variant pages
│   ├── components/
│   │   ├── Nav.astro                ← Sticky header (logo + "Únete a la lista" button)
│   │   ├── Hero.astro               ← Main headline + CTA
│   │   ├── HowItWorks.astro         ← Section title + carousel wrapper
│   │   ├── Carousel.astro           ← Interactive 6-slide demo of Parlo features
│   │   ├── PhoneMockup.astro        ← WhatsApp phone frame
│   │   ├── ChatMessage.astro        ← Individual chat bubble (text, voice, payment)
│   │   ├── Benefits.astro           ← 4-column benefits grid
│   │   ├── BenefitCard.astro        ← Single benefit card
│   │   ├── WaitlistForm.astro       ← Signup form (sends data to Google Sheets)
│   │   └── Footer.astro             ← Footer with contact email
│   ├── layouts/
│   │   └── BaseLayout.astro         ← HTML shell + SEO meta tags + scroll animations
│   ├── data/
│   │   ├── variants.ts             ← ⭐ THE VARIANT MATRIX — add experiment rows here
│   │   ├── benefits.ts              ← Default beauty benefits (text, icons, stats)
│   │   ├── slides.ts               ← Default beauty carousel slides
│   │   └── industries/              ← Base configs per industry
│   │       ├── index.ts             ← IndustryConfig type + exports
│   │       ├── clinicas.ts          ← Medical clinics config
│   │       ├── talleres.ts          ← Auto repair shops config
│   │       ├── fitness.ts           ← Gyms & studios config
│   │       └── mascotas.ts          ← Pet care & veterinary config
│   └── styles/
│       └── global.css               ← Tailwind setup + custom CSS utilities
├── public/
│   ├── favicon.svg                  ← Browser tab icon
│   └── robots.txt                   ← SEO: tells search engines to index the site
├── astro.config.mjs                 ← Astro settings (Tailwind, site URL)
├── tailwind.config.mjs              ← Colors, fonts, animations
├── package.json                     ← Dependencies and scripts
└── dist/                            ← Build output (don't edit — auto-generated)
```

### How Pages Are Built

**The homepage** (`src/pages/index.astro`) is the beauty/barbershop default. It uses component defaults and doesn't pass any props.

**All other landing pages** are generated automatically from the variant matrix in `src/data/variants.ts`. A single dynamic route file (`src/pages/[...slug].astro`) reads the matrix at build time and creates one page per row. You never create individual `.astro` page files — you just add rows to the matrix.

Currently the matrix generates **20 pages** across 4 industries x 5 variants each (base + 4 feature angles):

| | Base | Pagos | Recordatorios | Agenda | Marketing |
|---|---|---|---|---|---|
| **Clínicas** | `/clinicas` | `/clinicas/pagos` | `/clinicas/recordatorios` | `/clinicas/agenda` | `/clinicas/marketing` |
| **Talleres** | `/talleres` | `/talleres/pagos` | `/talleres/recordatorios` | `/talleres/agenda` | `/talleres/marketing` |
| **Fitness** | `/fitness` | `/fitness/pagos` | `/fitness/recordatorios` | `/fitness/agenda` | `/fitness/marketing` |
| **Mascotas** | `/mascotas` | `/mascotas/pagos` | `/mascotas/recordatorios` | `/mascotas/agenda` | `/mascotas/marketing` |

Each variant has a unique `fuente` value (e.g., `landing-clinicas-pagos`) so we can track which landing page each waitlist signup came from in the Google Sheet.

### What `.astro` Files Look Like

```astro
---
// This top section (between the ---) is the "setup" area.
// It runs on the server, not in the browser.
import Layout from '../layouts/BaseLayout.astro';
const pageTitle = "Reserva tu cita en segundos";
---

<!-- This bottom section is your HTML -->
<Layout title={pageTitle}>
  <h1>{pageTitle}</h1>
  <p>Parlo helps your business manage appointments via WhatsApp.</p>
  <a href="/signup">Empieza gratis</a>
</Layout>
```

The top part (between `---`) imports things and sets up variables. The bottom part is HTML with `{curly braces}` for dynamic values.

### File Types You'll Encounter

| File type | What it is |
|-----------|-----------|
| `.astro` | Astro page or component (HTML + a little logic) |
| `.ts` | TypeScript data files (where content like carousel slides lives) |
| `.css` | Styles (we mostly use Tailwind classes directly on HTML) |
| `.md` / `.mdx` | Markdown content (blog posts, articles — not used yet) |
| `.mjs` | Config files (Astro config, Tailwind config) |
| `.json` | Data files (package.json for dependencies) |

---

## 2. The Design System (Colors, Fonts, Brand)

All of this is defined in `tailwind.config.mjs`. This is important to know so the pages you create look consistent.

### Colors

| Name | Hex | What it's used for |
|------|-----|-------------------|
| **Primary** | `#7C3AED` (purple) | Buttons, highlights, brand accent |
| **Primary dark** | `#6D28D9` | Button hover states |
| **Secondary** | `#3B82F6` (blue) | Gradients (purple-to-blue) |
| **Accent** | `#F97316` (orange) | Not heavily used yet — available for emphasis |
| **WhatsApp green** | `#25D366` | WhatsApp-themed elements |
| **Text** | `#1F2937` (dark gray) | Body text |
| **Text light** | `#6B7280` (medium gray) | Secondary text, descriptions |
| **Border** | `#E5E7EB` (light gray) | Card borders, dividers |
| **Background** | `#FAFAFA` | Page background |

### Fonts

| Use | Font | Example |
|-----|------|---------|
| Headings | **Outfit** (weights 400–800) | Page titles, section headers, buttons |
| Body text | **Plus Jakarta Sans** (variable) | Paragraphs, descriptions |

### Key CSS Utilities

These are custom classes defined in `global.css` that you'll see throughout:

| Class | What it does |
|-------|-------------|
| `gradient-text` | Makes text purple-to-blue gradient (used for the "Parlo" brand name) |
| `gradient-bg` | Purple-to-blue gradient background (used on CTA buttons and waitlist section) |
| `reveal` | Fade-in-from-below animation triggered when element scrolls into view |

### Animations

Elements use `animate-fade-in` (and `animate-fade-in-delay-1` through `delay-4`) for staggered entrance animations. The Hero section uses these so elements appear one after another when the page loads.

---

## 3. Where the Content Lives (What You'll Edit Most)

As a growth person, you'll spend most of your time editing **content**, not code structure. Here's where everything lives:

### The Variant Matrix — `src/data/variants.ts` (YOUR MAIN FILE)

**This is the file you'll work with most.** It contains every landing page variant as a row in an array. Each row defines a complete page config: slug (URL), SEO title/description, hero headline/subheadline, carousel slides, benefits, waitlist form copy, and footer.

Each variant spreads from a base industry config and overrides specific fields. For example, `clinicas/pagos` starts with all the clinicas content but swaps the hero headline and subheadline to focus on the payments angle.

**What each variant overrides:**
- `seo.title` and `seo.description` — browser tab + Google results
- `hero.headline` and `hero.subheadline` — the main hook visitors see first
- `waitlist.fuente` — tracking tag sent to Google Sheets (how you know which ad worked)

**What stays the same from the base industry config:**
- Carousel slides (the 6 WhatsApp demo conversations)
- Benefits cards (the 4 stats/features below the carousel)
- Waitlist form placeholders, footer tagline, badge, CTA text, promo line

### Base Industry Configs — `src/data/industries/`

Each industry has a full config file with all content (slides, benefits, etc.):
- `clinicas.ts` — Medical clinics & dental offices
- `talleres.ts` — Auto repair shops
- `fitness.ts` — Gyms & fitness studios
- `mascotas.ts` — Pet grooming & veterinary

These are imported by the variant matrix. You edit them when you want to change the carousel conversations, benefits, or other shared content for an entire industry.

### Hero Section — `src/components/Hero.astro`

The Hero component accepts props for all its text. For the beauty homepage (`index.astro`), these are hardcoded defaults. For all industry/feature variants, the text comes from the variant matrix.

**For the beauty homepage,** the defaults are:
- **Badge:** "Tu asistente por WhatsApp"
- **Headline:** "Quieres crecer tu estética o barbería?..."
- **CTA button:** "Únete a la lista de espera exclusiva"

To change beauty homepage copy, edit `Hero.astro` defaults. To change any variant's copy, edit the variant's row in `variants.ts`.

### Carousel Slides — `src/data/slides.ts`

**This is the file you'll edit most.** It contains the 6 demo conversations that show how Parlo works. The file has a helpful comment at the top explaining the format.

The 6 slides are:

1. **Configuración** — Business owner sets up Parlo (5-min chat)
2. **Agendar** — A client books an appointment
3. **Gestionar** — Owner manages their schedule via voice note
4. **Recordatorios** — Automatic reminder + client reschedules
5. **Pagos** — Client pays through WhatsApp
6. **Promociones** — Parlo sends a personalized promo to a returning client

Each slide has:
```typescript
{
  tabLabel: 'Tab text',          // What the tab button says
  stepNumber: 1,                  // Number badge
  slideTitle: 'Title above phone',
  chatHeader: {
    name: 'Business Name',        // Top of the WhatsApp chat
    subtitle: 'en línea',
    avatarEmoji: '✂️',
    avatarStyle: 'parlo' | 'business',  // Purple avatar vs colored
  },
  messages: [
    { role: 'bot', text: 'Message text', time: '9:41' },
    { role: 'client', text: 'Client message' },
    { role: 'owner', text: 'Owner message' },
    // Special types:
    { role: 'owner', text: '', voiceNote: { duration: '0:03', transcript: '"..."' } },
    { role: 'bot', text: '', paymentLink: { label: 'Pagar $350 MXN', amount: '$350' } },
  ],
}
```

The `text` field supports basic HTML: `<br>` for line breaks, `<strong>` for bold, `<em>` for italic.

**Message roles:**
- `bot` = Parlo's response (appears on the left, white bubble)
- `client` = End customer (appears on the right, green bubble)
- `owner` = Business owner (appears on the right, green bubble)

### Benefits — `src/data/benefits.ts`

The 4 benefit cards below the carousel:

1. "Tiempo ahorrado al día" (2 horas stat)
2. "Incrementa tu negocio"
3. "Recibe menos efectivo"
4. "Menos citas perdidas"

Each benefit has: `icon` (emoji), optional `stat` (big number), `title`, and `text`.

### Waitlist Form — `src/components/WaitlistForm.astro`

Collects 4 fields: name, business name, business type, WhatsApp number. Submits to a Google Apps Script webhook that writes to a [Google Sheet](https://docs.google.com/spreadsheets/d/1WRR2A1s5jYzqGuoKGbrUoWhGgFL1mNZtXHmAw4lw3Ig/edit?usp=sharing). The form fields and success message text can be edited here.

### Nav — `src/components/Nav.astro`

Sticky header with the "Parlo" logo (using `gradient-text` for the purple-to-blue effect) and a CTA button that scrolls to the waitlist form.

### Footer — `src/components/Footer.astro`

Simple footer: "Hecho en México" + contact email (`hola@parlo.mx`).

### SEO & Meta Tags — `src/layouts/BaseLayout.astro`

Page title, description, Open Graph tags, Twitter cards, and JSON-LD structured data. The defaults are:
- **Title:** "Parlo - Tu Asistente Inteligente para Estéticas y Barberías"
- **Description:** "Conecta Parlo a tu WhatsApp en 2 minutos. Tu asistente 24/7 que reserva clientes..."

---

## 4. Your Tools

You have three Claude-powered tools at your disposal.

### Claude.ai (chat interface)

The chat interface at claude.ai. You talk to Claude, attach files, and ask questions.

Use it for:
- Asking questions ("What does this error mean?", "How do I add a new page?")
- Drafting copy and content before putting it in the codebase
- Reviewing screenshots and asking for design feedback
- Planning what you want to build before jumping into code

### Claude Code (terminal tool)

A command-line tool that runs in your terminal. Claude Code can read your project files, write code, run commands, and push to GitHub — all through conversation. **This is your primary tool for making changes.**

#### Installing Claude Code

1. Open Terminal (search "Terminal" in Spotlight with `Cmd + Space`)

2. Install Homebrew (if you don't have it):
   ```
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

3. Install Node.js:
   ```
   brew install node
   ```

4. Install Claude Code:
   ```
   npm install -g @anthropic-ai/claude-code
   ```

5. Navigate to the landing page folder:
   ```
   cd ~/path/to/yume/parlo-landing
   ```
   (Diego will give you the exact path after you clone the repo — see Section 5.)

6. Launch Claude Code:
   ```
   claude
   ```

7. It will ask you to log in with your Anthropic account the first time. Follow the prompts.

#### How to Use Claude Code

Once inside, just talk to it naturally:

```
You: "Show me the current hero headline"

Claude: [reads Hero.astro and shows you the text]

You: "Change it to 'Tu barbería merece un asistente que no descansa'"

Claude: [edits the file]

You: "Add a new carousel slide that shows a walk-in client booking"

Claude: [adds a new entry to src/data/slides.ts]

You: "Commit and push this"

Claude: [runs git commands]
```

**Key commands inside Claude Code:**
- Just type naturally to ask for changes
- Type `/help` to see available commands
- `Ctrl + C` to cancel something in progress
- `/exit` or `Ctrl + D` to quit

### Claude Cowork (desktop app)

A desktop app where Claude can work with your files more visually — creating, editing, and managing files on your computer.

Use it for:
- Working with images and assets
- Managing files across folders
- Tasks that involve multiple applications

---

## 5. Setting Up: Getting the Code on Your Machine

### One-time Setup

**Step 1 — Install Git**
```
brew install git
```

**Step 2 — Configure Git with your identity**
```
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

**Step 3 — Set up GitHub access**
1. Go to github.com and log in (or create an account and ask Diego to add you to the repo)
2. Install the GitHub CLI:
   ```
   brew install gh
   ```
3. Authenticate:
   ```
   gh auth login
   ```
   Follow the prompts — choose "GitHub.com", "HTTPS", and "Login with a web browser".

**Step 4 — Clone the repo**
```
git clone https://github.com/diegovillafuerte/yume.git
cd yume/parlo-landing
```

**Step 5 — Install project dependencies**
```
npm install
```

**Step 6 — Start the dev server**
```
npm run dev
```

Open your browser to `http://localhost:4321`. Every time you save a file, the page updates automatically.

---

## 6. Your Daily Workflow

### Starting your session

```bash
cd ~/path/to/yume/parlo-landing  # Navigate to the project
git pull                          # Get latest changes
npm run dev                       # Start the preview server (keep this running)
```

Then in a **new terminal tab** (`Cmd + T`):

```bash
cd ~/path/to/yume/parlo-landing
claude                            # Launch Claude Code
```

### Common Tasks (What You'll Actually Ask Claude to Do)

#### Changing copy/text

```
"Change the hero headline to 'La agenda inteligente para tu salón'"
"Update the first benefit card stat from '2 horas' to '3 horas'"
"Change the footer email to contacto@parlo.mx"
"Update the SEO description to mention nail salons"
```

#### Working with carousel slides

```
"Show me all 6 carousel slides and their titles"
"Edit slide 2 (Agendar) — change the client name from Carlos to Miguel"
"Add a 7th carousel slide showing a client canceling an appointment"
"Change the business name in slide 5 from 'Estética Lourdes' to 'Estética María'"
"Add a voice note message to slide 3 where the owner asks about tomorrow's earnings"
```

#### Adding new experiment variants

```
"Add a new variant at /clinicas/pagos-v2 with a different headline that emphasizes
 reducing no-shows instead of collecting deposits"
"Add a new industry for dentists at /dentistas with custom slides and benefits"
"Show me all the current variant slugs and their headlines"
```

New variant pages are created by adding rows to `src/data/variants.ts`. You never create individual `.astro` page files — the dynamic route handles everything automatically.

#### Working with images

```
"I put a new image at public/images/hero-photo.jpg — add it to the hero section"
"Replace the emoji icons in the benefits section with SVG icons"
```

Note: Currently the site uses emojis instead of images (for icons and avatars). To add actual images, place them in the `public/` folder and reference them as `/filename.jpg` in your HTML.

#### Design changes

```
"Make the CTA button larger"
"Change the primary color from purple to a darker shade"
"Add more spacing between the benefits cards"
"Make the hero section taller on mobile"
```

#### Creating blog posts (once we set up a blog)

Create a `.md` file in a content folder:

```markdown
---
title: "Cómo Parlo ayuda a tu barbería"
date: 2026-02-10
description: "Descubre cómo automatizar tus citas"
---

Your blog content goes here. Write in plain text with
**bold** and *italic* and [links](https://parlo.mx).
```

### Previewing Changes

Keep `npm run dev` running and check `http://localhost:4321`. Changes appear instantly as Claude edits files.

### Saving, Pushing, and Deploying

When you're happy with your changes:

```
You: "Commit these changes with message 'Update hero copy for barber campaign' and push"
```

Claude runs the git commands for you. Under the hood, that's:

```bash
git add .
git commit -m "Update hero copy for barber campaign"
git push origin main
```

**Deployment is automatic.** Vercel is connected to the GitHub repo, so every push to `main` triggers a new deploy. Your changes will be live on `parlo.mx` within a couple of minutes after pushing — no extra steps needed. You can check the deploy status at [vercel.com](https://vercel.com) if you want to confirm it went through.

---

## 7. Common Recipes

### Recipe: Add an A/B Test Variant (Feature Angle)

This is the most common task. You want to test a different headline angle for an existing industry.

Tell Claude Code:

```
"Add a new variant at /clinicas/urgencias with a headline focused on
same-day appointment booking for urgent cases. Use clinicasConfig as base,
override the hero headline and subheadline, and set fuente to
'landing-clinicas-urgencias'."
```

Claude will add a row to `src/data/variants.ts`. The page will be live at `parlo.mx/clinicas/urgencias` after the next deploy. That's it — no new files needed.

**You can also do it manually.** Open `src/data/variants.ts` and add a row:

```typescript
{
  slug: 'clinicas/urgencias',
  ...clinicasConfig,
  seo: {
    title: 'Parlo - Citas de Urgencia por WhatsApp para tu Clínica',
    description: 'Tus pacientes agendan citas urgentes por WhatsApp en segundos.',
  },
  hero: {
    ...clinicasConfig.hero,
    headline: '¿Pacientes urgentes que no pueden esperar?<br /><span class="gradient-text">Parlo</span> les agenda cita en segundos por WhatsApp',
    subheadline: 'Tu asistente identifica urgencias y ofrece el primer horario disponible — <strong>sin que tu recepción deje de atender</strong>.',
  },
  waitlist: { ...clinicasConfig.waitlist, fuente: 'landing-clinicas-urgencias' },
},
```

### Recipe: Add a New Industry

Tell Claude Code:

```
"Add a new industry config for dental offices at src/data/industries/dentistas.ts
with custom slides showing dental-specific conversations (cleanings, whitening,
implants) and dental-specific benefits. Then add it to the variant matrix with
slug 'dentistas' and fuente 'landing-parlo-dentistas'."
```

Claude will create the industry config file and add the base variant to the matrix. You can then add feature variants (`dentistas/pagos`, `dentistas/agenda`, etc.) as separate rows.

### Recipe: Change the Waitlist Form Fields

```
"Add a dropdown field to the waitlist form asking 'How many employees do you have?'
with options: 1, 2-3, 4-6, 7+"
```

Claude will edit `src/components/WaitlistForm.astro` and make sure the new field is included in the Google Sheets submission.

### Recipe: Update the Chat Demo Conversations for an Industry

The carousel slides are defined in each industry config file (`src/data/industries/clinicas.ts`, etc.):

```
"In the clinicas config, change slide 2 (Agendar) — update the services to include
implant consultations at $2,000 and orthodontist evaluation at $500"
```

This will update the carousel for ALL clinicas variants (base + pagos + recordatorios + agenda + marketing) since they all inherit from the same config.

### Recipe: Build Locally (for debugging)

```bash
npm run build     # Builds everything into the dist/ folder — should produce 21 pages
npm run preview   # Preview the built version locally
```

You shouldn't need to do this often since Vercel builds automatically on push. But if you want to verify the production build locally before pushing, this is how. The build output will list every generated page — check that your new variant appears.

---

## 8. Architecture Notes (Good to Know, Not Critical)

### How the experiment engine works

The core of the landing page system is a **variant matrix** (`src/data/variants.ts`). Each row is a complete page config with a `slug` (URL path) and all the content needed to render the page.

At build time, Astro's dynamic route (`src/pages/[...slug].astro`) reads the matrix and generates one static HTML page per row using `getStaticPaths()`. This means:
- Adding a variant = adding a row to the array. No new files.
- Removing a variant = deleting the row. The URL stops existing.
- The build will fail if two variants share the same slug (duplicate guard).

**The inheritance pattern:** Feature variants spread from a base industry config and override only the fields they need (usually hero + SEO + fuente). This means a change to `clinicasConfig` automatically propagates to all clinicas variants.

### How the carousel works

The carousel in `HowItWorks` uses `Carousel.astro` which creates a horizontally scrolling container with snap-scroll behavior. It has tab buttons, dot indicators, and arrow navigation. The phone mockup (`PhoneMockup.astro`) renders WhatsApp-style chat using `ChatMessage.astro` components. All the conversation data comes from each variant's `slides` array (inherited from the industry config).

### How scroll animations work

`BaseLayout.astro` includes an IntersectionObserver script. Any element with the `reveal` class starts invisible and slides up when it enters the viewport. The benefit cards use this.

### How the form works

`WaitlistForm.astro` has a `<script>` tag that intercepts form submission, packages the data as JSON, and POSTs it to a Google Apps Script URL that writes to a Google Sheet. The `fuente` field is set per variant, so you can see in the Sheet which landing page each signup came from.

### How styling works

We use Tailwind CSS, which means styles are written as classes directly on HTML elements (like `class="text-lg font-bold text-primary"`). The custom colors, fonts, and animations are all defined in `tailwind.config.mjs`. The few custom utilities (`gradient-text`, `gradient-bg`, `reveal`) are in `src/styles/global.css`.

---

## 9. When Things Go Wrong

### "I broke something"

Tell Claude Code: "Something is broken, can you check what's wrong?"

If you want to undo everything since your last commit:
```
git checkout .
```

### "The dev server won't start"

```
npm install
npm run dev
```

If it still fails, tell Claude Code and paste the error.

### "I need to undo my last push"

Ask Diego before doing this. Reverting pushed changes can affect others. But you can tell Claude Code: "I need to revert the last commit" and it will guide you.

### "Git says there's a conflict"

This happens when someone else changed the same file you changed. Tell Claude Code: "I have a merge conflict, can you help me resolve it?"

### "The page looks weird on mobile"

Ask Claude: "Check if the hero section is responsive" or "Make the benefits grid stack into a single column on mobile." Tailwind handles this with responsive prefixes like `md:grid-cols-2` (2 columns on medium screens and up).

---

## 10. Quick Reference

| I want to... | Do this |
|--------------|---------|
| Start working | `cd ~/path/to/yume/parlo-landing && git pull && claude` |
| Preview the site | `npm run dev` then open `localhost:4321` |
| Make a change | Tell Claude Code what you want |
| **Add a new experiment variant** | **Add a row to `src/data/variants.ts`** (or ask Claude) |
| Change a variant's headline | Edit its row in `src/data/variants.ts` (or ask Claude) |
| Change beauty homepage copy | Edit `src/components/Hero.astro` defaults (or ask Claude) |
| Edit industry carousel/benefits | Edit the config in `src/data/industries/` (or ask Claude) |
| Edit waitlist form | Edit `src/components/WaitlistForm.astro` (or ask Claude) |
| Change colors/fonts | Edit `tailwind.config.mjs` (or ask Claude) |
| See all current variants | Open `src/data/variants.ts` and look at the `slug` values |
| Check which fuente maps to which URL | `npm run build` — it lists all generated pages |
| Add an image | Put it in `public/` and reference as `/filename.jpg` |
| Save, push & deploy | "Commit and push with message '...'" (auto-deploys to parlo.mx) |
| Undo unsaved changes | `git checkout .` |
| See what changed | `git status` |
| Build for production | `npm run build` (should produce 21+ pages) |
| Stop Claude Code | `Ctrl + D` or `/exit` |
| Stop the dev server | `Ctrl + C` |

---

## 11. Tips

- **Commit often.** Small, frequent commits are better than one giant one. Each commit is a save point you can go back to.
- **Write descriptive commit messages.** "Update pricing" is better than "changes". "Add barbershop landing page with Spanish copy" is better still.
- **Always `git pull` before starting work.** This avoids conflicts with changes Diego or others may have pushed.
- **Don't be afraid to ask Claude.** Whether in Claude Code or claude.ai, just describe what you want in plain language. You don't need to know the technical terms.
- **If something feels risky, ask Diego.** Especially anything involving deleting files, changing configurations, or modifying files outside the `parlo-landing` folder.
- **Keep all content in Mexican Spanish.** Use "tú" not "usted". Currency as "$150". Dates as "viernes 15 de enero". Times as "3:00 PM" (12-hour).
- **`variants.ts` is your best friend.** It's the single file that controls all experiment pages. Industry configs (`src/data/industries/`) control the shared content (slides, benefits) per vertical.
- **Every variant needs a unique `fuente`.** This is how you track ad performance in the Google Sheet. Convention: `landing-{industry}-{feature}` (e.g., `landing-clinicas-pagos`).
- **Don't edit the `dist/` folder.** It's auto-generated when you run `npm run build`. Your changes go in `src/`.
- **Don't create individual `.astro` page files for variants.** The dynamic route handles everything — just add rows to the matrix.
