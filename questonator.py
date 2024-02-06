#beware: this script makes questionable use of global variables and employs very frail logic 
#to hold together all the data, so it's extremely prone to breaking from very minor changes 
#and can be very cryptic when debugging.
#it uses folders to temporarily store the images because it felt simpler to implement in
#a rush than dynamic dicts which kept breaking and ruining my lists. it's sub-optimal
#works though!

from config import numPaginas1, numPaginas2, aceitarDiscursivas, portugues, apenasDiscursivas, primeiro_link, segundo_link
from modulo_criar_lista import criar_pdf
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from bs4 import BeautifulSoup
import requests
import os
import time
import shutil

discursivas = []
falhou = []
solucoes = []
questoes_com_erro = []
erros = []

def main():
    
    ponteiro_numquestao = 0
    shutil.rmtree("imagens_extraidas_2")

    for i in range(numPaginas1):  
        url = formatar_URL(primeiro_link, i)
        driver = webdriver.Chrome()
        driver.maximize_window()
        driver.get(url)
        roubar_imagens(driver, ponteiro_numquestao)
        coletar_gabarito(driver, ponteiro_numquestao, url)
        ponteiro_numquestao += 5

    if segundo_link:
        for j in range(numPaginas2): 
            url2 = formatar_URL(segundo_link, j)
            driver = webdriver.Chrome()
            driver.maximize_window()
            driver.get(url2)
            roubar_imagens(url2, ponteiro_numquestao)
            coletar_gabarito(driver, url2, ponteiro_numquestao)
            ponteiro_numquestao += 5

    shutil.rmtree("imagens_modificadas_2")

    criar_pdf(discursivas, questoes_com_erro, solucoes)
    
def roubar_imagens(driver, ponteiro_numquestao):

    pasta_saida = "imagens_extraidas_2"
    
    os.makedirs(pasta_saida, exist_ok=True)

    driver.refresh()

    elementos = driver.find_elements(By.CSS_SELECTOR, ".divQuestao.center-block")
    print(len(elementos))

    print('Processando Imagens')
    for i, elemento in enumerate(elementos):

        numquestao = ponteiro_numquestao+i+1


        diretorio_div = os.path.join(pasta_saida, f"{ponteiro_numquestao+i+1}")

        os.makedirs(diretorio_div, exist_ok=True)

        if portugues:
            texto_button_id = f"formResultados:questoes:{i}:questao:basic"

            try:
                vertexto_button = driver.find_element(By.ID, texto_button_id)
            except Exception as e:
                time.sleep(1)
                try:
                    vertexto_button = driver.find_element(By.ID, texto_button_id)
                except Exception:
                    print(f"questão{numquestao} sem botao de texto")
                    vertexto_button = 0

            #exception handling excessivo temporariamente por questõse de debugging. alterar depois <3

            if vertexto_button != 0:
                try:
                    driver.execute_script("arguments[0].click()", vertexto_button)
                except Exception as e:
                    try:
                        time.sleep(2)
                        driver.execute_script("arguments[0].click()", vertexto_button)
                    except Exception as e:
                        print(f"ERRO: texto nao obtido questao {numquestao} (botao nao apertado)\n ERRO: {e}")

        time.sleep(2)

        try:
            imagens_questao = elemento.find_elements(By.TAG_NAME, "img")
        except Exception as e:
            print(e)
            roubar_imagens(driver, ponteiro_numquestao)
            return

        count = 0
        for img in imagens_questao:
            count+=1
            filename_imagem = str(count)
            caminho_imagem = os.path.join(diretorio_div, filename_imagem)

            response = requests.get(img.get_attribute("src"))
            with open(caminho_imagem, 'wb') as image_file:
                image_file.write(response.content)

    
