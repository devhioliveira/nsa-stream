import os
import time
import textwrap
from PIL import Image, ImageFont, ImageDraw
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import chromedriver_autoinstaller

# ------------------------------------------------------------------------------------------
# PARTE 1: Funções de Geração de Imagens
# ------------------------------------------------------------------------------------------

def criarImagens(infoLiturgia):
    # 1. Configuração de Diretórios e Arquivos
    # ALTERAÇÃO: Pasta definida como 'src'
    nome_pasta = "src"
    
    # Cria a pasta 'src' se não existir
    if not os.path.exists(nome_pasta):
        os.makedirs(nome_pasta)

    # Salva o arquivo de informações na pasta src
    caminho_txt = os.path.join(nome_pasta, 'informações.txt')
    with open(caminho_txt, 'w', encoding='utf-8') as f:
        for info in infoLiturgia:
            f.write(f'{info}\n')

    # 2. Processamento das Informações da Liturgia
    if len(infoLiturgia) < 6:
        print("Erro: Lista infoLiturgia não contém elementos suficientes.")
        return

    primeiraLeitura = infoLiturgia[3]
    salmo = infoLiturgia[4]
    respostaSalmo = infoLiturgia[-1]
    evangelho = infoLiturgia[-2]
    
    segundaLeitura = ""
    infoLiturgia_1 = str(infoLiturgia[1])
    
    if "DOMINGO" in str(infoLiturgia[0]).upper():
        if len(infoLiturgia) > 5:
            segundaLeitura = infoLiturgia[5]
        
        if infoLiturgia_1 and infoLiturgia_1[0].isdigit():
            idx_insert = 2 if len(infoLiturgia_1) > 1 and infoLiturgia_1[1].isdigit() else 2
            if "DOMINGO" not in infoLiturgia_1.upper():
                 infoLiturgia[1] = infoLiturgia_1[:idx_insert] + " DOMINGO" + infoLiturgia_1[idx_insert:]

    tempoLiturgico = infoLiturgia[1].title()

    # 3. Definição de Cores
    mapa_cores = {
        "branco": "white", "verde": "green", "vermelho": "red",
        "roxo": "purple", "rosa": "pink", "azul": "blue"
    }
    
    cor_str = "white"
    info_cor = str(infoLiturgia[2]).lower()
    for cor_pt, cor_en in mapa_cores.items():
        if cor_pt in info_cor:
            cor_str = cor_en
            break
            
    if cor_str == "white":
        colorText1 = "black"
        colorText2 = "black"
    else:
        colorText1 = "white"
        colorText2 = cor_str

    # 4. Configuração de Fontes e Layout
    caminho_fonte = "./Resources/Fontes/arial_bold.TTF"
    
    try:
        font_main = ImageFont.truetype(caminho_fonte, 20, encoding='utf-8')
        font_salmo = ImageFont.truetype(caminho_fonte, 18, encoding='utf-8')
    except IOError:
        print(f"Aviso: Fonte não encontrada em {caminho_fonte}. Usando padrão.")
        font_main = ImageFont.load_default()
        font_salmo = font_main

    liturgia = [
        ["Primeira Leitura", primeiraLeitura, tempoLiturgico],
        ["Salmo", salmo, respostaSalmo],
        ["Segunda Leitura", segundaLeitura, tempoLiturgico],
        ["Evangelho", evangelho, tempoLiturgico]
    ]

    outrosCards = [
        "Canto de Entrada", "Ato Penitencial", "Glória a Deus", "Canto da Comunhão", 
        "Rito do Ofertório", "Preces da Assembleia", "Liturgia Eucarística", 
        "Profissão de Fé", "Preparação das Oferendas", "Oração Eucarística", "Rito da Comunhão"
    ]
    
    def centralizar_texto(draw, texto, y_pos, fonte, largura_img, cor):
        if not texto: return
        bbox = draw.textbbox((0, 0), texto, font=fonte)
        text_width = bbox[2] - bbox[0]
        x_pos = (largura_img - text_width) / 2
        draw.text((x_pos, y_pos), texto, font=fonte, fill=cor)

    def processar_imagem(nome_arquivo, texto_sup, texto_inf, eh_salmo=False):
        if nome_arquivo == "Segunda Leitura" and not texto_sup:
            return

        caminho_img = f'Resources/Imagens/{cor_str}.png'
        
        if not os.path.exists(caminho_img):
            print(f"Erro: Imagem de fundo não encontrada: {caminho_img}")
            return

        try:
            image = Image.open(caminho_img)
            draw = ImageDraw.Draw(image)
            img_w, img_h = image.size
            
            draw.text((165, 12), texto_sup, font=font_main, fill=colorText1)

            y_inferior = 62 
            
            if eh_salmo:
                y_inferior = 56
                font_uso = font_main
                
                bbox = draw.textbbox((0, 0), texto_inf, font=font_uso)
                text_w = bbox[2] - bbox[0]
                
                if text_w > (img_w * 0.80):
                    meio_char = len(texto_inf) // 2
                    split_idx = texto_inf.rfind(' ', 0, meio_char)
                    if split_idx == -1: split_idx = texto_inf.find(' ', meio_char)
                    
                    if split_idx != -1:
                        parte1 = texto_inf[:split_idx].strip()
                        parte2 = texto_inf[split_idx:].strip()
                        
                        centralizar_texto(draw, parte1, 52, font_salmo, img_w, colorText2)
                        centralizar_texto(draw, parte2, 77, font_salmo, img_w, colorText2)
                    else:
                        centralizar_texto(draw, texto_inf, y_inferior, font_salmo, img_w, colorText2)
                else:
                    centralizar_texto(draw, texto_inf, y_inferior, font_uso, img_w, colorText2)
            else:
                centralizar_texto(draw, texto_inf, y_inferior, font_main, img_w, colorText2)

            # Salva na pasta definida (src)
            image.save(os.path.join(nome_pasta, f'{nome_arquivo}.png'))
            image.close()
            
        except Exception as e:
            print(f"Erro ao processar {nome_arquivo}: {e}")

    # Loop de Geração
    for item in liturgia:
        nome, txt_sup, txt_inf = item
        eh_salmo = (nome == "Salmo")
        processar_imagem(nome, txt_sup, txt_inf, eh_salmo)

    for card in outrosCards:
        processar_imagem(card, card, tempoLiturgico)

    print(f"Finalizado: {len(liturgia) + len(outrosCards)} imagens geradas em './{nome_pasta}'")


