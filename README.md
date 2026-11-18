# Cha.IA — assistente jurídico para o Claude

Skill para o Claude voltada à advocacia brasileira, com ênfase em Direito Digital:
pesquisa jurídica, jurisprudência verificada, análise de autos, prazos, cálculos,
elaboração e revisão de peças com auditoria adversarial (protocolo 2.0),
contratos, preparação de audiência e revisão de artigos e livros.

## O que vem na pasta `cha-ia/`
- `SKILL.md` — instruções da skill (núcleo, protocolo 2.0, módulos, entregáveis).
- `config/titular.md` — seus dados e preferências (preencher).
- `assets/` — onde vai o seu papel timbrado (`timbrado.docx`).
- `scripts/cha_docs.py` — gera a peça em DOCX e os relatórios em PDF sobre o seu timbrado.
- `tests/` — critérios de aceitação e prompts de teste para homologar a skill.

## Instalação no Claude (claude.ai e app)

O Claude não instala skills direto de um link do GitHub: a skill é enviada como arquivo .zip.

**Instalação rápida**
1. Baixe o arquivo [`instalar/cha-ia.zip`](instalar/cha-ia.zip) deste repositório (botão *Download raw file*).
2. No Claude, abra **Customize > Skills**, clique em **+**, depois **Create skill** e **Upload a skill**, e envie o `cha-ia.zip`.
3. Ative a execução de código e criação de arquivos e a pesquisa na web; conecte o Google Drive se quiser usar biblioteca de modelos e arquivo de peças.
4. Numa conversa nova, digite `/setup`: o Cha.IA pergunta seus dados, devolve o `config/titular.md` preenchido e testa pesquisa, timbrado e geração de arquivos.

**Instalação personalizada (recomendada)**
1. Baixe o repositório, preencha `cha-ia/config/titular.md` e coloque o seu `timbrado.docx` em `cha-ia/assets/`.
2. Compacte a pasta `cha-ia` a partir da pasta acima dela, de modo que o .zip contenha `cha-ia/SKILL.md` (o nome da pasta precisa ser `cha-ia`, igual ao campo `name` do `SKILL.md`).
3. Envie o .zip como no passo 2 da instalação rápida. Para atualizar a configuração depois, gere um novo .zip e substitua a skill.

**Claude Code**
Copie a pasta `cha-ia` para `~/.claude/skills/` (uso pessoal) ou para `.claude/skills/` do projeto.

Os nomes dos menus podem mudar; em caso de dúvida, veja a central de ajuda do Claude (support.claude.com, artigos sobre skills).


## Para conferir ementas palavra por palavra
A leitura de páginas do Claude devolve uma versão processada do texto, então a skill só marca uma ementa como VERIFICADA quando a lê no original. Para isso, faça pelo menos uma destas coisas:
- libere os domínios dos tribunais na lista de domínios permitidos das configurações de capacidades do Claude (por exemplo `scon.stj.jus.br`, `processo.stj.jus.br`, `ww2.stj.jus.br`, `portal.stf.jus.br`, `jurisprudencia.stf.jus.br` e o portal do seu TJ);
- use o Claude com um navegador disponível (Claude no Chrome ou o navegador do app de desktop);
- envie o PDF do acórdão na conversa.

## Limites
- A skill não substitui o advogado: toda peça é minuta para revisão profissional.
- Não há conector de jurisprudência brasileira: a verificação é feita nos portais oficiais pela pesquisa web.
- Prazos e cálculos sempre exigem conferência no sistema do tribunal.
- Dados de clientes não devem ir para buscas públicas (a skill anonimiza as consultas).

## Licença

CC BY-NC-SA 4.0: pode usar e adaptar com crédito ao autor, sem fins comerciais, e as adaptações devem ser distribuídas sob a mesma licença. Veja os arquivos `LICENSE` e `NOTICE`. © 2026 Raphael Sérgio Rios Chaia Jacob.
