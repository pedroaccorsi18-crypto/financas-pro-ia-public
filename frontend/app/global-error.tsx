"use client";

export default function GlobalError({
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="pt-BR">
      <body>
        <main className="statePage globalErrorPage">
          <h1>Algo saiu do ar por instantes</h1>
          <p>Recarregue a página para tentar novamente.</p>
          <button className="primaryButton" type="button" onClick={reset}>
            Recarregar
          </button>
        </main>
      </body>
    </html>
  );
}
