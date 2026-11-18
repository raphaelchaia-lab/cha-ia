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

## Instalação no Claude
1. Preencha `cha-ia/config/titular.md` e coloque o seu `timbrado.docx` em `cha-ia/assets/`.
2. Compacte a pasta `cha-ia` em um .zip (a pasta inteira, com o `SKILL.md` dentro dela).
3. No Claude, ative a execução de código e criação de arquivos e a pesquisa na web.
4. Em Configurações > Capacidades > Skills, envie o .zip.
5. Opcional: conecte o Google Drive para usar a biblioteca de modelos e o arquivo de peças.
6. Numa conversa nova, digite `/setup` para testar pesquisa, timbrado e geração de arquivos.

As opções de menu podem mudar; consulte a central de ajuda do Claude se não encontrar.

## Limites
- A skill não substitui o advogado: toda peça é minuta para revisão profissional.
- Não há conector de jurisprudência brasileira: a verificação é feita nos portais oficiais pela pesquisa web.
- Prazos e cálculos sempre exigem conferência no sistema do tribunal.
- Dados de clientes não devem ir para buscas públicas (a skill anonimiza as consultas).