def coletar_gabarito(driver, ponteiro_numquestao, url):

    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    divs = soup.find_all("div", class_="col-md-12")

    #placeholder
    respostas = ['N/A']*5
    num=0
    num_discursivas = len(discursivas)
    num_erros = len(questoes_com_erro)
    for i, div in enumerate(divs):

        numquestao = ponteiro_numquestao+i+1

        if num>4:
            break
        num +=1
        
        radio_button_id = f"formResultados:questoes:{i}:questao:options:0"
        
        try:
            radio_button = driver.find_element(By.ID, radio_button_id)
        except Exception as e:
            time.sleep(1)
            try:
                radio_button = driver.find_element(By.ID, radio_button_id)
            except Exception:
                print(f" questão {numquestao} discursiva")
                respostas[i] = "Discursiva"
                discursivas.append(numquestao)
                continue
        
        if radio_button:
            try:
                driver.execute_script("arguments[0].click()", radio_button)
            except Exception as e:
                try:
                    time.sleep(2)
                    driver.execute_script("arguments[0].click()", radio_button)
                except Exception as e:
                    print(f"ERRO: botão não clicado, questão {numquestao} (Stale Element)")
                    erros.append(f"Erro na questão {numquestao}: Stale element")
                    respostas[i] = "N/A"
                    questoes_com_erro.append(numquestao)
                    continue
            time.sleep(2)

        span_resposta_ids = [
            f"formResultados:questoes:{i}:questao:j_idt642:alertDescription",
            f"formResultados:questoes:{i}:questao:j_idt647:alertDescription",
            f"formResultados:questoes:{i}:questao:j_idt645:alertDescription",
            f"formResultados:questoes:{i}:questao:j_idt646:alertDescription",
            f"formResultados:questoes:{i}:questao:j_idt643:alertDescription",
            f"formResultados:questoes:{i}:questao:j_idt648:alertDescription",
            f"formResultados:questoes:{i}:questao:j_idt641:alertDescription",
            f"formResultados:questoes:{i}:questao:j_idt649:alertDescription",
            f"formResultados:questoes:{i}:questao:j_idt644:alertDescription",
            f"formResultados:questoes:{i}:questao:j_idt640:alertDescription",
        ]

        time.sleep(2)

        max_tenativas = len(span_resposta_ids)
        tentativas=0

        #very ugly. pode ser consertado com um for/else
        for span_resposta_id in span_resposta_ids:
            try:
                span_resposta = driver.find_element(By.ID, span_resposta_id)
                if "acertos" in span_resposta.text:
                    continue
                break  
            except Exception:
                tentativas += 1
                continue 

        if tentativas < max_tenativas:
            try:
                texto_resposta = span_resposta.text.split("Resposta:")[1].strip() # type: ignore
                print(f"questao {numquestao}: resposta encontrada")
            except IndexError:
                print(f"ERRO: indexerror na questao {numquestao}")
                erros.append(f"Questão {numquestao} IndexError")
                questoes_com_erro.append(numquestao)
                respostas[i] = "IndexError"
                continue
            texto_resposta = texto_resposta[:2]
            respostas[i] = texto_resposta
        else:
            print(f'Resposta não encontrada')
            respostas[i] = "N/A"
            questoes_com_erro.append(numquestao)
            continue

    print()
    discursivas_a_somar = 0
    num_erros_novos = 0
    for g in range(5):
        global solucoes
        if apenasDiscursivas:
            if respostas[g] == "Discursiva":
                solucoes.append(f"Questão {ponteiro_numquestao+g+1-(num_erros_novos+num_erros)} : {respostas[g]}") 
            else:
                num_erros_novos +=1
                continue
        elif aceitarDiscursivas:
            if respostas[g] != "N/A":
                solucoes.append(f"Questão {ponteiro_numquestao+g+1-(num_erros_novos+num_erros)} : {respostas[g]}")      
            else:
                num_erros_novos +=1
                continue
        else:
            if respostas[g] != "Discursiva" and respostas[g] != "N/A":
                solucoes.append(f"Questão {ponteiro_numquestao+g+1-(discursivas_a_somar+num_discursivas+num_erros)} : {respostas[g]}")      
            else:
                discursivas_a_somar += 1

def formatar_URL(url, page):
    try:
        parsed_URL = urlparse(url)
        query_params = parse_qs(parsed_URL.query)
        query_params['page'] = [str(page)]
        nova_string_query = urlencode(query_params, doseq=True)
        url_formatado = urlunparse((parsed_URL.scheme, parsed_URL.netloc, parsed_URL.path,
                                parsed_URL.params, nova_string_query, parsed_URL.fragment))
        return url_formatado

    except Exception as e:
        print(e)
        print("ERRO: Link deve ser tirado da segunda pagina ou posterior para conter o parametro '&page=XYZ'")
        quit()


if __name__ == '__main__':
    main()
    print(f"{len(erros)} questões perdidas: \n {erros}")