# ------------------------------------------------------------------------------------------
# PARTE 2: Classe do Scraper
# ------------------------------------------------------------------------------------------

class LiturgiaScraper:
    def __init__(self, headless=True):
        chromedriver_autoinstaller.install("./")
        
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        self.browser = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.browser, 10)

    def acessar_site(self, link):
        self.browser.get(link)

    def _obter_texto_elemento(self, xpath, default=""):
        try:
            element = self.browser.find_element("xpath", xpath)
            return element.text.strip()
        except:
            return default

    def _obter_html_elemento(self, by, value):
        try:
            element = self.browser.find_element(by, value)
            return element.get_attribute('outerHTML')
        except:
            return None

    def obter_titulo_dia_semana(self):
        xpath_titulo = '//*[@id="interno"]/div[2]'
        return self._obter_texto_elemento(xpath_titulo)

    def obter_tempo_liturgico(self):
        html = self._obter_html_elemento("id", 'texto')
        if not html:
            return "Tempo não encontrado", "Cor não encontrada"

        soup = BeautifulSoup(html, 'html.parser')
        paragrafos = soup.find_all('p')

        tempo_liturgico = paragrafos[0].text if paragrafos else ""
        
        cor_liturgico = ""
        for p in paragrafos:
            if '(' in p.text:
                cor_liturgico = p.text
                break
        
        return tempo_liturgico, cor_liturgico

    def obter_resposta_salmo(self, soup_liturgias):
        divs = soup_liturgias.find_all("div", {"class": "subtitulo-liturgia"})
        
        for div in divs:
            if "Salmo" in div.text or "Sl" in div.text:
                next_elem = div.find_next_sibling(['p', 'b'])
                if next_elem:
                    return next_elem.get_text(strip=True)
        return ""

    def obter_liturgia(self):
        html = self._obter_html_elemento("tag name", 'body')
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        divs_liturgia = soup.find_all("div", {"class": "subtitulo-liturgia"})
        
        dados = {
            "primeira": "",
            "salmo": "",
            "segunda": "",
            "evangelho": ""
        }
        
        resposta_salmo = self.obter_resposta_salmo(soup)
        
        for div in divs_liturgia:
            texto = div.get_text(strip=True).lower()
            
            if "primeira leitura" in texto:
                dados["primeira"] = div.get_text(strip=True)
            elif "segunda leitura" in texto:
                dados["segunda"] = div.get_text(strip=True)
            elif "salmo" in texto or texto.startswith("sl"):
                dados["salmo"] = div.get_text(strip=True)
            elif "evangelho" in texto:
                dados["evangelho"] = div.get_text(strip=True)
        
        return [
            dados["primeira"],
            dados["salmo"],
            dados["segunda"],
            dados["evangelho"],
            resposta_salmo
        ]

    # ALTERAÇÃO: Método renomeado e simplificado para processar apenas o dia atual
    def processar_dia_atual(self):
        print("Processando liturgia do dia atual...")
        
        titulo_dia = self.obter_titulo_dia_semana()
        tempo, cor = self.obter_tempo_liturgico()
        liturgia_lista = self.obter_liturgia()
        
        infoLiturgia = [
            titulo_dia,
            tempo.split("\n")[0],
            cor,
            liturgia_lista[0],
            liturgia_lista[1],
            liturgia_lista[2],
            liturgia_lista[3],
            liturgia_lista[4]
        ]
        
        print(f"  -> Gerando imagens para: {titulo_dia}")
        try:
            criarImagens(infoLiturgia)
        except Exception as e:
            print(f"  -> Erro ao gerar imagens: {e}")

    def fechar(self):
        self.browser.quit()


# ------------------------------------------------------------------------------------------
# PARTE 3: Execução Principal
# ------------------------------------------------------------------------------------------

link = "https://www.paulus.com.br/portal/liturgia-diaria/"

def main():
    print("Iniciando navegador...")
    # headless=False para ver o navegador abrir. Mude para True para rodar escondido.
    scraper = LiturgiaScraper(headless=False)
    
    try:
        scraper.acessar_site(link)
        # Chama o novo método para processar apenas o dia atual
        scraper.processar_dia_atual()
        
    except Exception as e:
        print(f"Ocorreu um erro durante a execução: {e}")
    finally:
        print("Fechando navegador...")
        scraper.fechar()

if __name__ == "__main__":
    main()
    print("Processo finalizado com sucesso!")