"use client";

import { SiteHeader } from "@/components/brand";

export default function ErrorPage({
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main>
      <SiteHeader />
      <section className="statePage">
        <h1>Não foi possível carregar esta página</h1>
        <p>Atualize a página ou tente novamente em alguns instantes.</p>
        <button className="primaryButton" type="button" onClick={reset}>
          Tentar novamente
        </button>
      </section>
    </main>
  );
}
