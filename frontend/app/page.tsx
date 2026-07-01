const benefits = [
  "Importe extratos e cartões em segundos",
  "Visualize seus gastos com clareza",
  "Receba insights e recomendações da IA",
  "Planeje metas e acompanhe sua evolução"
];

const summaryCards = [
  { label: "Saldo atual", value: "R$ 8.560,45", note: "+ R$ 1.230,00 vs Maio" },
  { label: "Receitas", value: "R$ 12.450,00", note: "Junho 2026" },
  { label: "Despesas", value: "R$ 3.889,55", note: "Junho 2026" },
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
  { title: "Seus gastos com delivery aumentaram 32%", action: "Ver detalhes" },
  { title: "Você pode economizar até R$ 320/mês", action: "Revisar" },
  { title: "Você está no caminho certo para alcançar suas metas", action: "Ver metas" }
];

const goals = [
  { name: "Viagem férias", value: "R$ 2.450,00 / R$ 5.000,00", progress: 49, icon: "palm" },
  { name: "Reserva de emergência", value: "R$ 8.560,00 / R$ 15.000,00", progress: 57, icon: "home" },
  { name: "Educação", value: "R$ 1.200,00 / R$ 10.000,00", progress: 12, icon: "cap" }
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

function LogoMark() {
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

function Icon({ name }: { name: string }) {
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

function GoalIcon({ icon }: { icon: string }) {
  return (
    <span className={`goalIcon ${icon}`} aria-hidden="true">
      {icon === "palm" ? "✦" : icon === "home" ? "⌂" : "◆"}
    </span>
  );
}

export default function Home() {
  return (
    <main>
      <header className="siteHeader">
        <a className="brand" href="#" aria-label="Finanças Pro IA">
          <LogoMark />
          <span>Finanças Pro IA</span>
        </a>
        <nav aria-label="Navegação principal">
          <a href="#beneficios">Benefícios</a>
          <a href="#planos">Planos</a>
          <a href="#entrar">Entrar</a>
        </nav>
        <a className="headerCta" href="#planos">
          Começar grátis
        </a>
      </header>

      <section className="hero" id="beneficios">
        <div className="heroCopy">
          <h1>Controle financeiro pessoal com IA</h1>
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
            <a className="primaryButton" href="#planos">
              Começar grátis
            </a>
            <a className="secondaryButton" href="/login">
              Já tenho conta
            </a>
          </div>
          <p className="securityNote">Seus dados protegidos com segurança de nível bancário.</p>
        </div>

        <div className="productPreview" aria-label="Prévia do painel financeiro">
          <aside className="previewSidebar">
            <LogoMark />
            {["Resumo", "Transações", "Relatórios", "Metas", "Planejamento", "Insights da IA", "Contas"].map(
              (item, index) => (
                <span className={index === 0 ? "active" : ""} key={item}>
                  {item}
                </span>
              )
            )}
            <button>Ajuda</button>
          </aside>
          <div className="previewContent">
            <div className="previewTopbar">
              <h2>Resumo</h2>
              <div className="topbarControls">
                <span>Junho 2026</span>
                <span>Olá, Pedro</span>
              </div>
            </div>
            <div className="summaryGrid">
              {summaryCards.map((card) => (
                <article key={card.label} className="summaryCard">
                  <span>{card.label}</span>
                  <strong>{card.value}</strong>
                  <small>{card.note}</small>
                </article>
              ))}
            </div>
            <div className="dashboardGrid">
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
                <h3>Insights da IA</h3>
                {insights.map((insight) => (
                  <div className="insightRow" key={insight.title}>
                    <span>{insight.title}</span>
                    <button>{insight.action}</button>
                  </div>
                ))}
              </section>
            </div>
            <section className="goalsPanel">
              <h3>Progresso das metas</h3>
              <div className="goalsGrid">
                {goals.map((goal) => (
                  <article key={goal.name}>
                    <GoalIcon icon={goal.icon} />
                    <div>
                      <strong>{goal.name}</strong>
                      <span>{goal.value}</span>
                      <div className="progressTrack">
                        <i style={{ width: `${goal.progress}%` }} />
                      </div>
                    </div>
                    <small>{goal.progress}%</small>
                  </article>
                ))}
              </div>
            </section>
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
