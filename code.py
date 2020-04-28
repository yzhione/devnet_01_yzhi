#!python
# -*- coding: utf-8 -*-
''' Необходимо:1.
Собрать со всех устройств файлы конфигураций, сохранить их на диск,
используя имя устройства и текущую дату в составе имени файла.
2. Проверить на всех коммутаторах-включен ли протокол CDP и
есть ли упроцесса CDPна каждом из устройств данные о соседях.
3. Проверить, какой тип программного обеспечения(NPEили PE)* используется на устройствах
 исобрать со всех устройств данные о верси ииспользуемого ПО.
4. Настроить на всех устройствах timezone GMT+0, получение данных для синхронизациивремени
от источника во внутренней сети, предварительно проверив его доступность.
5. Вывести отчет в виде нескольких строк, каждая изкоторых имеет следующийформат,
близкий к такому:
Имя устройства -тип устройства -версия ПО -NPE/PE -CDP on/off, Xpeers-NTP in sync/not sync.

Пример:
ms-gw-01|ISR4451/K9|BLD_V154_3_S_XE313_THROTTLE_LATEST |PE|CDP is ON,5peers|Clock in Sync
ms-gw-02|ISR4451/K9|BLD_V154_3_S_XE313_THROTTLE_LATEST |NPE|CDP is ON,0 peers|Clock in Sync
'''

import os
from netmiko import ConnectHandler
import datetime
from pprint import pprint

### Peremennie ne stal otel'no vinosit', vse po prostetcki.
full_dic = {}           ### Sozdayou obshiy slovar', dlya obshego vyvoda v zadanie 5
MESTO='C:\\###ARCHIVE'  ### Prosto papka v korne gde vse lezhat' budet
device_ip_list = ['192.168.10.70','192.168.10.71','192.168.10.72']
device_cred = {
    "ip": '127.0.0.1',
    "username": "test",
    "password": "test",
    "device_type": "cisco_xe",
}

#0 Nastroika NTP server + Time zone (nastroika v nachale chtob dat' vremay na syncronizaciu)
def config_ntp_before_start(device_cred, device_ip_list):
    for ip in device_ip_list:
        device_cred["ip"] = ip
        with ConnectHandler(**device_cred) as ssh:
            check_ntp_server = ssh.send_command("ping vrf MNGMT 10.10.1.1")  ### Proveryaem cho server dostupen (prostoi icmp)
            if not 'Success rate is 0' in check_ntp_server:
                print(f"NTP dostupen s hosta {ip}")
                ssh.send_config_set(["clock timezone GMT +0", 'ntp server vrf MNGMT 10.10.1.1'])  ### Prosto otpravlyaem, konfig
            else:
                print(f"NTP ne otvechaet na ICMP s hosta {ip}")
        ssh.disconnect()

#1 Zadanie:
def mesto_s_archivom(MESTO):    #### ARCHIVE
    if not os.path.exists(MESTO): # Proverka est li takoe mesto
        os.mkdir(MESTO)
        print(f"Sozdana dir {MESTO} dlya archiva")

def get_date_time():
    date_time = datetime.datetime.now()
    return date_time.strftime("%Y_%m_%d-%H_%M_%S")

def safe_file_to_disk(safe_place,safe_name,safe_file):   #### Funciya sohraneniya konfigi
    safe_name_all = safe_name+'_'+str(get_date_time())   ### Imya faila = imya + data i vremya
    with open(f'{safe_place}/{safe_name_all}.txt','w',encoding='UTF8') as file:
        file.write(f"{safe_file}")
        print(f'OK, saved {safe_name}')

def get_show_run(device_cred,device_ip_list):   #### Zapros configuracii i otpravka ee v archive
    for ip in device_ip_list:
        full_dic[f'{ip}'] = {}
        device_cred["ip"] = ip
        with ConnectHandler(**device_cred) as ssh:
            safe_hostname = ssh.send_command("sh run | i hostname") ### berem imya ustroistva
            safe_hostname = safe_hostname.split()[1]                ### otdelyaem tolko imya
            full_dic[f'{ip}']['hostname'] = safe_hostname           ### Peremennaya HOSTNAME v slovar'
            # print(safe_hostname)
            safe_file = ssh.send_command("sh run")                  #### berem configuraciu
        ssh.disconnect()
        safe_file_to_disk(MESTO,f'{safe_hostname}',safe_file)       ### shlem v archivr

#4.1 Nastroika NTP server + Time zone (nastroika v nachale chtob dat' vremay na syncronizaciu)

