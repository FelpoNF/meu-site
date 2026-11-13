# Byline Studio — site

Página única do estúdio que produz produtos digitais sob medida a partir do conteúdo de criadores. Site normal, sem campanha: serve para o criador que chega por indicação, por busca ou por um link que você mandou.

## Arquivos

| Arquivo | O que é |
|---|---|
| `index.html` | a página inteira (CSS e JS embutidos, sem build, sem dependências) |
| `privacy.html` | política de privacidade em linguagem simples |
| `og-image.png` | 1200×630 — o cartão que aparece quando alguém compartilha o link |
| `favicon.svg` | ícone da aba (os cinco livros, fundo transparente, 675 bytes) |
| `apple-touch-icon.png` | 180×180 — ícone do atalho na tela inicial do iPhone (iOS ignora transparência, por isso tem fundo `#F2F4F7`) |
| `verify.py` | verificação de desenvolvimento (170 checagens em Chrome headless); não precisa ir para o servidor |
| `preview-desktop.png` / `preview-mobile.png` | primeira tela em 1440×900 e 500×800 (não precisam ir para o servidor) |
| `preview-finale.png` | a seção amarela com o calendário, 1440×520 |

Nenhum arquivo do site depende de servidor, Node, npm ou build step. Copiar a pasta para qualquer host funciona.

## O que você precisa preencher (3 linhas)

No topo do `<script>` de `index.html`:

```js
const BRAND        = "Byline Studio";
const EMAIL        = "studiobyline@gmail.com";
const WHATSAPP     = "";   // só dígitos com DDI, ex. "5511999999999" — vazio = botão do hero escondido
const CALENDLY_URL = "";   // ← cole seu link do Calendly aqui
```

Enquanto `CALENDLY_URL` estiver vazio, o botão principal vira **"Email us"** com a mensagem já escrita, e o secundário se esconde. A página nunca fica com botão morto.

## Link com nicho

Opcional. Um link como `https://bylineeditions.com/?niche=food` abre a lombada correspondente já selecionada.
Valores: `fitness`, `food`, `finance`, `wellness`, `travel`, `education`, `photography`.
Sem o parâmetro, a página abre no primeiro formato.

## Deploy

1. Suba os arquivos na raiz do domínio (ou numa pasta — os caminhos são relativos).
2. Se ficar em subpasta, troque `content="og-image.png"` por `content="https://seudominio.com/og-image.png"` — alguns previews exigem URL absoluta.
3. A página está com `noindex, nofollow`: não aparece em busca. Se quiser que apareça, apague essa linha; é a única mudança necessária.

## A intro

A primeira carga de cada sessão abre com uma cortina: a prateleira se desenha, os cinco livros caem, o nome sai de trás do ícone e, então, uma onda colorida nasce da logo e o site cresce dentro dela. A logo não viaja até o canto: é o quadro inteiro que se afasta dela.

- Roda **uma vez por sessão** (`sessionStorage`, chave `byline-intro`). Recarregar na mesma aba não repete; aba nova ou anônima repete.
- Qualquer clique na tela, `Esc` ou `Espaço` pula direto para a página.
- Quem configurou `prefers-reduced-motion` não vê nada: a página abre normal, sem cortina.
- O ritmo está em `SPEED`, no script do fim do `index.html`. A timeline inteira é dividida por ele: aumentar acelera, diminuir desacelera. Hoje `1.265`.
- O zoom é feito **na página**, não na logo: ela nasce ampliada na escala exata que faz a logo da nav coincidir com a logo grande (verificado: desvio 0 em x, y, largura e altura). Por isso a troca de uma cópia pela outra é invisível, e por isso a logo chega ao canto sem parecer que andou.
- O raio da abertura cresce **linear no tempo** e a escala da página usa `easeCam` (entra e sai devagar). São curvas separadas de propósito: o anel é a borda da abertura, então é o raio linear que mantém o anel atravessando a tela durante toda a abertura. Com o `easeOut³` antigo ele entregava 88% da distância na primeira metade e sumia no canto, deixando a segunda metade sem anel.
- `rMax` é a distância até o canto mais longe do viewport **medida a partir de onde a onda nasce**, mais 24px. A diagonal inteira (`hypot(w,h)`) exagerava a partir de uma origem no canto: o excedente era tempo com o anel já fora da tela.
- A espessura do anel vem de `--ring-w` (18px no tamanho cheio). Como o elemento é escalado por `rs/rMax`, a faixa engrossa conforme atravessa a tela: ~5px ao nascer junto da logo, 18px no canto. O anel não tem fade: ele sai pela borda da tela no último quadro.
- Um único valor manda na onda: ele define o raio do círculo, o anel na borda desse círculo e o centro da abertura. Logo, onda e abertura ficam concêntricos o tempo todo.
- Se a animação falhar por qualquer motivo, um vigia tira a cortina em 9s e a página aparece.

