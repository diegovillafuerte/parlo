import { NextRequest, NextResponse } from 'next/server';

const RESERVED_SUBDOMAINS = new Set(['www', 'app', 'admin', 'api', 'staging']);

export function middleware(request: NextRequest) {
  const hostname = request.headers.get('host') || '';
  const url = request.nextUrl.clone();

  let subdomain: string | null = null;

  if (hostname.endsWith('.parlo.mx')) {
    subdomain = hostname.replace('.parlo.mx', '');
  } else if (hostname.match(/^[^.]+\.localhost(:\d+)?$/)) {
    subdomain = hostname.split('.')[0];
  }

  if (!subdomain || RESERVED_SUBDOMAINS.has(subdomain)) {
    return NextResponse.next();
  }

  // Prevent infinite rewrite
  if (url.pathname.startsWith('/site/')) {
    return NextResponse.next();
  }

  url.pathname = `/site/${subdomain}${url.pathname === '/' ? '' : url.pathname}`;
  return NextResponse.rewrite(url);
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|api).*)'],
};