#2 Zadanie:
def get_cdp(device_cred,device_ip_list):   ##### CDP proverka
    for ip in device_ip_list:
        # full_dic[f'{ip}'] = {} ### sozdaem ip key
        device_cred["ip"] = ip # postavlyaem ip v shablon
        with ConnectHandler(**device_cred) as ssh:
            sh_cdp_run = ssh.send_command("sh run all | i cdp run") ### Skonfigurirovan ili net cdp
            if sh_cdp_run == 'cdp run':                             ### esli da to >>>
                sh_cdp_nei = ssh.send_command("sh cdp neighbors deta | i Device")  ### proveryaem skolko sosedey
                # print(sh_cdp_nei)
                sh_cdp_nei = len(sh_cdp_nei.split('\n'))            ### Schitaem skolko sosedey
                full_dic[f"{ip}"]['cdp_run'] = f"CDP is ON, {sh_cdp_nei} peer's"    ### Peremennya CDP_RUN v slovar'
            else:
                full_dic[f"{ip}"]['cdp_run'] = 'CDP is OFF'         ### Esli net to >>> Peremennya CDP_RUN v slovar'
        ssh.disconnect()
    # print (full_dic)

# 3 Zadanie:
def proverka_ios(device_cred,device_ip_list):   #### IOS/NPE/Model'
    for ip in device_ip_list:
        # full_dic[f'{ip}'] = {} ### sozdaem ip key
        device_cred["ip"] = ip # postavlyaem ip v shablon
        with ConnectHandler(**device_cred) as ssh:
            #### IOS version proverka
            sh_version = ssh.send_command("sh version | i Cisco IOS Sof") ### show version
            sh_version = sh_version.split(',') ### example ['Cisco IOS Software', 'C2900 Software (C2900-UNIVERSALK9-M)', 'Version 15.5(2)T', 'RELEASE SOFTWARE (fc1)']
            full_dic[f"{ip}"]['version'] = sh_version[2] ### example 'Version 15.5(2)T', Peremennaya VERSION v slovar'
            full_dic[f"{ip}"]['soft'] = sh_version[1].split()[-1].strip('()') ### example C2900-UNIVERSALK9-M,  Peremennaya SOFT v slovar'
            #### teper_image_NPE/PE
            sh_version_npe = ssh.send_command("sh version | in System ima") ### System image file is "flash:/c3750-ipservicesk9-mz.122-55.SE9.bin"
            if 'npe' in sh_version_npe.split()[-1]: ### "flash:/c3750-ipservicesk9-mz.122-55.SE9.bin"
                full_dic[f"{ip}"]['type_ios'] = 'NPE'
            else:
                full_dic[f"{ip}"]['type_ios'] = 'PE'
            #### teper' model ustroistva
            sh_model = ssh.send_command("sh version | i bytes of m") ### cisco CSR1000V (VXE) processor (revision VXE) with 1985409K/3075K bytes of memory
            sh_model = sh_model.split()[1] ### CSR1000V
            full_dic[f"{ip}"]['model'] = f"{sh_model}" ### Peremennaya MODEL v slovar'
        ssh.disconnect()
    # print(full_dic)

# 4 Zadanie:
def check_ntp_status(device_cred,device_ip_list):
    for ip in device_ip_list:
        device_cred["ip"] = ip
        with ConnectHandler(**device_cred) as ssh:
            ntp_status = ssh.send_command("sh ntp status | i Cloc")  ### proveryaem status servera so sync
            full_dic[f"{ip}"]['ntp_status'] = ntp_status.lstrip().split(',')[0]  ### Peremennaya NTP_STATUS v slovar'
#5 otchet
def otchet(): ### Sobiraem vyvod iz slovarya v stroku  hostname > model > version > type_ios > cdp_run > ntp_status
    # pprint(full_dic)
    config_ntp_before_start(device_cred, device_ip_list)
    mesto_s_archivom(MESTO)
    get_show_run(device_cred,device_ip_list)
    get_cdp(device_cred, device_ip_list)
    proverka_ios(device_cred, device_ip_list)
    check_ntp_status(device_cred, device_ip_list)
    for i in full_dic.values():
        print(f"{i['hostname']}|{i['model']}|{i['version']}|{i['type_ios']}|{i['cdp_run']}|{i['ntp_status']}")

if __name__ == '__main__':
    #### proverka po otdelnosti
    # config_ntp_before_start(device_cred, device_ip_list1)
    # mesto_s_archivom(MESTO)
    # get_show_run(device_cred,device_ip_list1)
    # get_cdp(device_cred, device_ip_list1)
    # proverka_ios(device_cred, device_ip_list1)
    # check_ntp_status(device_cred, device_ip_list1)
    otchet()
