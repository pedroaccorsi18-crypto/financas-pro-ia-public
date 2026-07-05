import { SiteHeader } from "@/components/brand";

export default function NotFound() {
  return (
    <main>
      <SiteHeader />
      <section className="statePage">
        <h1>Página não encontrada</h1>
        <p>O endereço acessado não existe ou foi movido.</p>
        <a className="primaryButton" href="/">
          Voltar para o início
        </a>
      </section>
    </main>
  );
}
