import os
import threading
from PIL import Image, ImageFont, ImageDraw
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import chromedriver_autoinstaller
import tkinter as tk
from tkinter import ttk, messagebox

# ------------------------------------------------------------------------------------------
# PARTE 1: Lógica de Backend (Scraper e Geração de Imagens)
# ------------------------------------------------------------------------------------------

def criarImagens(infoLiturgia, status_callback=print):
    # 1. Configuração de Diretórios
    nome_pasta = "src"
    if not os.path.exists(nome_pasta):
        os.makedirs(nome_pasta)

    caminho_txt = os.path.join(nome_pasta, 'informações.txt')
    try:
        with open(caminho_txt, 'w', encoding='utf-8') as f:
            for info in infoLiturgia:
                f.write(f'{info}\n')
    except Exception as e:
        status_callback(f"Erro ao salvar txt: {e}")

    if len(infoLiturgia) < 6:
        status_callback("Erro: Dados insuficientes.")
        return

    # 2. Processamento
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

    # 3. Cores
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

    # 4. Fontes
    caminho_fonte = "./Resources/Fontes/arial_bold.TTF"
    try:
        font_main = ImageFont.truetype(caminho_fonte, 20, encoding='utf-8')
        font_salmo = ImageFont.truetype(caminho_fonte, 18, encoding='utf-8')
    except IOError:
        status_callback("Aviso: Fonte não encontrada.")
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
            status_callback(f"Erro: Fundo {cor_str}.png não encontrado.")
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

            image.save(os.path.join(nome_pasta, f'{nome_arquivo}.png'))
            image.close()
        except Exception as e:
            status_callback(f"Erro ao processar {nome_arquivo}: {e}")

    for item in liturgia:
        nome, txt_sup, txt_inf = item
        eh_salmo = (nome == "Salmo")
        processar_imagem(nome, txt_sup, txt_inf, eh_salmo)

    for card in outrosCards:
        processar_imagem(card, card, tempoLiturgico)

    status_callback(f"Sucesso! {len(liturgia) + len(outrosCards)} imagens geradas em './{nome_pasta}'")


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
            return self.browser.find_element("xpath", xpath).text.strip()
        except:
            return default

    def _obter_html_elemento(self, by, value):
        try:
            return self.browser.find_element(by, value).get_attribute('outerHTML')
        except:
            return None

    def obter_titulo_dia_semana(self):
        return self._obter_texto_elemento('//*[@id="interno"]/div[2]')

    def obter_tempo_liturgico(self):
        html = self._obter_html_elemento("id", 'texto')
        if not html: return "Tempo não encontrado", "Cor não encontrada"
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
                if next_elem: return next_elem.get_text(strip=True)
        return ""

    def obter_liturgia(self):
        html = self._obter_html_elemento("tag name", 'body')
        if not html: return []
        soup = BeautifulSoup(html, 'html.parser')
        divs_liturgia = soup.find_all("div", {"class": "subtitulo-liturgia"})
        
        dados = {"primeira": "", "salmo": "", "segunda": "", "evangelho": ""}
        resposta_salmo = self.obter_resposta_salmo(soup)
        
        for div in divs_liturgia:
            texto = div.get_text(strip=True).lower()
            if "primeira leitura" in texto: dados["primeira"] = div.get_text(strip=True)
            elif "segunda leitura" in texto: dados["segunda"] = div.get_text(strip=True)
            elif "salmo" in texto or texto.startswith("sl"): dados["salmo"] = div.get_text(strip=True)
            elif "evangelho" in texto: dados["evangelho"] = div.get_text(strip=True)
        
        return [dados["primeira"], dados["salmo"], dados["segunda"], dados["evangelho"], resposta_salmo]

    def fechar(self):
        self.browser.quit()


# ------------------------------------------------------------------------------------------
# PARTE 2: Interface Gráfica (Tkinter Moderno)
# ------------------------------------------------------------------------------------------

class LiturgiaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Liturgia Generator v2.0")
        self.root.geometry("650x750")
        self.root.configure(bg="#f0f2f5")
        
        # Estilo Moderno
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Cores e Fontes
        self.bg_color = "#f0f2f5"
        self.btn_color = "#4CAF50"
        self.btn_hover = "#45a049"
        self.font_family = "Segoe UI"
        
        # Configuração de Estilos
        self.style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        self.style.configure("TNotebook.Tab", padding=[20, 10], font=(self.font_family, 11, 'bold'), background="#ffffff")
        self.style.map("TNotebook.Tab", background=[("selected", self.btn_color)], foreground=[("selected", "white"), ("!selected", "black")])
        
        self.style.configure("TFrame", background="#ffffff")
        self.style.configure("TLabel", background="#ffffff", font=(self.font_family, 10), foreground="#333333")
        self.style.configure("Header.TLabel", font=(self.font_family, 16, 'bold'), foreground="#2c3e50")
        self.style.configure("Status.TLabel", font=(self.font_family, 10, "italic"), foreground="#7f8c8d")
        
        self.style.configure("Accent.TButton", font=(self.font_family, 11, 'bold'), padding=15, background=self.btn_color, foreground="white")
        self.style.map("Accent.TButton", background=[("active", self.btn_hover)])

        self.style.configure("TEntry", padding=10, font=(self.font_family, 10), fieldbackground="white")

        # Container Principal
        self.main_frame = tk.Frame(root, bg=self.bg_color)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        header = tk.Label(self.main_frame, text="GERADOR DE LITURGIA", font=(self.font_family, 22, 'bold'), bg=self.bg_color, fg="#2c3e50")
        header.pack(pady=(0, 20))

        # Notebook (Abas)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True)

        # --- ABA AUTOMÁTICA ---
        self.tab_auto = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(self.tab_auto, text="Automático")
        
        auto_title = ttk.Label(self.tab_auto, text="Modo Automático", style="Header.TLabel")
        auto_title.pack(pady=(0, 10))
        
        auto_desc = ttk.Label(self.tab_auto, text="O sistema acessará o site da Paulus\nbaixará a liturgia do dia e gerará as imagens.", justify="center")
        auto_desc.pack(pady=(0, 30))

        self.btn_gerar_auto = ttk.Button(self.tab_auto, text="GERAR LITURGIA DO DIA", style="Accent.TButton", command=self.iniciar_automatico)
        self.btn_gerar_auto.pack(pady=20, ipadx=20)
        
        self.status_label_auto = ttk.Label(self.tab_auto, text="Aguardando...", style="Status.TLabel")
        self.status_label_auto.pack(pady=20)

        # --- ABA MANUAL (CORRIGIDA) ---
        self.tab_manual = ttk.Frame(self.notebook, padding=0)
        self.notebook.add(self.tab_manual, text="Manual")

        # Canvas e Scrollbar para a aba manual
        canvas = tk.Canvas(self.tab_manual, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab_manual, orient="vertical", command=canvas.yview)
        
        # Frame que estará dentro do Canvas (onde os widgets ficam)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Cria a janela dentro do canvas contendo o frame
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=600) # Largura fixa para evitar encolhimento

        # Configura o canvas para usar a scrollbar
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Empacota o Canvas e a Scrollbar (ISSO ESTAVA FALTANDO)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Frame interno para organizar os widgets com padding visual
        form_frame = ttk.Frame(scrollable_frame, padding=20)
        form_frame.pack(fill="both", expand=True)

        manual_title = ttk.Label(form_frame, text="Inserir Dados Manualmente", style="Header.TLabel")
        manual_title.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="ew")

        # Campos de Entrada
        self.entries = {}
        campos = [
            ("titulo", "Título (Nome da Pasta)"),
            ("tempo", "Tempo Litúrgico (Ex: 23º Domingo Comum)"),
            ("cor", "Cor (verde, branco, vermelho, roxo, rosa)"),
            ("primeira", "Primeira Leitura"),
            ("salmo", "Salmo (Referência)"),
            ("resposta", "Resposta do Salmo"),
            ("evangelho", "Evangelho"),
            ("segunda", "Segunda Leitura (Deixar vazio se não houver)")
        ]

        for i, (key, label) in enumerate(campos):
            lbl = ttk.Label(form_frame, text=label)
            lbl.grid(row=i+1, column=0, sticky="w", pady=5, padx=(0, 10))
            
            entry = ttk.Entry(form_frame, width=40)
            entry.grid(row=i+1, column=1, pady=5, sticky="ew")
            self.entries[key] = entry
        
        # Configura a coluna 1 para expandir
        form_frame.columnconfigure(1, weight=1)

        self.btn_gerar_manual = ttk.Button(form_frame, text="GERAR IMAGENS MANUAIS", style="Accent.TButton", command=self.iniciar_manual)
        self.btn_gerar_manual.grid(row=len(campos)+2, column=0, columnspan=2, pady=30, sticky="ew")

    def update_status(self, message):
        """Atualiza o label de status na aba automática."""
        self.status_label_auto.config(text=message)
        self.root.update_idletasks()

    def iniciar_automatico(self):
        """Inicia o processo automático em uma thread separada para não travar a UI."""
        self.btn_gerar_auto.config(state="disabled")
        self.status_label_auto.config(text="Iniciando navegador...")
        
        thread = threading.Thread(target=self.run_automatico_thread)
        thread.start()

    def run_automatico_thread(self):
        link = "https://www.paulus.com.br/portal/liturgia-diaria/"
        scraper = None
        try:
            # headless=True para não aparecer a janela do chrome (rodar em segundo plano)
            scraper = LiturgiaScraper(headless=True)
            scraper.acessar_site(link)
            
            self.update_status("Coletando dados...")
            titulo_dia = scraper.obter_titulo_dia_semana()
            tempo, cor = scraper.obter_tempo_liturgico()
            liturgia_lista = scraper.obter_liturgia()
            
            infoLiturgia = [
                titulo_dia, tempo.split("\n")[0], cor,
                liturgia_lista[0], liturgia_lista[1], liturgia_lista[2],
                liturgia_lista[3], liturgia_lista[4]
            ]
            
            self.update_status("Gerando imagens...")
            criarImagens(infoLiturgia, status_callback=self.update_status)
            
            self.update_status(f"Concluído: {titulo_dia}")
            messagebox.showinfo("Sucesso", f"Liturgia de '{titulo_dia}' gerada com sucesso na pasta 'src'!")
            
        except Exception as e:
            self.update_status("Ocorreu um erro.")
            messagebox.showerror("Erro", f"Erro durante a automação:\n{str(e)}")
        finally:
            if scraper:
                scraper.fechar()
            # Reabilita o botão na thread principal
            self.root.after(0, lambda: self.btn_gerar_auto.config(state="normal"))

    def iniciar_manual(self):
        """Pega dados dos campos e gera imagens."""
        dados = {k: v.get() for k, v in self.entries.items()}
        
        # Validação básica
        obrigatorios = ["tempo", "cor", "primeira", "salmo", "resposta", "evangelho"]
        for campo in obrigatorios:
            if not dados[campo]:
                messagebox.showerror("Erro", f"O campo '{campo}' é obrigatório!")
                return

        # Monta a lista no formato esperado por criarImagens
        infoLiturgia = [
            dados.get("titulo") if dados.get("titulo") else dados.get("tempo"), # Nome da pasta
            dados["tempo"],
            dados["cor"],
            dados["primeira"],
            dados["salmo"],
            dados["segunda"], # Pode ser vazio
            dados["evangelho"],
            dados["resposta"]
        ]

        try:
            criarImagens(infoLiturgia, status_callback=self.update_status)
            messagebox.showinfo("Sucesso", "Imagens geradas com sucesso na pasta 'src'!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar imagens:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LiturgiaApp(root)
    root.mainloop()