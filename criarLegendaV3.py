import os
import subprocess
import sys
import argparse
from datetime import datetime, timedelta

import requests
from PIL import Image, ImageFont, ImageDraw

# ------------------------------------------------------------------------------------------
# CONFIGURAÇÕES GLOBAIS
# ------------------------------------------------------------------------------------------

API_BASE_URL = "https://liturgia.up.railway.app/v2/"
OUTPUT_DIR = "src"

# ------------------------------------------------------------------------------------------
# PARTE 1: Busca da liturgia via API
# ------------------------------------------------------------------------------------------

def fetch_liturgy(day_offset: int = 0) -> dict:
    """
    Busca a liturgia do dia via API.
    day_offset: 0 = hoje, 1 = amanhã, 2 = daqui 2 dias, etc.
    """
    target_date = datetime.now() + timedelta(days=day_offset)
    day = target_date.strftime("%d")
    month = target_date.strftime("%m")
    year = target_date.strftime("%Y")

    url = f"{API_BASE_URL}?dia={day}&mes={month}&ano={year}"
    print(f"[INFO] Buscando liturgia de {target_date.strftime('%d/%m/%Y')}...")
    print(f"[INFO] URL: {url}")

    response = requests.get(url, timeout=15)

    # Verifica se a liturgia foi encontrada
    if response.status_code == 404:
        error_data = response.json()
        raise Exception(f"Liturgia não encontrada: {error_data.get('erro', 'Erro desconhecido')}")

    response.raise_for_status()
    return response.json()


def parse_liturgy_data(api_data: dict) -> list:
    """
    Converte o JSON da API para o formato de lista que criarImagens espera.
    Estrutura: [titulo, tempo, cor, primeira, salmo, segunda, evangelho, respostaSalmo]
    """
    leituras = api_data.get("leituras", {})

    # Extrai referências das leituras (pega o primeiro item de cada array)
    def get_referencia(key: str) -> str:
        items = leituras.get(key, [])
        return items[0].get("referencia", "") if items else ""

    primeira_leitura = get_referencia("primeiraLeitura")
    segunda_leitura = get_referencia("segundaLeitura")
    evangelho = get_referencia("evangelho")

    # Salmo tem estrutura diferente: referencia + refrao
    salmo_data = leituras.get("salmo", [])
    salmo_ref = salmo_data[0].get("referencia", "") if salmo_data else ""
    resposta_salmo = salmo_data[0].get("refrao", "") if salmo_data else ""

    info_liturgy = [
        api_data.get("liturgia", ""),   # [0] título do dia (ex: "Sábado da 5ª Semana...")
        api_data.get("liturgia", ""),   # [1] tempo litúrgico
        api_data.get("cor", "Branco"),  # [2] cor litúrgica
        primeira_leitura,               # [3] primeira leitura
        salmo_ref,                      # [4] salmo (referencia)
        segunda_leitura,                # [5] segunda leitura (vazio se não houver)
        evangelho,                      # [6] evangelho (index -2)
        resposta_salmo,                 # [7] resposta do salmo (index -1)
    ]

    print(f"[INFO] Liturgia: {info_liturgy[0]}")
    print(f"[INFO] Cor: {info_liturgy[2]}")
    print(f"[INFO] Primeira Leitura: {info_liturgy[3]}")
    print(f"[INFO] Salmo: {info_liturgy[4]}")
    print(f"[INFO] Resposta do Salmo: {info_liturgy[7]}")
    print(f"[INFO] Evangelho: {info_liturgy[6]}")
    if segunda_leitura:
        print(f"[INFO] Segunda Leitura: {info_liturgy[5]}")

    return info_liturgy


# ------------------------------------------------------------------------------------------
# PARTE 2: Geração das imagens (mesma lógica, sem GUI)
# ------------------------------------------------------------------------------------------

