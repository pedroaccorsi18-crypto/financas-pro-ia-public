import { SiteHeader } from "@/components/brand";

export default function CadastroPage() {
  return (
    <main>
      <SiteHeader ctaHref="/login" ctaLabel="Entrar" />
      <section className="authPage">
        <div className="authIntro">
          <p className="previewLabel">Comece grátis</p>
          <h1>Crie sua conta e organize seu dinheiro com clareza.</h1>
          <p>
            Comece pelo plano gratuito, teste a organização mensal e evolua para recursos Pro ou
            Família quando fizer sentido para sua rotina.
          </p>
          <div className="authChecklist">
            <span>Sem cartão no primeiro acesso</span>
            <span>Dados isolados por usuário</span>
            <span>Você escolhe quando evoluir de plano</span>
          </div>
        </div>

        <form className="authCard" aria-label="Criar conta">
          <h2>Criar conta</h2>
          <label>
            Nome
            <input type="text" name="name" placeholder="Seu nome" autoComplete="name" />
          </label>
          <label>
            E-mail
            <input type="email" name="email" placeholder="voce@email.com" autoComplete="email" />
          </label>
          <label>
            Senha
            <input type="password" name="password" placeholder="Crie uma senha segura" autoComplete="new-password" />
          </label>
          <button type="button" className="primaryButton authSubmit">
            Começar grátis
          </button>
          <a href="/login">Já tenho conta</a>
          <p className="formNote">Você começa pelo plano gratuito e pode revisar seu plano depois.</p>
        </form>
      </section>
    </main>
  );
}
