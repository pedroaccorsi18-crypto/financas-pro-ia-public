# Testes reais de RLS

Esta suíte valida o isolamento entre dois usuários reais em um projeto Supabase
exclusivamente de teste. Ela não cria usuários, não usa `service_role` e não
altera schema, migrations, policies ou autenticação.

## Cobertura

- SELECT, INSERT, UPDATE e DELETE isolados em `transacoes`,
  `metas_financeiras` e `feedbacks_oraculo`.
- Tentativas de INSERT com `user_id` forjado e INSERT de transação com
  `user_id` nulo.
- Tentativa de transferir a propriedade de uma transação via UPDATE.
- RPC `substituir_lote_importado` com `user_id` forjado no payload,
  `p_user_id` forjado no parâmetro e validação específica do proprietário e
  do lote final.
- SELECT, INSERT e RPC sem sessão autenticada.

## Proteções

- A execução é opt-in e fica ignorada sem `SUPABASE_RLS_INTEGRATION_TESTS=1`.
- A URL precisa corresponder exatamente à URL explicitamente permitida.
- É necessário confirmar que o projeto não é produção.
- URLs cujo host contenha `prod`, `production` ou `live` são bloqueadas.
- Somente chave publishable ou JWT legado com papel `anon` é aceita.
- Tokens, senhas, JWTs e secrets não são impressos.
- Cada execução usa um marcador UUID e o cleanup afeta somente descrições com
  esse marcador ou campos equivalentes nas tabelas auditadas.

## Limite do cleanup

O cleanup usa somente os dois usuários autenticados e respeita a própria RLS.
Por isso, ele consegue remover e verificar apenas registros visíveis para esses
usuários. Se uma falha de segurança criar um registro com proprietário
inesperado e invisível para ambos, a suíte não consegue detectá-lo ou removê-lo
sem elevar privilégios.

Cleanup global só é garantido executando a suíte em ambiente descartável, que
possa ser recriado após o teste, ou usando uma rotina administrativa externa,
separada da suíte e cuidadosamente limitada ao marcador UUID da execução.

## Configuração

Configure as variáveis somente no terminal usado para o teste:

```powershell
$env:SUPABASE_RLS_INTEGRATION_TESTS = "1"
$env:SUPABASE_RLS_CONFIRMED_NON_PRODUCTION = "YES"
$env:SUPABASE_RLS_TEST_URL = "https://PROJETO-DE-TESTE.supabase.co"
$env:SUPABASE_RLS_ALLOWED_URL = $env:SUPABASE_RLS_TEST_URL
$env:SUPABASE_RLS_TEST_ANON_KEY = "CHAVE_PUBLICA_OU_ANON"
$env:SUPABASE_RLS_TEST_USER_A_EMAIL = "usuario-a-de-teste@example.com"
$env:SUPABASE_RLS_TEST_USER_A_PASSWORD = "senha-do-usuario-a"
$env:SUPABASE_RLS_TEST_USER_B_EMAIL = "usuario-b-de-teste@example.com"
$env:SUPABASE_RLS_TEST_USER_B_PASSWORD = "senha-do-usuario-b"
```

Os dois usuários devem existir previamente no Supabase Auth do projeto de teste.
Não reutilize credenciais ou URL de produção.

## Execução

Execute apenas a suíte de integração:

```powershell
python -m unittest tests.integration.test_supabase_rls -v
```

Sem o opt-in, a suíte é ignorada. Em caso de falha no cleanup, o resultado
informa o marcador único, a tabela e os IDs que permaneceram visíveis para cada
usuário.