def create_images(info_liturgy: list):
    """
    Gera as imagens de liturgia na pasta OUTPUT_DIR.
    Espera lista: [titulo, tempo, cor, primeira, salmo, segunda, evangelho, respostaSalmo]
    """
    # Cria pasta de saída se não existir
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Salva dados em txt para debug/histórico
    txt_path = os.path.join(OUTPUT_DIR, "informacoes.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        for info in info_liturgy:
            f.write(f"{info}\n")

    if len(info_liturgy) < 6:
        raise ValueError("Dados insuficientes para gerar imagens.")

    # Extrai os campos
    primeira_leitura = info_liturgy[3]
    salmo = info_liturgy[4]
    resposta_salmo = info_liturgy[-1]
    evangelho = info_liturgy[-2]
    segunda_leitura = ""

    info_liturgy_1 = str(info_liturgy[1])

    # Verifica se é domingo para incluir segunda leitura
    if "DOMINGO" in str(info_liturgy[0]).upper():
        if len(info_liturgy) > 5:
            segunda_leitura = info_liturgy[5]
        # Formata o número do domingo (ex: "23" → "23 DOMINGO")
        if info_liturgy_1 and info_liturgy_1[0].isdigit():
            idx = 2
            if "DOMINGO" not in info_liturgy_1.upper():
                info_liturgy[1] = info_liturgy_1[:idx] + " DOMINGO" + info_liturgy_1[idx:]

    liturgical_time = info_liturgy[1].title()

    # Mapeamento de cores PT → EN (para nome dos arquivos de fundo)
    color_map = {
        "branco": "white",
        "verde": "green",
        "vermelho": "red",
        "roxo": "purple",
        "rosa": "pink",
        "azul": "blue",
    }

    color_str = "white"
    color_info = str(info_liturgy[2]).lower()
    for pt_color, en_color in color_map.items():
        if pt_color in color_info:
            color_str = en_color
            break

    # Define cores do texto baseado na cor de fundo
    if color_str == "white":
        text_color_1 = "black"
        text_color_2 = "black"
    else:
        text_color_1 = "white"
        text_color_2 = color_str

    # Carrega fontes
    font_path = "./Resources/Fontes/arial_bold.TTF"
    try:
        font_main = ImageFont.truetype(font_path, 20, encoding="utf-8")
        font_psalm = ImageFont.truetype(font_path, 18, encoding="utf-8")
    except IOError:
        print("[AVISO] Fonte não encontrada, usando padrão do sistema.")
        font_main = ImageFont.load_default()
        font_psalm = font_main

    # Leituras principais e cards extras
    liturgy_slides = [
        ["Primeira Leitura", primeira_leitura, liturgical_time],
        ["Salmo", salmo, resposta_salmo],
        ["Segunda Leitura", segunda_leitura, liturgical_time],
        ["Evangelho", evangelho, liturgical_time],
    ]

    extra_cards = [
        "Canto de Entrada", "Ato Penitencial", "Glória a Deus",
        "Canto da Comunhão", "Rito do Ofertório", "Preces da Assembleia",
        "Liturgia Eucarística", "Profissão de Fé", "Preparação das Oferendas",
        "Oração Eucarística", "Rito da Comunhão",
    ]

    def center_text(draw, text: str, y_pos: int, font, img_width: int, color: str):
        """Centraliza horizontalmente um texto na imagem."""
        if not text:
            return
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x_pos = (img_width - text_width) / 2
        draw.text((x_pos, y_pos), text, font=font, fill=color)

    def process_image(file_name: str, top_text: str, bottom_text: str, is_psalm: bool = False):
        """Abre o fundo correto, escreve os textos e salva a imagem."""
        if file_name == "Segunda Leitura" and not top_text:
            return  # Pula segunda leitura se não houver

        bg_path = f"Resources/Imagens/{color_str}.png"
        if not os.path.exists(bg_path):
            print(f"[ERRO] Fundo não encontrado: {bg_path}")
            return

        try:
            image = Image.open(bg_path)
            draw = ImageDraw.Draw(image)
            img_w, img_h = image.size

            # Escreve o texto superior
            draw.text((165, 12), top_text, font=font_main, fill=text_color_1)

            y_bottom = 62

            if is_psalm:
                # Salmo: quebra o texto em duas linhas se muito longo
                y_bottom = 56
                bbox = draw.textbbox((0, 0), bottom_text, font=font_main)
                text_w = bbox[2] - bbox[0]

                if text_w > (img_w * 0.80):
                    mid_char = len(bottom_text) // 2
                    split_idx = bottom_text.rfind(" ", 0, mid_char)
                    if split_idx == -1:
                        split_idx = bottom_text.find(" ", mid_char)

                    if split_idx != -1:
                        line1 = bottom_text[:split_idx].strip()
                        line2 = bottom_text[split_idx:].strip()
                        center_text(draw, line1, 52, font_psalm, img_w, text_color_2)
                        center_text(draw, line2, 77, font_psalm, img_w, text_color_2)
                    else:
                        center_text(draw, bottom_text, y_bottom, font_psalm, img_w, text_color_2)
                else:
                    center_text(draw, bottom_text, y_bottom, font_main, img_w, text_color_2)
            else:
                center_text(draw, bottom_text, y_bottom, font_main, img_w, text_color_2)

            output_path = os.path.join(OUTPUT_DIR, f"{file_name}.png")
            image.save(output_path)
            image.close()
            print(f"[OK] {file_name}.png gerado.")

        except Exception as e:
            print(f"[ERRO] Falha ao processar {file_name}: {e}")

    # Gera imagens das leituras litúrgicas
    for slide in liturgy_slides:
        name, top, bottom = slide
        process_image(name, top, bottom, is_psalm=(name == "Salmo"))

    # Gera cards dos outros momentos da missa
    for card in extra_cards:
        process_image(card, card, liturgical_time)

    total = len(liturgy_slides) + len(extra_cards)
    print(f"\n[SUCESSO] {total} imagens geradas em './{OUTPUT_DIR}'")


# ------------------------------------------------------------------------------------------
# PARTE 3: Atualização do repositório GitHub
# ------------------------------------------------------------------------------------------

def push_to_github():
    """Executa git add, commit e push para atualizar o repositório."""
    print("\n[GIT] Atualizando repositório GitHub...")

    try:
        # Adiciona todas as alterações
        subprocess.run(["git", "add", "."], check=True)
        print("[GIT] git add . ✓")

        # Faz o commit (ignora erro se não houver mudanças)
        result = subprocess.run(
            ["git", "commit", "-m", "nsa-stream up"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("[GIT] git commit ✓")
        else:
            print("[GIT] Nada novo para commitar, seguindo com push...")

        # Envia para o remoto com force
        subprocess.run(["git", "push", "origin", "main", "--force"], check=True)
        print("[GIT] git push ✓")
        print("[GIT] Repositório atualizado com sucesso!")

    except subprocess.CalledProcessError as e:
        print(f"[ERRO GIT] Falha no comando Git: {e}")
        sys.exit(1)


# ------------------------------------------------------------------------------------------
# ENTRYPOINT
# ------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Gerador de Liturgia - NSA Stream")
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Quantos dias à frente buscar (0=hoje, 1=amanhã, 2=daqui 2 dias...)"
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Gera as imagens mas NÃO faz push para o GitHub"
    )
    args = parser.parse_args()

    print("=" * 50)
    print("   NSA STREAM - GERADOR DE LITURGIA")
    print("=" * 50)

    # 1. Busca liturgia na API
    api_data = fetch_liturgy(day_offset=args.offset)

    # 2. Converte dados da API para o formato interno
    info_liturgy = parse_liturgy_data(api_data)

    # 3. Gera as imagens
    print("\n[INFO] Gerando imagens...")
    create_images(info_liturgy)

    # 4. Atualiza GitHub (a menos que --no-push seja passado)
    if not args.no_push:
        push_to_github()
    else:
        print("\n[INFO] Push para GitHub pulado (--no-push ativo).")

    print("\n[DONE] Processo finalizado!")


if __name__ == "__main__":
    main()