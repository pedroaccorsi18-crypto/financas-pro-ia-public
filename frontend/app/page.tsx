import { Icon, SiteHeader } from "@/components/brand";

const benefits = [
  "Importe extratos e cartões em segundos",
  "Visualize seus gastos com clareza",
  "Receba insights e recomendações da IA",
  "Planeje metas e acompanhe sua evolução"
];

const summaryCards = [
  { label: "Receitas", value: "R$ 12.450,00", note: "Junho 2026" },
  { label: "Despesas", value: "R$ 3.889,55", note: "Junho 2026" },
  { label: "Saldo", value: "R$ 8.560,45", note: "+ R$ 1.230,00 vs Maio" },
  { label: "Reservas", value: "R$ 15.780,30", note: "+ R$ 620,30 vs Maio" }
];

const categories = [
  { name: "Moradia", value: "29%", amount: "R$ 1.128,00", color: "#536dfe" },
  { name: "Alimentação", value: "18%", amount: "R$ 700,80", color: "#2fc66d" },
  { name: "Transporte", value: "15%", amount: "R$ 583,40", color: "#f7b731" },
  { name: "Saúde", value: "10%", amount: "R$ 389,90", color: "#ef4d5d" },
  { name: "Lazer", value: "8%", amount: "R$ 311,50", color: "#48a6ff" },
  { name: "Outros", value: "20%", amount: "R$ 775,95", color: "#cdd5df" }
];

const insights = [
  { title: "Seu gasto com delivery aumentou 32% este mês.", action: "Ver detalhes" },
  { title: "Que tal definir um limite de R$ 320/mês nessa categoria?", action: "Revisar" }
];

const plans = [
  {
    name: "Gratuito",
    price: "R$ 0",
    suffix: "para começar",
    features: [
      "Lançamentos manuais",
      "Dashboard com visão geral",
      "Metas por categoria",
      "Relatórios básicos"
    ],
    cta: "Começar grátis",
    featured: false
  },
  {
    name: "Pro",
    price: "R$ 29,90",
    suffix: "/mês",
    description: "organize e evolua suas finanças",
    features: [
      "Importação assistida de extratos",
      "Insights e recomendações da IA",
      "Metas avançadas e planejamento",
      "Relatórios completos e personalizados"
    ],
    cta: "Testar 7 dias grátis",
    featured: true
  },
  {
    name: "Família",
    price: "R$ 49,90",
    suffix: "/mês",
    description: "para até 4 pessoas",
    features: [
      "Tudo do plano Pro",
      "Até 4 contas conectadas",
      "Objetivos familiares compartilhados",
      "Visão consolidada da família"
    ],
    cta: "Testar 7 dias grátis",
    featured: false
  }
];

export default function Home() {
  return (
    <main>
      <SiteHeader />

      <section className="hero" id="beneficios">
        <div className="heroCopy">
          <h1>
            Controle financeiro
            <span>pessoal com IA</span>
          </h1>
          <p>
            Organize suas finanças, entenda seus gastos, defina metas realistas e receba
            orientações inteligentes para tomar melhores decisões todos os dias.
          </p>
          <ul className="benefitList">
            {benefits.map((benefit) => (
              <li key={benefit}>
                <span className="checkDot">
                  <Icon name="check" />
                </span>
                {benefit}
              </li>
            ))}
          </ul>
          <div className="heroActions" id="entrar">
            <a className="primaryButton" href="/cadastro">
              Começar grátis
            </a>
            <a className="secondaryButton" href="#planos">
              Ver planos
            </a>
          </div>
          <p className="securityNote">Seus dados protegidos com segurança de nível bancário.</p>
        </div>

        <div className="productPreview" aria-label="Prévia do painel financeiro">
          <div className="previewContent">
            <div className="previewTopbar">
              <div>
                <span className="previewLabel">Painel inteligente</span>
                <h2>Resumo mensal</h2>
              </div>
              <div className="topbarControls">
                <span>Junho 2026</span>
              </div>
            </div>
            <div className="monthlyStats">
              {summaryCards.slice(0, 3).map((card) => (
                <article key={card.label} className="summaryCard">
                  <span>{card.label}</span>
                  <strong>{card.value}</strong>
                  <small>{card.note}</small>
                </article>
              ))}
            </div>
            <div className="previewMainGrid">
              <section className="categoryPanel">
                <h3>Gastos por categoria</h3>
                <div className="categoryBody">
                  <div className="donut" aria-hidden="true">
                    <span>Total<br />R$ 3.889,55</span>
                  </div>
                  <div className="categoryRows">
                    {categories.map((category) => (
                      <div className="categoryRow" key={category.name}>
                        <i style={{ background: category.color }} />
                        <span>{category.name}</span>
                        <b>{category.value}</b>
                        <small>{category.amount}</small>
                      </div>
                    ))}
                  </div>
                </div>
              </section>
              <section className="insightsPanel">
                <h3>Insight da IA</h3>
                {insights.map((insight) => (
                  <div className="insightRow" key={insight.title}>
                    <span>{insight.title}</span>
                    <button>{insight.action}</button>
                  </div>
                ))}
              </section>
            </div>
          </div>
        </div>
      </section>

      <section className="pricing" id="planos">
        <p className="sectionLabel">Planos simples e transparentes</p>
        <h2>Escolha o plano ideal para você</h2>
        <div className="plansGrid">
          {plans.map((plan) => (
            <article className={`planCard ${plan.featured ? "featured" : ""}`} key={plan.name}>
              {plan.featured && <span className="popular">Mais escolhido</span>}
              <h3>{plan.name}</h3>
              <div className="priceLine">
                <strong>{plan.price}</strong>
                <span>{plan.suffix}</span>
              </div>
              {plan.description && <p>{plan.description}</p>}
              <ul>
                {plan.features.map((feature) => (
                  <li key={feature}>
                    <Icon name="check" />
                    {feature}
                  </li>
                ))}
              </ul>
              <a className={plan.featured ? "primaryButton" : "outlineButton"} href="/cadastro">
                {plan.cta}
              </a>
            </article>
          ))}
        </div>
      </section>

      <section className="trustStrip" aria-label="Confiança e segurança">
        <article>
          <Icon name="shield" />
          <div>
            <strong>Seus dados protegidos</strong>
            <span>Segurança de nível bancário</span>
          </div>
        </article>
        <article>
          <Icon name="lock" />
          <div>
            <strong>Privacidade em primeiro lugar</strong>
            <span>Seus dados não são compartilhados</span>
          </div>
        </article>
        <article>
          <Icon name="cloud" />
          <div>
            <strong>Sincronização segura</strong>
            <span>Acesse de qualquer lugar</span>
          </div>
        </article>
        <article>
          <Icon name="support" />
          <div>
            <strong>Suporte humano</strong>
            <span>Estamos aqui para ajudar</span>
          </div>
        </article>
      </section>
    </main>
  );
}
