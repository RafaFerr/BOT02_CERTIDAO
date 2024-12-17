import logging
import holidays
import holidays.countries
import os
import pandas as pd
import psutil
import slack.errors
from botcity.core import DesktopBot
from botcity.plugins.files import BotFilesPlugin
from botcity.plugins.slack import BotSlackPlugin
from botcity.web import WebBot, Browser, By
from botcity.web.browsers.chrome import default_options
from credencial import segredos
from datetime import date, datetime
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager


def main():
    data_atual_com_traco = datetime.today().date().strftime("%d-%m-%Y")
    agora = datetime.now().strftime('%d-%m-%Y_%H-%M')
    logging.basicConfig(level=logging.INFO,
                        filename=fr'\\192.168.0.5\COMPARTILHADA\CONTROLE_CNIB\13_log\bot02_certidao\log_certidao_onr_{data_atual_com_traco}.log',
                        format="%(asctime)s $ %(message)s", datefmt='%d/%m/%Y %H:%M:%S', encoding='utf-8')

    desktop_bot = DesktopBot()
    files = BotFilesPlugin()
    webbot = WebBot()
    logging.info('-----BOT IMPORT CERTIDAO ONR Iniciado')
    try:
        token_slack = segredos.get('segredo_slack')
        channel_slack = segredos.get('segredo_slack_channel')
        client = BotSlackPlugin(slack_token=token_slack, channel=channel_slack)
        logging.info('CONEXÃO OK COM API SLACK')
    except slack.errors.SlackApiError as e:
        logging.info(fr'FALHA NA CONEXÃO COM SLACK {e}')
        while 'The request to the Slack API failed' in e:
            logging.info(fr'TENTATIVA DE NOVA CONEXÃO')
            token_slack = segredos.get('segredo_slack')
            channel_slack = segredos.get('segredo_slack_channel')
            client = BotSlackPlugin(slack_token=token_slack, channel=channel_slack)
        else:
            print('CONEXÃO OK COM API SLACK')
            token_slack = segredos.get('segredo_slack')
            channel_slack = segredos.get('segredo_slack_channel')
            client = BotSlackPlugin(slack_token=token_slack, channel=channel_slack)
            logging.info('CONEXÃO OK COM API SLACK')
            pass

    # Validar Feriado

    br_holidays = holidays.Brazil()
    today = datetime.today()
    if today in br_holidays:
        logging.info(f"Hoje é feriado: {br_holidays[today]}. A operação não pode continuar.")
        logging.info('-----BOT CERTIDAO ONR FINALIZADO')
        return

    # VARIAVEIS DE COMUNICACAO

    user_register = segredos.get('segredo_userregister')
    user_register2 = segredos.get('segredo_userregister2')
    senha_register = segredos.get('segredo_senharegister')
    token = segredos.get('segredo_tokenA3')

    #FECHANDO INSTANCIAS DO REGISTER
    for i in range(4):
        try:
            if desktop_bot.find_process('sqlreg.exe'):
                desktop_bot.wait(3000)
                register = desktop_bot.find_process('sqlreg.exe')
                logging.info(fr'PROCESSO {register} ENCONTRADO')
                print('aberto')
                desktop_bot.terminate_process(register)
                print('fechando')
                logging.info(fr'PROCESSO {register} FINALIZADO')
            else:
                logging.info(fr'PROCESSO NÃO ENCONTRADO')
                pass
        except psutil.AccessDenied as e:
            logging.info(fr'Falha ao encerrar processo{e}')
            pass

    desktop_bot.type_keys(['win', 'd'])

    def acessar_site_oficioeletronico():
        logging.info(fr'INICIO DO PROCESSO ACESSAR SITE')
        webbot.headless = False
        webbot.browser = Browser.CHROME
        download_folder_path = r'\\safira\COMPARTILHADA\CONTROLE_CNIB\10_arquivos_zip'
        logging.info(fr'PASTA {download_folder_path} DEFINIDA')
        try:
            webbot.driver_path = ChromeDriverManager().install()
            logging.info('INSTANCIA WEBDRIVER MANAGER')
        except:
            webbot.driver_path = r"\\SAFIRA\COMPARTILHADA\CONTROLE_CNIB\12_extensoes\chromedriver.exe"
            logging.info('INSTANCIA WEBDRIVER LOCAL')
        extension_path = r"\\Safira\COMPARTILHADA\CONTROLE_CNIB\12_extensoes\webpki-chrome-ext.crx"
        logging.info(fr'{extension_path} CARREGADA')
        def_options = default_options()
        prefs = {
            'download.prompt_for_download': False,
            "download.default_directory": download_folder_path,
            "savefile.default_directory": download_folder_path,
            'safebrowsing.enabled': True
        }
        def_options.add_experimental_option("prefs", prefs)
        def_options.add_extension(extension_path)
        webbot.options = def_options

        try:
            webbot.browse('https://oficioeletronico.com.br/')
            webbot.maximize_window()
            logging.info('PAGINA CARREGADA')
            desktop_bot.wait(2000)
            if webbot.find("alerta", matching=0.97, waiting_time=5000):
                desktop_bot.get_screenshot(
                    fr"\\Safira\COMPARTILHADA\CONTROLE_CNIB\14_prints\bot02_certidao\alerta_{agora}")
                webbot.click_relative(315, 8)
                logging.info('MENSAGEM DE ALERTA')
            else:
                pass
        except WebDriverException as e1:
            client.send_simple_message(text=fr'{e1}')
            print(f'Erro {e1}')
            logging.info(e)
            webbot.stop_browser()
            webbot.wait(4000)
            acessar_site_oficioeletronico()
        webbot.wait(2000)
        # if webbot.find_element('a.cc-btn:nth-child(1)',by=By.CSS_SELECTOR):
        #     permitir_cookies = webbot.find_element('a.cc-btn:nth-child(1)', by=By.CSS_SELECTOR)
        #     permitir_cookies.click()
        #     print('CLICAR PERMITIR COOKIES')
        # else:
        #     print('SEM COOKIES')
        #     pass
        # webbot.wait(2000)

        bt_autenticar = webbot.find_element('#btnCallLogin', by=By.CSS_SELECTOR)
        bt_autenticar.click()
        logging.info('BTN AUTENTICAR')
        desktop_bot.wait(1500)
        certificado = webbot.find_element('#certificateSelect > option:nth-child(1)', by=By.CSS_SELECTOR)
        certificado.click()

        desktop_bot.wait(1500)
        selecionar_certificado = webbot.find_element('#signInButton', by=By.CSS_SELECTOR)
        selecionar_certificado.click()
        logging.info('CERTIFICADO SELECIONADO')
        desktop_bot.wait(1500)

        while desktop_bot.find('erro', waiting_time=5000):
            print('ERRO CERTIFICADO')
            logging.info('ERRO CERTIFICADO')
            desktop_bot.enter()
            desktop_bot.key_f5()
            bt_autenticar = webbot.find_element('#btnCallLogin', by=By.CSS_SELECTOR)
            bt_autenticar.click()
            desktop_bot.wait(1500)
            certificado = webbot.find_element('#certificateSelect > option:nth-child(1)', by=By.CSS_SELECTOR)
            certificado.click()
            desktop_bot.wait(1500)
            selecionar_certificado = webbot.find_element('#signInButton', by=By.CSS_SELECTOR)
            selecionar_certificado.click()
            desktop_bot.wait(1500)
        else:
            pass
        webbot.wait(2000)
        desktop_bot.click_at(591, 343)
        desktop_bot.tab(presses=2)
        desktop_bot.enter()

        desktop_bot.find("pin", matching=0.97, waiting_time=10000)
        desktop_bot.wait(2000)
        desktop_bot.kb_type(text=token)
        logging.info('DIGITADO TOKEN')
        desktop_bot.enter()

        if webbot.find("falha_acesso", matching=0.97, waiting_time=2000):
            desktop_bot.wait(2000)
            webbot.stop_browser()
            logging.info('FALHA ACESSO')
            webbot.browse('https://oficioeletronico.com.br/')
            webbot.maximize_window()
            webbot.wait(2000)
            acesso = webbot.find_element('#btnCallLogin', by=By.CSS_SELECTOR)
            acesso.click()
            certificado = webbot.find_element('#certificateSelect > option:nth-child(3)', by=By.CSS_SELECTOR)
            certificado.click()
            certificado_selecionado = webbot.find_element('#signInButton', by=By.CSS_SELECTOR)
            certificado_selecionado.click()
            webbot.wait(2000)

            desktop_bot.click_at(591, 343)
            desktop_bot.tab(presses=2)
            desktop_bot.enter()

            desktop_bot.find("pin", matching=0.97, waiting_time=10000)
            desktop_bot.wait(2000)
            desktop_bot.kb_type(text=token)
            desktop_bot.enter()
        else:
            pass
        print('acessou')

    acessar_site_oficioeletronico()
    response_message = client.send_simple_message(text='OFICIO ELETRONICO ACESSADO - CERTIDAO')

    webbot.wait(2000)

    if webbot.find_element('#popupDivTermo', by=By.CSS_SELECTOR):
        btFecharPopup = webbot.find_element('#divModalMSGCTP > div > div > div.d-flex.justify-content-end > button:nth-child(2)',by=By.CSS_SELECTOR)
        btFecharPopup.click()
    else:
        pass

    if desktop_bot.find("pendentes", matching=0.97, waiting_time=2000):
        print('achou pendentes')
        logging.info('ALERTA PENDENTES')
        desktop_bot.click_relative(-174, 217)
    elif desktop_bot.find("comunicado2", matching=0.97, waiting_time=10000):
        print('achou comunicado')
        logging.info('ALERTA COMUNICADO')
        desktop_bot.click_relative(368, -28)
    elif webbot.find_element('//*[@id="popupComunicado"]', by=By.XPATH):
        logging.info('CERTIFICADO SELECIONADO')
        print('achou popup')
        if webbot.find_element('#popupComunicado > div > div > div.modal-header > button', by=By.CSS_SELECTOR):
            botao_fechar = webbot.find_element('#popupComunicado > div > div > div.modal-header > button',
                                               by=By.CSS_SELECTOR)
            try:
                botao_fechar.click()
            except:
                pass
        else:
            pass
    else:
        print('nao achou nada')
        pass

    certidao_emitir = webbot.find_element(
        '#tabledash > tbody:nth-child(2) > tr:nth-child(1) > td:nth-child(1) > a:nth-child(1)', by=By.CSS_SELECTOR,
        waiting_time=60000)
    certidao_emitir.click()
    desktop_bot.wait(1500)
    logging.info('CERTIDOES A EMITIR')
    if desktop_bot.find("pendentes", matching=0.97, waiting_time=2000):
        desktop_bot.click_relative(-174, 217)
        logging.info('ALERTA PENDENTES')
    else:
        logging.info('SEM PENDENTES')
        pass
    desktop_bot.find("cert_emitir", matching=0.97, waiting_time=15000)
    for i in range(2):
        print(i)
        if i == 0:
            certidao_emaberto = webbot.find_element('#filterStatus > option:nth-child(5)', by=By.CSS_SELECTOR)
            certidao_emaberto.click()
            logging.info('CERTIDOES EM ABERTO')
            print('CERTIDAO EM ABERTO')
            desktop_bot.wait(1500)
            bt_filtrar = webbot.find_element('/html/body/section/div[1]/div/div[2]/ul/li[1]/button', by=By.XPATH)
            try:
                bt_filtrar.click()
                logging.info('FILTRO CERTIDOES EM ABERTO')
                print('entrou no try do bt click')
                while webbot.find_element('//*[@id="loading"]', by=By.XPATH):
                    print('loading existe')
                    logging.info('AGUARDANDO')
                else:
                    print('não existe')
            except:
                print('entrou no except')
                desktop_bot.key_f5()
                logging.info('RECARREGANDO PAGINA')
                bt_filtrar = webbot.find_element('/html/body/section/div[1]/div/div[2]/ul/li[1]/button', by=By.XPATH)
                bt_filtrar.click()
                print('saiu do except')
                while webbot.find_element('//*[@id="loading"]', by=By.XPATH):
                    print('loading existe')
                    logging.info('AGUARDANDO')
                else:
                    print('não existe')
            desktop_bot.wait(2000)
            bt_exportar = webbot.find_element('/html/body/section/div[1]/div/div[2]/ul/li[3]/button', by=By.XPATH)
            bt_exportar.click()
            webbot.wait(1000)
            logging.info('CLQ BOTAO EXPORTAR EM ABERTO')
            dialogo = webbot.get_js_dialog()
            try:
                texto = dialogo.text
                if 'Não foram localizados registros para exportação!' in texto:
                    logging.info(fr'{texto} - NENHUMA CERTIDAO EM ABERTO')
                    print('achou')
                    dialogo.dismiss()
                    webbot.wait(2000)
                    continue
                else:
                    print('sem')
                    logging.info('CERTIDOES EM ABERTO ENCONTRADAS')
                    pass
            except:
                print('passou do try')
                pass

            while webbot.find_element('//*[@id="loading"]', by=By.XPATH):
                print('loading existe')
            else:
                print('não existe')
            print('CLICAR EXPORTAR')
            if desktop_bot.find('erro', waiting_time=3000):
                logging.info('ERRO')
                desktop_bot.enter()
                desktop_bot.wait(2000)
                continue
            else:
                desktop_bot.find("bt_download", matching=0.97, waiting_time=30000)
                bt_download = webbot.find_element('#btnDownloadXML', by=By.CSS_SELECTOR)
                bt_download.click()
                logging.info('CLQ BOTAO DOWNLOAD')
                desktop_bot.click_at(866, 222)
                logging.info('AGUARDANDO ARQUIVO')
                webbot.wait_for_new_file(path=webbot.download_folder_path, file_extension=".zip", timeout=10000)
                logging.info('ARQUIVO BAIXADO')
                print('DOWNLOAD CERTIDAO EM ABERTO')
                desktop_bot.key_esc()
        else:
            certidao_em_processamento = webbot.find_element('#filterStatus > option:nth-child(6)', by=By.CSS_SELECTOR)
            certidao_em_processamento.click()
            logging.info('CERTIDOES EM PROCESSAMENTO')
            print('CERTIDAO EM PROCESSAMENTO')
            desktop_bot.wait(1500)

            bt_filtrar = webbot.find_element('/html/body/section/div[1]/div/div[2]/ul/li[1]/button', by=By.XPATH)
            bt_filtrar.click()
            logging.info('BTN FILTRAR')

            while webbot.find_element('//*[@id="loading"]', by=By.XPATH):
                print('loading existe')
                logging.info('AGUARDANDO')
            else:
                print('não existe')

            print('CLICAR EM FILTRAR')
            # webbot.wait(7000)

            bt_exportar = webbot.find_element('/html/body/section/div[1]/div/div[2]/ul/li[3]/button', by=By.XPATH)
            bt_exportar.click()
            logging.info('BTN EXPORTAR')
            webbot.wait(1000)
            dialogo = webbot.get_js_dialog()
            try:
                texto = dialogo.text
                if 'Não foram localizados registros para exportação!' in texto:
                    print('achou')
                    logging.info(fr'{texto} - NENHUMA ORDEM EM PROCESSAMENTO ENCONTRADA')
                    dialogo.dismiss()
                    webbot.wait(2000)
                    break
                else:
                    print('sem')
                    pass
            except:
                print('passou do try')
                pass

            while webbot.find_element('//*[@id="loading"]', by=By.XPATH):
                print('loading existe')
                logging.info('AGUARDANDO')
            else:
                print('não existe')
            print('CLICAR EXPORTAR')

            desktop_bot.find("bt_download", matching=0.97, waiting_time=30000)

            bt_download = webbot.find_element('#btnDownloadXML', by=By.CSS_SELECTOR)
            bt_download.click()
            desktop_bot.click_at(866, 222)
            logging.info('AGUARDANDO ARQUIVO')
            webbot.wait_for_new_file(path=webbot.download_folder_path, file_extension=".zip", timeout=10000)
            logging.info('ARQUIVO BAIXADO')
            print('DOWNLOAD CERTIDAO EM PROCESSAMENTO')
            desktop_bot.key_esc()

    webbot.stop_browser()
    logging.info('FECHANDO NAVEGADOR')

    app_path = r"C:\Escriba\Register3\sqlreg.exe"
    # app_path = r"C:\EscribaTeste\Register3\sqlreg.exe"
    desktop_bot.execute(app_path)
    logging.info('EXECUTANDO REGISTER')
    print('ACESSANDO REGISTER')
    # AGUARDANDO TELA DE LOGIN
    desktop_bot.find('acessar_register', matching=0.97, waiting_time=35000)
    print('AGUARDANDO LOGIN')

    if not desktop_bot.find("campo_nome", matching=0.97, waiting_time=10000):
        not_found("campo_nome")
    desktop_bot.delete()
    desktop_bot.paste(user_register)
    desktop_bot.enter()
    desktop_bot.paste(senha_register)
    desktop_bot.enter()
    print('ACESSO OK')
    logging.info('LOGIN REALIZADO')

    if desktop_bot.find("atencao", matching=0.97, waiting_time=3000):
        logging.info('ERRO NO LOGIN')
        print('erro no acesso tentativa nova')
        desktop_bot.enter()
        desktop_bot.wait(1000)
        desktop_bot.execute(app_path)
        desktop_bot.find('acessar_register', matching=0.97, waiting_time=35000)
        if not desktop_bot.find("campo_nome", matching=0.97, waiting_time=10000):
            not_found("campo_nome")
        desktop_bot.delete()
        desktop_bot.paste(user_register2)
        logging.info(fr'LOGIN COM {user_register2}')
        desktop_bot.enter()
        desktop_bot.paste(senha_register)
        desktop_bot.enter()
        print('LOGIN NO REGISTER REALIZADO')
    elif desktop_bot.find('error', matching=0.97, waiting_time=3000):
        logging.info('ERRO NO LOGIN 2')
        print('erro no usuario ou senha')
        try:
            print('try')
            desktop_bot.enter()
            desktop_bot.wait(1000)
            desktop_bot.delete()
            desktop_bot.paste(user_register)
            desktop_bot.enter()
            desktop_bot.paste(senha_register)
            desktop_bot.enter()
            if not desktop_bot.find("cadastro", matching=0.97, waiting_time=10000):
                conta = 1 / 0  # FORÇAR ERRO PARA PULAR PARA O EXCEPT
                logging.info('FORÇANDO SAIDA PARA EXCEPT')
        except:
            print('except')
            desktop_bot.enter()
            desktop_bot.wait(1000)
            desktop_bot.delete()
            desktop_bot.paste(user_register2)
            desktop_bot.enter()
            desktop_bot.paste(senha_register)
            desktop_bot.enter()
    else:
        pass
    if desktop_bot.find('cadastro', waiting_time=20000):
        # Abrir tela de cadastro de indisponibilidade
        desktop_bot.type_keys(['alt', 'e', 'c'])
        desktop_bot.wait(1200)
    desktop_bot.wait(2000)
    logging.info('ACESSADO RECEPCAO')
    arquivos_zip = files.get_all_file_paths(r'\\safira\COMPARTILHADA\CONTROLE_CNIB\10_arquivos_zip')
    for zipado in arquivos_zip:
        files.unzip_all(zipado,
                        destination_folder=r'\\safira\COMPARTILHADA\CONTROLE_CNIB\11_arquivos_extraidos')
        logging.info(fr'{zipado} - EXTRAIDO')
    desktop_bot.wait(2000)
    desktop_bot.find("bt_onr", waiting_time=10000)
    print('botao onr acionado')
    if not desktop_bot.find("bt_onr", matching=0.97, waiting_time=10000):
        not_found("bt_onr")
    desktop_bot.click()
    logging.info('BTN ONR ACIONADO')
    desktop_bot.type_down()
    desktop_bot.enter()
    desktop_bot.wait(2000)
    print('antes do for')
    arquivos_extraidos = files.get_all_file_paths(r'\\safira\COMPARTILHADA\CONTROLE_CNIB\11_arquivos_extraidos')
    for xml in arquivos_extraidos:
        print(xml)
        logging.info(fr'CARREGADO O ARQUIVO {xml}')
        print('entrou no for')
        desktop_bot.paste(xml)
        print('copiado')
        desktop_bot.wait(2000)

        desktop_bot.type_keys(['shift', 'tab'])
        desktop_bot.enter()
        print('importando')
        while desktop_bot.find("aguardar", matching=0.97, waiting_time=2000):
            desktop_bot.wait(2000)
            print('aguardando importar')
        else:
            if desktop_bot.find('atencao'):
                desktop_bot.wait(2000)
                desktop_bot.enter()
                if not desktop_bot.find("campo_arisp", matching=0.97, waiting_time=5000):
                    not_found("campo_arisp")
                desktop_bot.click_relative(-1, 68)
                desktop_bot.control_a()
                desktop_bot.delete()
            else:
                if not desktop_bot.find("campo_arisp", matching=0.97, waiting_time=5000):
                    not_found("campo_arisp")
                desktop_bot.click_relative(-1, 68)
                desktop_bot.control_a()
                desktop_bot.delete()
    print('saiu do for')

    if not desktop_bot.find("bt_fechar", matching=0.97, waiting_time=10000):
        not_found("bt_fechar")
    desktop_bot.click()
    enviar_chat = 1
    print('fechou a tela')
    sistema = desktop_bot.find_process('sqlreg.exe')
    if desktop_bot.find_process('sqlreg.exe'):
        desktop_bot.terminate_process(sistema)
        print('encerrou o register')
        logging.info('REGISTER ENCERRADO')
    else:
        pass

    if enviar_chat == 1:
        logging.info('ENVIAR CHAT CERTIDOES PROTOCOLADAS')
        contatos = pd.read_excel(r"\\SAFIRA\COMPARTILHADA\CONTROLE_CNIB\8_contato\contatos.xlsx", 'certidao',
                                 keep_default_na=False)
        total_contatos = len(contatos['NOME'])

        desktop_bot.execute(r"C:\Program Files\Spark\Spark.exe")
        desktop_bot.find('spark', waiting_time=10000)
        desktop_bot.wait(1000)
        desktop_bot.type_keys(['alt', 'l'])
        print('ABRINDO SPARK')
        if desktop_bot.find("online", matching=0.97, waiting_time=10000):
            logging.info('SPARK ONLINE')
            for i in range(total_contatos):
                desktop_bot.wait(1000)
                desktop_bot.control_f()
                desktop_bot.wait(2000)
                nome = str(contatos['NOME'][i])
                desktop_bot.kb_type(text=nome)
                desktop_bot.enter()
                desktop_bot.wait(1000)
                desktop_bot.kb_type(
                    text=f'Serviço de Automação 3º Ofício de Registro de Imóveis - Importacação ONR - Pedidos Importados')
                desktop_bot.enter()
            print(f'MENSAGENS ENVIADAS COM ORDENS PROTOCOLADAS')
            desktop_bot.wait(1000)
            process_spark = desktop_bot.find_process("Spark.exe")
            desktop_bot.terminate_process(process_spark)
            logging.info('SPARK ENCERRADO')
            process_register = desktop_bot.find_process("sqlreg.exe")
            try:
                desktop_bot.terminate_process(process_register)
            except:
                logging.info('REGISTER NAO FOI FECHADO')
                pass
    else:
        logging.info('SEM CERTIDOES')
        contatos = pd.read_excel(r"\\SAFIRA\COMPARTILHADA\CONTROLE_CNIB\8_contato\contatos.xlsx", 'certidao',
                                 keep_default_na=False)
        total_contatos = len(contatos['NOME'])
        # ROTINA PARA ENVIAR MENSAGEM PARA O SETOR RESPONSAVEL POR SELAR E IMPRIMIR
        desktop_bot.execute(r"C:\Program Files\Spark\Spark.exe")
        desktop_bot.find('spark', waiting_time=10000)
        desktop_bot.wait(1000)
        desktop_bot.type_keys(['alt', 'l'])
        print('ABRINDO SPARK')
        if desktop_bot.find("online", matching=0.97, waiting_time=10000):
            for i in range(total_contatos):
                desktop_bot.wait(1000)
                desktop_bot.control_f()
                desktop_bot.wait(2000)
                nome = str(contatos['NOME'][i])
                desktop_bot.kb_type(text=nome)
                desktop_bot.enter()
                desktop_bot.wait(1000)
                desktop_bot.kb_type(
                    text=f'Serviço de Automação 3º Ofício de Registro de Imóveis - Importacação ONR - Nenhum pedido foi encontrado e importado')
                desktop_bot.enter()
            print(f'MENSAGENS ENVIADAS COM ORDENS PROTOCOLADAS')
            desktop_bot.wait(1000)
            process_spark = desktop_bot.find_process("Spark.exe")
            desktop_bot.terminate_process(process_spark)
            process_register = desktop_bot.find_process("sqlreg.exe")
            desktop_bot.terminate_process(process_register)

    print('apagando arquivos')

    arquivos_zip = files.get_all_file_paths(r'\\safira\COMPARTILHADA\CONTROLE_CNIB\10_arquivos_zip')
    for item in arquivos_zip:
        os.remove(item)
    logging.info(fr'ARQUIVOS DA PASTA {arquivos_zip} DELETADOS')
    arquivos_xml = files.get_all_file_paths(r'\\safira\COMPARTILHADA\CONTROLE_CNIB\11_arquivos_extraidos')
    for item in arquivos_xml:
        os.remove(item)
    logging.info(fr'ARQUIVOS DA PASTA {arquivos_xml} DELETADOS')
    response_message = client.send_simple_message(text='FINALIZADO CERTIDAO')


def not_found(label):
    print(f"Element not found: {label}")


if __name__ == '__main__':
    main()
