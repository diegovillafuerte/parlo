import type { SlideData } from '../slides';
import type { Benefit } from '../benefits';

export interface IndustryConfig {
  seo: {
    title: string;
    description: string;
  };
  hero: {
    badge: string;
    headline: string;
    subheadline: string;
    cta: string;
    promoLine: string;
  };
  howItWorks: {
    subtitle: string;
  };
  slides: SlideData[];
  benefits: Benefit[];
  waitlist: {
    heading: string;
    subtitle: string;
    businessPlaceholder: string;
    activityPlaceholder: string;
    fuente: string;
  };
  footer: {
    tagline: string;
  };
}

export { clinicasConfig } from './clinicas';
export { talleresConfig } from './talleres';
export { fitnessConfig } from './fitness';
export { mascotasConfig } from './mascotas';
