type SiteHeaderProps = {
  ctaHref?: string;
  ctaLabel?: string;
};

export function LogoMark() {
  return (
    <span className="logoMark" aria-hidden="true">
      <svg viewBox="0 0 32 32" role="img">
        <path d="M7 24V13" />
        <path d="M13 24V7" />
        <path d="M19 24V10" />
        <path d="M25 24V4" />
        <path d="M6 25c5.8 3.4 14.4 3.3 20 0" />
      </svg>
    </span>
  );
}

export function Icon({ name }: { name: string }) {
  if (name === "shield") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 3l7 3v5c0 4.6-2.8 8.2-7 10-4.2-1.8-7-5.4-7-10V6l7-3z" />
        <path d="M9 12l2 2 4-5" />
      </svg>
    );
  }
  if (name === "lock") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <rect x="5" y="10" width="14" height="10" rx="2" />
        <path d="M8 10V7a4 4 0 0 1 8 0v3" />
      </svg>
    );
  }
  if (name === "cloud") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M8 18H7a4 4 0 1 1 1.1-7.8A6 6 0 0 1 19.6 12 3 3 0 0 1 19 18h-3" />
        <path d="M12 12v8" />
        <path d="M9 15l3-3 3 3" />
      </svg>
    );
  }
  if (name === "support") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M5 13a7 7 0 0 1 14 0" />
        <path d="M5 13v4a2 2 0 0 0 2 2h1v-6H5z" />
        <path d="M19 13v4a2 2 0 0 1-2 2h-1v-6h3z" />
        <path d="M13 21h2a4 4 0 0 0 4-4" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20 6L9 17l-5-5" />
    </svg>
  );
}

export function SiteHeader({ ctaHref = "/cadastro", ctaLabel = "Começar grátis" }: SiteHeaderProps) {
  return (
    <header className="siteHeader">
      <a className="brand" href="/" aria-label="Finanças Pro IA">
        <LogoMark />
        <span>Finanças Pro IA</span>
      </a>
      <nav aria-label="Navegação principal">
        <a href="/#beneficios">Benefícios</a>
        <a href="/#planos">Planos</a>
        <a href="/login">Entrar</a>
      </nav>
      <a className="headerCta" href={ctaHref}>
        {ctaLabel}
      </a>
    </header>
  );
}
