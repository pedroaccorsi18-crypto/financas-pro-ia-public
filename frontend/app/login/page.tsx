import { SiteHeader } from "@/components/brand";

export default function LoginPage() {
  return (
    <main>
      <SiteHeader ctaHref="/cadastro" ctaLabel="Criar conta" />
      <section className="authPage">
        <div className="authIntro">
          <p className="previewLabel">Acesso seguro</p>
          <h1>Entre para acompanhar sua vida financeira.</h1>
          <p>
            Continue de onde parou: lançamentos, metas, importações e insights organizados em
            uma visão clara do seu mês.
          </p>
          <div className="authProof">
            <strong>Seu painel fica protegido por autenticação segura.</strong>
            <span>Use seu e-mail para acessar seu histórico e continuar acompanhando suas metas.</span>
          </div>
        </div>

        <form className="authCard" aria-label="Entrar na conta">
          <h2>Entrar</h2>
          <label>
            E-mail
            <input type="email" name="email" placeholder="voce@email.com" autoComplete="email" />
          </label>
          <label>
            Senha
            <input type="password" name="password" placeholder="Sua senha" autoComplete="current-password" />
          </label>
          <button type="button" className="primaryButton authSubmit">
            Entrar
          </button>
          <a href="/cadastro">Ainda não tenho conta</a>
          <a className="subtleLink" href="#">
            Esqueci minha senha
          </a>
        </form>
      </section>
    </main>
  );
}