## Verificação

Não existe build nem framework de teste: a página é um HTML estático com CSS e JS inline. O `verify.py` é a suíte que existe — ele abre a página num Chrome headless de verdade e mede o que foi renderizado, em vez de confiar no código-fonte.

```bash
python3 verify.py
```

170 checagens: marca e logo, hero em 2 linhas e 90svh em sete larguras, os 3 passos, acordeão do FAQ (uma resposta aberta por vez), simetria do FAQ, faixa de 7 segmentos, botão do WhatsApp, ícone da aba, calendário desenhado, overflow e erros de JS — mais a intro inteira medida no navegador: cortina no primeiro paint, logo grande e logo da nav coincidindo pixel a pixel no início da onda, anel concêntrico, escala natural no fim, abertura cobrindo todos os cantos do viewport, `skip`, `prefers-reduced-motion` e a marcação da sessão. Sai com `0` quando tudo passa e `1` quando algo falha; em caso de falha os arquivos de probe ficam em `%TEMP%` para inspeção.

Precisa de Python 3 e Chrome (o `CHROME_PATH` resolve se o Chrome estiver fora do padrão). Se o `node` existir, ele também valida a sintaxe dos scripts inline; sem node essa checagem é pulada e o script diz isso.

Rodar sempre depois de editar `index.html` ou `privacy.html`, e antes de dar push.

## O que a página promete (confirme antes de publicar)

A página não inventa fato nenhum — mas afirma coisas sobre o seu processo. Você precisa conseguir cumprir todas:

- Você aprova cada rascunho antes de qualquer publicação; nada sai sem o seu sim.
- A escrita, a capa e os arquivos são produzidos por você; o criador não escreve nem diagrama.
- A entrega ao comprador é sua ("everything between the buyer and the product is ours to handle").
- Você entrega o material de anúncio (copy + imagens) junto com o produto.
- A conversa sobre termos acontece linha por linha, e cláusula pode ser negociada.

Se alguma dessas não for verdade, me diga qual e eu reescrevo a seção — não deixo a página prometer o que você não faz.

## O que ficou de fora, de propósito

- **Preço, divisão de receita, propriedade, prazo.** Nenhum número no site. A seção "The terms" diz que os termos são escritos e revisados linha por linha antes de assinar. Quando você tiver os números, viram uma seção própria.
- **Depoimentos.** Nada. Placeholder em página de confiança é pior que ausência.
- **Página de Terms.** Não se publica termo de um acordo que ainda não existe.
- **Formulário.** Não existe: CTA é agenda ou e-mail. Zero fricção, zero dado coletado.

## Decisões de estrutura que valem saber

- **A estante é o sistema visual.** Os sete formatos são amostras de produto (cookbook, workbook, journal, guide), não trabalhos de clientes — o painel diz isso explicitamente.
- **"Digital product" no posicionamento, "livro" no formato.** O hero fala de produto digital; os formatos mostram que o produto é um livro/workbook. Se um dia você fizer curso ou ferramenta, a estante continua servindo.
- **Sem a moldura de convite.** Não há "prepared for [nome]", nem "you got our email", nem `?name=`. A página se sustenta sozinha em qualquer origem de tráfego.

## Pendências suas

1. O site usa `studiobyline@gmail.com` (Gmail). Se um dia registrar `bylineeditions.com`, troque só a constante `EMAIL`.
2. Criar a conta no Calendly e colar o link.
3. Confirmar a lista de promessas acima.
4. Logo definitivo — o mark de três lombadas é placeholder funcional e já combina com a página.
5. Se trocar o nome da marca: `BRAND`, `EMAIL`, `<title>`, os `[data-brand]`, `og:site_name`, `og:title` e `og-image.png`. Eu refaço em um minuto.
